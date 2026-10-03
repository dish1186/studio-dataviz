#!/usr/bin/env python3
"""
scripts/reddit/normals_02_compare.py

Normals, Step 2: choose the Reddit normal (neighbor weeks vs same-month weeks) for the PM2.5
experiment, using the rules fixed in docs/experiment-design-pm25.md BEFORE any shares were computed
(approved by Dish, 2026-10-03). It never computes a Reddit rise.

Safeguards:
  - reads only data/processed/reddit/normals_no_usernames/ (never event_weeks_no_usernames/)
  - drops every post/comment in the city's event week right after reading, before anything is counted
  - no event-week share, no ratio, no difference against the event week

Input (read only):
  data/processed/reddit/normals_no_usernames/<city>/*.jsonl      (Gina, normals Step 1)
  data/lexicons/lexicon_air_v1.csv                               (frozen 2026-10-03)
  data/processed/openaq/step07_screening/weekly_all.csv          (reference PM2.5 by week)
Output: data/processed/reddit/normals_02_compare/
  weekly.csv      one row per city x normal x candidate week: volume, air-talk share, PM2.5, kept or why dropped
  tests.csv       one row per city x normal: tests 1-3 and the reported-only numbers
  cleaning.csv    per city: rows read, duplicates, event-week rows dropped, removed/deleted, bots, empty, kept
  decision.md     plain-language result

Rules (A = which weeks; B = tests; C = decision):
  A1 Week = Monday-Sunday, local time (America/Los_Angeles for both cities).
  A2 Neighbor = the 6 weeks before and after the event week, minus the week directly before and after (10 weeks).
     Month = every week whose Thursday falls in the event's month, 2019-2025, minus the event week.
  A3 A week is dropped if: PM2.5 week average > 35.5 (average of the days with data), no PM2.5 data at all,
     it contains Jul 4-5 or Dec 31-Jan 1 (fireworks), or it has fewer than 100 kept posts + comments.
     A week with 1-4 days of PM2.5 data is kept if its average is <= 35.5, and flagged.
  A4 Air talk = a kept post or comment matching any `include` term of lexicon_air_v1 (after `exclude`
     patterns are blanked), using scripts/reddit/study.py flag_topic. Share = air-talk items / kept items.
  A5 Cleaning = scripts/reddit/02_clean.py: removed/deleted (is_removed), text cleaning (clean), post text =
     title + body. Bots: usernames were stripped in normals Step 1, so 02_clean's name list can't work; a bot is
     any post or comment distinguished "moderator", or whose text contains "I am a bot" (Claude's choice).
     Duplicates (the same id in two downloads) are counted once.
  B1 Enough weeks: >= 6 usable weeks, otherwise the normal fails.
  B2 Steady: interquartile range (75th - 25th percentile) of the weekly air-talk share, in percentage points.
     Smaller is better.
  B3 No drift: neighbor = |median share of before-weeks - median share of after-weeks|; month = |median share
     2019-2021 - median share 2023-2025|; in percentage points. Smaller is better. If one side has no usable
     week, B3 can't be computed.
  C1 Eugene decides (its event week has never been looked at). If one normal fails B1, the other is chosen;
     if both fail, neither. Otherwise a normal that is smaller on both B2 and B3 is chosen; a split, a tie,
     or a B3 that can't be computed goes to the month normal (it matches the PM2.5 normal).
  C2 Bakersfield is computed the same way, as a check only (not blind: its event-week rise was seen in the
     earlier study). If it disagrees, that is reported, not acted on.
Run from the repo root: python3 scripts/reddit/normals_02_compare.py   (local files only)
"""

import csv
import importlib.util
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from study import load_topic_lexicon, flag_topic   # noqa: E402
_spec = importlib.util.spec_from_file_location("clean02", HERE / "02_clean.py")
clean02 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(clean02)

IN = Path("data/processed/reddit/normals_no_usernames")
LEX = Path("data/lexicons/lexicon_air_v1.csv")
PM = Path("data/processed/openaq/step07_screening/weekly_all.csv")
OUT = Path("data/processed/reddit/normals_02_compare")
TZ = ZoneInfo("America/Los_Angeles")
HARM, MIN_ITEMS, MIN_WEEKS, MIN_PM_DAYS = 35.5, 100, 6, 5
FIREWORKS = {(7, 4), (7, 5), (12, 31), (1, 1)}
BOT_TEXT = "i am a bot"
CITIES = {  # event week start (Monday) from step07_screening/city_screening.csv, reference
    "eugene": {"event": date(2020, 9, 7), "month": 9, "role": "decides"},
    "bakersfield": {"event": date(2024, 12, 2), "month": 12, "role": "check only"},
}
OUT.mkdir(parents=True, exist_ok=True)
monday = lambda d: d - timedelta(d.weekday())
pp = lambda x: None if x is None else round(100 * x, 3)

lex = load_topic_lexicon(LEX)
pm = {}
for r in csv.DictReader(open(PM, encoding="utf-8")):
    if r["source"] == "reference" and r["city"] in CITIES:
        pm[(r["city"], date.fromisoformat(r["week_start"]))] = r


