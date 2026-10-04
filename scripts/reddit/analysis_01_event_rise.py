#!/usr/bin/env python3
"""
scripts/reddit/analysis_01_event_rise.py

PM2.5 experiment, main analysis: did Reddit air talk rise more in cities whose bad week was more ABNORMAL
(PM2.5 ratio to normal), or in cities whose bad week was more HARMFUL (absolute PM2.5)?

Rules: docs/experiment-design-pm25.md, "Analysis rules", approved by Dish 2026-10-03 BEFORE any event-week
Reddit data was opened. This script is committed before it runs and runs once, on all cities together.
Rule numbers below (A1, B5, ...) refer to that section.

Input (read only):
  data/processed/reddit/normals_no_usernames/<city>/*.jsonl     month pulls (event week inside) + Detroit/Pittsburgh event files
  data/lexicons/lexicon_air_v1.csv                              frozen 2026-10-03
  data/processed/openaq/step08_pm_normals/pm_normals.csv        event weeks, PM2.5 normal, ratio, bad days/yr, dropped
  data/processed/openaq/step08_pm_normals/pairs.csv             pairs fixed from PM2.5 only
  data/processed/openaq/step07_screening/weekly_all.csv         PM2.5 per week (reference)
  data/processed/reddit/normals_02_compare/tests.csv            neighbor normal for Eugene/Bakersfield (check F17)
Output: data/processed/reddit/analysis_01/
  weekly.csv        every candidate normal week + the event week, per city: volume, shares, PM2.5, kept or why dropped
  cities.csv        one row per city: event/normal share, rise (ratio, pp), percentile, PM2.5, status
  tests.csv         main test and checks (Spearman correlations, verdicts)
  pairs.csv         each pair with its outcome
  results.md        plain-language summary
Run from the repo root: python3 scripts/reddit/analysis_01_event_rise.py   (local files only)
       python3 scripts/reddit/analysis_01_event_rise.py --check-inputs   (only checks that every city's files are in place)
       python3 scripts/reddit/analysis_01_event_rise.py --interim        (Dish, 2026-10-03: only the cities that are ready,
                                                                         to analysis_01_interim/; labeled interim; same computation)
"""

import csv
import importlib.util
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from study import load_topic_lexicon, flag_topic   # noqa: E402
_spec = importlib.util.spec_from_file_location("clean02", HERE / "02_clean.py")
clean02 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(clean02)

REDDIT = Path("data/processed/reddit/normals_no_usernames")
LEX = Path("data/lexicons/lexicon_air_v1.csv")
PMN = Path("data/processed/openaq/step08_pm_normals/pm_normals.csv")
PAIRS = Path("data/processed/openaq/step08_pm_normals/pairs.csv")
WEEKLY_PM = Path("data/processed/openaq/step07_screening/weekly_all.csv")
NEIGHBOR = Path("data/processed/reddit/normals_02_compare/tests.csv")
OUT = Path("data/processed/reddit/analysis_01")
TZ = {"eugene": "America/Los_Angeles", "bakersfield": "America/Los_Angeles", "fresno": "America/Los_Angeles",
      "sanjose": "America/Los_Angeles", "seattle": "America/Los_Angeles", "fairbanks": "America/Anchorage",
      "detroit": "America/Detroit", "pittsburgh": "America/New_York", "indianapolis": "America/Indiana/Indianapolis"}  # A3
HARM, MIN_ITEMS, MIN_ACTIVE_DAYS, MIN_WEEKS = 35.5, 100, 5, 6                         # B5, B6
LOW_NORMAL = 0.001                                                                    # C8: normal share < 0.1%
MARGIN = 0.2                                                                          # D10
BOT_TEXT = "i am a bot"                                                               # A2
OUT.mkdir(parents=True, exist_ok=True)
monday = lambda d: d - timedelta(d.weekday())
r3 = lambda x: None if x is None else round(x, 3)

lex = load_topic_lexicon(LEX)
pmn = {r["city"]: r for r in csv.DictReader(open(PMN, encoding="utf-8"))}
pm_week = {(r["city"], date.fromisoformat(r["week_start"])): r
           for r in csv.DictReader(open(WEEKLY_PM, encoding="utf-8")) if r["source"] == "reference"}
