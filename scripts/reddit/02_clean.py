#!/usr/bin/env python3
"""
scripts/reddit/02_clean.py

Step 02 of the Reddit case study (Eugene vs Bakersfield: do people react to
harm or to abnormality?). Reads the 12 raw Arctic Shift downloads and writes
one cleaned file per window. Nothing is scored or classified here.

Run from the repo root:
    python scripts/reddit/02_clean.py            # all windows
    python scripts/reddit/02_clean.py --force    # overwrite existing outputs

Input:   data/raw/reddit/arctic-shift/<window>_posts.jsonl
         data/raw/reddit/arctic-shift/<window>_comments.jsonl
Output:  data/processed/reddit/step02_clean/<window>.csv   one row per kept post or comment
         data/processed/reddit/step02_clean/summary.csv    rows in, rows dropped (by reason), rows kept
         data/processed/reddit/step02_clean/per_day.csv    kept rows per local day
         data/processed/reddit/step02_clean/bots_found.txt bot accounts dropped (for audit)

What happens to each raw row, in this order (first reason that applies wins):
    1. duplicate id                    -> dropped ("duplicate")
    2. outside the local week          -> dropped ("outside_window")
    3. removed or deleted              -> dropped ("removed_deleted")
    4. posted by a bot                 -> dropped ("bot")
    5. no text left after cleaning     -> dropped ("empty_after_clean")
    6. otherwise                       -> kept

Claude defaults (log these as decisions, change any you disagree with):
    C1  Week = local Monday 00:00 to the next Monday 00:00, in America/Los_Angeles
        for both cities (handles PDT in August and PST in December).
    C2  Removed or deleted = any of: _meta.removal_type set; _meta.was_deleted_later
        true; removed_by_category set; author "[deleted]"; body/selftext "[removed]"
        or "[deleted]". Archived text of removed items is never used, even where
        the archive kept it.
    C3  Bots = an explicit list of known bot accounts (BOTS below), "<sub>-ModTeam"
        accounts, and comments distinguished as "moderator" (official mod notices).
        Revised 2026-09-30 after auditing bots_found.txt: the earlier "name ends in
        bot" rule also caught human accounts ending in "robot". The accounts dropped
        are listed in bots_found.txt for audit.
    C4  Usernames are not carried into processed files. "u/name" mentions inside
        text become "u/[user]".
    C5  Text cleaning: HTML entities decoded; quoted lines (starting with ">") removed,
        since they are someone else's words; markdown links [text](url) kept as text;
        bare URLs removed; markdown symbols (*, _, ~, #, `) removed; whitespace collapsed.
    C6  A post's text = title + body. Link-only posts keep their title.
    C7  Comments are kept even when their parent post was removed or falls outside
        the week; each comment is judged on its own time and status.
    C8  thread_id = the post id (for posts) or the parent post id from link_id
        (for comments). Used later for the thread-level bootstrap.
"""

import argparse
import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

RAW = Path("data/raw/reddit/arctic-shift")
OUT = Path("data/processed/reddit/step02_clean")
TZ = ZoneInfo("America/Los_Angeles")   # C1

# window name, city, week type, subreddit, first local day of the week (a Monday)
WINDOWS = [
    ("eugene_event_2026-08-03",      "Eugene",      "event",    "Eugene",      date(2026, 8, 3)),
    ("eugene_base_2024-08-05",       "Eugene",      "baseline", "Eugene",      date(2024, 8, 5)),
    ("eugene_base_2025-08-04",       "Eugene",      "baseline", "Eugene",      date(2025, 8, 4)),
    ("bakersfield_event_2024-12-02", "Bakersfield", "event",    "bakersfield", date(2024, 12, 2)),
    ("bakersfield_base_2023-12-04",  "Bakersfield", "baseline", "bakersfield", date(2023, 12, 4)),
    ("bakersfield_base_2025-12-01",  "Bakersfield", "baseline", "bakersfield", date(2025, 12, 1)),
]
KINDS = ["posts", "comments"]

GONE_TEXT = {"[removed]", "[deleted]"}
# C3 (revised after audit of bots_found.txt, 2026-09-30): explicit list, not a name pattern.
BOTS = {"automoderator", "sneakpeekbot", "haikusbot", "sokkahaikubot", "amputatorbot", "vettedbot",
        "wikisummarizerbot", "remindmebot", "savevideo", "savevideobot", "repostsleuthbot"}
MODTEAM = re.compile(r"-modteam$", re.IGNORECASE)
URL = re.compile(r"https?://\S+|www\.\S+")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
USER = re.compile(r"(?<![\w/])/?u/[A-Za-z0-9_-]+")
MD_SYMBOLS = re.compile(r"[*_~`#]+")
SPACES = re.compile(r"\s+")


def week_bounds(monday):
    start = datetime.combine(monday, time(0, 0), TZ)
    end = datetime.combine(monday + timedelta(days=7), time(0, 0), TZ)
    return int(start.timestamp()), int(end.timestamp())


def is_removed(x, kind):                                         # C2
    meta = x.get("_meta") or {}
    body = (x.get("selftext") if kind == "posts" else x.get("body")) or ""
    return bool(
        meta.get("removal_type")
        or meta.get("was_deleted_later")
        or x.get("removed_by_category")
        or x.get("author") == "[deleted]"
        or body.strip() in GONE_TEXT
    )


def is_bot(x, kind):                                             # C3
    a = x.get("author") or ""
    return a.lower() in BOTS or bool(MODTEAM.search(a)) or (kind == "comments" and x.get("distinguished") == "moderator")


