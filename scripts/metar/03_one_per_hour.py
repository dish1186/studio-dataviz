"""
Step 3 · METAR · One reading per airport per hour (keep the haziest).
Groups reports by station + clock hour (13:00-13:59 = hour 13, local time).
Keeps the report with the lowest visibility; ties go to the earliest report.
Also records, for the whole hour: how many reports there were, every weather
code seen, and the highest RH, so Step 5's "remove wet hours" filter can
see wet conditions even if they weren't on the haziest report.

Run from the repo root:  python3 scripts/metar/03_one_per_hour.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step02_valid"
OUT = "data/processed/metar/step03_hourly"
os.makedirs(OUT, exist_ok=True)

summary = []
for path in sorted(glob.glob(f"{IN}/metar_*_valid.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_valid.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    df["hour"] = df["valid"].str[:13] + ":00"           # "2016-01-01 13:53" -> "2016-01-01 13:00"
    df["_vsby"] = pd.to_numeric(df["vsby"])
    df["_relh"] = pd.to_numeric(df["relh"].replace("", None), errors="coerce")
    keys = ["station", "hour"]

    # Hour-level context from ALL reports in the hour
    n = df.groupby(keys).size().rename("n_reports_in_hour")
    relh_max = df.groupby(keys)["_relh"].max().rename("relh_max_in_hour")
    wx = df[df["wxcodes"] != ""]
    wx_any = (wx.groupby(keys)["wxcodes"]
                .agg(lambda s: " ".join(sorted(set(" ".join(s).split()))))
                .rename("wx_any_in_hour"))

    # Pick the haziest report per hour (ties -> earliest)
    pick = (df.sort_values(keys + ["_vsby", "valid"])
              .drop_duplicates(keys, keep="first")
              .set_index(keys))
    out = (pick[["valid", "vsby", "relh", "wxcodes"]]
             .join([n, relh_max, wx_any])
             .reset_index()
             .rename(columns={"valid": "picked_report_time"}))
    out["wx_any_in_hour"] = out["wx_any_in_hour"].fillna("")
    out = out.sort_values(keys)
    out.to_csv(f"{OUT}/metar_{city}_hourly.csv", index=False)

    for station, g in out.groupby("station"):
        rows_in = int((df["station"] == station).sum())
        summary.append({
            "city": city, "station": station,
            "reports_in": rows_in,
            "hours_out": len(g),
            "hours_with_multiple_reports": int((g["n_reports_in_hour"] > 1).sum()),
            "reports_collapsed": rows_in - len(g),
        })

summ = pd.DataFrame(summary)
summ.to_csv(f"{OUT}/step03_summary.csv", index=False)
print(summ.to_string(index=False))
t = summ[["reports_in", "hours_out", "reports_collapsed"]].sum()
print(f"\nTOTAL reports in {t.reports_in} -> hours out {t.hours_out} (collapsed {t.reports_collapsed})")
assert t.reports_in == t.hours_out + t.reports_collapsed
