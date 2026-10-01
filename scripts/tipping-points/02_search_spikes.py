"""Tipping points Step 2: start from the reaction. Where do searches jump?

Uses the Google Trends numbers exactly as downloaded (one term each, no sums,
no fitting):
  air  -> "air purifier"      (air-search files)
  heat -> "air conditioner"   (heat-search files)
Jump = this month's value minus last month's value.
For each city and term, the 3 biggest jumps are the "spikes".
For each spike month, reports what the city measured that month:
  air:  worst PM2.5 day (city daily mean, reference first, low-cost where none)
  heat: hottest felt-heat day (UTCI daily high, deg F) and how far above the
        1991-2020 normal for that date it was
Official lines to compare against (not used in any calculation):
  PM2.5 24 h: WHO 2021 guideline 15 µg/m³; EPA "Unhealthy for Sensitive Groups" 35.5
  Felt heat: UTCI "strong heat stress" 89.6 °F (32 °C), "very strong" 100.4 °F (38 °C)

Run from repo root:  python3 scripts/tipping-points/02_search_spikes.py
Writes data/processed/tipping-points/step02_series.csv and step02_spikes.csv.
"""
from pathlib import Path

import pandas as pd

P = Path("data/processed")
OUT = P / "tipping-points"
LAST_FULL_MONTH = "2026-08-01"  # Sept 2026 is partial in Trends
TOP_N = 3
FILES = {  # city: (heat-search file, air-search file)
    "bakersfield": ("bakersfield-ca-heat-search.csv", "bakersfield-ca-air-search.csv"),
    "fresno": ("Fresno-Visalia CA-ca-heat-search.csv", "fresno-visalia-ca-air-search.csv"),
    "brownsville": ("Harlingen-Weslaco-Brownsville-McAllen TX-tx-heat-search.csv",
                    "Harlingen-Weslaco-Brownsville-McAllen TX-air-search.csv"),
    "sanfrancisco": ("San Francisco-Oakland-San Jose CA-ca-heat-search.csv",
                     "San Francisco-Oakland-San Jose CA-ca-air-search.csv"),
    "boston": ("boston MA-Manchester-NH-heat-search.csv", "boston-ma-air-search.csv"),
    "detroit": ("detroit-mi-heat-search.csv", "detroit-mi-air-search.csv"),
    "eugene": ("eugene-or-heat-search.csv", "eugene-or-air-search.csv"),
    "fairbanks": ("fairbanks-ak-heat-search.csv", "fairbanks-ak-air-search.csv"),
    "losangeles": ("losangeles-ca-heat-search.csv", "la-ca-air-search.csv"),
    "phoenix": ("phoenix-az-heat-search.csv", "phoenix-az-air-search.csv"),
    "sandiego": ("sandiego-ca-heat-search.csv", "san diego-ca-air-search.csv"),
}


def trend(folder, f, term):
    t = pd.read_csv(P / "google-trends" / folder / f)
    t = t[t["Time"] <= LAST_FULL_MONTH]
    return pd.DataFrame({"month": t["Time"].str[:7], "searches": t[term].values})


series, spikes = [], []
for city, (hf, af) in FILES.items():
    pm = pd.read_csv(P / f"openaq/step05_averages/pm25_{city}_daily.csv")
    pm["pm"] = pm["ref_mean"].fillna(pm["lowcost_mean"])
    pm = pm.dropna(subset=["pm"])
    ut = pd.read_csv(P / f"utci/final/utci_{city}_daily.csv")
    ut = ut[ut["valid"] == 1]
    for topic, folder, f, term in [("air", "air-search", af, "air purifier"),
                                   ("heat", "heat-search", hf, "air conditioner")]:
        s = trend(folder, f, term)
        s["jump"] = s["searches"].diff()
        s.insert(0, "topic", topic)
        s.insert(0, "city", city)
        s["term"] = term
        s["spike_rank"] = s["jump"].rank(ascending=False, method="first")
        s.loc[s["spike_rank"] > TOP_N, "spike_rank"] = pd.NA
        series.append(s)
        for _, r in s.dropna(subset=["spike_rank"]).iterrows():
            row = {"city": city, "topic": topic, "term": term, "month": r["month"], "rank": int(r["spike_rank"]),
                   "searches": int(r["searches"]), "last_month": int(r["searches"] - r["jump"]), "jump": int(r["jump"])}
            if topic == "air":
                m = pm[pm["date"].str[:7] == r["month"]]
                if len(m):
                    w = m.loc[m["pm"].idxmax()]
                    row.update(worst_pm=round(float(w["pm"]), 1), worst_pm_date=w["date"], pm_days=len(m))
            else:
                m = ut[ut["date"].str[:7] == r["month"]]
                if len(m):
                    w = m.loc[m["utci_max_f"].idxmax()]
                    row.update(hottest_felt_f=round(float(w["utci_max_f"]), 1), hottest_date=w["date"],
                               above_normal_f=round(float(w["anomaly_f"]), 1), stress=w["stress_category"])
            spikes.append(row)

se = pd.concat(series)
se.to_csv(OUT / "step02_series.csv", index=False)
sp = pd.DataFrame(spikes).sort_values(["topic", "city", "rank"])
sp.to_csv(OUT / "step02_spikes.csv", index=False)
pd.set_option("display.width", 220)
print(sp.to_string(index=False))
