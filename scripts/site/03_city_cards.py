"""Site step 3: the data behind each city card (the panel beside the city explorer map).

This is the code that built the card data on 2026-10-06 (run in the chat at the time), saved here so it can be re-run.
The only change is where it reads the city facts: site/data/pm25.js instead of a downloaded copy of the artifact's data.js.

Per city:
  name, state, dates, cause, week_start, pm, normal (= pm_normal), ratio, rise, share_normal, share_event, items
      copied from site/data/pm25.js (see scripts/site/05_pm25.py and the comments in site/js/plates-shared.js)
  tone        corrected counts A, J, E, N, 2 decimals: spectrum_07_corrected/city_shares.csv, method = corrected
  living_lo, living_hi, n_checked   the 95% range of the corrected "living with it" share and the number of hand-checked items
              (same file: two_living_lo, two_living_hi, n_checked)
  keywords    the 5 air terms matched most often in the city's worst-week air items (spectrum_01_air_items, matched_terms;
              "*" and " (plain)" stripped, "the air" and "air quality" left out because every city has them)
  daily       daily PM2.5 from OpenAQ reference monitors (step05_averages/pm25_<city>_daily.csv, ref_mean, 1 decimal),
              one value per day from 2019-01-01 to 2026-09-25, null where there is no data
Output: site/data/cards.js, window.CARDS = {city: {...}}. Run from the repo root:  python3 scripts/site/03_city_cards.py
"""
import collections
import csv
import datetime as D
import glob
import json
import sys

sys.path.insert(0, "scripts/site")
from _stamp import write_js

PM25 = "site/data/pm25.js"
SHARES = "data/processed/reddit/spectrum_07_corrected/city_shares.csv"
START, END = D.date(2019, 1, 1), D.date(2026, 9, 25)   # END = the study's last day (Dish's Decision D1)
LEFT_OUT = ("the air", "air quality")

text = open(PM25, encoding="utf-8").read()
pm = json.loads(text[text.index("window.PM25"):].split("=", 1)[1].strip().rstrip(";"))
cities = {c["slug"]: c for c in pm["cities"]}
corr = {r["city"]: r for r in csv.DictReader(open(SHARES, encoding="utf-8")) if r["method"] == "corrected"}

inputs, res = [PM25, SHARES], {}
for k, c in cities.items():
    daily_f = f"data/processed/openaq/step05_averages/pm25_{k}_daily.csv"
    inputs.append(daily_f)
    rows = {r["date"]: r["ref_mean"] for r in csv.DictReader(open(daily_f, encoding="utf-8"))}
    daily = []
    for i in range((END - START).days + 1):
        v = rows.get((START + D.timedelta(i)).isoformat(), "")
        daily.append(round(float(v), 1) if v not in ("", None) else None)
    kw = collections.Counter()
    for f in glob.glob(f"data/processed/reddit/spectrum_01_air_items/{k}_*_air_items.csv"):
        if "comparison" in f:
            continue
        inputs.append(f)
        for r in csv.DictReader(open(f, encoding="utf-8")):
            for t in r["matched_terms"].split(";"):
                t = t.strip().replace("*", "").replace(" (plain)", "")
                if t and t not in LEFT_OUT:
                    kw[t] += 1
    q = corr[k]
    res[k] = dict(name=c["name"], state=c["state"], dates=c["dates"], cause=c["cause"], week_start=c["week_start"], pm=c["pm"],
                  normal=c["pm_normal"], ratio=c["ratio"], rise=c["rise"], share_normal=c["share_normal"], share_event=c["share_event"],
                  items=c["items"], tone={b: round(float(q["count_" + b]), 2) for b in "AJEN"}, living_lo=float(q["two_living_lo"]),
                  living_hi=float(q["two_living_hi"]), n_checked=int(q["n_checked"]), keywords=[t for t, _ in kw.most_common(5)], daily=daily)

write_js("site/data/cards.js", "CARDS", res, "scripts/site/03_city_cards.py", inputs,
         notes=['Keywords leave out "the air" and "air quality" (Claude\'s choice when the card was built, 2026-10-06; approved by Gina 2026-10-07).'])
print({k: v["keywords"] for k, v in res.items()})
