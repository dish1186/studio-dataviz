"""UTCI Step 6: 1991–2020 normals (±7-day calendar window, Feb 29 -> Feb 28), 10th/90th percentiles,
anomaly and 'abnormally high' (> p90), in °F (D13). Writes the final per-city files.
Rows run 2016-01-01 -> 2026-09-24 (D4) so they line up with METAR and gridMET; days after the UTCI
data end (last complete day 2026-06-12; 2026-06-13 incomplete) are blank rows (valid = 0).
Read-only on inputs. Output: data/processed/utci/final/utci_<city>_daily.csv (+ summary)."""
import pathlib, numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
IN = ROOT/"data/processed/utci/step05_stress"
W = pd.read_csv(ROOT/"data/processed/utci/step02_cell_weights/cell_weights.csv")
OUT = ROOT/"data/processed/utci/final"; OUT.mkdir(parents=True, exist_ok=True)
CITIES = list(dict.fromkeys(W.city))                          # D10 order
BASE = ("1991-01-01", "2020-12-31"); STUDY = ("2016-01-01", "2026-09-24")   # D4 end date
HALF = 7

def doy365(dates):
    """Day of year on a 365-day calendar; Feb 29 -> Feb 28 (= day 59)."""
    d = pd.to_datetime(pd.Series(dates))
    doy = d.dt.dayofyear.to_numpy()
    leap = d.dt.is_leap_year.to_numpy()
    return np.where(leap & (doy >= 60), doy - 1, doy)          # Feb 29 (60) -> 59; later days shift back

summary, base_check = [], []
for city in CITIES:
    d = pd.read_csv(IN/f"utci_{city}_stress.csv")
    d["doy"] = doy365(d.date)
    base = d[(d.date >= BASE[0]) & (d.date <= BASE[1]) & (d.valid == 1)]
    bdoy, bval = base.doy.to_numpy(), base.utci_max_f.to_numpy()
    norm = {}
    for t in range(1, 366):
        dist = np.abs(bdoy - t); dist = np.minimum(dist, 365 - dist)      # circular window
        v = bval[dist <= HALF]
        norm[t] = (v.mean(), np.percentile(v, 10), np.percentile(v, 90), v.size)
    # method check: share of baseline days above their own p90 (should be ~10%)
    bp90 = np.array([norm[t][2] for t in bdoy])
    base_check.append(round(float((bval > bp90).mean() * 100), 2))
    s = d[(d.date >= STUDY[0]) & (d.date <= STUDY[1])].copy()
    s = s.set_index("date").reindex(pd.date_range(*STUDY).strftime("%Y-%m-%d")).rename_axis("date").reset_index()
    s["doy"] = doy365(s.date); s["valid"] = s.valid.fillna(0).astype(int)
    N = np.array([norm[t] for t in s.doy])
    s["normal_f"], s["p10_f"], s["p90_f"] = N[:, 0].round(2), N[:, 1].round(2), N[:, 2].round(2)
    s["n_baseline_values"] = N[:, 3].astype(int)
    s["anomaly_f"] = (s.utci_max_f - N[:, 0]).round(2)
    s["abnormally_high"] = pd.array(np.where(s.valid == 1, (s.utci_max_f > N[:, 2]).astype(int), -1), dtype="Int64")
    s.loc[s.valid == 0, "abnormally_high"] = pd.NA
    w = W[W.city == city].sort_values("weight", ascending=False)
    s["cells_used"] = "; ".join(f"{a:.2f},{b:.2f} ({x*100:.1f}%)" for a, b, x in zip(w.lat, w.lon, w.weight))
    cols = ["date","utci_max_f","utci_max_c","stress_level","stress_category","stress_range_f",
            "normal_f","p10_f","p90_f","anomaly_f","abnormally_high","n_baseline_values","valid","cells_used"]
    s[cols].to_csv(OUT/f"utci_{city}_daily.csv", index=False)
    v = s[s.valid == 1]
    summary.append(dict(city=city, n_rows=len(s), n_valid=len(v), first_row=s.date.min(), last_row=s.date.max(),
        last_valid=v.date.max(), pool_min=int(s.n_baseline_values.min()), pool_max=int(s.n_baseline_values.max()),
        baseline_share_above_p90=base_check[-1],
        share_abnormally_high_2016on=round(v.abnormally_high.astype(int).mean()*100, 1),
        mean_anomaly_f=round(v.anomaly_f.mean(), 2)))
pd.DataFrame(summary).to_csv(OUT/"step06_summary.csv", index=False)
print(pd.DataFrame(summary).to_string(index=False))
