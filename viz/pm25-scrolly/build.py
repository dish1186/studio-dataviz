"""Build data.js for the PM2.5 scrollytelling page ("boiling frog").
Reads the experiment's outputs (read-only) and writes viz/pm25-scrolly/data.js (window.PM25 = {...}).
Run from the repo root:
    python3 viz/pm25-scrolly/build.py            # interim run, 6 of 9 cities (analysis_01_interim)
    python3 viz/pm25-scrolly/build.py --full     # result of record (analysis_01), once the full run exists
    python3 viz/pm25-scrolly/build.py --full --out PATH   # same, written to PATH instead of viz/pm25-scrolly/data.js
Nothing here changes the analysis: every number comes from the CSVs. Rank correlations are recomputed
from cities.csv only as a cross-check against results.md (assert below)."""
import csv, json, re, statistics, sys, datetime

FULL = "--full" in sys.argv
RUN_DIR = "data/processed/reddit/analysis_01" if FULL else "data/processed/reddit/analysis_01_interim"
ORDER = ["bakersfield", "fairbanks", "fresno", "eugene", "sanjose", "indianapolis", "seattle", "detroit", "pittsburgh"]
STATE = {"bakersfield": "CA", "fairbanks": "AK", "fresno": "CA", "eugene": "OR", "sanjose": "CA",
         "indianapolis": "IN", "seattle": "WA", "detroit": "MI", "pittsburgh": "PA"}
DOC_NAME = {"San Jose": "sanjose"}

def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))

def num(v):
    return None if v in (None, "") else float(v)

# event causes, from the design doc's event table
causes = {}
for line in open("docs/experiment-design-pm25.md", encoding="utf-8"):
    m = re.match(r"\| (?!~~)([A-Z][A-Za-z ]+?) \| (.+?) \| [\d.]+ \| \d/7 \| \d+ \| (.+?) \|$", line.strip())
    if m:
        causes[DOC_NAME.get(m.group(1), m.group(1).lower())] = {"dates": m.group(2), "cause": m.group(3)}

pm = {r["city"]: r for r in rows("data/processed/openaq/step08_pm_normals/pm_normals.csv") if not r["dropped"]}
res = {r["city"]: r for r in rows(f"{RUN_DIR}/cities.csv")}

# Days a year above 15 µg/m³ (WHO daily guideline), 2019-2025, for the map hover (display only).
# Share of measured days above 15, scaled to 365, because some years have gaps (2021 especially).
def days_over_15(slug):
    v = [float(r["ref_mean"]) for r in rows(f"data/processed/openaq/step05_averages/pm25_{slug}_daily.csv")
         if "2019-01-01" <= r["date"] <= "2025-12-31" and r["ref_mean"]]
    return round(sum(x > 15 for x in v) / len(v) * 365)

cities = []
for slug in ORDER:
    p, r = pm[slug], res.get(slug)
    ready = bool(r) and r["included"] == "1"
    c = {"slug": slug, "name": p["city_name"].rsplit(" ", 1)[0], "state": STATE[slug],
         "week_start": p["event_week_start"], "week_end": p["event_week_end"],
         "dates": causes[slug]["dates"], "cause": causes[slug]["cause"],
         "pm": num(p["event_week_pm25"]), "pm_normal": num(p["pm25_normal"]), "ratio": num(p["ratio_to_normal"]),
         "bad_days": int(float(p["median_days_ge_35_5_2019_2025"])), "days_over_15": days_over_15(slug), "ready": ready}
    if ready:
        c.update({"share_event": num(r["event_share_pct"]), "share_normal": num(r["normal_share_pct"]),
                  "rise": num(r["rise_ratio"]), "rise_pp": num(r["rise_pp"]), "beat": r["percentile_higher_than"],
                  "items": int(r["event_kept_items"]), "fire_event": num(r["fire_event_share_pct"]),
                  "fire_normal": num(r["fire_normal_share_pct"])})
    cities.append(c)

def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk

def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    return statistics.correlation(ra, rb)

ready = [c for c in cities if c["ready"]]
rise = [c["rise"] for c in ready]
rho = {"ratio": round(spearman(rise, [c["ratio"] for c in ready]), 3),
       "abs": round(spearman(rise, [c["pm"] for c in ready]), 3),
       "measures": round(spearman([c["ratio"] for c in ready], [c["pm"] for c in ready]), 3),
       "bad_days": round(spearman(rise, [c["bad_days"] for c in ready]), 3)}
# cross-check against the analysis script's own numbers
md = open(f"{RUN_DIR}/results.md", encoding="utf-8").read()
m = re.search(r"\| MAIN \(D10\): rise ratio \| \d+ \| ([\d.-]+) \| ([\d.-]+) \|", md)
assert m and abs(float(m.group(1)) - rho["ratio"]) < 0.002 and abs(float(m.group(2)) - rho["abs"]) < 0.002, (m and m.groups(), rho)
verdict = re.search(r"## Main test: \*\*(\w+)\*\*", md).group(1)

pairs = []
for r in rows(f"{RUN_DIR}/pairs.csv"):
    pairs.append({"type": r["type"], "worse": r["worse_air_city"], "other": r["other_city"],
                  "pm_worse": num(r["pm25_worse"]), "pm_other": num(r["pm25_other"]),
                  "ratio_worse": num(r["ratio_worse"]), "ratio_other": num(r["ratio_other"]),
                  "rise_worse": num(r["rise_worse"]), "rise_other": num(r["rise_other"]),
                  "bigger": r["bigger_rise"] or None, "outcome": r["outcome"]})

# every week for the two case-study cities: event + normal weeks (same month, 2019-2025)
weekly = {}
for r in rows(f"{RUN_DIR}/weekly.csv"):
    if r["city"] not in ("bakersfield", "indianapolis"):
        continue
    weekly.setdefault(r["city"], []).append({
        "week": r["week_start"], "type": r["week_type"], "pm": num(r["pm25_week_avg"]),
        "share": num(r["air_share_pct"]), "usable": r["week_type"] == "event" or r["usable"] == "1",
        "drop": r["drop_reasons"]})

# Fairbanks by month, 2019-2025: median daily reference PM2.5 and days >= 35.5 per year (display only)
fb = {m: [] for m in range(1, 13)}
for r in rows("data/processed/openaq/step05_averages/pm25_fairbanks_daily.csv"):
    if "2019-01-01" <= r["date"] <= "2025-12-31" and r["ref_mean"]:
        fb[int(r["date"][5:7])].append(float(r["ref_mean"]))
fair_months = [{"m": m, "median": round(statistics.median(v), 2), "bad_per_yr": round(sum(x >= 35.5 for x in v) / 7, 1),
                "days": len(v)} for m, v in fb.items()]

out = {"run": "full" if FULL else "interim", "n_ready": len(ready), "n_total": len(cities),
       "built": datetime.date.today().isoformat(), "source": RUN_DIR, "verdict": verdict,
       "cities": cities, "rho": rho, "pairs": pairs, "weekly": weekly, "fairbanks_months": fair_months}
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "viz/pm25-scrolly/data.js"   # --out: write elsewhere (scripts/site/05_pm25.py)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// Generated by viz/pm25-scrolly/build.py - do not edit by hand.\nwindow.PM25 = ")
    json.dump(out, f, separators=(",", ":"))
    f.write(";\n")
print(out["run"], f"{len(ready)}/{len(cities)} ready", rho, verdict, "causes:", len(causes))
print("fairbanks months:", [(x["m"], x["median"], x["bad_per_yr"]) for x in fair_months])
