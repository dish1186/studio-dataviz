"""Build data.json for the Heat Field visualization (V10).
Per city, May-Sep 2022-2026: each day placed by abnormality (x) and felt heat (y),
with the heat-ER rate for its HHS region and the Google Trends value of the week it falls in.
Run from the repo root: python3 viz/heat-field/build.py
"""
import csv, json, datetime as dt, collections as C

CITIES = {  # city: (label, HHS region, AC trends file, ice cream trends file)
    "detroit": ("Detroit", "Region 5", "detroit_trends_aircon_5yr.csv", "detroit_ice_5yr.csv"),
    "boston": ("Boston", "Region 1", "boston_manch_trends_aircon_5yr.csv", "boston_ice_5yr.csv"),
    "eugene": ("Eugene", "Region 10", "eugene_aircon_5yr.csv", "eugene_ice_5yr.csv"),
    "bakersfield": ("Bakersfield", "Region 9", "bakersfield_aircon_5yr.csv", "bakersfield_ice_5yr.csv"),
    "phoenix": ("Phoenix", "Region 9", "phoenix_trends_aircon_5yr.csv", "phoenix_ice_5yr.csv"),
    "sandiego": ("San Diego", "Region 9", "sandiego_trends_aircon_5yr.csv", "sandiego_ice_5yr.csv"),
    "sanfrancisco": ("San Francisco", "Region 9", "sanfran_metro_trends_aircon_5yr.csv", "san fran_ice_5yr.csv"),
}
DANGER = {"Strong heat stress", "Very strong heat stress", "Extreme heat stress"}
summer = lambda d: 5 <= int(d[5:7]) <= 9 and "2022" <= d[:4] <= "2026"

def pct(vals):
    """Share of values strictly below each value, plus half the ties (mid-rank percentile)."""
    s = sorted(vals); n = len(s); out = {}
    for v in set(vals):
        lo = sum(1 for x in s if x < v); eq = sum(1 for x in s if x == v)
        out[v] = (lo + eq / 2) / n
    return out

ER = C.defaultdict(dict)
for r in csv.DictReader(open("data/processed/cdc-tracking/daily_hri_ed_rate_by_hhs_region.csv")):
    if r["suppressed"] == "0":
        ER[r["hhs_region"]][r["date"]] = float(r["hri_ed_per_100k_ed_visits"])

def trends(folder, f):
    rows = list(csv.reader(open(f"data/raw/google-trends/{folder}/{f}")))[3:]
    # keep weeks that overlap May-Sep (a week starting up to 6 days before May 1 still covers May days)
    keep = lambda w: "2022" <= w[:4] <= "2026" and (summer(w) or w[5:] >= "04-25" and w[5:7] == "04")
    return {w: (0 if v == "<1" else int(v)) for w, v in rows if w and keep(w)}

out = {}
for c, (label, reg, acf, icf) in CITIES.items():
    U = {r["date"]: r for r in csv.DictReader(open(f"data/processed/utci/final/utci_{c}_daily.csv"))}
    days = []
    for r in csv.DictReader(open(f"data/processed/gridmet/final/temp_{c}_daily.csv")):
        d = r["date"]
        if not summer(d): continue
        u = U.get(d, {})
        if not u.get("utci_max_f"): continue  # no felt heat -> cannot be placed on the danger axis
        t, n, p90 = float(r["tmax_f"]), float(r["normal_f"]), float(r["p90_f"])
        days.append({"d": d, "t": t, "n": n, "p90": p90, "x": (t - n) / (p90 - n),
                     "f": float(u["utci_max_f"]), "c": u["stress_category"], "er": ER[reg].get(d)})
    ac, ic = trends("heat-search-weekly", acf), trends("icecream-search-weekly", icf)
    acp, icp = pct(list(ac.values())), pct(list(ic.values()))
    def week_of(d):  # Google Trends weeks start on Sunday
        x = dt.date.fromisoformat(d); return (x - dt.timedelta((x.weekday() + 1) % 7)).isoformat()
    erp = pct([x["er"] for x in days if x["er"] is not None])
    out[c] = {"label": label, "region": reg, "last": days[-1]["d"],
              # [date, high, normal, p90, abnormality, felt, stress category, ER rate, ER pct, AC, AC pct, ice, ice pct]
              "days": [[x["d"], round(x["t"], 1), round(x["n"], 1), round(x["p90"], 1), round(x["x"], 3), round(x["f"], 1),
                        x["c"], x["er"], None if x["er"] is None else round(erp[x["er"]], 3),
                        ac.get(week_of(x["d"])), None if week_of(x["d"]) not in ac else round(acp[ac[week_of(x["d"])]], 3),
                        ic.get(week_of(x["d"])), None if week_of(x["d"]) not in ic else round(icp[ic[week_of(x["d"])]], 3)]
                       for x in days]}
    print(c, len(days), "days, last felt", days[-1]["d"], "| no AC week:", sum(r[9] is None for r in out[c]["days"]))
json.dump(out, open("viz/heat-field/data.json", "w"), separators=(",", ":"))
