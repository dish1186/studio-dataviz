# Google Trends Step 3 · processed copies of the heat-search files with 3 terms, plus their sum and average.
#
# For each raw file in data/raw/google-trends/heat-search/ (not modified), write a copy with the same name to
# data/processed/google-trends/heat-search/ that:
#   - drops the columns "cooling center" and "cooling fan" (Gina, 2026-09-27)
#   - keeps Time, "air conditioner", "fan", "AC" exactly as downloaded
#   - adds total_interest_index = air conditioner + fan + AC, and avg_interest_index = total_interest_index / 3 (rounded to 2 decimals)
# Column names changed from total_searches / avg_searches at Gina's request (2026-09-27).
# Values are Google Trends relative interest (0-100, scaled within each file), so total_interest_index and avg_interest_index are
# sums / averages of those index values, not counts of searches.
# Run from the repo root: python3 scripts/google-trends/02_heat_search_three_terms.py
import csv, glob, os

IN = "data/raw/google-trends/heat-search"
OUT = "data/processed/google-trends/heat-search"
KEEP = ["air conditioner", "fan", "AC"]
os.makedirs(OUT, exist_ok=True)
n = 0
for fn in sorted(glob.glob(f"{IN}/*-heat-search.csv")):
    R = list(csv.DictReader(open(fn, encoding="utf-8")))
    assert list(R[0].keys()) == ["Time", "air conditioner", "cooling center", "fan", "AC", "cooling fan"], fn
    out = []
    for r in R:
        vals = [int(r[k]) for k in KEEP]
        out.append({"Time": r["Time"], **{k: int(r[k]) for k in KEEP}, "total_interest_index": sum(vals), "avg_interest_index": round(sum(vals) / len(vals), 2)})
    with open(f"{OUT}/{os.path.basename(fn)}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Time"] + KEEP + ["total_interest_index", "avg_interest_index"], quoting=csv.QUOTE_NONNUMERIC)
        w.writeheader(); w.writerows(out)
    n += 1
print(n, "files written to", OUT)
