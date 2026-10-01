# CDC Tracking · Step 3 · flatten the three annual state measures (Step 1 raw JSON) into simple CSVs.
#
# Input (not modified): data/raw/cdc-tracking/measure_<id>_<name>/4_getCoreHolder_all.json, list "tableResult":
#   438  Annual number of emergency-department visits for HRI        -> annual_ed_visits_hri_by_state.csv
#   370  Annual number of heat-related deaths (May-Sep)               -> annual_heat_deaths_by_state.csv
#   431  Annual number of hospitalizations for HRI                   -> annual_hospitalizations_hri_by_state.csv
# One row per state and year, values copied as given (dataValue). Suppressed values (suppressionFlag 1) are left
# blank with suppressed = 1; they are NOT zero. CDC suppresses small counts to protect confidentiality.
# Run from the repo root: python3 scripts/cdc-tracking/03_annual_state_csv.py
import csv, json, os

OUT = "data/processed/cdc-tracking"
FILES = [("438_annual_ed_visits_hri", "annual_ed_visits_hri_by_state.csv", "ed_visits"),
         ("370_annual_heat_deaths", "annual_heat_deaths_by_state.csv", "deaths"),
         ("431_annual_hospitalizations_hri", "annual_hospitalizations_hri_by_state.csv", "hospitalizations")]
os.makedirs(OUT, exist_ok=True)
for src, out, col in FILES:
    L = json.load(open(f"data/raw/cdc-tracking/measure_{src}/4_getCoreHolder_all.json", encoding="utf-8"))["tableResult"]
    rows = [{"state": r["geo"], "state_fips": r["geoId"], "year": int(r["temporal"]),
             col: "" if r["suppressionFlag"] == "1" or r["dataValue"] is None else int(float(r["dataValue"])),
             "suppressed": int(r["suppressionFlag"] == "1")} for r in L]
    rows.sort(key=lambda r: (r["state"], r["year"]))
    with open(f"{OUT}/{out}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    ys = [r["year"] for r in rows]
    print(out, len(rows), "rows,", len({r['state'] for r in rows}), "states,", min(ys), "-", max(ys), ",", sum(r["suppressed"] for r in rows), "suppressed")