cities = [c for c in TZ if c in pmn and not pmn[c]["dropped"]]

# Safeguard: every city's Reddit files must be in place (per normals_no_usernames/coverage.csv), or nothing runs,
# so a city that is still downloading can't be counted as "too few posts".
cov = defaultdict(set)
for r in csv.DictReader(open(REDDIT / "coverage.csv", encoding="utf-8")):
    cov[r["city"]].add(r["file"])
missing = []
for c in cities:
    files = {f.name for f in (REDDIT / c).glob("*.jsonl")}
    need = {f for f in cov.get(c, ()) if "_month_" in f or "_event_" in f}
    if not need or not need <= files or not any("_month_" in f for f in need):
        missing.append(c)
    elif c in ("detroit", "pittsburgh") and not any("_event_" in f for f in need):
        missing.append(c)
INTERIM = "--interim" in sys.argv
if missing and not INTERIM:
    sys.exit(f"NOT RUN: Reddit files missing or not yet checked-and-stripped for: {', '.join(missing)}")
if INTERIM:
    # Interim run (Dish, 2026-10-03): only the cities whose files are ready; separate output folder; same computation.
    cities = [c for c in cities if c not in missing]
    OUT = Path("data/processed/reddit/analysis_01_interim")
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"INTERIM RUN on {len(cities)} cities ({', '.join(cities)}); left out (not ready): {', '.join(missing) or 'none'}")
if "--check-inputs" in sys.argv:
    print(f"inputs OK for all {len(cities)} cities: {', '.join(cities)} (nothing computed)"); sys.exit(0)


def read_city(city):
    """A1-A3: weekly counts of kept items, air talk (include), wide (include or candidate), fire; active days."""
    tz, seen, st = ZoneInfo(TZ[city]), set(), Counter()
    wk = defaultdict(Counter)
    active = defaultdict(set)                      # B5: local days with at least one comment (any status)
    for f in sorted((REDDIT / city).glob("*.jsonl")):
        for x in clean02.iter_rows(f):
            if x is None:
                st["unreadable"] += 1; continue
            kind = "post" if "title" in x else "comment"
            if (kind, x["id"]) in seen:
                st["duplicate"] += 1; continue
            seen.add((kind, x["id"]))
            d = datetime.fromtimestamp(int(float(x["created_utc"])), timezone.utc).astimezone(tz).date()
            w = monday(d)
            if kind == "comment":
                active[w].add(d)
            raw = (x.get("title", "") + "\n" + (x.get("selftext") or "")) if kind == "post" else (x.get("body") or "")
            if clean02.is_removed(x, kind):
                st["removed_deleted"] += 1; continue
            if x.get("distinguished") == "moderator" or BOT_TEXT in raw.lower():
                st["bot"] += 1; continue
            text = clean02.clean(raw)
            if not text:
                st["empty"] += 1; continue
            st["kept"] += 1
            inc, wide, seps, _ = flag_topic(text, lex)
            c = wk[w]
            c["kept"] += 1; c["air"] += inc; c["wide"] += wide; c["fire"] += seps.get("fire", False)
    return wk, active, st


def month_weeks(m, ev):
    out = []
    for y in range(2019, 2026):
        d = monday(date(y, m, 1))
        while d <= date(y, m, 28) + timedelta(7):
            if (d + timedelta(3)).month == m and (d + timedelta(3)).year == y and d != ev:
                out.append(d)
            d += timedelta(7)
    return out


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 3:
        return None
    try:
        return statistics.correlation(ranks(x), ranks(y))
    except statistics.StatisticsError:
        return None


