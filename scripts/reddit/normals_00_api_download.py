#!/usr/bin/env python3
"""
scripts/reddit/normals_00_api_download.py

Normals, Step 0: download the planned Reddit pulls from the Arctic Shift API instead of clicking
through the download tool (which runs on the same API). Same file names and folders as the manual
downloads, so normals_01_check_and_strip_usernames.py checks the result the same way.

Plan: read from the pull-plan docs (the tables are the single source of truth):
  docs/reddit-pull-month-normals-8-cities.md   (default)
  docs/reddit-pull-eugene-bakersfield.md       (only used for the validation test)
Each table row gives a file name (<city>_<month|event|neighbor>_<date>_posts.jsonl), a "download from"
date and a "download to" date. Window = [from 00:00 UTC, to 00:00 UTC), as in the download tool.

API: https://arctic-shift.photon-reddit.com/api/{posts,comments}/search
     ?subreddit=..&after=<epoch>&before=<epoch>&sort=asc&limit=auto
     (docs: github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md; limit=auto returns
     100-1000 items per request.) Paging: one UTC day at a time; within a day, the next request starts at the last item's created_utc;
     items are de-duplicated by id, and only items inside the window are kept.
Politeness: 1.5 s between requests. On HTTP 429 (rate limit) or 422 ("Timeout. Maybe slow down a bit",
seen on the busiest days, e.g. r/Detroit 2026-07-16) waits 20 s x try number (long waits did not help) and asks for pages of 50, then 25,
instead of "auto"; other errors retry with growing waits, 10 tries, then the pull is reported as failed (not fatal for the others).
Resumable: a finished file is never downloaded again. Files are written to <name>.part and renamed
only when the pull is complete, so a half-finished file never looks finished.
Records are saved exactly as the API returns them (usernames included, like the tool's files);
normals_01 strips them.

Run from the repo root:
  python3 scripts/reddit/normals_00_api_download.py --dry-run          (list what would be downloaded)
  python3 scripts/reddit/normals_00_api_download.py                    (download everything to ~/Downloads/<city>/)
  python3 scripts/reddit/normals_00_api_download.py --only detroit     (only file names containing "detroit")
  python3 scripts/reddit/normals_00_api_download.py --skip detroit_event   (everything except that pull)
  python3 scripts/reddit/normals_00_api_download.py --plan docs/reddit-pull-eugene-bakersfield.md \
      --only bakersfield_month_2019-12-02 --out <folder>                (validation test)
"""

import argparse
import json
import os
import re
import sys
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone

API = "https://arctic-shift.photon-reddit.com/api/{kind}/search"
SUBREDDITS = {"eugene": "Eugene", "bakersfield": "bakersfield", "fairbanks": "Fairbanks", "fresno": "fresno",
              "detroit": "Detroit", "seattle": "Seattle", "indianapolis": "indianapolis",
              "pittsburgh": "pittsburgh", "sanjose": "SanJose"}
ROW = re.compile(r"`(([a-z]+)_(?:month|event|neighbor)_\d{4}-\d{2}-\d{2})_posts\.jsonl`")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
PAUSE, TRIES, DAY = 1.5, 10, 86400


def read_plan(path):
    pulls = []
    for line in open(path, encoding="utf-8"):
        m = ROW.search(line)
        if not m or not line.lstrip().startswith("|"):
            continue
        name, city = m.group(1), m.group(2)
        dates = DATE.findall(line[:m.start()])          # dates before the file name; last two = from, to
        pulls.append({"name": name, "city": city, "from": dates[-2], "to": dates[-1]})
    return pulls


def epoch(d):
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp())


