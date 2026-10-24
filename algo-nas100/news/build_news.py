#!/usr/bin/env python3
"""Build news/us_high_impact.csv (NY local time) used by the --news-file filter.
Sources: FOMC statement days parsed from federalreserve.gov HTML saved locally (2018-2026),
NFP = first Friday of the month 08:30 (BLS rule of thumb; a handful of real releases were shifted
by holidays/shutdowns), CPI 08:30 on BLS release dates (2022-2025 typed in from the BLS schedule;
other years approximated as the 2nd Wednesday). Replace with a broker calendar export for live use."""
import re, html, sys, datetime as dt, calendar
import pandas as pd
rows = []
MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}
def fomc_from_text(txt, year):
    # patterns like "January 30-31", "Jan/Feb 31-1", "Apr/May 30-1", "March 3" (unscheduled)
    for m in re.finditer(r'([A-Z][a-z]+)(?:/([A-Z][a-z]+))?\s+(\d{1,2})(?:-(\d{1,2}))?\*?\s+(?:Statement|Meeting|\(unscheduled\)|\(notation vote\)|\(cancelled\))', txt):
        m1, m2, d1, d2 = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        full = {k[:3]: v for k, v in MONTHS.items()}
        mon = m2 or m1
        if mon[:3] not in full: continue
        month = full[mon[:3]]
        day = int(d2) if d2 else d1
        try: rows.append((dt.datetime(year, month, day, 14, 0), 'FOMC'))
        except ValueError: pass
def text(fn):
    t = open(fn, encoding='utf-8', errors='ignore').read()
    t = re.sub(r'<script.*?</script>', '', t, flags=re.S); t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))
cal = text('/tmp/fomc_cal.html')
for y in range(2021, 2027):
    i = cal.find(f'{y} FOMC Meetings')
    if i < 0: continue
    j = cal.find('FOMC Meetings', i + 20)
    seg = cal[i:j] if j > i else cal[i:i+4000]
    fomc_from_text(seg, y)
for y in (2018, 2019, 2020):
    t = text(f'/tmp/fomc_{y}.html'); i = t.find('Meeting'); fomc_from_text(t[i:], y)
# NFP: first Friday 08:30
for y in range(2017, 2027):
    for mth in range(1, 13):
        d = dt.date(y, mth, 1)
        while d.weekday() != 4: d += dt.timedelta(days=1)
        rows.append((dt.datetime.combine(d, dt.time(8, 30)), 'NFP'))
# CPI
cpi_known = {
 2022: ['01-12','02-10','03-10','04-12','05-11','06-10','07-13','08-10','09-13','10-13','11-10','12-13'],
 2023: ['01-12','02-14','03-14','04-12','05-10','06-13','07-12','08-10','09-13','10-12','11-14','12-12'],
 2024: ['01-11','02-13','03-12','04-10','05-15','06-12','07-11','08-14','09-11','10-10','11-13','12-11'],
 2025: ['01-15','02-12','03-12','04-10','05-13','06-11','07-15','08-12','09-11','10-24','11-13','12-10'],
}
for y in range(2017, 2027):
    if y in cpi_known:
        for md in cpi_known[y]:
            rows.append((dt.datetime.strptime(f'{y}-{md} 08:30', '%Y-%m-%d %H:%M'), 'CPI'))
    else:
        for mth in range(1, 13):
            d = dt.date(y, mth, 1)
            while d.weekday() != 2: d += dt.timedelta(days=1)
            d += dt.timedelta(days=7)
            rows.append((dt.datetime.combine(d, dt.time(8, 30)), 'CPI~approx'))
df = pd.DataFrame(rows, columns=['time_ny', 'event']).drop_duplicates().sort_values('time_ny')
df.to_csv('news/us_high_impact.csv', index=False, date_format='%Y-%m-%d %H:%M')
print(df.event.value_counts()); print(df[df.event == 'FOMC'].time_ny.dt.year.value_counts().sort_index())