weekly, rows, cleaning = [], [], []
for city in cities:
    P = pmn[city]
    ev, m = date.fromisoformat(P["event_week_start"]), int(P["event_month"])
    wk, active, st = read_city(city)
    cleaning.append({"city": city, **{k: st[k] for k in ["unreadable", "duplicate", "removed_deleted", "bot", "empty", "kept"]}})
    usable = []
    for w in [ev] + month_weeks(m, ev):
        c, p = wk.get(w, Counter()), pm_week.get((city, w))
        n_days = int(p["n_days"]) if p else 0
        avg = float(p["week_avg"]) if p and p["week_avg"] else None
        fw = p["fireworks_dates"] if p else ""
        share = c["air"] / c["kept"] if c["kept"] else None
        is_event = w == ev
        why = [] if is_event else [r for r, bad in [
            ("pm_over_35.5", avg is not None and avg > HARM), ("no_pm_data", n_days == 0), ("fireworks", bool(fw)),
            (f"under_{MIN_ITEMS}_items", c["kept"] < MIN_ITEMS),
            (f"comments_on_under_{MIN_ACTIVE_DAYS}_days", len(active.get(w, ())) < MIN_ACTIVE_DAYS)] if bad]
        row = {"city": city, "week_start": w, "week_type": "event" if is_event else "normal", "year": w.year,
               "kept_items": c["kept"], "air_items": c["air"], "air_share_pct": r3(100 * share) if share is not None else None,
               "wide_share_pct": r3(100 * c["wide"] / c["kept"]) if c["kept"] else None,
               "fire_share_pct": r3(100 * c["fire"] / c["kept"]) if c["kept"] else None,
               "comment_days": len(active.get(w, ())), "pm25_week_avg": avg, "pm25_days": n_days,
               "pm25_partial_flag": int(0 < n_days < 5), "fireworks_dates": fw,
               "usable": "" if is_event else int(not why), "drop_reasons": "; ".join(why)}
        weekly.append(row)
        if is_event:
            evrow, evc = row, c
        elif not why:
            usable.append((row, c))

    status = []
    if evc["kept"] < MIN_ITEMS: status.append(f"check 2: event week has {evc['kept']} kept items (< {MIN_ITEMS})")
    if len(usable) < MIN_WEEKS: status.append(f"only {len(usable)} usable normal weeks (< {MIN_WEEKS})")
    shares = [c["air"] / c["kept"] for _, c in usable]
    normal = statistics.median(shares) if shares else None
    event = evc["air"] / evc["kept"] if evc["kept"] else None
    ratio = event / normal if event is not None and normal else None
    pp = 100 * (event - normal) if event is not None and normal is not None else None
    below = sum(s < event for s in shares) if event is not None else None
    wide_n = statistics.median([c["wide"] / c["kept"] for _, c in usable]) if usable else None
    fire_n = statistics.median([c["fire"] / c["kept"] for _, c in usable]) if usable else None
    rows.append({
        "city": city, "city_name": P["city_name"], "included": int(not status), "status": "; ".join(status) or "in",
        "event_week_start": ev, "event_kept_items": evc["kept"], "event_air_items": evc["air"],
        "usable_normal_weeks": len(usable), "event_share_pct": r3(100 * event) if event is not None else None,
        "normal_share_pct": r3(100 * normal) if normal is not None else None,
        "rise_ratio": r3(ratio), "rise_pp": r3(pp), "low_normal_flag": int(normal is not None and normal < LOW_NORMAL),
        "percentile_higher_than": f"{below} of {len(shares)}" if below is not None else "",
        "percentile": r3(below / len(shares)) if shares and below is not None else None,
        "pm25_event": float(P["event_week_pm25"]), "pm25_normal": float(P["pm25_normal"]), "pm25_ratio": float(P["ratio_to_normal"]),
        "pm25_ratio_without_polluted_weeks": float(P["sens_ratio_without_polluted_weeks"]) if P["sens_ratio_without_polluted_weeks"] else None,
        "bad_days_per_year": float(P["median_days_ge_35_5_2019_2025"]),
        "wide_rise_ratio": r3((evc["wide"] / evc["kept"]) / wide_n) if wide_n else None,
        "fire_event_share_pct": r3(100 * evc["fire"] / evc["kept"]) if evc["kept"] else None,
        "fire_normal_share_pct": r3(100 * fire_n) if fire_n is not None else None,
    })

IN = [r for r in rows if r["included"]]