def candidate_weeks(city, ev, m):
    nb = [(ev + timedelta(7 * k), f"{k:+d}") for k in list(range(-6, -1)) + list(range(2, 7))]
    mo = []
    for y in range(2019, 2026):
        d = monday(date(y, m, 1))
        while d <= date(y, m, 28) + timedelta(7):
            if (d + timedelta(3)).month == m and (d + timedelta(3)).year == y and d != ev:
                mo.append((d, str(y)))
            d += timedelta(7)
    return {"neighbor": nb, "month": mo}


weekly, tests, cleaning = [], [], []
for city, C in CITIES.items():
    ev = C["event"]
    seen, st = set(), Counter()
    wk = defaultdict(lambda: Counter())
    for f in sorted((IN / city).glob("*.jsonl")):
        for x in clean02.iter_rows(f):
            st["rows_read"] += 1
            if x is None:
                st["unreadable"] += 1; continue
            kind = "post" if "title" in x else "comment"
            if (kind, x["id"]) in seen:
                st["duplicate"] += 1; continue
            seen.add((kind, x["id"]))
            d = datetime.fromtimestamp(int(x["created_utc"]), timezone.utc).astimezone(TZ).date()
            w = monday(d)
            if w == ev:                                   # safeguard: event week never counted
                st["event_week_dropped"] += 1; continue
            raw = (x.get("title", "") + "\n" + (x.get("selftext") or "")) if kind == "post" else (x.get("body") or "")
            if clean02.is_removed(x, kind):
                st["removed_deleted"] += 1; wk[w]["removed"] += 1; continue
            if x.get("distinguished") == "moderator" or BOT_TEXT in raw.lower():
                st["bot"] += 1; wk[w]["bot"] += 1; continue
            text = clean02.clean(raw)
            if not text:
                st["empty"] += 1; continue
            st["kept"] += 1
            wk[w]["kept"] += 1; wk[w][f"kept_{kind}s"] += 1
            if flag_topic(text, lex)[0]:
                wk[w]["air"] += 1
    cleaning.append({"city": city, **{k: st[k] for k in ["rows_read", "unreadable", "duplicate", "event_week_dropped",
                                                          "removed_deleted", "bot", "empty", "kept"]}})

    for normal, weeks in candidate_weeks(city, ev, C["month"]).items():
        usable = []
        for w, label in weeks:
            c, p = wk.get(w, Counter()), pm.get((city, w))
            n_days = int(p["n_days"]) if p else 0
            avg = float(p["week_avg"]) if p and p["week_avg"] else None
            fw = p["fireworks_dates"] if p else ""
            share = c["air"] / c["kept"] if c["kept"] else None
            why = [r for r, bad in [("pm_over_35.5", avg is not None and avg > HARM), ("no_pm_data", n_days == 0),
                                    ("fireworks", bool(fw)), (f"under_{MIN_ITEMS}_items", c["kept"] < MIN_ITEMS)] if bad]
            row = {"city": city, "normal": normal, "week_start": w, "label": label, "kept_items": c["kept"],
                   "kept_posts": c["kept_posts"], "kept_comments": c["kept_comments"], "air_items": c["air"],
                   "air_share_pct": pp(share), "removed": c["removed"], "bot": c["bot"],
                   "pm25_week_avg": avg, "pm25_days": n_days, "pm25_partial_flag": int(0 < n_days < MIN_PM_DAYS),
                   "fireworks_dates": fw, "usable": int(not why), "drop_reasons": "; ".join(why)}
            weekly.append(row)
            if not why:
                usable.append(row)
        sh = [r["air_share_pct"] for r in usable]
        if normal == "neighbor":
            a = [r["air_share_pct"] for r in usable if r["label"].startswith("-")]
            b = [r["air_share_pct"] for r in usable if r["label"].startswith("+")]
            drift_def = "before vs after"
        else:
            a = [r["air_share_pct"] for r in usable if int(r["label"]) <= 2021]
            b = [r["air_share_pct"] for r in usable if int(r["label"]) >= 2023]
            drift_def = "2019-2021 vs 2023-2025"
        vol = [r["kept_items"] for r in usable]
        tests.append({
            "city": city, "role": C["role"], "normal": normal, "candidate_weeks": len(weeks), "usable_weeks": len(usable),
            "dropped_pm_over": sum("pm_over" in r["drop_reasons"] for r in weekly if r["city"] == city and r["normal"] == normal),
            "dropped_no_pm": sum("no_pm" in r["drop_reasons"] for r in weekly if r["city"] == city and r["normal"] == normal),
            "dropped_fireworks": sum("fireworks" in r["drop_reasons"] for r in weekly if r["city"] == city and r["normal"] == normal),
            "dropped_low_volume": sum("under_" in r["drop_reasons"] for r in weekly if r["city"] == city and r["normal"] == normal),
            "usable_pm_partial": sum(r["pm25_partial_flag"] for r in usable),
            "B1_enough_weeks": int(len(usable) >= MIN_WEEKS),
            "B2_iqr_pp": round(float(np.percentile(sh, 75) - np.percentile(sh, 25)), 3) if len(sh) >= 2 else None,
            "B3_drift_pp": round(abs(statistics.median(a) - statistics.median(b)), 3) if a and b else None,
            "B3_definition": drift_def, "B3_n_weeks": f"{len(a)} vs {len(b)}",
            "report_median_share_pct": round(statistics.median(sh), 3) if sh else None,
            "report_volume_min": min(vol) if vol else None, "report_volume_median": statistics.median(vol) if vol else None,
            "report_smoky_weeks_ge15": sum(1 for r in usable if r["pm25_week_avg"] is not None and r["pm25_week_avg"] >= 15),
        })


