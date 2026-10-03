"""Event weeks, Step 1: copy Gina's Arctic Shift event-week pulls with username fields removed.

Input:  ~/Downloads/event week/r_<subreddit>_{posts,comments}.jsonl  (Gina's downloads; never modified, read only)
Output: data/processed/reddit/event_weeks_no_usernames/<same file name>
        data/processed/reddit/event_weeks_no_usernames/coverage.csv  (one row per file)

Removed from every record, at every level of nesting: every field whose name starts with "author"
(username, user ID, account creation time, flair, premium/patreon status, cakeday, is_blocked;
also the original poster inside crosspost_parent_list and author_name/author_url of embedded
media such as YouTube or Twitter) and "link_author" (the username of the post a comment belongs
to). Everything else is kept as downloaded.
Usernames typed inside post or comment text (e.g. "u/name") are NOT removed.
"""
import collections, csv, datetime as dt, json, os, sys

SRC = os.path.expanduser("~/Downloads/event week")
OUT = sys.argv[1]
UTC = dt.timezone.utc

def drop(key):
    return key.startswith("author") or key == "link_author"

def strip(obj, removed):
    """Remove username fields from obj and everything nested inside it."""
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

rows = []
for name in sorted(os.listdir(SRC)):
    if not name.endswith(".jsonl"):
        continue  # skips .DS_Store and any unfinished .crswap download
    n, removed, ts, ids, subs = 0, collections.Counter(), [], set(), set()
    with open(os.path.join(SRC, name), encoding="utf-8") as fin, \
         open(os.path.join(OUT, name), "w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line)
            strip(rec, removed)
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            ts.append(float(rec["created_utc"]))
            ids.add(rec["id"])
            subs.add(rec["subreddit"])
    first = dt.datetime.fromtimestamp(min(ts), UTC)
    last = dt.datetime.fromtimestamp(max(ts), UTC)
    rows.append({"file": name, "subreddit": "|".join(sorted(subs)),
                 "kind": "comments" if "_comments" in name else "posts",
                 "records": n, "unique_ids": len(ids),
                 "first_utc": first.strftime("%Y-%m-%d %H:%M"), "last_utc": last.strftime("%Y-%m-%d %H:%M"),
                 "field_names_removed": len(removed), "values_removed": sum(removed.values())})
    print(f"{name}: {n} records, {sum(removed.values())} username values removed ({len(removed)} field names), {first:%b %d %H:%M} -> {last:%b %d %H:%M} UTC")

with open(os.path.join(OUT, "coverage.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# check: no author fields left in any output
for name in os.listdir(OUT):
    if name.endswith(".jsonl"):
        with open(os.path.join(OUT, name), encoding="utf-8") as f:
            assert not any(has_author(json.loads(line)) for line in f), name
print("check passed: no author fields at any level in any output file")
