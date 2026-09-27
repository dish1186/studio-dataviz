"""
Step 8 · METAR · Combine airports into one value per city per hour.
Two-airport cities (Detroit DET+DTW, Pittsburgh AGC+PIT): mean extinction of
the airports with a dry daytime reading that hour (at least 1 of 2).
Single-airport cities: passed through, flagged point_sample = 1.
Each airport's own extinction is kept as its own column (ext_<STATION>).

Run from the repo root:  python3 scripts/metar/08_combine_airports.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step07_extinction"
OUT = "data/processed/metar/step08_city_hourly"
os.makedirs(OUT, exist_ok=True)

summary = []
for path in sorted(glob.glob(f"{IN}/metar_*_extinction.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_extinction.csv", "")
    df = pd.read_csv(path, dtype={"station": str, "hour": str})
    stations = sorted(df["station"].unique())

    # One column per airport: ext_DET, ext_DTW, ... (blank if that airport had no dry reading)
    wide = df.pivot(index="hour", columns="station", values="extinction_km")
    wide.columns = [f"ext_{s}" for s in wide.columns]

    out = wide.copy()
    out["extinction_km"] = wide.mean(axis=1, skipna=True)     # mean of available airports
    out["n_stations"] = wide.notna().sum(axis=1)
    out["stations_reporting"] = wide.notna().apply(
        lambda r: " ".join(s.replace("ext_", "") for s, ok in r.items() if ok), axis=1)
    out["rh_missing_any"] = df.groupby("hour")["rh_missing"].max()
    out["point_sample"] = int(len(stations) == 1)
    out.insert(0, "city", city)
    out = out.reset_index().sort_values("hour")
    out.to_csv(f"{OUT}/metar_{city}_cityhour.csv", index=False)

    row = {"city": city, "stations": " ".join(stations),
           "station_hours_in": len(df), "city_hours_out": len(out),
           "hours_both_airports": int((out.n_stations == 2).sum())}
    for s in stations:
        row[f"hours_only_{s}"] = int((out.stations_reporting == s).sum()) if len(stations) == 2 else None
    summary.append(row)

summ = pd.DataFrame(summary)
summ.to_csv(f"{OUT}/step08_summary.csv", index=False)
print(summ.to_string(index=False))
print(f"\nTOTAL station-hours in {summ.station_hours_in.sum()} -> city-hours out {summ.city_hours_out.sum()}")
