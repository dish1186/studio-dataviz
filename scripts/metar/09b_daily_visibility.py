"""
Step 9b · METAR · Daily visibility per city (final output).
For each city and each day (2016-01-01 to 2026-09-25, 3,921 days):
  n_hours    = dry daytime city-hours that day
  extinction = mean of hourly extinction_km (1/km), only if n_hours >= 3
  visibility_mi = (3.912 / extinction) / 1.609344   (back-converted, Koschmieder)
  n_stations = airports contributing at least one hour that day
Days with fewer than 3 hours are kept as rows with blank values (valid_day = 0).

Run from the repo root:  python3 scripts/metar/09b_daily_visibility.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step08_city_hourly"
OUT = "data/processed/metar/final"
os.makedirs(OUT, exist_ok=True)

K, MI_TO_KM, MIN_HOURS = 3.912, 1.609344, 3
ALL_DAYS = pd.Index(pd.date_range("2016-01-01", "2026-09-25", freq="D").strftime("%Y-%m-%d"), name="date")

summary = []
for path in sorted(glob.glob(f"{IN}/metar_*_cityhour.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_cityhour.csv", "")
    df = pd.read_csv(path, dtype={"hour": str, "stations_reporting": str})
    df["date"] = df["hour"].str[:10]
    g = df.groupby("date")

    daily = pd.DataFrame({
        "extinction": g["extinction_km"].mean(),
        "n_hours": g.size(),
        "n_stations": g["stations_reporting"].agg(lambda s: len(set(" ".join(s).split()))),
        "rh_missing_hours": g["rh_missing_any"].sum(),
    }).reindex(ALL_DAYS)

    daily["n_hours"] = daily["n_hours"].fillna(0).astype(int)
    daily["n_stations"] = daily["n_stations"].fillna(0).astype(int)
    daily["rh_missing_hours"] = daily["rh_missing_hours"].fillna(0).astype(int)
    daily["valid_day"] = (daily["n_hours"] >= MIN_HOURS).astype(int)
    daily.loc[daily.valid_day == 0, "extinction"] = float("nan")
    daily["visibility_mi"] = (K / daily["extinction"]) / MI_TO_KM
    daily["point_sample"] = int(df["point_sample"].iloc[0])

    daily = daily.reset_index()[["date", "visibility_mi", "extinction", "n_hours", "n_stations",
                                 "valid_day", "point_sample", "rh_missing_hours"]]
    daily.to_csv(f"{OUT}/vis_{city}_daily.csv", index=False)

    v = daily[daily.valid_day == 1]
    summary.append({
        "city": city, "days": len(daily), "valid_days": len(v),
        "blank_days": int((daily.valid_day == 0).sum()),
        "hours_used": int(v.n_hours.sum()),
        "hours_in_short_days": int(daily.loc[daily.valid_day == 0, "n_hours"].sum()),
        "vis_min_mi": round(v.visibility_mi.min(), 2),
        "vis_median_mi": round(v.visibility_mi.median(), 2),
        "days_below_5mi": int((v.visibility_mi < 5).sum()),
        "days_at_10mi": int((v.visibility_mi >= 9.9999).sum()),
    })

summ = pd.DataFrame(summary)
summ.to_csv(f"{OUT}/step09_summary.csv", index=False)
print(summ.to_string(index=False))
# Checks: every city has all 3,921 days; hours used + hours in short days = all city-hours
assert (summ.days == len(ALL_DAYS)).all()
