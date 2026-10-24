#!/usr/bin/env python3
"""
orb_walkforward.py  --  honest walk-forward tester for NAS100 (US100) intraday strategies.

Pipeline:  M1 bars (NY local time)  ->  trading days (17:00 prev day .. 16:59)  ->  strategy = f(day, params) -> <=1 trade
           -> common bar-by-bar simulator (stop / take / time exit, costs)  ->  metrics  ->  walk-forward
           (parameters picked on IS by profit factor, OOS looked at once)  ->  windows table + OOS trades + summary.

Strategies (--strategy):
  orb          Opening range breakout, range 5/15/30 min, entry on breakout (stop orders) or in the direction of the
               opening range bar (Zarattini & Aziz 2023), stop = other side of range or 0.1..1.0 ATR(14,D1),
               optional 3R take, time exit 15:55 NY.
  im           Intraday momentum (Gao, Han, Li, Zhou 2018): sign of first 30/60 min (from open or prev close)
               -> same-direction position from 15:00/15:30 to 15:55, ATR stop 0.25/0.5/1.0.
  asian        Asian-range sweep + M5 rejection (19:00-02:00 range, 02:00-11:00 sweep window), RSI(14,M5) filter on/off,
               stop beyond sweep extreme +0.1 ATR(D1), take 2R/3R, exit 15:55, one trade/day.
  vwap         Reversion to session VWAP: |close - VWAP| > k ATR(14,M15) in first 2h -> fade, stop 1.0/1.5 ATR, take = VWAP.
  gap          Opening gap > g% vs previous 16:00 close: continuation or fade, ATR stop, optional gap-fill / 2R take.
  lasthour     15:00 entry in the direction of (15:00 - 09:30 open), ATR stop, exit 15:55.
  orb_vol      First-hour range breakout with activity filter (sum of M1 ranges > 1.5x 20-day median; data has no volume).
  asian_limit  Asian sweep without RSI, limit entry at the midpoint of the rejection bar.

Costs (every backtest): spread 2.0 pts round trip + slippage 0.5 pts per side = 3.0 pts per trade (--spread/--slip).
Sizing for metrics: fixed risk per trade (--risk-pct of --account), non compounding, so every trade is measured in R.
"""
import argparse, json, os, sys, glob, time, itertools, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
def K(hh, mm=0):            # minutes since 17:00 NY of the previous calendar day
    return (hh * 60 + mm - 17 * 60) % 1440
OPEN_K, EXIT_K, CLOSE_K = K(9, 30), K(15, 55), K(16, 0)

