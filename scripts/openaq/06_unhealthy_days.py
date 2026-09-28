# OpenAQ Step 6 · unhealthy PM2.5 days per city and day (for the "Unhealthy Air Days" calendar, Visualization V3).
#
# Input: the Step 5 sensor-day audit files (data/processed/openaq/step05_averages/audit/), so Step 5's rules carry over:
# negatives set to 0, flagged low-cost days out, low-cost outlier rule, sites = sensors within 50 m (Step 3).
# Two versions of each day:
#   strict  = Step 5 included sensor-days only (>= 18 of 24 hours observed; 40 CFR 50 App. N)
#   partial = strict, plus sensor-days excluded ONLY for too few hours that have >= 12 hours (low-cost ones must also be
#             unflagged and <= 1,000 µg/m³). A site uses its strict sensor-days when it has any that day; otherwise its
#             partial ones, and the site-day is then marked partial.
# Site-day = mean of the site's sensor-days used. For each version and each sensor subset (all / reference / low-cost):
#   n_sites, n_above35 (site-days above 35 µg/m³), max_site (highest site-day), plus site IDs above 35.
# "Above 35": the site-day truncated to 1 decimal is >= 35.5 µg/m³, i.e. EPA AQI "Unhealthy for Sensitive Groups" or
# worse (40 CFR Part 58 App. G, Table 2: PM2.5 is truncated to 1 decimal; USG starts at 35.5). 35 µg/m³ is the level of
# the 24-hour PM2.5 standard (40 CFR 50.13).
# Category of max_site (truncated): 0 Good 0.0-9.0 · 1 Moderate 9.1-35.4 · 2 USG 35.5-55.4 · 3 Unhealthy 55.5-125.4 ·
#   4 Very Unhealthy 125.5-225.4 · 5 Hazardous >= 225.5.
# single_lowcost_flag (partial, all sensors): exactly one site above 35, it is low-cost, and no reference site is above 35
# on a day when at least one other site reported (a possible single-sensor artefact; marked, not removed; Gina 2026-09-28).
# Every date of the study period gets a row per city.
# Run from the repo root: python3 scripts/openaq/06_unhealthy_days.py
import csv, datetime, math, os, statistics
from collections import defaultdict

START, END = datetime.date(2016, 3, 6), datetime.date(2026, 9, 25)
IN = "data/processed/openaq/step05_averages/audit"
OUT = "data/processed/openaq/unhealthy_days"
MIN_PARTIAL_HOURS, CEILING = 12, 1000.0
CITIES = ["annarbor", "bakersfield", "boston", "brownsville", "delano", "detroit", "eugene", "fairbanks", "fresno",
          "losangeles", "phoenix", "raymondville", "sandiego", "sanfrancisco", "springfield", "warren"]
BREAKS = [9.0, 35.4, 55.4, 125.4, 225.4]
trunc1 = lambda v: math.floor(v * 10 + 1e-9) / 10
cat = lambda v: sum(trunc1(v) > b for b in BREAKS)
above = lambda v: trunc1(v) >= 35.5
DATES = [(START + datetime.timedelta(d)).isoformat() for d in range((END - START).days + 1)]
os.makedirs(OUT, exist_ok=True)

summary = []
for city in CITIES:
    fn = f"{IN}/sensor_day_audit_{city}.csv"
    rows = list(csv.DictReader(open(fn, encoding="utf-8"))) if os.path.exists(fn) else []
    by = defaultdict(lambda: {"strict": [], "partial": []})       # (date, site) -> sensor-day values
    cls = {}
    for r in rows:
        if r["pm25_used"] in ("", "None"):
            continue
        v, key = float(r["pm25_used"]), (r["date_local"], r["site_id"])
        cls[r["site_id"]] = r["sensor_class"]
        if r["included"] == "1":
            by[key]["strict"].append(v)
        elif (r["exclusion_reason"].startswith("fewer than") and int(r["hours_observed"] or 0) >= MIN_PARTIAL_HOURS
              and not (r["sensor_class"] == "low-cost" and r["has_flags"] == "True") and v <= CEILING):
            by[key]["partial"].append(v)
    days = defaultdict(lambda: {"strict": [], "partial": []})       # date -> [(site, class, value, is_partial)]
    for (d, s), e in by.items():
        if e["strict"]:
            m = statistics.mean(e["strict"])
            days[d]["strict"].append((s, cls[s], m, 0)); days[d]["partial"].append((s, cls[s], m, 0))
        elif e["partial"]:
            days[d]["partial"].append((s, cls[s], statistics.mean(e["partial"]), 1))
    out = []
    for d in DATES:
        row = {"date": d}
        for mode in ("strict", "partial"):
            for sub, keep in (("all", None), ("ref", "reference"), ("low", "low-cost")):
                L = [x for x in days[d][mode] if keep is None or x[1] == keep]
                ab = [x for x in L if above(x[2])]
                mx = max((x[2] for x in L), default=None)
                row[f"n_sites_{mode}_{sub}"] = len(L)
                row[f"n_above35_{mode}_{sub}"] = len(ab)
                row[f"max_site_{mode}_{sub}"] = "" if mx is None else round(mx, 2)
                row[f"worst_category_{mode}_{sub}"] = "" if mx is None else cat(mx)
            row[f"sites_above35_{mode}"] = "; ".join(sorted(x[0] for x in days[d][mode] if above(x[2])))
        P = days[d]["partial"]
        row["partial_day"] = int(any(x[3] for x in P))
        abP = [x for x in P if above(x[2])]
        row["single_lowcost_flag"] = int(len(abP) == 1 and abP[0][1] == "low-cost" and len(P) >= 2)
        out.append(row)
    with open(f"{OUT}/unhealthy_days_{city}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    summary.append({"city": city,
                    "days_with_data_partial_all": sum(r["n_sites_partial_all"] > 0 for r in out),
                    "days_above35_strict_ref": sum(r["n_above35_strict_ref"] > 0 for r in out),
                    "days_above35_partial_ref": sum(r["n_above35_partial_ref"] > 0 for r in out),
                    "days_above35_partial_all": sum(r["n_above35_partial_all"] > 0 for r in out),
                    "single_lowcost_flag_days": sum(r["single_lowcost_flag"] for r in out)})
with open(f"{OUT}/unhealthy_days_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
for s in summary:
    print(s)
