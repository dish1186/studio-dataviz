"""ERA5-Land Step 3 (Fairbanks): 1991-2020 normals, anomalies, abnormally high, monthly roll-up.
Exact recipe of gridMET Step 5 / 5b (scripts/gridmet/05_normals_final.py, 05b_monthly.py) and UTCI Step 6.
Outputs go to data/processed/gridmet/final/ with the gridMET file names and columns, so the viz loads all
12 cities the same way (decided by Dish); the SOURCE for Fairbanks is ERA5-Land, not gridMET.
  temp_fairbanks_daily.csv    3,920 rows 2016-01-01 -> 2026-09-24 (D4); blank after the data end
  temp_fairbanks_normals.csv  365 rows
  temp_fairbanks_monthly.csv  129 rows (n_days = days with a value)
Summary: data/processed/era5land/step03_summary.csv. Read-only on inputs."""
import pathlib, numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
IN = ROOT/"data/processed/era5land/step02_daily/fairbanks_daily_max.csv"
OUT = ROOT/"data/processed/gridmet/final"
BASE = ("1991-01-01", "2020-12-31"); STUDY = ("2016-01-01", "2026-09-24"); HALF = 7

def doy365(dates):
    d = pd.to_datetime(pd.Series(dates)); doy = d.dt.dayofyear.to_numpy()
    return np.where(d.dt.is_leap_year.to_numpy() & (doy >= 60), doy - 1, doy)

d = pd.read_csv(IN)
base = d[(d.date >= BASE[0]) & (d.date <= BASE[1]) & (d.valid == 1)]
bdoy, bval = doy365(base.date), base.tmax_f.to_numpy()
norm = {}
for t in range(1, 366):
    dist = np.abs(bdoy - t); dist = np.minimum(dist, 365 - dist)
    v = bval[dist <= HALF]
    norm[t] = (v.mean(), np.percentile(v, 10), np.percentile(v, 90), v.size)
MD = pd.date_range("2021-01-01", "2021-12-31").strftime("%m-%d")
pd.DataFrame({"month_day": MD,
              "normal_f": [round(norm[t][0], 2) for t in range(1, 366)],
              "p10_f": [round(norm[t][1], 2) for t in range(1, 366)],
              "p90_f": [round(norm[t][2], 2) for t in range(1, 366)],
              "n_baseline_values": [norm[t][3] for t in range(1, 366)]}).to_csv(OUT/"temp_fairbanks_normals.csv", index=False)
bshare = round(float((bval > np.array([norm[t][2] for t in bdoy])).mean() * 100), 2)

s = d.set_index("date").reindex(pd.date_range(*STUDY).strftime("%Y-%m-%d")).rename_axis("date").reset_index()
s.loc[s.valid != 1, "tmax_f"] = np.nan
N = np.array([norm[t] for t in doy365(s.date)]); tmax = s.tmax_f.to_numpy()
out = pd.DataFrame({"date": s.date, "tmax_f": tmax,
    "normal_f": N[:, 0].round(2), "p10_f": N[:, 1].round(2), "p90_f": N[:, 2].round(2),
    "anomaly_f": (tmax - N[:, 0]).round(2),
    "abnormally_high": pd.array(np.where(np.isnan(tmax), 0, tmax > N[:, 2]).astype(int), dtype="Int64"),
    "n_baseline_values": N[:, 3].astype(int)})
out.loc[np.isnan(tmax), "abnormally_high"] = pd.NA
out.to_csv(OUT/"temp_fairbanks_daily.csv", index=False)

v = out.dropna(subset=["tmax_f"]).copy(); v["month"] = v.date.str[:7]
g = v.groupby("month", sort=True); hot = v.loc[g.tmax_f.idxmax()].set_index("month")
m = pd.DataFrame({"n_days": g.size(),
    "days_in_month": [pd.Period(x).days_in_month for x in g.size().index],
    "tmax_mean_f": g.tmax_f.mean().round(2), "normal_mean_f": g.normal_f.mean().round(2),
    "anomaly_mean_f": g.anomaly_f.mean().round(2), "n_abnormally_high": g.abnormally_high.sum().astype(int),
    "hottest_date": hot.date, "hottest_tmax_f": hot.tmax_f}).reset_index()
m["complete"] = (m.n_days == m.days_in_month).astype(int)
m.to_csv(OUT/"temp_fairbanks_monthly.csv", index=False)

summ = pd.DataFrame([dict(city="fairbanks", source="ERA5-Land hourly time-series (CDS), 8 cells area-weighted",
    n_rows=len(out), n_blank=int(out.tmax_f.isna().sum()), first_row=out.date.min(), last_row=out.date.max(),
    last_valid=v.date.max(), pool_min=int(out.n_baseline_values.min()), pool_max=int(out.n_baseline_values.max()),
    baseline_share_above_p90=bshare, share_abnormally_high_2016on=round(v.abnormally_high.astype(int).mean()*100, 1),
    mean_anomaly_f=round(v.anomaly_f.mean(), 2), hottest_day=v.loc[v.tmax_f.idxmax(), "date"], hottest_tmax_f=v.tmax_f.max(),
    n_months=len(m), most_abnormal_month=m.loc[m.n_abnormally_high.idxmax(), "month"],
    most_abnormal_n=int(m.n_abnormally_high.max()),
    warmest_anomaly_month=m.loc[m.anomaly_mean_f.idxmax(), "month"], warmest_anomaly_f=m.anomaly_mean_f.max())])
summ.to_csv(ROOT/"data/processed/era5land/step03_summary.csv", index=False)
print(summ.T.to_string(header=False))
