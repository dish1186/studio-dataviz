"""gridMET Step 5: 1991-2020 normals of the daily high (±7-day calendar window, Feb 29 -> Feb 28),
10th/90th percentiles, anomaly and 'abnormally high' (> p90), in °F. Same recipe as UTCI Step 6
(scripts/utci/06_normals_final.py) so the two join on date row for row.
Cities: the 11 gridMET cities of D10 (Fairbanks has no gridMET; Pittsburgh, Warren, Delano,
Raymondville, Springfield are not processed).
Read-only on inputs: raw ClimateEngine CSVs are checked against the SHA-256 in the log and never written.
Outputs (data/processed/gridmet/final/):
  temp_<city>_daily.csv    3,920 rows, 2016-01-01 -> 2026-09-24 (D4)
  temp_<city>_normals.csv  365 rows, one per calendar day (Feb 29 folded into Feb 28)
  step05_summary.csv"""
import hashlib, pathlib, numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT/"data/raw/gridmet/climateengine"
OUT = ROOT/"data/processed/gridmet/final"; OUT.mkdir(parents=True, exist_ok=True)
BASE = ("1991-01-01", "2020-12-31"); STUDY = ("2016-01-01", "2026-09-24")   # D4 end date
HALF = 7

# D10 order, gridMET cities only. SHA-256 from the log (Step 4 final, Step 4b): (baseline, study)
SHA = {
 "losangeles":   ("fe4b8b45cdcb22e29118be7fead545b2ef92ad6b81dfc0f25b9b0a7451268a34", "bb64c2829a1f01b68f556efe447a0588c1b7e063cceef4ced184c1059a6721ea"),
 "phoenix":      ("39af3dfac0a8617e56efa6fd611990d881215a2d0f0ef92f013f4e7aecc91f02", "6304dff1f202be86ac4aa68d21e33eec6e5fa09ddac58cca7eeac79d04ed244c"),
 "sandiego":     ("d0513df795492cab0f1c4553a43474961359077037d3d81c24e88ffa7552c80b", "144f68309dae3687401dc86aa7fc3645ff6074db04ec3e7f5210e3d5be6834d3"),
 "detroit":      ("289697e61b46ccd46aba6f88a036414857e6d5a13eadcbfee5c4c602313059cf", "23b99a51719cfd46119ae9c216664c5ffd0d99ecff3d84387c34fb1313c7a4b8"),
 "bakersfield":  ("c09960f59715601a9cd10d0e87148b254c218caed59e3c87cdbff1648eb6b70b", "2ae64c2a7830c3e70fa7b18a374d21fbf6ec72287bdff8af720c0de23552480b"),
 "sanfrancisco": ("6ed70bd8bc7fb4e8a0d75c0fe0b288c4babb33e078cd770ca6d24340cc17dd87", "d3b51456d12e35ee117a042ff39e1da4d07316da9740f52bd9389097f1c680e0"),
 "fresno":       ("0378ed17f7c4440d637c80983a8e72f3b49efc82bf4e9f3f8970a3fd5b645c28", "58eefa65bffd9c7ea4684f426e726214bdf60db82856fc01d2166add2126632b"),
 "boston":       ("0f682e54c6d4750674d86351a618e0ce904f12221700b607aea345af22a1370c", "8a043cc9317264b2da10cb76778ebcacbc53b58e59251a1a3f9a8f53c89cb394"),
 "eugene":       ("f4248f0a6e442015b7c2b9bd9ba5390cb77236b406d96bb8634bf706138b56e8", "1fc690435505f0013d7557e4c0bc40d771c2078872c4e7d85fe2e3f6974a00d3"),
 "brownsville":  ("57c129af19bb4a8baea4105c16590852d7a425f373a8f3d7271575069abeed75", "44c7be1de0a742b4fd011c16ec0b2f52861a946b075c48c314140046d73ff40c"),
 "annarbor":     ("561168597916315e44de093b528a00b64c64a47a7884f7db21dc4644d4657bb2", "9f60d57019555b8332bb294d7fc99390a2f0ca6d88334d356db3cccce4dbeecb"),
}

