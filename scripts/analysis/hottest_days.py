# Analysis A19 · the 10 hottest days of each year (daily maximum temperature, gridMET) for Boston, Detroit, Eugene,
# Bakersfield, 2016-2026 (2026 runs to 2026-09-24, the end of the gridMET file). Felt heat (UTCI daily maximum) is added
# where available (to 2026-06-12). Ties are broken by date. Inputs are read only.
# Run from the repo root: python3 scripts/analysis/hottest_days.py
import csv, datetime as dt

CITIES = ["boston", "detroit", "eugene", "bakersfield"]
rows = []
for c in CITIES:
    L = open(f"data/raw/gridmet/climateengine/gridmet_tmax_{c}_2016-2026.csv", encoding="utf-8-sig").read().splitlines()[1:]
    t = {dt.date.fromisoformat(a.strip('"')): float(b) for a, b in (l.split(",") for l in L if l)}
    u = {r["date"]: r["utci_max_f"] for r in csv.DictReader(open(f"data/processed/utci/final/utci_{c}_daily.csv", encoding="utf-8")) if r["valid"] == "1"}
    for y in sorted({d.year for d in t}):
        top = sorted([d for d in t if d.year == y], key=lambda d: (-t[d], d))[:10]
        for k, d in enumerate(top, 1):
            rows.append({"city": c, "year": y, "rank": k, "date": d.isoformat(), "tmax_F": round(t[d], 1), "felt_utci_max_F": u.get(d.isoformat(), "")})
with open("data/processed/analysis/hottest_10_days_per_year.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
