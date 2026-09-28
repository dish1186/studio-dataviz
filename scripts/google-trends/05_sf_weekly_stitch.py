# Google Trends Step 8 · stitch the weekly San Francisco "air purifier" files onto one scale.
#
# Each weekly raw file in data/raw/google-trends/air-search-weekly/san-francisco/ (not modified) covers one calendar
# year and is scaled 0-100 within itself, so values can't be compared across files. Each file is put on the scale of the
# monthly San Francisco-Oakland-San Jose file (data/raw/google-trends/air-search/, "air purifier" column, one scale for
# 2016-2026):
#   1. Spread each week's value over its 7 days (weeks start on Sunday) and average by calendar month (months with >= 20 days).
#   2. factor = least-squares scale (through 0) that best matches those monthly averages to the monthly file's values,
#      using only the file's own calendar year.
#   3. calibrated_index = raw weekly value x factor (units of the monthly file's index).
# Weeks that appear in two files (the week straddling New Year) are kept once, as the mean of the two calibrated values;
# the gap between them is written to the file as a check. 2024 has no weekly file yet, so its weeks are absent.
# Run from the repo root: python3 scripts/google-trends/05_sf_weekly_stitch.py
import csv, glob, os, datetime as dt, statistics as st

IN = "data/raw/google-trends/air-search-weekly/san-francisco"
MONTHLY = "data/raw/google-trends/air-search/San Francisco-Oakland-San Jose CA-ca-air-search.csv"
OUT = "data/processed/google-trends/air-search-weekly"
os.makedirs(OUT, exist_ok=True)
M = {r["Time"][:7]: int(r["air purifier"]) for r in csv.DictReader(open(MONTHLY, encoding="utf-8"))}

weeks, factors = {}, []
for fn in sorted(glob.glob(f"{IN}/time_series_807_*.csv")):
    R = list(csv.DictReader(open(fn, encoding="utf-8")))
    assert list(R[0].keys()) == ["Time", "air purifier"], fn
    rows = [(dt.date.fromisoformat(r["Time"]), int(r["air purifier"])) for r in R]
    year = os.path.basename(fn).split("_")[3][:4]
    acc = {}
    for d0, v in rows:
        for k in range(7):
            d = d0 + dt.timedelta(k)
            acc.setdefault(f"{d.year}-{d.month:02d}", []).append(v)
    mw = {k: st.mean(v) for k, v in acc.items() if len(v) >= 20 and k.startswith(year) and k in M}
    fac = sum(M[k] * mw[k] for k in mw) / sum(mw[k] ** 2 for k in mw)
    r_fit = st.correlation([M[k] for k in mw], [mw[k] for k in mw])
    factors.append({"file": os.path.basename(fn), "year": year, "months_used": len(mw), "factor": round(fac, 4), "fit_r": round(r_fit, 3),
                    "max_abs_residual": round(max(abs(M[k] - fac * mw[k]) for k in mw), 2)})
    for d0, v in rows:
        weeks.setdefault(d0, []).append((os.path.basename(fn), v, fac))

out = []
for d0 in sorted(weeks):
    e = weeks[d0]
    cal = [v * f for _, v, f in e]
    out.append({"week_start": d0.isoformat(), "source_files": " | ".join(x[0] for x in e), "raw_index": " | ".join(str(x[1]) for x in e),
                "factor": " | ".join(f"{x[2]:.4f}" for x in e), "calibrated_index": round(st.mean(cal), 2),
                "overlap_gap": round(abs(cal[0] - cal[1]), 2) if len(cal) == 2 else ""})
with open(f"{OUT}/sf_air_purifier_weekly.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
with open(f"{OUT}/sf_air_purifier_weekly_factors.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(factors[0].keys())); w.writeheader(); w.writerows(factors)
print(len(out), "weeks;", [(x["year"], x["factor"], x["fit_r"]) for x in factors])
print("overlap gaps:", [(o["week_start"], o["overlap_gap"]) for o in out if o["overlap_gap"] != ""])
