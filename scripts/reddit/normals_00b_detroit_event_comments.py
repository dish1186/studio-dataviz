#!/usr/bin/env python3
"""
scripts/reddit/normals_00b_detroit_event_comments.py

Normals, Step 0b (plan B for one file): build ~/Downloads/detroit/detroit_event_2026-07-13_comments.jsonl
without asking the Arctic Shift API for r/Detroit's busiest stretch (Jul 16, 2026, the record smoke day),
where every request kept failing with HTTP 422 "Timeout. Maybe slow down a bit".

The planned window is [2026-07-12 00:00, 2026-07-21 00:00) UTC (docs/reddit-pull-month-normals-8-cities.md).
Final version (2026-10-03): ONLY the middle piece below is used; see the note in the code. Originally planned as three pieces:
  [Jul 12, Jul 13) UTC   new API download (quiet day before the week)
  [Jul 13, Jul 20) UTC   Gina's complete download of the event week, already checked and username-stripped:
                         data/processed/reddit/event_weeks_no_usernames/r_Detroit_comments.jsonl
                         (5,908 comments, Jul 13 00:06 -> Jul 19 23:59 UTC; see scripts/reddit/event_weeks_02_detroit3_comments.py)
  [Jul 20, Jul 21) UTC   new API download (covers Sunday evening local time, which Gina's UTC-day file missed)
  The two API pieces stop at Jul 12 21:00 and Jul 20 19:00 UTC: the hours after those always time out on the API,
  and they are padding outside the local event week (normals_01b reports the early end as a warning).
Records are de-duplicated by id and sorted by time. Gina's records already have no username fields; the new
ones still do, and normals_01_check_and_strip_usernames.py removes them, so the end result is the same.
normals_01 then checks the combined file like any other (window, no empty day, comments to the last day).

Run from the repo root: python3 scripts/reddit/normals_00b_detroit_event_comments.py
"""

import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("dl", HERE / "normals_00_api_download.py")
dl = importlib.util.module_from_spec(spec); spec.loader.exec_module(dl)

GINA = Path("data/processed/reddit/event_weeks_no_usernames/r_Detroit_comments.jsonl")
OUT = Path(os.path.expanduser("~/Downloads/detroit/detroit_event_2026-07-13_comments.jsonl"))
A, MID1, MID2, B = (dl.epoch(d) for d in ("2026-07-12", "2026-07-13", "2026-07-20", "2026-07-21"))

if OUT.exists():
    raise SystemExit(f"{OUT} already exists; nothing to do (delete it first to rebuild)")
OUT.parent.mkdir(parents=True, exist_ok=True)

recs = {}
gina = [json.loads(l) for l in open(GINA, encoding="utf-8")]
inside = [r for r in gina if MID1 <= float(r["created_utc"]) < MID2]
print(f"Gina's file: {len(gina)} comments, {len(inside)} inside [Jul 13, Jul 20) UTC")
for r in inside:
    recs[r["id"]] = r

# 2026-10-03 (Dish: "accept the gap and log it"): no API pieces. r/Detroit comment search for Jul 12 and Jul 20, 2026
# timed out on every request (even one hour at a time), while posts for the same hours downloaded fine. The file is
# Gina's copy only, [Jul 13 00:00, Jul 20 00:00) UTC. The local event week (Mon Jul 13 04:00 -> Mon Jul 20 04:00 UTC)
# is therefore missing Sunday Jul 19, 8 pm-midnight EDT (a typical evening slot holds about 3.4% of the week's comments).
# normals_01b checks this file against [Jul 13, Jul 20) UTC instead of the plan's download window.
rows = sorted(recs.values(), key=lambda r: float(r["created_utc"]))
with open(str(OUT) + ".part", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
os.replace(str(OUT) + ".part", OUT)
print(f"wrote {OUT}: {len(rows)} comments")
