"""Normals, Step 1b: check Dish's API downloads for the other cities against the pull plan, then copy them with
username fields removed. Same checks and same username rule as Gina's normals_01_check_and_strip_usernames.py
(which has Eugene and Bakersfield hard-coded and rewrites coverage.csv); this version reads the plan from the
pull-plan doc, runs one city at a time, and adds/replaces only that city's rows in coverage.csv.

Plan:   docs/reddit-pull-month-normals-8-cities.md (read with normals_00_api_download.read_plan)
Input:  ~/Downloads/<city>/<name>_{posts,comments}.jsonl   (Dish's downloads; read only)
Output: data/processed/reddit/normals_no_usernames/<city>/<same file name>
        data/processed/reddit/normals_no_usernames/coverage.csv   (rows for this city replaced; others kept)

Checks. Any of these and nothing is written for that city:
  - every planned file exists and no unplanned .jsonl file is in the folder
  - every line is valid JSON; no duplicate ids; only the city's subreddit (case-insensitive: the API returns
    the subreddit's own spelling, e.g. "SanJose")
  - every record falls inside the planned window [download from 00:00 UTC, download to 00:00 UTC)
  - comments: the first and last day of the window each have records (a truncated download fails this)
Warnings (reported in coverage.csv, not fatal; Claude's choice, because small subreddits such as r/Fairbanks
can have a genuinely empty day or a quiet last evening):
  - empty days inside the window
  - comments ending more than 2 hours before the window ends
  - posts: an empty first or last day (r/Fairbanks June 2019 had ~1.4 posts a day and none on the padding day
    Jun 2, while its comments covered both edges; added 2026-10-03)
Username removal: every field whose name starts with "author", and "link_author", at every level of nesting
(same rule as normals_01). Usernames typed inside the text are not removed.

Run from the repo root, one city at a time, e.g.:
  python3 scripts/reddit/normals_01b_check_and_strip_more_cities.py fairbanks
"""
import collections, csv, datetime as dt, importlib.util, json, os, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("dl", Path(__file__).parent / "normals_00_api_download.py")
dl = importlib.util.module_from_spec(spec); spec.loader.exec_module(dl)

PLAN_DOC = "docs/reddit-pull-month-normals-8-cities.md"
SRC = os.path.expanduser("~/Downloads")
OUT = "data/processed/reddit/normals_no_usernames"
UTC = dt.timezone.utc
city = sys.argv[1]
sub = dl.SUBREDDITS[city]
pulls = [p for p in dl.read_plan(PLAN_DOC) if p["city"] == city]
if not pulls:
    sys.exit(f"no pulls for {city} in {PLAN_DOC}")


def drop(key):
    return key.startswith("author") or key == "link_author"


def strip(obj, removed):
    if isinstance(obj, dict):
        for k in [k for k in obj if drop(k)]:
            removed[k] += 1
            del obj[k]
        for v in obj.values():
            strip(v, removed)
    elif isinstance(obj, list):
        for v in obj:
            strip(v, removed)


def has_author(obj):
    if isinstance(obj, dict):
        return any(drop(k) or has_author(v) for k, v in obj.items())
    if isinstance(obj, list):
        return any(has_author(v) for v in obj)
    return False


def day(s):
    return dt.datetime.fromisoformat(s).replace(tzinfo=UTC)


# ---- 1. check everything first
problems, rows = [], []
folder = os.path.join(SRC, city)
planned = {f"{p['name']}_{k}.jsonl" for p in pulls for k in ("posts", "comments")}
present = {f for f in os.listdir(folder) if f.endswith(".jsonl")} if os.path.isdir(folder) else set()
problems += [f"missing {f}" for f in sorted(planned - present)]
problems += [f"unplanned file {f}" for f in sorted(present - planned)]
for p in pulls:
    A, B = day(p["from"]), day(p["to"])
    for kind in ("posts", "comments"):
        f = f"{p['name']}_{kind}.jsonl"
        if f not in present:
            continue
        ts, ids, subs, bad = [], set(), set(), 0
        for line in open(os.path.join(folder, f), encoding="utf-8"):
            try:
                o = json.loads(line)
            except ValueError:
                bad += 1; continue
            ts.append(float(o["created_utc"])); ids.add(o["id"]); subs.add(o["subreddit"].lower())
        if not ts:
            problems.append(f"{f}: empty file"); continue
        when = [dt.datetime.fromtimestamp(t, UTC) for t in ts]
        days = collections.Counter(w.date() for w in when)
        all_days = [(A + dt.timedelta(d)).date() for d in range((B - A).days)]
        empty = [str(d) for d in all_days if days[d] == 0]
        outside = sum(1 for w in when if not A <= w < B)
        last = max(when)
        bad_list = []
        if bad: bad_list.append(f"{bad} unreadable lines")
        if len(ids) != len(ts): bad_list.append(f"{len(ts) - len(ids)} duplicate ids")
        if subs != {sub.lower()}: bad_list.append(f"subreddits {subs}")
        if outside: bad_list.append(f"{outside} records outside the window")
        edge_empty = days[all_days[0]] == 0 or days[all_days[-1]] == 0
        if edge_empty and kind == "comments": bad_list.append("first or last day of the window is empty")
        problems += [f"{f}: {x}" for x in bad_list]
        warn = []
        if empty: warn.append(f"empty days {empty}")
        if edge_empty and kind == "posts": warn.append("first or last day of the window has no posts")
        if kind == "comments" and last < B - dt.timedelta(hours=2): warn.append(f"comments end at {last:%Y-%m-%d %H:%M} UTC")
        rows.append({"city": city, "file": f, "pull": p["name"].split("_")[1], "kind": kind,
                     "download_from": p["from"], "download_to": p["to"], "records": len(ts),
                     "first_utc": f"{min(when):%Y-%m-%d %H:%M}", "last_utc": f"{last:%Y-%m-%d %H:%M}",
                     "days_in_window": (B - A).days, "empty_days": len(empty), "warnings": "; ".join(warn)})

if problems:
    print(f"{city}: NOT COMPLETE, nothing written:"); print("\n".join("  " + x for x in problems)); sys.exit(1)
print(f"{city}: all checks passed: {len(rows)} files, {sum(r['records'] for r in rows)} records")
for r in rows:
    if r["warnings"]:
        print(f"  warning {r['file']}: {r['warnings']}")

# ---- 2. write cleaned copies
os.makedirs(os.path.join(OUT, city), exist_ok=True)
for r in rows:
    removed = collections.Counter()
    with open(os.path.join(folder, r["file"]), encoding="utf-8") as fin, \
         open(os.path.join(OUT, city, r["file"]), "w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line); strip(rec, removed)
            assert not has_author(rec)
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    r["values_removed"] = sum(removed.values())

# ---- 3. coverage.csv: replace this city's rows, keep everyone else's
cov = os.path.join(OUT, "coverage.csv")
old = list(csv.DictReader(open(cov, encoding="utf-8"))) if os.path.exists(cov) else []
cols = list(rows[0])
for c in (old[0].keys() if old else []):
    if c not in cols: cols.append(c)
keep = [r for r in old if r["city"] != city]
with open(cov, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, restval=""); w.writeheader(); w.writerows(keep + rows)
print(f"{city}: wrote {len(rows)} files to {OUT}/{city}/ and updated coverage.csv ({len(keep)} other rows kept)")
