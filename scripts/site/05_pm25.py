"""Site step 5: the city facts and results (worst weeks, PM2.5, × normal, air talk, pairs, rank correlations).

Runs the existing builder, viz/pm25-scrolly/build.py --full (the result of record, data/processed/reddit/analysis_01),
writing to a temporary file, then stamps it into site/data/pm25.js. How each number is made is written at the top of
site/js/plates-shared.js and in build.py.

One field does not come from the repo: days_over_15 ("about N bad days a year" in the map tooltip, js/map-plate.js).
Dish added it to the published data by hand; none of the repo's files reproduce it (median or mean days a year over
15 µg/m³, 2016-2025 or 2019-2025, from the daily city average or the highest site, were all tried on 2026-10-07).
Until Dish says how it was made, it is copied from the published snapshot (commit d689e08, site/data.js) and
listed as copied in the file header.
Output: site/data/pm25.js, window.PM25. Run from the repo root:  python3 scripts/site/05_pm25.py
"""
import json
import subprocess
import sys
import tempfile

sys.path.insert(0, "scripts/site")
from _stamp import write_js

SNAPSHOT = "d689e08"


def load(text):
    return json.loads(text[text.index("window.PM25"):].split("=", 1)[1].strip().rstrip(";"))


with tempfile.NamedTemporaryFile(suffix=".js") as tmp:
    subprocess.run([sys.executable, "viz/pm25-scrolly/build.py", "--full", "--out", tmp.name], check=True)
    pm = load(open(tmp.name, encoding="utf-8").read())

published = load(subprocess.run(["git", "show", f"{SNAPSHOT}:site/data.js"], check=True, capture_output=True, text=True).stdout)
copied = {c["slug"]: c["days_over_15"] for c in published["cities"]}
for c in pm["cities"]:   # keep the published key order: days_over_15 right after bad_days
    items = list(c.items())
    i = [k for k, _ in items].index("bad_days") + 1
    new = dict(items[:i] + [("days_over_15", copied[c["slug"]])] + items[i:])
    c.clear(); c.update(new)

inputs = ["viz/pm25-scrolly/build.py", "data/processed/openaq/step08_pm_normals/pm_normals.csv",
          "data/processed/reddit/analysis_01/cities.csv", "data/processed/reddit/analysis_01/pairs.csv",
          "data/processed/reddit/analysis_01/weekly.csv", "data/processed/reddit/analysis_01/results.md",
          "data/processed/openaq/step05_averages/pm25_fairbanks_daily.csv", "docs/experiment-design-pm25.md"]
write_js("site/data/pm25.js", "PM25", pm, "scripts/site/05_pm25.py (runs viz/pm25-scrolly/build.py --full)", inputs,
         notes=[f"days_over_15 is COPIED from the published snapshot ({SNAPSHOT}:site/data.js), not computed: method to be confirmed by Dish."])
print(pm["run"], pm["verdict"], pm["rho"], "days_over_15 copied:", copied)
