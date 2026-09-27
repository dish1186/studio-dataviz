"""
Step 9a · METAR · How many dry daytime hours does each day have? (read-only)
For each city: distribution of dry daytime city-hours per calendar day (0-10),
and how many of the 3,920 days would remain at minimum-hours thresholds 1-6.
Removes and averages nothing.

Run from the repo root:  python3 scripts/metar/09a_hours_per_day_audit.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step08_city_hourly"
OUT = "data/processed/metar/step09a_hours_per_day"
os.makedirs(OUT, exist_ok=True)

ALL_DAYS = pd.date_range("2016-01-01", "2026-09-24", freq="D").strftime("%Y-%m-%d")  # 3,920 days (D4: study period ends 2026-09-24)
THRESHOLDS = [1, 2, 3, 4, 5, 6]

dist_rows, trade_rows = [], []
for path in sorted(glob.glob(f"{IN}/metar_*_cityhour.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_cityhour.csv", "")
    df = pd.read_csv(path, dtype={"hour": str})
    per_day = df["hour"].str[:10].value_counts().reindex(ALL_DAYS, fill_value=0)

    counts = per_day.value_counts().reindex(range(11), fill_value=0)
    dist_rows.append({"city": city, **{f"{h}h": int(counts[h]) for h in range(11)}})

    row = {"city": city, "total_days": len(ALL_DAYS)}
    for k in THRESHOLDS:
        kept = int((per_day >= k).sum())
        row[f"days_min{k}"] = kept
        row[f"pct_min{k}"] = round(100 * kept / len(ALL_DAYS), 1)
    trade_rows.append(row)

dist = pd.DataFrame(dist_rows); trade = pd.DataFrame(trade_rows)
dist.to_csv(f"{OUT}/hours_per_day_distribution.csv", index=False)
trade.to_csv(f"{OUT}/min_hours_tradeoff.csv", index=False)
print("DAYS BY NUMBER OF DRY DAYTIME HOURS\n", dist.to_string(index=False))
print("\n% OF DAYS KEPT AT EACH MINIMUM\n",
      trade[["city"] + [f"pct_min{k}" for k in THRESHOLDS]].to_string(index=False))
