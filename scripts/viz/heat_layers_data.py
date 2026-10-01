# Visualization V7 data · weekly heat layers for Boston, Detroit, Eugene, Bakersfield ("Heat Layers" page).
#
# One row per city and Trends week (Sunday-Saturday), 2021-09-26 to 2026-09-20 (the last, partial week is dropped):
#   high_F      mean of the 7 gridMET daily maxima                         data/raw/gridmet/climateengine/gridmet_tmax_<city>_2016-2026.csv
#   felt_F      mean of the 7 UTCI daily maxima (all 7 valid; ends 2026-06-12) data/processed/utci/final/utci_<city>_daily.csv
#   icecream    weekly Google Trends "ice cream" index                     data/raw/google-trends/icecream-search-weekly/
#   ac          Google Trends "air conditioner": weekly for Boston and Detroit (data/raw/google-trends/heat-search-weekly/);
#               MONTHLY for Eugene and Bakersfield (no weekly file): each week takes its month's value
#               (data/raw/google-trends/heat-search/, "air conditioner" column); ac_resolution says which.
#   er          HRI ED visits per 100,000 ED visits, weekly, HHS region (Region 1 Boston, 5 Detroit, 10 Eugene, 9 Bakersfield),
#               data/processed/cdc-tracking/weekly_hri_ed_rate_by_hhs_region.csv; the week ending Saturday S is matched to the
#               Trends week starting S - 6 days.
# Every source file is read only. Each signal is also given its within-city percentile (0-1) across the weeks, so
# signals on different scales can be compared ("how unusual is this week for this city").
# Run from the repo root: python3 scripts/viz/heat_layers_data.py
import csv, datetime as dt, json, os, statistics as st

CITIES = {"boston": ("boston_ice_5yr.csv", "boston_manch_trends_aircon_5yr.csv", None, "Region 1"),
          "detroit": ("detroit_ice_5yr.csv", "detroit_trends_aircon_5yr.csv", None, "Region 5"),
          "eugene": ("eugene_ice_5yr.csv", None, "eugene-or-heat-search.csv", "Region 10"),
          "bakersfield": ("bakersfield_ice_5yr.csv", None, "bakersfield-ca-heat-search.csv", "Region 9")}
OUT = "data/processed/viz"
os.makedirs(OUT, exist_ok=True)


def trends_weekly(path):
    L = open(path, encoding="utf-8").read().splitlines()
    return {dt.date.fromisoformat(a): int(b) for a, b in (l.split(",") for l in L[3:] if l)}


def daily(path, col=None):
    if col is None:   # gridMET: header line, then "date",value
        L = open(path, encoding="utf-8-sig").read().splitlines()[1:]
        return {dt.date.fromisoformat(a.strip('"')): float(b) for a, b in (l.split(",") for l in L if l)}
    return {dt.date.fromisoformat(r["date"]): float(r[col]) for r in csv.DictReader(open(path, encoding="utf-8"))
            if r["valid"] == "1" and r[col] != ""}


er = {}
for r in csv.DictReader(open("data/processed/cdc-tracking/weekly_hri_ed_rate_by_hhs_region.csv", encoding="utf-8")):
    er[(r["hhs_region"], dt.date.fromisoformat(r["week_ending"]) - dt.timedelta(6))] = float(r["hri_ed_per_100k_ed_visits"])

rows = []
for city, (ice_f, acw_f, acm_f, region) in CITIES.items():
    ice = trends_weekly(f"data/raw/google-trends/icecream-search-weekly/{ice_f}")
    acw = trends_weekly(f"data/raw/google-trends/heat-search-weekly/{acw_f}") if acw_f else None
    acm = {r["Time"][:7]: int(r["air conditioner"]) for r in csv.DictReader(open(f"data/raw/google-trends/heat-search/{acm_f}", encoding="utf-8"))} if acm_f else None
    tmax = daily(f"data/raw/gridmet/climateengine/gridmet_tmax_{city}_2016-2026.csv")
    utci = daily(f"data/processed/utci/final/utci_{city}_daily.csv", "utci_max_f")
    for w in sorted(ice)[:-1]:
        days = [w + dt.timedelta(k) for k in range(7)]
        hi = [tmax.get(d) for d in days]; fe = [utci.get(d) for d in days]
        rows.append({"city": city, "week_start": w.isoformat(),
                     "high_F": round(st.mean(hi), 1) if None not in hi else "",
                     "felt_F": round(st.mean(fe), 1) if None not in fe else "",
                     "icecream": ice[w],
                     "ac": acw[w] if acw else acm.get(f"{w.year}-{w.month:02d}", ""),
                     "ac_resolution": "weekly" if acw else "monthly",
                     "er": er.get((region, w), ""), "er_region": region})

for city in CITIES:
    R = [r for r in rows if r["city"] == city]
    for k in ("high_F", "felt_F", "icecream", "ac", "er"):
        vals = sorted(r[k] for r in R if r[k] != "")
        for r in R:
            r[k + "_pct"] = "" if r[k] == "" else round(sum(v <= r[k] for v in vals) / len(vals), 3)

cols = list(rows[0])
with open(f"{OUT}/heat_layers_weekly.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
for city in CITIES:
    R = [r for r in rows if r["city"] == city]
    print(city, len(R), "weeks; missing high", sum(r["high_F"] == "" for r in R), "felt", sum(r["felt_F"] == "" for r in R),
          "ac", sum(r["ac"] == "" for r in R), "er", sum(r["er"] == "" for r in R))
