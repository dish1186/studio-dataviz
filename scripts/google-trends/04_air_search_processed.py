# Google Trends Step 5 · processed copies of the air-quality search files, with total and average interest index.
#
# For each raw file in data/raw/google-trends/air-search/ (not modified), write a copy with the same name to
# data/processed/google-trends/air-search/ that keeps Time, "air purifier", "air filter", "n95" exactly as downloaded
# (all three terms kept, Gina 2026-09-27) and adds:
#   total_interest_index = air purifier + air filter + n95
#   avg_interest_index   = total_interest_index / 3 (rounded to 2 decimals)
# Values are Google Trends relative interest (0-100, scaled within each file); sums/averages of index values, not counts.
# Run from the repo root: python3 scripts/google-trends/04_air_search_processed.py
import csv, glob, os

IN = "data/raw/google-trends/air-search"
OUT = "data/processed/google-trends/air-search"
KEEP = ["air purifier", "air filter", "n95"]
os.makedirs(OUT, exist_ok=True)
n = 0
for fn in sorted(glob.glob(f"{IN}/*-air-search.csv")):
    R = list(csv.DictReader(open(fn, encoding="utf-8")))
    assert list(R[0].keys()) == ["Time"] + KEEP, fn
    out = []
    for r in R:
        vals = [int(r[k]) for k in KEEP]
        out.append({"Time": r["Time"], **{k: int(r[k]) for k in KEEP}, "total_interest_index": sum(vals), "avg_interest_index": round(sum(vals) / len(vals), 2)})
    with open(f"{OUT}/{os.path.basename(fn)}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Time"] + KEEP + ["total_interest_index", "avg_interest_index"], quoting=csv.QUOTE_NONNUMERIC)
        w.writeheader(); w.writerows(out)
    n += 1
print(n, "files written to", OUT)