# ----------------------------------------------------------------------------- data
class Data:
    def __init__(self, df, start=None, end=None, warmup_days=40):
        df = df.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
        ts = df.ts.values.astype("datetime64[m]")
        tod = (ts - ts.astype("datetime64[D]")).astype("timedelta64[m]").astype(np.int64)
        self.k = ((tod - 17 * 60) % 1440).astype(np.int64)
        self.day = (ts + np.timedelta64(7 * 60, "m")).astype("datetime64[D]")
        self.ts, self.o, self.h, self.l, self.c = ts, df.open.values.astype(float), df.high.values.astype(float), df.low.values.astype(float), df.close.values.astype(float)
        self.days, self.starts = np.unique(self.day, return_index=True)
        self.ends = np.append(self.starts[1:], len(ts))
        nd = len(self.days)
        # ---- daily stats, ATR(14,D1) simple MA of TR, previous-day value
        H = np.array([self.h[s:e].max() for s, e in zip(self.starts, self.ends)])
        L = np.array([self.l[s:e].min() for s, e in zip(self.starts, self.ends)])
        C = np.array([self.c[e - 1] for e in self.ends])
        Cp = np.r_[np.nan, C[:-1]]
        tr = np.nanmax(np.c_[H - L, np.abs(H - Cp), np.abs(L - Cp)], axis=1)
        atr = pd.Series(tr).rolling(14).mean().values
        self.atr_d1 = np.r_[np.nan, atr[:-1]]                     # known at the start of the day
        # ---- session close (last bar before 16:00) and validity
        self.sess_close = np.full(nd, np.nan); self.valid = np.zeros(nd, bool); self.valid_asia = np.zeros(nd, bool)
        self.act1h = np.full(nd, np.nan)
        for d, (s, e) in enumerate(zip(self.starts, self.ends)):
            k = self.k[s:e]
            i0 = np.searchsorted(k, OPEN_K); i1 = np.searchsorted(k, CLOSE_K)
            if i1 > i0: self.sess_close[d] = self.c[s + i1 - 1]
            nsess = i1 - i0
            if nsess >= 380 and k[i0] == OPEN_K and np.any(k[i0:i1] == EXIT_K) and (np.diff(k[i0:i1]).max() <= 5):
                self.valid[d] = True
                j1 = np.searchsorted(k, K(10, 30))
                self.act1h[d] = (self.h[s + i0:s + j1] - self.l[s + i0:s + j1]).sum()
            ia0 = np.searchsorted(k, K(19, 0)); ia1 = np.searchsorted(k, K(2, 0)); iw1 = np.searchsorted(k, K(11, 0))
            if self.valid[d] and (ia1 - ia0) >= 300 and (iw1 - ia1) >= 0.9 * (K(11, 0) - K(2, 0)):
                self.valid_asia[d] = True
        self.prev_sess_close = np.r_[np.nan, self.sess_close[:-1]]
        self.vwap = np.full(len(ts), np.nan)                       # equal-weight session "VWAP" from 09:30 (no volume in data)
        for d in np.nonzero(self.valid)[0]:
            i0 = self.exact(d, OPEN_K); i1 = self.at(d, CLOSE_K) or self.ends[d]
            tp_ = (self.h[i0:i1] + self.l[i0:i1] + self.c[i0:i1]) / 3
            self.vwap[i0:i1] = np.cumsum(tp_) / np.arange(1, len(tp_) + 1)
        self.act1h_med20 = pd.Series(self.act1h).rolling(20, min_periods=15).median().shift(1).values
        # ---- M5 series with RSI(14) Wilder, and M15 ATR(14) simple
        self.m5_id, self.m5_first = self._buckets(5)
        c5 = self.c[np.append(self.m5_first[1:], len(ts)) - 1]
        self.rsi5 = rsi_wilder(c5, 14)                            # value of the completed M5 bar j
        self.m15_id, self.m15_first = self._buckets(15)
        f15 = self.m15_first; e15 = np.append(f15[1:], len(ts))
        h15 = np.maximum.reduceat(self.h, f15); l15 = np.minimum.reduceat(self.l, f15); c15 = self.c[e15 - 1]
        cp15 = np.r_[np.nan, c15[:-1]]
        tr15 = np.nanmax(np.c_[h15 - l15, np.abs(h15 - cp15), np.abs(l15 - cp15)], axis=1)
        a15 = pd.Series(tr15).rolling(14).mean().values
        self.atr15_prev = np.r_[np.nan, a15[:-1]]                 # ATR of completed bars before bucket j
        # ---- restrict day range for trading (indicators already warm)
        lo = 0 if start is None else np.searchsorted(self.days, np.datetime64(start))
        hi = nd if end is None else np.searchsorted(self.days, np.datetime64(end))
        self.trade_days = [d for d in range(max(lo, 20), hi)]

    def _buckets(self, m):
        bid = np.searchsorted(self.days, self.day) * (1440 // m) + self.k // m
        _, first = np.unique(bid, return_index=True)
        idx = np.searchsorted(first, np.arange(len(bid)), side="right") - 1
        return idx, first

    # index helpers inside day d
    def at(self, d, kmin):
        s, e = self.starts[d], self.ends[d]
        i = s + np.searchsorted(self.k[s:e], kmin)
        return i if i < e else None
    def exact(self, d, kmin):
        i = self.at(d, kmin)
        return i if i is not None and self.k[i] == kmin else None

def rsi_wilder(c, n):
    d = np.diff(c, prepend=np.nan)
    up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    au = np.full(len(c), np.nan); ad = np.full(len(c), np.nan)
    if len(c) <= n: return au
    au[n] = np.nanmean(up[1:n + 1]); ad[n] = np.nanmean(dn[1:n + 1])
    a = (n - 1) / n
    for i in range(n + 1, len(c)):
        au[i] = au[i - 1] * a + up[i] / n; ad[i] = ad[i - 1] * a + dn[i] / n
    rs = au / np.where(ad == 0, np.nan, ad)
    rsi = 100 - 100 / (1 + rs)
    rsi[(ad == 0) & (au > 0)] = 100.0
    return rsi

def load_data(paths):
    frames = [pd.read_csv(p, parse_dates=["ts"]) for p in paths]
    return pd.concat(frames, ignore_index=True)

# ----------------------------------------------------------------------------- simulator
def sim_exit(D, i_entry, direction, stop, take, i_exit, take_arr=None):
    """Bars i_entry..i_exit may hit stop/take (stop wins inside one bar); otherwise exit at close of i_exit."""
    o, h, l, c = D.o, D.h, D.l, D.c
    sl = slice(i_entry, i_exit + 1)
    if direction > 0:
        sh = l[sl] <= stop
        th = None if (take is None and take_arr is None) else (h[sl] >= (take if take is not None else take_arr[sl]))
    else:
        sh = h[sl] >= stop
        th = None if (take is None and take_arr is None) else (l[sl] <= (take if take is not None else take_arr[sl]))
    fs = int(np.argmax(sh)) if sh.any() else None
    ft = int(np.argmax(th)) if (th is not None and th.any()) else None
    if fs is not None and (ft is None or fs <= ft):
        j = i_entry + fs; px = stop
        if j > i_entry and ((direction > 0 and o[j] < stop) or (direction < 0 and o[j] > stop)): px = o[j]
        return j, px, "stop"
    if ft is not None:
        j = i_entry + ft; tk = take if take is not None else take_arr[j]; px = tk
        if j > i_entry and ((direction > 0 and o[j] > tk) or (direction < 0 and o[j] < tk)): px = o[j]
        return j, px, "take"
    return i_exit, c[i_exit], "time"

def sim_stop_entry(D, i_from, i_to, buy_lvl, sell_lvl):
    if i_to < i_from: return None
    o, h, l = D.o, D.h, D.l
    sl = slice(i_from, i_to + 1)
    fb = fs = None
    if buy_lvl is not None:
        bh = h[sl] >= buy_lvl
        if bh.any(): fb = int(np.argmax(bh))
    if sell_lvl is not None:
        sh = l[sl] <= sell_lvl
        if sh.any(): fs = int(np.argmax(sh))
    if fb is None and fs is None: return None
    if fs is None or (fb is not None and fb < fs): side = 1
    elif fb is None or fs < fb: side = -1
    else:
        j = i_from + fb; side = 1 if abs(o[j] - buy_lvl) <= abs(o[j] - sell_lvl) else -1
    if side > 0:
        j = i_from + fb; return j, 1, max(buy_lvl, o[j])
    j = i_from + fs; return j, -1, min(sell_lvl, o[j])

def sim_limit_entry(D, i_from, i_to, direction, lvl):
    if i_to < i_from: return None
    o, h, l = D.o, D.h, D.l
    sl = slice(i_from, i_to + 1)
    hit = (l[sl] <= lvl) if direction > 0 else (h[sl] >= lvl)
    if not hit.any(): return None
    j = i_from + int(np.argmax(hit))
    return j, direction, (min(o[j], lvl) if direction > 0 else max(o[j], lvl))

class Sim:
    def __init__(self, D, cost, min_risk):
        self.D, self.cost, self.min_risk = D, cost, min_risk
    def trade(self, d, i_entry, direction, entry, stop, take, i_exit, take_arr=None, tag=""):
        risk = abs(entry - stop)
        if not np.isfinite(risk) or risk < self.min_risk: return None
        if (direction > 0 and stop >= entry) or (direction < 0 and stop <= entry): return None
        if take is not None and ((direction > 0 and take <= entry) or (direction < 0 and take >= entry)): return None
        j, px, reason = sim_exit(self.D, i_entry, direction, stop, take, i_exit, take_arr)
        pnl = (px - entry) * direction - self.cost
        return dict(day=str(self.D.days[d]), dir=direction, entry_ts=str(self.D.ts[i_entry]), entry=round(entry, 2),
                    stop=round(stop, 2), take=(None if take is None else round(take, 2)), exit_ts=str(self.D.ts[j]),
                    exit=round(px, 2), reason=reason, risk_pts=round(risk, 2), pnl_pts=round(pnl, 2), r=round(pnl / risk, 4), tag=tag)

# ----------------------------------------------------------------------------- strategies
def grid(**kw):
    keys = list(kw)
    out = []
    for vals in itertools.product(*[kw[k] for k in keys]):
        p = dict(zip(keys, vals)); out.append(("|".join(f"{k}={v}" for k, v in p.items()), p))
    return out

def stop_from(entry, direction, mode, atr, rng_hi, rng_lo):
    if mode == "rng": return rng_lo if direction > 0 else rng_hi
    x = float(mode[3:]) * atr
    return entry - direction * x

def strat_orb(D, S, d, p, pre):
    rng = p["rng"]; i0 = pre["i_open"]; ie = pre["i_exit"]; atr = pre["atr"]
    i_r1 = D.exact(d, OPEN_K + rng)                       # first bar after the range
    if i_r1 is None or i_r1 - i0 < rng - 1: return None
    rh = D.h[i0:i_r1].max(); rl = D.l[i0:i_r1].min()
    if p["mode"] == "dir":
        direction = np.sign(D.c[i_r1 - 1] - D.o[i0])
        if direction == 0: return None
        i_e, entry = i_r1, D.o[i_r1]
    else:
        i_last = D.at(d, K(15, 0))
        r = sim_stop_entry(D, i_r1, min(i_last, ie) - 1, rh, rl)
        if r is None: return None
        i_e, direction, entry = r
    stop = stop_from(entry, direction, p["stop"], atr, rh, rl)
    risk = abs(entry - stop)
    take = None if p["tp"] is None else entry + direction * p["tp"] * risk
    return S.trade(d, i_e, direction, entry, stop, take, ie)

def strat_im(D, S, d, p, pre):
    i0 = pre["i_open"]; ie = pre["i_exit"]; atr = pre["atr"]
    i_sig = D.exact(d, OPEN_K + p["win"] - 1)
    if i_sig is None: return None
    base = D.o[i0] if p["base"] == "open" else D.prev_sess_close[d]
    if not np.isfinite(base): return None
    direction = np.sign(D.c[i_sig] - base)
    if direction == 0: return None
    i_e = D.exact(d, p["entry"])
    if i_e is None or i_e >= ie: return None
    entry = D.o[i_e]
    return S.trade(d, i_e, direction, entry, entry - direction * p["stop"] * atr, None, ie)

def asian_setup(D, d, pre, use_rsi, k_end=K(11, 0)):
    """first M5 rejection bar in 02:00-11:00 -> (i_next_m1, direction, bar_hi, bar_lo, bar_close)"""
    s = D.starts[d]
    ia0, ia1 = D.at(d, K(19, 0)), D.at(d, K(2, 0))
    ah = D.h[ia0:ia1].max(); al = D.l[ia0:ia1].min()
    iw1 = D.at(d, k_end)
    b0, b1 = D.m5_id[ia1], D.m5_id[iw1 - 1]
    for b in range(b0, b1 + 1):
        f = D.m5_first[b]; e = D.m5_first[b + 1] if b + 1 < len(D.m5_first) else len(D.ts)
        if D.day[f] != D.days[d] or D.k[f] < K(2, 0): continue
        hb = D.h[f:e].max(); lb = D.l[f:e].min(); cb = D.c[e - 1]
        if lb < al and cb > al and (not use_rsi or D.rsi5[b] < 35):
            return e, 1, hb, lb, cb, ah, al
        if hb > ah and cb < ah and (not use_rsi or D.rsi5[b] > 65):
            return e, -1, hb, lb, cb, ah, al
    return None

def strat_asian(D, S, d, p, pre):
    if not D.valid_asia[d]: return None
    r = asian_setup(D, d, pre, p["rsi"])
    if r is None: return None
    i_e, direction, hb, lb, cb, ah, al = r
    if i_e >= pre["i_exit"]: return None
    entry = D.o[i_e]; atr = pre["atr"]
    stop = (lb - 0.1 * atr) if direction > 0 else (hb + 0.1 * atr)
    risk = abs(entry - stop)
    return S.trade(d, i_e, direction, entry, stop, entry + direction * p["tp"] * risk, pre["i_exit"])

def strat_asian_limit(D, S, d, p, pre):
    if not D.valid_asia[d]: return None
    r = asian_setup(D, d, pre, False)
    if r is None: return None
    i_e0, direction, hb, lb, cb, ah, al = r
    mid = (hb + lb) / 2
    i_to = (i_e0 + p["valid"] - 1) if isinstance(p["valid"], int) else D.at(d, K(11, 0)) - 1
    i_to = min(i_to, pre["i_exit"] - 1)
    f = sim_limit_entry(D, i_e0, i_to, direction, mid)
    if f is None: return None
    i_e, _, entry = f
    atr = pre["atr"]
    stop = (lb - 0.1 * atr) if direction > 0 else (hb + 0.1 * atr)
    risk = abs(entry - stop)
    return S.trade(d, i_e, direction, entry, stop, entry + direction * p["tp"] * risk, pre["i_exit"])

def strat_vwap(D, S, d, p, pre):
    i0 = pre["i_open"]; ie = pre["i_exit"]
    i_start = D.at(d, K(9, 45)); i_end = D.at(d, K(11, 30))
    vw = D.vwap
    a15 = D.atr15_prev[D.m15_id[i_start:i_end]]
    dev = D.c[i_start:i_end] - vw[i_start:i_end]
    thr = p["k"] * a15
    sig = np.where(np.isfinite(thr) & (dev > thr), -1, np.where(np.isfinite(thr) & (dev < -thr), 1, 0))
    nz = np.nonzero(sig)[0]
    if len(nz) == 0: return None
    i_s = i_start + nz[0]; direction = int(sig[nz[0]]); i_e = i_s + 1
    if i_e >= ie: return None
    atr = a15[nz[0]]; entry = D.o[i_e]
    stop = entry - direction * p["stop"] * atr
    return S.trade(d, i_e, direction, entry, stop, None, ie, take_arr=vw)

def strat_gap(D, S, d, p, pre):
    i0 = pre["i_open"]; ie = pre["i_exit"]; atr = pre["atr"]; pc = D.prev_sess_close[d]
    if not np.isfinite(pc): return None
    gap = (D.o[i0] - pc) / pc * 100
    if abs(gap) < p["g"]: return None
    direction = int(np.sign(gap)) * (1 if p["mode"] == "cont" else -1)
    entry = D.o[i0]; stop = entry - direction * p["stop"] * atr; risk = abs(entry - stop)
    take = None
    if p["tp"] == "fill" and p["mode"] == "fade": take = pc
    elif p["tp"] == "2r": take = entry + direction * 2 * risk
    elif p["tp"] == "fill": return None                             # fill-take only defined for fade
    return S.trade(d, i0, direction, entry, stop, take, ie)

def strat_lasthour(D, S, d, p, pre):
    i0 = pre["i_open"]; ie = pre["i_exit"]; atr = pre["atr"]
    i_e = D.exact(d, K(15, 0))
    if i_e is None: return None
    move = D.c[i_e - 1] - D.o[i0]
    if abs(move) < p["minmove"] * atr or move == 0: return None
    direction = int(np.sign(move)); entry = D.o[i_e]
    return S.trade(d, i_e, direction, entry, entry - direction * p["stop"] * atr, None, ie)

def strat_orb_vol(D, S, d, p, pre):
    i0 = pre["i_open"]; ie = pre["i_exit"]; atr = pre["atr"]
    if p["filt"]:
        med = D.act1h_med20[d]
        if not np.isfinite(med) or D.act1h[d] <= 1.5 * med: return None
    i_r1 = D.exact(d, K(10, 30))
    if i_r1 is None: return None
    rh = D.h[i0:i_r1].max(); rl = D.l[i0:i_r1].min()
    r = sim_stop_entry(D, i_r1, min(D.at(d, K(15, 0)), ie) - 1, rh, rl)
    if r is None: return None
    i_e, direction, entry = r
    stop = stop_from(entry, direction, p["stop"], atr, rh, rl); risk = abs(entry - stop)
    take = None if p["tp"] is None else entry + direction * p["tp"] * risk
    return S.trade(d, i_e, direction, entry, stop, take, ie)

STRATEGIES = {
    "orb":         (strat_orb,         grid(rng=[5, 15, 30], mode=["brk", "dir"], stop=["rng", "atr0.1", "atr0.25", "atr0.5", "atr1.0"], tp=[None, 3.0])),
    "im":          (strat_im,          grid(win=[30, 60], base=["open", "prevclose"], entry=[K(15, 0), K(15, 30)], stop=[0.25, 0.5, 1.0])),
    "asian":       (strat_asian,       grid(rsi=[True, False], tp=[2.0, 3.0])),
    "vwap":        (strat_vwap,        grid(k=[1.0, 1.5, 2.0], stop=[1.0, 1.5])),
    "gap":         (strat_gap,         grid(g=[0.3, 0.5, 0.8], mode=["cont", "fade"], stop=[0.5, 1.0], tp=[None, "fill", "2r"])),
    "lasthour":    (strat_lasthour,    grid(stop=[0.25, 0.5, 1.0], minmove=[0.0, 0.25])),
    "orb_vol":     (strat_orb_vol,     grid(filt=[True, False], stop=["rng", "atr0.5"], tp=[None, 2.0])),
    "asian_limit": (strat_asian_limit, grid(valid=[30, "window"], tp=[2.0, 3.0])),
}

def generate(D, S, name, news=None, news_win=15):
    fn, g = STRATEGIES[name]
    out = {pid: [] for pid, _ in g}
    for d in D.trade_days:
        if not D.valid[d] or not np.isfinite(D.atr_d1[d]): continue
        pre = dict(i_open=D.exact(d, OPEN_K), i_exit=D.exact(d, EXIT_K), atr=D.atr_d1[d])
        for pid, p in g:
            t = fn(D, S, d, p, pre)
            if t is None: continue
            if news is not None:
                et = np.datetime64(t["entry_ts"])
                j = np.searchsorted(news, et)
                near = [news[i] for i in (j - 1, j) if 0 <= i < len(news)]
                if any(abs((et - n) / np.timedelta64(1, "m")) <= news_win for n in near): continue
            t["params"] = pid; out[pid].append(t)
    return {pid: pd.DataFrame(v) for pid, v in out.items()}

# ----------------------------------------------------------------------------- metrics / walk-forward
def metrics(df):
    if df is None or len(df) == 0:
        return dict(n=0, pf=np.nan, netR=0.0, avgR=np.nan, win=np.nan, maxDD_R=0.0, worst_day_R=0.0)
    r = df.r.values
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    eq = np.cumsum(r); dd = (np.maximum.accumulate(np.r_[0, eq]) [1:] - eq)
    byday = df.groupby("day").r.sum()
    return dict(n=int(len(r)), pf=(gp / gl if gl > 0 else np.inf), netR=float(r.sum()), avgR=float(r.mean()),
                win=float((r > 0).mean()), maxDD_R=float(dd.max()) if len(dd) else 0.0, worst_day_R=float(byday.min()))

def month_add(ts, m):
    return (pd.Timestamp(ts).to_period("M") + m).to_timestamp()

def walk_forward(trades, start, data_end, is_m, oos_m, step_m, min_is):
    all_days = pd.Timestamp(start)
    windows = []; oos_parts = []
    w = 0; cur = pd.Timestamp(start)
    while True:
        is0, is1 = cur, month_add(cur, is_m); oos1 = month_add(is1, oos_m)
        if is1 >= pd.Timestamp(data_end): break
        oos1c = min(oos1, pd.Timestamp(data_end) + pd.Timedelta(days=1))
        best = None
        for pid, df in trades.items():
            if len(df) == 0: continue
            dd = pd.to_datetime(df.day)
            m = metrics(df[(dd >= is0) & (dd < is1)])
            if m["n"] < min_is: continue
            key = (m["pf"], m["n"])
            if best is None or key > best[0]: best = (key, pid, m)
        row = dict(window=w, is_start=str(is0.date()), is_end=str((is1 - pd.Timedelta(days=1)).date()),
                   oos_start=str(is1.date()), oos_end=str((oos1c - pd.Timedelta(days=1)).date()),
                   partial=bool(oos1 > oos1c))
        if best is None:
            row.update(params=None, is_n=0, is_pf=np.nan, oos_n=0, oos_pf=np.nan, oos_netR=0.0, oos_maxDD_R=0.0)
        else:
            _, pid, m = best
            df = trades[pid]; dd = pd.to_datetime(df.day)
            o = df[(dd >= is1) & (dd < oos1c)].copy(); o["window"] = w
            mo = metrics(o)
            row.update(params=pid, is_n=m["n"], is_pf=round(m["pf"], 3), oos_n=mo["n"], oos_pf=(round(mo["pf"], 3) if np.isfinite(mo["pf"]) else mo["pf"]),
                       oos_netR=round(mo["netR"], 2), oos_maxDD_R=round(mo["maxDD_R"], 2))
            oos_parts.append(o)
        windows.append(row); w += 1; cur = month_add(cur, step_m)
    oos = pd.concat(oos_parts, ignore_index=True) if oos_parts else pd.DataFrame()
    if len(oos): oos = oos.sort_values(["entry_ts"]).reset_index(drop=True)
    return pd.DataFrame(windows), oos

GATES = dict(pf_min=1.2, n_min=100, pos_windows_min=0.60, maxdd_pct_max=8.0)

def verdict(win_df, oos, account, risk_pct):
    m = metrics(oos)
    risk_usd = account * risk_pct / 100
    nwin = len(win_df); npos = int((win_df.oos_netR > 0).sum())
    g = dict(pf_oos=m["pf"], n_oos=m["n"], pos_windows=f"{npos}/{nwin}", pos_frac=(npos / nwin if nwin else 0),
             maxDD_R=m["maxDD_R"], maxDD_usd=m["maxDD_R"] * risk_usd, maxDD_pct=m["maxDD_R"] * risk_usd / account * 100,
             netR=m["netR"], net_usd=m["netR"] * risk_usd, worst_day_R=m["worst_day_R"], worst_day_pct=m["worst_day_R"] * risk_usd / account * 100,
             win_rate=m["win"], avgR=m["avgR"])
    checks = dict(pf=(m["pf"] > GATES["pf_min"]) if np.isfinite(m["pf"]) else False, n=m["n"] > GATES["n_min"],
                  windows=g["pos_frac"] >= GATES["pos_windows_min"], dd=g["maxDD_pct"] < GATES["maxdd_pct_max"])
    g["checks"] = checks; g["PASS"] = all(checks.values())
    return g

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strategy", default="orb", help=",".join(STRATEGIES) + " or all")
    ap.add_argument("--data", default=os.path.join(HERE, "data", "NAS100_m1_NY_*.csv.gz"))
    ap.add_argument("--start", default="2018-01-01", help="first IS day (indicators warm up on earlier data)")
    ap.add_argument("--end", default=None)
    ap.add_argument("--is", dest="is_m", type=int, default=24); ap.add_argument("--oos", type=int, default=6); ap.add_argument("--step", type=int, default=6)
    ap.add_argument("--spread", type=float, default=2.0, help="points, round trip"); ap.add_argument("--slip", type=float, default=0.5, help="points per side")
    ap.add_argument("--min-is-trades", type=int, default=40); ap.add_argument("--min-risk", type=float, default=None, help="skip trades with stop < this many points (default = cost)")
    ap.add_argument("--account", type=float, default=50000); ap.add_argument("--risk-pct", type=float, default=0.5)
    ap.add_argument("--news-file", default=None); ap.add_argument("--news-win", type=int, default=15)
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--dump", default=None, help="params id: write every trade of that parameter set (no walk-forward) to --out/<strategy>_dump.csv")
    a = ap.parse_args()
    paths = sorted(glob.glob(a.data)); assert paths, f"no data at {a.data}"
    t0 = time.time(); df = load_data(paths)
    warm_start = (pd.Timestamp(a.start) - pd.DateOffset(months=3)).strftime("%Y-%m-%d")
    df = df[df.ts >= warm_start]
    if a.end: df = df[df.ts < a.end]
    D = Data(df, start=a.start, end=a.end)
    cost = a.spread + 2 * a.slip
    S = Sim(D, cost, a.min_risk if a.min_risk is not None else cost)
    news = None
    if a.news_file:
        news = np.sort(pd.to_datetime(pd.read_csv(a.news_file).time_ny).values.astype("datetime64[m]"))
    print(f"data {df.ts.min()} .. {df.ts.max()}  bars={len(df)}  days={len(D.days)}  valid_session_days={int(D.valid[D.trade_days].sum())}  cost={cost} pts  loaded in {time.time()-t0:.1f}s")
    os.makedirs(a.out, exist_ok=True)
    names = list(STRATEGIES) if a.strategy == "all" else a.strategy.split(",")
    summary = {}
    for name in names:
        t1 = time.time()
        trades = generate(D, S, name, news, a.news_win)
        if a.dump:
            trades[a.dump].to_csv(os.path.join(a.out, f"{name}_dump.csv"), index=False); print("dumped", a.dump, len(trades[a.dump])); continue
        win_df, oos = walk_forward(trades, a.start, str(D.days[D.trade_days[-1]]), a.is_m, a.oos, a.step, a.min_is_trades)
        g = verdict(win_df, oos, a.account, a.risk_pct)
        win_df.to_csv(os.path.join(a.out, f"{name}_windows.csv"), index=False)
        oos.to_csv(os.path.join(a.out, f"{name}_oos_trades.csv"), index=False)
        full = {pid: metrics(df_) for pid, df_ in trades.items()}
        pd.DataFrame(full).T.to_csv(os.path.join(a.out, f"{name}_grid_fullperiod.csv"))
        g["strategy"] = name; g["cost_pts"] = cost; g["risk_pct"] = a.risk_pct; g["gates"] = GATES; g["windows"] = len(win_df)
        g["settings"] = dict(start=a.start, is_m=a.is_m, oos_m=a.oos, step_m=a.step, min_is_trades=a.min_is_trades, news_file=a.news_file)
        summary[name] = g
        with open(os.path.join(a.out, f"{name}_summary.json"), "w") as f: json.dump(g, f, indent=1, default=lambda x: (None if (isinstance(x, float) and not np.isfinite(x)) else (x.item() if hasattr(x, "item") else str(x))))
        print(f"\n=== {name}  ({time.time()-t1:.0f}s) ===")
        print(win_df.to_string(index=False))
        print(f"OOS: n={g['n_oos']} PF={g['pf_oos']:.3f} netR={g['netR']:.1f} (${g['net_usd']:.0f} at {a.risk_pct}% risk) win={g['win_rate']:.2f} avgR={g['avgR']:.3f} "
              f"maxDD={g['maxDD_R']:.1f}R ({g['maxDD_pct']:.1f}%) worst_day={g['worst_day_R']:.1f}R ({g['worst_day_pct']:.1f}%) windows+={g['pos_windows']}")
        print("GATES:", g["checks"], "->", "PASS" if g["PASS"] else "FAIL")
    return summary

if __name__ == "__main__":
    main()
