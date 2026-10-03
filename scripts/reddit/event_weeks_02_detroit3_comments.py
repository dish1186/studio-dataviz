"""Event weeks, Step 2: replace the Detroit comments copy with Gina's complete 3rd/4th download ("Detroit3").

The Detroit comments file used in Step 1 stopped at Jul 19 21:11 UTC. Gina's later download
r_Detroit3_comments.jsonl (Jul 13-20, 2026) runs to Jul 19 23:59 UTC and contains every comment
of the first file plus 86 more. This script makes a cleaned copy of it, removing username fields
exactly as in Step 1, and saves it under the usual name r_Detroit_comments.jsonl.

Input:  ~/Downloads/r_Detroit3_comments.jsonl  (Gina's download; read only, never modified)
Output: data/processed/reddit/event_weeks_no_usernames/r_Detroit_comments.jsonl (replaced)
        data/processed/reddit/event_weeks_no_usernames/coverage.csv (Detroit comments row updated)
"""
import collections, csv, datetime as dt, json, os, sys

SRC = os.path.expanduser("~/Downloads/r_Detroit3_comments.jsonl")
OUT = sys.argv[1]
NAME = "r_Detroit_comments.jsonl"
UTC = dt.timezone.utc

def drop(key):
    return key.startswith("author") or key == "link_author"

def strip(obj, removed):
    """Remove username fields from obj and everything nested inside it (same rule as Step 1)."""
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

old_ids = {json.loads(l)["id"] for l in open(os.path.join(OUT, NAME), encoding="utf-8")}
n, removed, ts, ids, subs = 0, collections.Counter(), [], set(), set()
tmp = os.path.join(OUT, NAME + ".tmp")
with open(SRC, encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
    for line in fin:
        rec = json.loads(line)
        strip(rec, removed)
        assert not has_author(rec)
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n += 1; ts.append(float(rec["created_utc"])); ids.add(rec["id"]); subs.add(rec["subreddit"])
assert subs == {"Detroit"} and len(ids) == n
assert old_ids <= ids, "Detroit3 is missing comments that the Step 1 file had"
os.replace(tmp, os.path.join(OUT, NAME))

first, last = (dt.datetime.fromtimestamp(x, UTC) for x in (min(ts), max(ts)))
cov = os.path.join(OUT, "coverage.csv")
rows = list(csv.DictReader(open(cov)))
for r in rows:
    if r["file"] == NAME:
        r.update(records=n, unique_ids=len(ids), first_utc=first.strftime("%Y-%m-%d %H:%M"),
                 last_utc=last.strftime("%Y-%m-%d %H:%M"), field_names_removed=len(removed),
                 values_removed=sum(removed.values()))
with open(cov, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"{NAME}: {len(old_ids)} -> {n} comments (+{len(ids - old_ids)}), {first:%b %d %H:%M} -> {last:%b %d %H:%M} UTC, "
      f"{sum(removed.values())} username values removed")