def test(name, rise_key, x_keys=("pm25_ratio", "pm25_event"), decide=True):
    v = [r for r in IN if r[rise_key] is not None]
    rise = [r[rise_key] for r in v]
    rho_ratio, rho_abs = spearman(rise, [r[x_keys[0]] for r in v]), spearman(rise, [r[x_keys[1]] for r in v])
    verdict = ""
    if decide and rho_ratio is not None and rho_abs is not None:
        d = rho_ratio - rho_abs
        verdict = "Pos" if d >= MARGIN else "Neg" if d <= -MARGIN else "Mixed"
    return {"test": name, "rise_measure": rise_key, "n_cities": len(v), "rho_with_ratio": r3(rho_ratio),
            "rho_with_absolute": r3(rho_abs), "difference": r3(rho_ratio - rho_abs) if rho_ratio is not None and rho_abs is not None else None,
            "verdict": verdict}


tests = [test("MAIN (D10): rise ratio", "rise_ratio"),
         test("check (D11): rise in percentage points", "rise_pp"),
         test("check (D11): percentile", "percentile"),
         test("check (F15): PM2.5 ratio without polluted weeks", "rise_ratio", ("pm25_ratio_without_polluted_weeks", "pm25_event")),
         test("check (F16): wider word list", "wide_rise_ratio")]
both = [r for r in IN]
tests.append({"test": "context (D12): PM2.5 ratio vs absolute PM2.5", "rise_measure": "", "n_cities": len(both),
              "rho_with_ratio": "", "rho_with_absolute": r3(spearman([r["pm25_ratio"] for r in both], [r["pm25_event"] for r in both])),
              "difference": "", "verdict": "(how strongly the two PM2.5 measures move together)"})
bd = [r for r in IN if r["rise_ratio"] is not None]
tests.append({"test": "check (F14): rise vs bad days per year", "rise_measure": "rise_ratio", "n_cities": len(bd),
              "rho_with_ratio": "", "rho_with_absolute": r3(spearman([r["rise_ratio"] for r in bd], [r["bad_days_per_year"] for r in bd])),
              "difference": "", "verdict": "(negative = cities used to bad air reacted less)"})

# E13 pairs
R = {r["city"]: r for r in IN}
pair_rows, won_ratio, won_abs_crossed, n_crossed = [], 0, 0, 0
for p in csv.DictReader(open(PAIRS, encoding="utf-8")):
    a, b = p["worse_air_city"], p["other_city"]
    if a not in R or b not in R or R[a]["rise_ratio"] is None or R[b]["rise_ratio"] is None:
        pair_rows.append({**p, "rise_worse": "", "rise_other": "", "bigger_rise": "", "outcome": "pair left out (a city is out or has no rise)"})
        continue
    hi_ratio = a if float(p["ratio_worse"]) > float(p["ratio_other"]) else b
    bigger = a if R[a]["rise_ratio"] > R[b]["rise_ratio"] else b if R[b]["rise_ratio"] > R[a]["rise_ratio"] else "tie"
    won_ratio += bigger == hi_ratio
    if p["type"] == "crossed":
        n_crossed += 1; won_abs_crossed += bigger == a
    pair_rows.append({**p, "rise_worse": R[a]["rise_ratio"], "rise_other": R[b]["rise_ratio"], "bigger_rise": bigger,
                      "outcome": "as Pos predicts" if bigger == hi_ratio else ("as Neg predicts" if p["type"] == "crossed" and bigger == a else "tie" if bigger == "tie" else "against Pos")})
n_pairs = sum(1 for p in pair_rows if p["bigger_rise"])


def write(name, data):
    with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
write("weekly.csv", weekly); write("cities.csv", rows); write("tests.csv", tests); write("pairs.csv", pair_rows)
write("cleaning.csv", cleaning)

# F17 neighbor normal for Eugene / Bakersfield
nb = {r["city"]: float(r["report_median_share_pct"]) for r in csv.DictReader(open(NEIGHBOR, encoding="utf-8")) if r["normal"] == "neighbor"}
nb_lines = [f"- {R[c]['city_name']}: event {R[c]['event_share_pct']}% vs neighbor normal {nb[c]}% → ratio {round(R[c]['event_share_pct'] / nb[c], 2)}× "
            f"(month normal: {R[c]['rise_ratio']}×)" for c in ("eugene", "bakersfield") if c in R and c in nb and nb[c]]