def read_raw(path, expected_sha):
    """Read one ClimateEngine CSV (BOM + header line with GEOID; columns date, value). Stops on hash mismatch."""
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    if h != expected_sha:
        raise SystemExit(f"SHA-256 mismatch for {path.name}: {h}")
    d = pd.read_csv(path, encoding="utf-8-sig", skiprows=1, header=None, names=["date", "tmax"])
    d["tmax"] = d.tmax.astype(float)
    return d

def doy365(dates):
    """Day of year on a 365-day calendar; Feb 29 -> Feb 28 (= day 59)."""
    d = pd.to_datetime(pd.Series(dates))
    doy = d.dt.dayofyear.to_numpy()
    leap = d.dt.is_leap_year.to_numpy()
    return np.where(leap & (doy >= 60), doy - 1, doy)

# month-day label for each of the 365 calendar days (non-leap year; Feb 29 is folded into Feb 28)
MD = pd.date_range("2021-01-01", "2021-12-31").strftime("%m-%d")

summary = []
for city, (sha_base, sha_study) in SHA.items():
    base = read_raw(RAW/f"gridmet_tmax_{city}_1991-2020.csv", sha_base)
    study = read_raw(RAW/f"gridmet_tmax_{city}_2016-2026.csv", sha_study)
    base = base[(base.date >= BASE[0]) & (base.date <= BASE[1])].dropna(subset=["tmax"])
    bdoy, bval = doy365(base.date), base.tmax.to_numpy()

    norm = {}
    for t in range(1, 366):
        dist = np.abs(bdoy - t); dist = np.minimum(dist, 365 - dist)      # circular window (wraps New Year)
        v = bval[dist <= HALF]
        norm[t] = (v.mean(), np.percentile(v, 10), np.percentile(v, 90), v.size)

    # normals table (365 rows)
    nt = pd.DataFrame({"month_day": MD,
                       "normal_f": [round(norm[t][0], 2) for t in range(1, 366)],
                       "p10_f":    [round(norm[t][1], 2) for t in range(1, 366)],
                       "p90_f":    [round(norm[t][2], 2) for t in range(1, 366)],
                       "n_baseline_values": [norm[t][3] for t in range(1, 366)]})
    nt.to_csv(OUT/f"temp_{city}_normals.csv", index=False)

    # method check: share of baseline days above their own p90 (~10% expected)
    bp90 = np.array([norm[t][2] for t in bdoy])
    base_share = round(float((bval > bp90).mean() * 100), 2)

    # daily file on the full D4 calendar (reindex so any gap would show as a blank row)
    s = study.set_index("date").reindex(pd.date_range(*STUDY).strftime("%Y-%m-%d")).rename_axis("date").reset_index()
    N = np.array([norm[t] for t in doy365(s.date)])
    tmax = s.tmax.to_numpy()
    out = pd.DataFrame({"date": s.date,
                        "tmax_f": tmax.round(2),
                        "normal_f": N[:, 0].round(2), "p10_f": N[:, 1].round(2), "p90_f": N[:, 2].round(2),
                        "anomaly_f": (tmax - N[:, 0]).round(2),                # before rounding
                        "abnormally_high": (tmax > N[:, 2]).astype(int),       # strict, unrounded values
                        "n_baseline_values": N[:, 3].astype(int)})
    out.to_csv(OUT/f"temp_{city}_daily.csv", index=False)

    hot = out.loc[out.tmax_f.idxmax()]
    summary.append(dict(city=city, n_rows=len(out), n_blank=int(out.isna().any(axis=1).sum()),
        first_row=out.date.min(), last_row=out.date.max(),
        pool_min=int(out.n_baseline_values.min()), pool_max=int(out.n_baseline_values.max()),
        baseline_share_above_p90=base_share,
        share_abnormally_high_2016on=round(out.abnormally_high.mean() * 100, 1),
        mean_anomaly_f=round(out.anomaly_f.mean(), 2),
        hottest_day=hot.date, hottest_tmax_f=hot.tmax_f))
pd.DataFrame(summary).to_csv(OUT/"step05_summary.csv", index=False)
print(pd.DataFrame(summary).to_string(index=False))
