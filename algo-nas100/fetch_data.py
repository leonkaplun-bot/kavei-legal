#!/usr/bin/env python3
"""
NAS100 (US100) M1 data: download from histdata.com (symbol NSXUSD, free) and build
a single clean CSV in New York local time.

Usage:
  python fetch_data.py --download --build          # full pipeline
  python fetch_data.py --build                     # rebuild from already downloaded zips
Options:
  --raw DIR      where zips/csvs live (default: data/raw)
  --out FILE     output csv.gz (default: data/NAS100_m1_NY.csv.gz)
  --start YEAR   first year to download (default 2010)

histdata.com facts (verified 2026-10-24):
  * ASCII M1 format: "YYYYMMDD HHMMSS;open;high;low;close;volume", volume is always 0
  * timestamps are EST (UTC-5) WITHOUT daylight saving adjustments -> we convert to
    America/New_York so that the cash session is always 09:30-16:00 local.
"""
import argparse, glob, io, os, re, sys, time, zipfile
import http.cookiejar, urllib.request, urllib.parse
import numpy as np, pandas as pd

BASE = "https://www.histdata.com"
PAIR = "nsxusd"

def download(raw_dir, start_year):
    os.makedirs(raw_dir, exist_ok=True)
    now = pd.Timestamp.utcnow()
    targets = [str(y) for y in range(start_year, now.year)] + [f"{now.year}/{m}" for m in range(1, now.month + 1)]
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def get(url, data=None, headers=None):
        req = urllib.request.Request(url, data=data, headers=headers or {})
        with opener.open(req, timeout=180) as r:
            return r.read(), r.headers
    for t in targets:
        fn = os.path.join(raw_dir, f"{PAIR}_{t.replace('/', '_')}.zip")
        if os.path.exists(fn) and os.path.getsize(fn) > 1000 and "/" not in t:
            print("skip", fn); continue
        page_url = f"{BASE}/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{PAIR}/{t}"
        try:
            html = get(page_url)[0].decode("utf-8", "ignore")
        except Exception as e:
            print("page fail", t, e); continue
        form = re.search(r'<form[^>]*id="file_down"(.*?)</form>', html, re.S)
        if not form:
            print("no form for", t); continue
        fields = {}
        for tag in re.findall(r'<input[^>]*>', form.group(1)):
            n = re.search(r'name="([^"]+)"', tag); v = re.search(r'value="([^"]*)"', tag)
            if n: fields[n.group(1)] = v.group(1) if v else ""
        body, hdrs = get(f"{BASE}/get.php", data=urllib.parse.urlencode(fields).encode(),
                         headers={"Referer": page_url, "Content-Type": "application/x-www-form-urlencoded"})
        if body[:2] != b"PK":
            print("not a zip:", t, hdrs.get("Content-Type"), body[:120]); continue
        open(fn, "wb").write(body)
        print("ok", fn, len(body), flush=True)
        time.sleep(1.5)

def build(raw_dir, out):
    frames = []
    for z in sorted(glob.glob(os.path.join(raw_dir, "*.zip"))):
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                if not name.lower().endswith(".csv"): continue
                df = pd.read_csv(io.BytesIO(zf.read(name)), sep=";", header=None,
                                 names=["ts", "open", "high", "low", "close", "vol"],
                                 dtype={"ts": str}, engine="c")
                frames.append(df)
                print(name, len(df))
    df = pd.concat(frames, ignore_index=True)
    ts_est = pd.to_datetime(df["ts"], format="%Y%m%d %H%M%S")
    # EST fixed (UTC-5) -> UTC -> New York local (handles DST)
    ts_utc = (ts_est + pd.Timedelta(hours=5)).dt.tz_localize("UTC")
    ts_ny = ts_utc.dt.tz_convert("America/New_York")
    df["ts"] = ts_ny.dt.tz_localize(None)
    df = df.drop(columns=["vol"]).sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    # basic sanity: drop impossible bars
    bad = (df.high < df.low) | (df.high < df[["open", "close"]].max(axis=1)) | (df.low > df[["open", "close"]].min(axis=1))
    print("dropping bad bars:", int(bad.sum()))
    df = df[~bad].reset_index(drop=True)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df.to_csv(out, index=False, float_format="%.3f", date_format="%Y-%m-%d %H:%M")
    print("written", out, len(df), df.ts.min(), df.ts.max())
    # quality report: cash session completeness per year
    s = df[(df.ts.dt.hour * 60 + df.ts.dt.minute >= 570) & (df.ts.dt.hour * 60 + df.ts.dt.minute < 960)]
    per_day = s.groupby(s.ts.dt.date).size()
    q = pd.DataFrame({"n": per_day})
    q["year"] = pd.to_datetime(q.index).year
    rep = q.groupby("year").agg(days=("n", "size"), full_days=("n", lambda x: int((x >= 380).sum())),
                                median_bars=("n", "median"), min_bars=("n", "min"))
    rep["pct_full"] = (100 * rep.full_days / rep.days).round(1)
    txt = rep.to_string()
    print(txt)
    with open(os.path.join(os.path.dirname(out), "quality.txt"), "w") as f:
        f.write("Cash-session (09:30-16:00 NY) completeness per year; 'full' = >=380 of 390 M1 bars\n")
        f.write(txt + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--raw", default=os.path.join(here, "data", "raw"))
    ap.add_argument("--out", default=os.path.join(here, "data", "NAS100_m1_NY.csv.gz"))
    ap.add_argument("--start", type=int, default=2010)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.download: download(a.raw, a.start)
    if a.build: build(a.raw, a.out)
    if not (a.download or a.build): ap.print_help()
