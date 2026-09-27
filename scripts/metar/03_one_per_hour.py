"""
Step 3 · METAR · One reading per airport per hour (keep the haziest).
Groups reports by station + clock hour (13:00-13:59 = hour 13, local time).
Keeps the report with the lowest visibility; ties go to the earliest report.
Also records, for the whole hour: how many reports there were, every weather
code seen, and the highest RH, so Step 5's "remove wet hours" filter can
see wet conditions even if they weren't on the haziest report.

D6 (added for the 17-city rerun, amended by Dish): for DLO and VLL (reports at
:15/:35/:55, drifting to :14/:34/:54 or :56 in some periods), one report per hour
is used: the one at :54-:56 closest to :55 (tie -> earliest). All other reports
are saved to metar_<city>_awos_set_aside.csv.

Run from the repo root:  python3 scripts/metar/03_one_per_hour.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step02_valid"
OUT = "data/processed/metar/step03_hourly"
os.makedirs(OUT, exist_ok=True)

AWOS_55_ONLY = {"DLO", "VLL"}   # D6 (amended): 3-reports-per-hour stations -> one report per hour at :54-:56
AWOS_MINUTES = {"54": 1, "55": 0, "56": 1}   # accepted minutes -> distance from :55 (closest wins; tie -> earliest)

summary = []
for path in sorted(glob.glob(f"{IN}/metar_*_valid.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_valid.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows_read = df.groupby("station").size()             # per station, before the D6 set-aside

    # D6 (amended): for DLO/VLL keep one report per hour at :54-:56 (closest to :55,
    # tie -> earliest); set every other report aside in an audit file
    is_awos = df["station"].isin(AWOS_55_ONLY)
    minute = df["valid"].str[14:16]
    dist = minute.map(AWOS_MINUTES)                       # NaN if not :54/:55/:56
    cand = df[is_awos & dist.notna()].assign(_d=dist, _h=df["valid"].str[:13])
    keep_idx = cand.sort_values(["station", "_h", "_d", "valid"]).drop_duplicates(["station", "_h"]).index
    is_set_aside = is_awos & ~df.index.isin(keep_idx)
    if is_set_aside.any():
        df[is_set_aside].to_csv(f"{OUT}/metar_{city}_awos_set_aside.csv", index=False)
    set_aside_by_station = df[is_set_aside].groupby("station").size()
    df = df[~is_set_aside].copy()

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
        rows_in = int(rows_read[station])
        set_aside = int(set_aside_by_station.get(station, 0))
        summary.append({
            "city": city, "station": station,
            "reports_in": rows_in,
            "awos_set_aside": set_aside,
            "hours_out": len(g),
            "hours_with_multiple_reports": int((g["n_reports_in_hour"] > 1).sum()),
            "reports_collapsed": rows_in - set_aside - len(g),
        })

summ = pd.DataFrame(summary)
summ.to_csv(f"{OUT}/step03_summary.csv", index=False)
print(summ.to_string(index=False))
t = summ[["reports_in", "awos_set_aside", "hours_out", "reports_collapsed"]].sum()
print(f"\nTOTAL reports in {t.reports_in} -> hours out {t.hours_out} "
      f"(set aside {t.awos_set_aside}, collapsed {t.reports_collapsed})")
assert t.reports_in == t.hours_out + t.awos_set_aside + t.reports_collapsed
