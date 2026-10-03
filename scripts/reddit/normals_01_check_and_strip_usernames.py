"""Normals, Step 1: check Gina's Eugene and Bakersfield "normal" pulls against the pull plan,
then copy them with username fields removed.

Plan: docs/reddit-pull-eugene-bakersfield.md (Dish + Claude, 2026-10-02): 8 pulls per city
(1 neighbor + 7 month), posts and comments each = 32 files.

Input:  ~/Downloads/{eugene,bakersfield}/<name>_{posts,comments}.jsonl  (Gina's downloads; read only)
Output: data/processed/reddit/normals_no_usernames/<city>/<same file name>
        data/processed/reddit/normals_no_usernames/coverage.csv

Checks (all must pass, or nothing is written):
  - every planned file exists and no unplanned .jsonl file is in the folder
  - every line is valid JSON; no duplicate ids; only the city's subreddit
  - every record falls inside the planned window [download from 00:00 UTC, download to 00:00 UTC)
  - no day in the window is empty, so the first and last day both have records
  - comments run to at least 22:00 UTC on the last day (a download that stopped early ends sooner)
Username removal: same rule as scripts/reddit/event_weeks_01_strip_usernames.py: every field whose
name starts with "author", and "link_author", at every level of nesting. Usernames typed inside
the text are not removed.
"""
import collections, csv, datetime as dt, json, os, sys

SRC = os.path.expanduser("~/Downloads")
OUT = sys.argv[1]
UTC = dt.timezone.utc
PLAN = {  # city: (subreddit, [(name, download from, download to)])  copied from the plan doc
    "eugene": ("Eugene", [
        ("eugene_neighbor_2020-07-27", "2020-07-26", "2020-10-27"),
        ("eugene_month_2019-09-02", "2019-09-01", "2019-10-01"),
        ("eugene_month_2020-08-31", "2020-08-30", "2020-09-29"),
        ("eugene_month_2021-08-30", "2021-08-29", "2021-10-05"),
        ("eugene_month_2022-08-29", "2022-08-28", "2022-10-04"),
        ("eugene_month_2023-09-04", "2023-09-03", "2023-10-03"),
        ("eugene_month_2024-09-02", "2024-09-01", "2024-10-01"),
        ("eugene_month_2025-09-01", "2025-08-31", "2025-09-30")]),
    "bakersfield": ("Bakersfield", [
        ("bakersfield_neighbor_2024-10-21", "2024-10-20", "2025-01-21"),
        ("bakersfield_month_2019-12-02", "2019-12-01", "2019-12-31"),
        ("bakersfield_month_2020-11-30", "2020-11-29", "2021-01-05"),
        ("bakersfield_month_2021-11-29", "2021-11-28", "2022-01-04"),
        ("bakersfield_month_2022-11-28", "2022-11-27", "2023-01-03"),
        ("bakersfield_month_2023-12-04", "2023-12-03", "2024-01-02"),
        ("bakersfield_month_2024-12-02", "2024-12-01", "2024-12-31"),
        ("bakersfield_month_2025-12-01", "2025-11-30", "2025-12-30")]),
}

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
for city, (sub, pulls) in PLAN.items():
    planned = {f"{n}_{k}.jsonl" for n, _, _ in pulls for k in ("posts", "comments")}
    present = {f for f in os.listdir(os.path.join(SRC, city)) if f.endswith(".jsonl")}
    problems += [f"{city}: missing {f}" for f in sorted(planned - present)]
    problems += [f"{city}: unplanned file {f}" for f in sorted(present - planned)]
    for name, a, b in pulls:
        A, B = day(a), day(b)
        for kind in ("posts", "comments"):
            f = f"{name}_{kind}.jsonl"
            if f not in present:
                continue
            ts, ids, subs, bad = [], set(), set(), 0
            for line in open(os.path.join(SRC, city, f), encoding="utf-8"):
                try:
                    o = json.loads(line)
                except ValueError:
                    bad += 1; continue
                ts.append(float(o["created_utc"])); ids.add(o["id"]); subs.add(o["subreddit"])
            when = [dt.datetime.fromtimestamp(t, UTC) for t in ts]
            days = collections.Counter(w.date() for w in when)
            empty = [str((A + dt.timedelta(d)).date()) for d in range((B - A).days)
                     if days[(A + dt.timedelta(d)).date()] == 0]
            outside = sum(1 for w in when if not A <= w < B)
            last = max(when)
            p = []
            if bad: p.append(f"{bad} unreadable lines")
            if len(ids) != len(ts): p.append(f"{len(ts) - len(ids)} duplicate ids")
            if subs != {sub}: p.append(f"subreddits {subs}")
            if outside: p.append(f"{outside} records outside the window")
            if empty: p.append(f"empty days {empty}")
            if kind == "comments" and last < B - dt.timedelta(hours=2): p.append(f"comments end early at {last:%Y-%m-%d %H:%M} UTC")
            problems += [f"{city}/{f}: {x}" for x in p]
            rows.append({"city": city, "file": f, "pull": name.split("_")[1], "kind": kind,
                         "download_from": a, "download_to": b, "records": len(ts),
                         "first_utc": f"{min(when):%Y-%m-%d %H:%M}", "last_utc": f"{last:%Y-%m-%d %H:%M}",
                         "days_in_window": (B - A).days, "empty_days": len(empty)})

if problems:
    print("NOT COMPLETE, nothing written:"); print("\n".join("  " + p for p in problems)); sys.exit(1)
print(f"all checks passed: {len(rows)} files, {sum(r['records'] for r in rows)} records")

# ---- 2. write cleaned copies
for r in rows:
    os.makedirs(os.path.join(OUT, r["city"]), exist_ok=True)
    removed = collections.Counter()
    with open(os.path.join(SRC, r["city"], r["file"]), encoding="utf-8") as fin, \
         open(os.path.join(OUT, r["city"], r["file"]), "w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line); strip(rec, removed)
            assert not has_author(rec)
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    r["values_removed"] = sum(removed.values())
    print(f"  {r['city']}/{r['file']}: {r['records']} records, {r['first_utc']} -> {r['last_utc']} UTC, {r['values_removed']} username values removed")

with open(os.path.join(OUT, "coverage.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