def decide(city):
    t = {r["normal"]: r for r in tests if r["city"] == city}
    n, m = t["neighbor"], t["month"]
    if not n["B1_enough_weeks"] and not m["B1_enough_weeks"]: return "neither", "both fail test 1"
    if not n["B1_enough_weeks"]: return "month", "neighbor fails test 1"
    if not m["B1_enough_weeks"]: return "neighbor", "month fails test 1"
    if n["B3_drift_pp"] is None or m["B3_drift_pp"] is None: return "month", "test 3 can't be computed -> tie-breaker"
    better = lambda k: "neighbor" if n[k] < m[k] else "month" if m[k] < n[k] else "tie"
    b2, b3 = better("B2_iqr_pp"), better("B3_drift_pp")
    if b2 == b3 and b2 != "tie": return b2, f"smaller on both test 2 and test 3"
    return "month", f"split (test 2: {b2}, test 3: {b3}) -> tie-breaker"


def write(name, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
write("weekly.csv", weekly); write("tests.csv", tests); write("cleaning.csv", cleaning)

choice = {c: decide(c) for c in CITIES}
L = ["# Reddit normal: neighbor vs month (normals Step 2)", "",
     f"Generated by `scripts/reddit/normals_02_compare.py` on {date.today()}. Rules fixed before any share was computed "
     "(design doc, approved by Dish 2026-10-03). Event weeks were removed on reading; no Reddit rise was computed.", "",
     f"## Decision: **{choice['eugene'][0]} normal** (Eugene decides: {choice['eugene'][1]})", "",
     f"Bakersfield check (not blind): {choice['bakersfield'][0]} ({choice['bakersfield'][1]}). "
     + ("Agrees." if choice["bakersfield"][0] == choice["eugene"][0] else "**Disagrees** - reported, not acted on."), "",
     "## Tests", "",
     "| City | Normal | Usable / candidate weeks | Test 1 (≥ 6) | Test 2 spread (pp) | Test 3 drift (pp) | Drift weeks | Median share % | Min / median weekly volume | Smoky usable weeks (≥ 15) |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for r in tests:
    L.append(f"| {r['city']} | {r['normal']} | {r['usable_weeks']} / {r['candidate_weeks']} | {'pass' if r['B1_enough_weeks'] else 'FAIL'} | "
             f"{r['B2_iqr_pp']} | {r['B3_drift_pp']} | {r['B3_definition']}: {r['B3_n_weeks']} | {r['report_median_share_pct']} | "
             f"{r['report_volume_min']} / {r['report_volume_median']} | {r['report_smoky_weeks_ge15']} |")
L += ["", "Dropped weeks (PM2.5 > 35.5 / no PM2.5 / fireworks / < 100 items): " + "; ".join(
      f"{r['city']} {r['normal']} {r['dropped_pm_over']}/{r['dropped_no_pm']}/{r['dropped_fireworks']}/{r['dropped_low_volume']}"
      f" (+{r['usable_pm_partial']} kept with partial PM2.5)" for r in tests), "",
      "## Cleaning", "", "| City | Rows read | Duplicates | Event-week rows dropped | Removed/deleted | Bots | Empty | Kept |", "|---|---|---|---|---|---|---|---|"]
for c in cleaning:
    L.append(f"| {c['city']} | {c['rows_read']} | {c['duplicate']} | {c['event_week_dropped']} | {c['removed_deleted']} | {c['bot']} | {c['empty']} | {c['kept']} |")
L += ["", "## Caveats", "",
      "- Bots: usernames were stripped before this step, so bots are found only by `distinguished = moderator` and "
      "\"I am a bot\" text (Claude's choice). Bots without either mark are counted as people.",
      "- 02_clean's `author == [deleted]` removal check can't fire on stripped files; deleted-author items whose text "
      "survives are kept.",
      "- lexicon_air_v1 caveats (only 2 cities tested; partly tuned on Bakersfield's event week): see the design doc.", ""]
open(OUT / "decision.md", "w", encoding="utf-8").write("\n".join(L))

for c in cleaning: print(c)
for r in tests:
    print(f"{r['city']:12s} {r['normal']:8s} usable {r['usable_weeks']:2d}/{r['candidate_weeks']:2d}  T1 {'pass' if r['B1_enough_weeks'] else 'FAIL'}"
          f"  T2 {r['B2_iqr_pp']}  T3 {r['B3_drift_pp']} ({r['B3_n_weeks']})")
for c, (ch, why) in choice.items(): print(f"{c}: {ch} ({why})")
print("DONE")