M = tests[0]
L = ["# PM2.5 experiment: main analysis" + (" - INTERIM (not the result of record)" if INTERIM else ""), "",
     *( [f"**Interim run on {len(cities)} of 9 cities** ({', '.join(missing)} not ready). Requested by Dish after the rules were fixed; "
         "the result of record is the full run on all cities with the same computation.", ""] if INTERIM else [] ),
     f"Generated by `scripts/reddit/analysis_01_event_rise.py` on {date.today()}. Rules fixed before any event-week Reddit data "
     "was opened (design doc, \"Analysis rules\"). Reported as a pattern across a few cities, not a significance test.", "",
     f"## Main test: **{M['verdict'] or 'not computable'}**", "",
     f"Across {M['n_cities']} cities, Reddit rise (ratio) ranks with the PM2.5 **ratio** at ρ = {M['rho_with_ratio']} and with "
     f"**absolute** PM2.5 at ρ = {M['rho_with_absolute']} (difference {M['difference']}; Pos/Neg need ≥ {MARGIN}).", "",
     "## Cities", "", "| City | Event share % | Normal share % | Rise (×) | Rise (pp) | Higher than | PM2.5 event | PM2.5 ratio | Bad days/yr | Status |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: -(r["rise_ratio"] or 0)):
    L.append(f"| {r['city_name']} | {r['event_share_pct']} | {r['normal_share_pct']} | {r['rise_ratio']}{' ⚑' if r['low_normal_flag'] else ''} | "
             f"{r['rise_pp']} | {r['percentile_higher_than']} | {r['pm25_event']} | {r['pm25_ratio']}× | {r['bad_days_per_year']} | {r['status']} |")
L += ["", "⚑ = normal share below 0.1%; quote percentage points for this city.", "", "## All tests", "",
      "| Test | Cities | ρ with ratio | ρ with absolute | Difference | Verdict |", "|---|---|---|---|---|---|"]
for t in tests:
    L.append(f"| {t['test']} | {t['n_cities']} | {t['rho_with_ratio']} | {t['rho_with_absolute']} | {t['difference']} | {t['verdict']} |")
L += ["", f"## Pairs (E13): higher-ratio city had the bigger rise in **{won_ratio} of {n_pairs}** pairs; "
      f"worse-air city had the bigger rise in **{won_abs_crossed} of {n_crossed}** crossed pairs", "",
      "| Type | Worse air | Other | Ratio (worse / other) | Rise (worse / other) | Outcome |", "|---|---|---|---|---|---|"]
for p in pair_rows:
    L.append(f"| {p['type']} | {p['worse_air_city']} | {p['other_city']} | {p['ratio_worse']} / {p['ratio_other']} | "
             f"{p['rise_worse']} / {p['rise_other']} | {p['outcome']} |")
L += ["", "## Check F17: neighbor normal (Eugene, Bakersfield)", ""] + (nb_lines or ["- not available"])
L += ["", "## Cleaning", "", "| City | Duplicates | Removed/deleted | Bots | Empty | Kept |", "|---|---|---|---|---|---|"]
for c in cleaning:
    L.append(f"| {c['city']} | {c['duplicate']} | {c['removed_deleted']} | {c['bot']} | {c['empty']} | {c['kept']} |")
L += ["", "Every week (kept or why dropped) is in `weekly.csv`.", ""]
open(OUT / "results.md", "w", encoding="utf-8").write("\n".join(L))

for r in rows:
    print(f"{r['city']:13s} {r['status'][:60]:60s} event {r['event_share_pct']}% normal {r['normal_share_pct']}% "
          f"rise {r['rise_ratio']}x ({r['rise_pp']} pp) higher than {r['percentile_higher_than']}")
for t in tests:
    print(f"{t['test']}: rho ratio {t['rho_with_ratio']} abs {t['rho_with_absolute']} -> {t['verdict']}")
print(f"pairs: higher-ratio city won {won_ratio}/{n_pairs}; worse-air city won {won_abs_crossed}/{n_crossed} crossed")
print("DONE")
