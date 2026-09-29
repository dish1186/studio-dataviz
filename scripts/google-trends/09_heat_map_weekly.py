# Google Trends Step 13 · weekly actual heat, felt heat and AC searches per city, for the "Find Your Threshold" map.
#
# Inputs (not modified):
#   data/processed/google-trends/heat-threshold/weekly_search_temp_<city>.csv  (Step 11: week, search, ratio, weekly high)
#   data/processed/utci/final/utci_<city>_daily.csv                           (daily maximum UTCI "felt heat", deg F)
# One row per city and Trends week (Sunday-Saturday). felt_F = mean of the 7 daily UTCI maxima (all 7 must be valid).
# The series is cut at the last week with felt heat for every city (Gina 2026-09-29: "cut the temp data used until when
# felt data stops"), so actual heat, felt heat and searches cover the same weeks.
# Run from the repo root: python3 scripts/google-trends/09_heat_map_weekly.py
import csv, datetime as dt, statistics as st

CITIES = ["boston", "sanfrancisco", "phoenix", "detroit", "sandiego"]
IN_W = "data/processed/google-trends/heat-threshold/weekly_search_temp_{}.csv"
IN_U = "data/processed/utci/final/utci_{}_daily.csv"
OUT = "data/processed/google-trends/heat-threshold/heat_map_weekly.csv"

rows, last_ok = [], {}
for c in CITIES:
    felt = {r["date"]: float(r["utci_max_f"]) for r in csv.DictReader(open(IN_U.format(c), encoding="utf-8"))
            if r["valid"] == "1" and r["utci_max_f"] != ""}
    for r in csv.DictReader(open(IN_W.format(c), encoding="utf-8")):
        d0 = dt.date.fromisoformat(r["week_start"])
        f = [felt.get((d0 + dt.timedelta(k)).isoformat()) for k in range(7)]
        ok = None not in f
        if ok:
            last_ok[c] = max(last_ok.get(c, d0), d0)
        rows.append({"city": c, "week_start": r["week_start"], "weekly_high_F": r["weekly_high_F"],
                     "felt_F": round(st.mean(f), 2) if ok else "", "search": r["search"], "ratio": r["ratio"]})
cut = min(last_ok.values())
out = [r for r in rows if dt.date.fromisoformat(r["week_start"]) <= cut]
missing = [r for r in out if r["felt_F"] == ""]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("cut at week", cut, "| rows", len(rows), "->", len(out), "| weeks without felt heat before the cut:", len(missing))
