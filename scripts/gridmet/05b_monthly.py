"""gridMET Step 5b: monthly roll-up of the final daily files (Procedure 2, step 6).
Input: data/processed/gridmet/final/temp_<city>_daily.csv (Step 5; read-only).
Output: data/processed/gridmet/final/temp_<city>_monthly.csv, one row per calendar month
2016-01 -> 2026-09 (129 rows; Sep 2026 is partial, 24 days), + step05b_summary.csv."""
import pathlib, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
F = ROOT/"data/processed/gridmet/final"
CITIES = ["losangeles","phoenix","sandiego","detroit","bakersfield","sanfrancisco",
          "fresno","boston","eugene","brownsville","annarbor"]            # D10 order, gridMET only

summary = []
for city in CITIES:
    d = pd.read_csv(F/f"temp_{city}_daily.csv")
    d["month"] = d.date.str[:7]                                            # YYYY-MM
    g = d.groupby("month", sort=True)
    hot = d.loc[g.tmax_f.idxmax()].set_index("month")                     # first day if tied
    m = pd.DataFrame({
        "n_days":            g.size(),
        "days_in_month":     g.date.first().map(lambda s: pd.Period(s[:7]).days_in_month),
        "tmax_mean_f":       g.tmax_f.mean().round(2),
        "normal_mean_f":     g.normal_f.mean().round(2),
        "anomaly_mean_f":    g.anomaly_f.mean().round(2),
        "n_abnormally_high": g.abnormally_high.sum().astype(int),
        "hottest_date":      hot.date,
        "hottest_tmax_f":    hot.tmax_f,
    }).reset_index()
    m["complete"] = (m.n_days == m.days_in_month).astype(int)
    m.to_csv(F/f"temp_{city}_monthly.csv", index=False)
    summary.append(dict(city=city, n_months=len(m), n_complete=int(m.complete.sum()),
        days_total=int(m.n_days.sum()), abnormally_high_total=int(m.n_abnormally_high.sum()),
        most_abnormal_month=m.loc[m.n_abnormally_high.idxmax(), "month"],
        most_abnormal_n=int(m.n_abnormally_high.max()),
        warmest_anomaly_month=m.loc[m.anomaly_mean_f.idxmax(), "month"],
        warmest_anomaly_f=m.anomaly_mean_f.max()))
pd.DataFrame(summary).to_csv(F/"step05b_summary.csv", index=False)
print(pd.DataFrame(summary).to_string(index=False))
