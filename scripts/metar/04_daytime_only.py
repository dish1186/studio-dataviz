"""
Step 4 · METAR · Daytime only (8:00-17:59 local).
Keeps station-hours whose clock hour is 8 through 17 (10 hours/day).
Times are already local (IEM download used each city's timezone,
including daylight saving). Rows are copied unchanged.

Run from the repo root:  python3 scripts/metar/04_daytime_only.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step03_hourly"
OUT = "data/processed/metar/step04_daytime"
os.makedirs(OUT, exist_ok=True)

FIRST_HOUR, LAST_HOUR = 8, 17        # 8:00 am to 5:59 pm

summary = []
for path in sorted(glob.glob(f"{IN}/metar_*_hourly.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_hourly.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    clock_hour = df["hour"].str[11:13].astype(int)      # "2016-01-01 13:00" -> 13
    keep = clock_hour.between(FIRST_HOUR, LAST_HOUR)

    df[keep].to_csv(f"{OUT}/metar_{city}_daytime.csv", index=False)

    for station in sorted(df["station"].unique()):
        s = df["station"] == station
        summary.append({
            "city": city, "station": station,
            "hours_in": int(s.sum()),
            "hours_removed_night": int((s & ~keep).sum()),
            "hours_out": int((s & keep).sum()),
        })

summ = pd.DataFrame(summary)
summ["pct_of_possible_daytime"] = (100 * summ.hours_out / (3921 * 10)).round(2)
summ.to_csv(f"{OUT}/step04_summary.csv", index=False)
print(summ.to_string(index=False))
t = summ[["hours_in", "hours_removed_night", "hours_out"]].sum()
print(f"\nTOTAL in {t.hours_in} | removed (night) {t.hours_removed_night} | out {t.hours_out}")
assert t.hours_in == t.hours_out + t.hours_removed_night
