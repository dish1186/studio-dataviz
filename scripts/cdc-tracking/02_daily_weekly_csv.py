# CDC Tracking · Step 2 · flatten the daily and weekly HRI emergency-department rates (Step 1 raw JSON) into CSVs.
#
# Input (not modified): data/raw/cdc-tracking/measure_1238_daily_ed_rate_hri_nonva/4_getCoreHolder_<year>.json
#                       data/raw/cdc-tracking/measure_1237_weekly_ed_rate_hri_nonva/4_getCoreHolder_<year>.json
# Rows are read from each file's regionPMTableResult list; values are copied as given (dataValue), not recalculated.
# Units: HRI-associated ED visits per 100,000 ED visits (all causes) in the region, from NSSP syndromic data
# (CDC Heat & Health Tracker description: https://www.cdc.gov/nssp/php/partnerships/cdc-heat-health-tracker-uses-nssp-data.html).
# The API's own label says "per 100,000 population"; values (up to 6,737) only make sense per 100,000 ED visits.
# Region states from data/raw/cdc-tracking/reference/hhs_regions.md (HHS.gov, accessed 2026-09-30).
# Run from the repo root: python3 scripts/cdc-tracking/02_daily_weekly_csv.py
import csv, glob, json, os, datetime as dt

OUT = "data/processed/cdc-tracking"
STATES = {"Region 1": "CT, ME, MA, NH, RI, VT", "Region 2": "NJ, NY, PR, VI", "Region 3": "DE, DC, MD, PA, VA, WV",
          "Region 4": "AL, FL, GA, KY, MS, NC, SC, TN", "Region 5": "IL, IN, MI, MN, OH, WI", "Region 6": "AR, LA, NM, OK, TX",
          "Region 7": "IA, KS, MO, NE", "Region 8": "CO, MT, ND, SD, UT, WY",
          "Region 9": "AZ, CA, HI, NV, AS, MP, FM, GU, MH, PW", "Region 10": "AK, ID, OR, WA"}
CITIES = {"Region 1": "boston", "Region 5": "detroit", "Region 9": "phoenix; sanfrancisco; sandiego"}
os.makedirs(OUT, exist_ok=True)

for m, name, kind in [(1238, "daily_ed_rate_hri_nonva", "daily"), (1237, "weekly_ed_rate_hri_nonva", "weekly")]:
    rows = []
    for f in sorted(glob.glob(f"data/raw/cdc-tracking/measure_{m}_{name}/4_getCoreHolder_*.json")):
        if f.endswith("_request.json"):
            continue
        for r in json.load(open(f, encoding="utf-8"))["regionPMTableResult"]:
            t = str(r["temporal"])
            row = {"hhs_region": r["geo"], "region_number": int(r["geo"].split()[-1])}
            d = dt.date(int(t[:4]), int(t[4:6]), int(t[6:])).isoformat()
            if kind == "daily":
                row["date"] = d
            else:   # weekly "temporal" is a Saturday date labelled "7 Days": taken as the week's last day (to verify)
                row["week_ending"] = d; row["year"] = r["parentTemporal"]
            row.update({"hri_ed_per_100k_ed_visits": r["dataValue"], "display_value": r["displayValue"],
                        "suppressed": r["suppressionFlag"], "region_states": STATES[r["geo"]], "study_cities": CITIES.get(r["geo"], "")})
            rows.append(row)
    key = "date" if kind == "daily" else "week_ending"
    rows.sort(key=lambda r: (r[key], r["region_number"]))
    cols = ["hhs_region", "region_number", key] + (["year"] if kind == "weekly" else []) + ["hri_ed_per_100k_ed_visits", "display_value", "suppressed", "region_states", "study_cities"]
    with open(f"{OUT}/{kind}_hri_ed_rate_by_hhs_region.csv", "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(kind, len(rows), "rows", rows[0][key], "to", rows[-1][key])