def get(base, params):
    # curl rather than urllib: this Mac's Python can't verify the site's SSL certificate (same approach as
    # scripts/openaq/04_download_daily.py)
    for attempt in range(1, TRIES + 1):
        # after a failure, ask for smaller pages (50, then 25). Pages of exactly 100 were refused instantly with
        # 422 while 5/25/50/auto worked (tested 2026-10-03 on r/Detroit comments).
        url = base + "?" + urllib.parse.urlencode({**params, "limit": "auto" if attempt == 1 else 50 if attempt == 2 else 25})
        r = subprocess.run(["curl", "-s", "-m", "180", "-A", "studio-dataviz research (MDE studio project)",
                            "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        if code == "200":
            try:
                data = json.loads(body)
                if not data.get("error"):
                    return data["data"]
                msg = str(data["error"])[:80]
            except ValueError:
                msg = "unreadable JSON"
            wait = 10 * attempt
        else:
            msg = f"HTTP {code or 'timeout'} {body.strip()[:120]}"
            # 429 = rate limit; 422 = "Timeout. Maybe slow down a bit" (server busy) -> long waits
            wait = 20 * attempt if code in ("429", "422") else 10 * attempt
        print(f"      {msg}, waiting {wait} s (try {attempt}/{TRIES})", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"failed after {TRIES} tries")


def download(sub, kind, a, b, path):
    # One UTC day at a time (2026-10-03): each request then covers a small slice of the archive, which the server
    # handles far more reliably than a month-long query (r/Detroit 2026 comments kept timing out otherwise).
    seen, n, req = set(), 0, 0
    with open(path + ".part", "w", encoding="utf-8") as out:
        for d0 in range(a, b, DAY):
            d1, after = min(d0 + DAY, b), d0
            while True:
                items = get(API.format(kind=kind), {"subreddit": sub, "after": after, "before": d1, "sort": "asc"})
                req += 1
                time.sleep(PAUSE)
                new = [x for x in items if x["id"] not in seen]
                for x in new:
                    seen.add(x["id"])
                    if a <= float(x["created_utc"]) < b:
                        out.write(json.dumps(x, ensure_ascii=False) + "\n"); n += 1
                if not items:
                    break
                last = int(float(items[-1]["created_utc"]))
                # next page starts at the last timestamp (duplicates are skipped by id); if a whole page was
                # already seen, step one second forward so the loop can't stall
                after = last if new else last + 1
                if after >= d1:
                    break
    os.replace(path + ".part", path)
    return n, req


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="docs/reddit-pull-month-normals-8-cities.md")
    ap.add_argument("--out", default=os.path.expanduser("~/Downloads"))
    ap.add_argument("--only", help="only pulls whose file name contains this text")
    ap.add_argument("--skip", help="leave out pulls whose file name contains this text")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pulls = [p for p in read_plan(args.plan) if (not args.only or args.only in p["name"])
             and not (args.skip and args.skip in p["name"])]
    print(f"{len(pulls)} pulls ({2 * len(pulls)} files) from {args.plan} -> {args.out}/<city>/", flush=True)
    failed, t0 = [], time.time()
    for i, p in enumerate(pulls, 1):
        sub = SUBREDDITS[p["city"]]
        if not args.dry_run:
            os.makedirs(os.path.join(args.out, p["city"]), exist_ok=True)
        for kind in ("posts", "comments"):
            path = os.path.join(args.out, p["city"], f"{p['name']}_{kind}.jsonl")
            label = f"[{i}/{len(pulls)}] r/{sub} {kind:8s} {p['from']} -> {p['to']}"
            if os.path.exists(path):
                print(f"{label}  already done, skipped", flush=True); continue
            if args.dry_run:
                print(f"{label}  -> {path}", flush=True); continue
            try:
                n, req = download(sub, kind, epoch(p["from"]), epoch(p["to"]), path)
                print(f"{label}  {n} records, {req} requests  ({(time.time() - t0) / 60:.1f} min so far)", flush=True)
            except RuntimeError as e:
                failed.append(path); print(f"{label}  FAILED: {e}", flush=True)
    if failed:
        print("\nFAILED (run again to retry; finished files are skipped):\n  " + "\n  ".join(failed)); sys.exit(1)
    print("DONE")


if __name__ == "__main__":
    main()
