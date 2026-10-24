#!/usr/bin/env python3
"""
ftmo_layer.py -- position sizing + Monte-Carlo pass/fail estimate for an FTMO 50K challenge,
built on the OOS trades produced by orb_walkforward.py (results/<strategy>_oos_trades.csv).

  python ftmo_layer.py --strategy orb_vol [--account 50000] [--paths 2000] [--days 30]

Sizing rule (fixed before the run): risk per trade such that the worst OOS day < 2.5% of the account
and the OOS max drawdown < 6%; rounded down to 0.05%.
FTMO rules modelled: target +10% (phase 1) / +5% (phase 2), max daily loss 5% of initial balance,
max overall loss 10% of initial balance, one trade per day (so the day's loss = that trade's loss).
Floating loss inside a day is bounded by the stop (1R) so closed-trade accounting is a close proxy.
"""
import argparse, json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))

def day_series(oos, all_days=None):
    r = oos.groupby("day").r.sum()
    if all_days is not None:
        r = r.reindex(all_days, fill_value=0.0)
    return r

def run_paths(dayR, risk_usd, account, target_pct, paths, horizon, rng, mode="iid"):
    n = len(dayR); vals = dayR.values
    res = {"pass": 0, "fail": 0, "undecided": 0}; t_dec = []
    for _ in range(paths):
        if mode == "iid":
            seq = vals[rng.integers(0, n, horizon)]
        else:  # contiguous block from the real OOS sequence (keeps regime clustering)
            s = rng.integers(0, n - horizon); seq = vals[s:s + horizon]
        eq = account; outcome = "undecided"
        for i, x in enumerate(seq):
            pnl = x * risk_usd
            if pnl < -0.05 * account:            # daily loss limit 5% (one trade per day)
                outcome = "fail"; t_dec.append(i + 1); break
            eq += pnl
            if eq <= 0.90 * account:             # overall loss limit 10%
                outcome = "fail"; t_dec.append(i + 1); break
            if eq >= account * (1 + target_pct / 100):
                outcome = "pass"; t_dec.append(i + 1); break
        res[outcome] += 1
    k = paths
    return {k_: v / k for k_, v in res.items()}, (float(np.mean(t_dec)) if t_dec else None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True); ap.add_argument("--results", default=os.path.join(HERE, "results"))
    ap.add_argument("--account", type=float, default=50000); ap.add_argument("--paths", type=int, default=2000)
    ap.add_argument("--days", type=int, default=30); ap.add_argument("--long-horizon", type=int, default=250)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    oos = pd.read_csv(os.path.join(a.results, f"{a.strategy}_oos_trades.csv"))
    wins = pd.read_csv(os.path.join(a.results, f"{a.strategy}_windows.csv"))
    # all OOS trading days (business days inside the OOS spans) so that no-trade days count as 0
    spans = [pd.bdate_range(r.oos_start, r.oos_end) for r in wins.itertuples()]
    all_days = pd.DatetimeIndex(np.unique(np.concatenate([s.values for s in spans]))).strftime("%Y-%m-%d")
    dayR = day_series(oos, all_days)
    r = oos.r.values; eq = np.cumsum(r); dd = (np.maximum.accumulate(np.r_[0, eq])[1:] - eq)
    worst_day_R = float(dayR.min()); maxDD_R = float(dd.max())
    risk_pct = min(2.5 / abs(worst_day_R) if worst_day_R < 0 else 99, 6.0 / maxDD_R if maxDD_R > 0 else 99)
    risk_pct = float(np.floor(risk_pct / 0.05) * 0.05)
    risk_usd = a.account * risk_pct / 100
    recent = oos[pd.to_datetime(oos.day) >= pd.to_datetime(oos.day).max() - pd.Timedelta(days=365)]
    med_stop = float(recent.risk_pts.median()) if len(recent) else float(oos.risk_pts.median())
    out = dict(strategy=a.strategy, account=a.account, oos_trades=int(len(oos)), oos_days=int(len(dayR)),
               worst_day_R=round(worst_day_R, 3), maxDD_R=round(maxDD_R, 3), sizing_rule="worst day < 2.5% and maxDD < 6%",
               risk_pct=round(risk_pct, 2), risk_usd=round(risk_usd, 2),
               median_stop_pts_last12m=round(med_stop, 1), lots_at_median_stop=round(risk_usd / med_stop, 2),
               note_lots="FTMO US100.cash: contract size 1 => 1 lot = 1 USD per index point; lots = risk_usd / stop_pts",
               net_usd_oos=round(float(r.sum()) * risk_usd, 0), maxDD_usd_oos=round(maxDD_R * risk_usd, 0),
               worst_day_usd=round(worst_day_R * risk_usd, 0), mc={})
    rng = np.random.default_rng(a.seed)
    for label, rp in [("chosen", risk_pct), ("0.5%", 0.5), ("1.0%", 1.0), ("2.0%", 2.0)]:
        ru = a.account * rp / 100
        block = {}
        for phase, tgt in (("phase1_10pct", 10.0), ("phase2_5pct", 5.0)):
            p30, t30 = run_paths(dayR, ru, a.account, tgt, a.paths, a.days, rng, "iid")
            pb, tb = run_paths(dayR, ru, a.account, tgt, a.paths, a.days, rng, "block")
            pl, tl = run_paths(dayR, ru, a.account, tgt, a.paths, a.long_horizon, rng, "iid")
            block[phase] = dict(iid_30d=p30, block_30d=pb, iid_250d=pl, mean_days_to_decision_30d=t30, mean_days_to_decision_250d=tl)
        out["mc"][label] = dict(risk_pct=rp, **block)
    with open(os.path.join(a.results, f"{a.strategy}_ftmo.json"), "w") as f: json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "mc"}, indent=1))
    for label, b in out["mc"].items():
        print(f"\n-- risk {label} ({b['risk_pct']}%) --")
        for phase in ("phase1_10pct", "phase2_5pct"):
            x = b[phase]
            print(f"  {phase}: 30d iid  pass={x['iid_30d']['pass']:.3f} fail={x['iid_30d']['fail']:.3f} undecided={x['iid_30d']['undecided']:.3f}"
                  f" | 30d block pass={x['block_30d']['pass']:.3f} fail={x['block_30d']['fail']:.3f}"
                  f" | 250d iid pass={x['iid_250d']['pass']:.3f} fail={x['iid_250d']['fail']:.3f} undecided={x['iid_250d']['undecided']:.3f}")

if __name__ == "__main__":
    main()
