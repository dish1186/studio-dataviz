# Google Trends Step 10 · US national "air conditioner" and "air purifier", 2004-2026: processed copies + yearly trend check.
#
# Reads two raw files in data/raw/google-trends/us-national/ (not modified): Dish's "air conditioner" download and
# Gina's "air purifier" download (her Google Trends Step 6). One search term per download, so each
# file is scaled to its own peak = 100 and the two cannot be compared in height. Writes:
#   data/processed/google-trends/us-national/us_national_monthly.csv  Time, air conditioner, air purifier (as downloaded)
#   data/processed/google-trends/us-national/us_national_yearly.csv   year, n_months, mean of each term, partial_year
# Then prints a trend check on the yearly means of the full years (2004-2025; 2026 is partial):
#   Kendall's tau with a two-sided permutation p-value (10,000 shuffles, fixed seed) and the Theil-Sen slope
#   (median of all pairwise slopes, index points per year), for 2004-2025, 2004-2015 and 2016-2025.
# Values are Google Trends relative interest (0-100), not search counts.
# Run from the repo root: python3 scripts/google-trends/06_us_national.py
import csv, os, random

IN = "data/raw/google-trends/us-national"
OUT = "data/processed/google-trends/us-national"
FILES = {"air conditioner": "airconditionersearch2004-2026.csv", "air purifier": "time_series_US_20031231-1900_20260928-1117.csv"}  # air purifier = Gina's download (Google Trends Step 6)
os.makedirs(OUT, exist_ok=True)

series = {}
for term, fn in FILES.items():
    R = list(csv.DictReader(open(f"{IN}/{fn}", encoding="utf-8")))
    assert list(R[0].keys()) == ["Time", term], fn
    series[term] = {r["Time"]: int(r[term]) for r in R}
months = list(series["air conditioner"])
assert months == list(series["air purifier"]), "month lists differ"
assert months[0] == "2004-01-01" and months[-1] == "2026-09-01" and len(months) == 273

with open(f"{OUT}/us_national_monthly.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
    w.writerow(["Time"] + list(FILES))
    for m in months:
        w.writerow([m] + [series[t][m] for t in FILES])

years = sorted({int(m[:4]) for m in months})
yearly = {}
for y in years:
    ms = [m for m in months if int(m[:4]) == y]
    yearly[y] = {t: sum(series[t][m] for m in ms) / len(ms) for t in FILES}
    yearly[y]["n"] = len(ms)
with open(f"{OUT}/us_national_yearly.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["year", "n_months", "air_conditioner_mean", "air_purifier_mean", "partial_year"])
    for y in years:
        w.writerow([y, yearly[y]["n"], round(yearly[y]["air conditioner"], 2), round(yearly[y]["air purifier"], 2), int(yearly[y]["n"] < 12)])

def sign(v): return (v > 0) - (v < 0)
def tau(v):
    n = len(v); s = sum(sign(j - i) * sign(v[j] - v[i]) for i in range(n) for j in range(i + 1, n))
    return s / (n * (n - 1) / 2)
def theil_sen(v):
    sl = sorted((v[j] - v[i]) / (j - i) for i in range(len(v)) for j in range(i + 1, len(v)))
    k = len(sl); return sl[k // 2] if k % 2 else (sl[k // 2 - 1] + sl[k // 2]) / 2
rng = random.Random(1)
def perm_p(v, t, n=10000):
    hits = 0
    for _ in range(n):
        s = v[:]; rng.shuffle(s)
        hits += abs(tau(s)) >= abs(t) - 1e-12
    return hits / n

print("monthly rows:", len(months), "| yearly rows:", len(years), "->", OUT)
for term in FILES:
    for lo, hi in [(2004, 2025), (2004, 2015), (2016, 2025)]:
        v = [yearly[y][term] for y in range(lo, hi + 1)]
        t = tau(v)
        print(f"{term:16s} {lo}-{hi}: tau {t:+.2f}  p {perm_p(v, t):.4f}  Theil-Sen {theil_sen(v):+.2f} per year")