def clean(text):                                                 # C4, C5
    t = html.unescape(text or "")
    t = "\n".join(line for line in t.split("\n") if not line.lstrip().startswith(">"))
    t = MD_LINK.sub(r"\1", t)
    t = URL.sub(" ", t)
    t = USER.sub("u/[user]", t)
    t = MD_SYMBOLS.sub(" ", t)
    t = t.replace("\u200b", " ")
    return SPACES.sub(" ", t).strip()


def read_jsonl(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    bad += 1
    if bad:
        print(f"    WARNING: {bad} unreadable lines in {path.name}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    summary, per_day, bots = [], [], defaultdict(Counter)

    for name, city, wtype, sub, monday in WINDOWS:
        out_path = OUT / f"{name}.csv"
        if out_path.exists() and not args.force:
            print(f"\n{name}: {out_path} exists, skipping (use --force to overwrite)")
            continue
        start, end = week_bounds(monday)
        print(f"\n{name}  local {monday} to {monday + timedelta(days=6)} "
              f"(UTC {datetime.fromtimestamp(start, timezone.utc):%Y-%m-%d %H:%M} -> "
              f"{datetime.fromtimestamp(end, timezone.utc):%Y-%m-%d %H:%M})")
        kept = []
        for kind in KINDS:
            path = RAW / f"{name}_{kind}.jsonl"
            if not path.exists():
                print(f"    MISSING: {path}")
                continue
            raw = read_jsonl(path)
            ts = [int(float(x["created_utc"])) for x in raw]
            # coverage check: does the raw file span the whole local week?
            if ts and (min(ts) > start + 3600 or max(ts) < end - 3600):
                print(f"    WARNING: raw {kind} cover {datetime.fromtimestamp(min(ts), timezone.utc):%m-%d %H:%M} -> "
                      f"{datetime.fromtimestamp(max(ts), timezone.utc):%m-%d %H:%M} UTC; the week may be incomplete")
            subs = Counter(x.get("subreddit") for x in raw)
            if {str(s).lower() for s in subs} - {sub.lower()}:
                print(f"    WARNING: unexpected subreddits {dict(subs)}")

            reasons, seen = Counter(), set()
            for x in raw:
                t = int(float(x["created_utc"]))
                if x["id"] in seen:
                    reasons["duplicate"] += 1; continue
                seen.add(x["id"])
                if not (start <= t < end):
                    reasons["outside_window"] += 1; continue
                if is_removed(x, kind):
                    reasons["removed_deleted"] += 1; continue
                if is_bot(x, kind):
                    reasons["bot"] += 1
                    bots[name][x.get("author") or "(none)"] += 1
                    continue
                if kind == "posts":                                   # C6
                    text = clean((x.get("title") or "") + "\n" + (x.get("selftext") or ""))
                    thread = x["id"]
                else:
                    text = clean(x.get("body"))
                    thread = (x.get("link_id") or "").replace("t3_", "")   # C8
                if not text:
                    reasons["empty_after_clean"] += 1; continue
                local = datetime.fromtimestamp(t, TZ)
                kept.append({
                    "window": name, "city": city, "week_type": wtype, "kind": kind[:-1],
                    "id": x["id"], "thread_id": thread,
                    "parent_id": (x.get("parent_id") or "") if kind == "comments" else "",
                    "created_utc": t, "created_local": local.strftime("%Y-%m-%d %H:%M"),
                    "local_date": local.strftime("%Y-%m-%d"),
                    "score": x.get("score"), "num_comments": x.get("num_comments") if kind == "posts" else None,
                    "text_clean": text, "n_chars": len(text),
                })
                reasons["kept"] += 1
            row = {"window": name, "city": city, "week_type": wtype, "kind": kind, "raw_rows": len(raw),
                   **{r: reasons.get(r, 0) for r in ["duplicate", "outside_window", "removed_deleted", "bot", "empty_after_clean", "kept"]}}
            in_week = len(raw) - row["duplicate"] - row["outside_window"]
            row["removed_share_of_week"] = round(row["removed_deleted"] / in_week, 3) if in_week else None
            summary.append(row)
            print(f"    {kind}: raw {len(raw)} | dup {row['duplicate']} | outside {row['outside_window']} | "
                  f"removed {row['removed_deleted']} ({row['removed_share_of_week']}) | bot {row['bot']} | "
                  f"empty {row['empty_after_clean']} | KEPT {row['kept']}")

        df = pd.DataFrame(kept)
        if not df.empty:
            df = df.sort_values("created_utc")
            df.to_csv(out_path, index=False)
            days = df.groupby(["local_date", "kind"]).size().unstack(fill_value=0)
            for d, r in days.iterrows():
                per_day.append({"window": name, "local_date": d, **r.to_dict()})
            print(f"    per local day:\n" + "\n".join(f"      {d}  " + "  ".join(f"{k} {v}" for k, v in r.items()) for d, r in days.iterrows()))
            print(f"    -> {out_path}")

    if summary:
        pd.DataFrame(summary).to_csv(OUT / "summary.csv", index=False)
        pd.DataFrame(per_day).fillna(0).to_csv(OUT / "per_day.csv", index=False)
        with open(OUT / "bots_found.txt", "w") as f:
            for name, c in bots.items():
                f.write(f"{name}\n" + "".join(f"  {a}: {n}\n" for a, n in c.most_common()))
        print(f"\nsummary -> {OUT / 'summary.csv'}\nper day -> {OUT / 'per_day.csv'}\nbots    -> {OUT / 'bots_found.txt'}")


if __name__ == "__main__":
    sys.exit(main())
