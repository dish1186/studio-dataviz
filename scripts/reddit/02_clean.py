#!/usr/bin/env python3
"""
scripts/reddit/02_clean.py  (study version)

Step 02: reads the raw Arctic Shift downloads for every city in a study file,
keeps each post or comment that falls inside one of the study's windows, and
writes one cleaned file for the whole study. Nothing is scored here.

Run from the repo root:
    python3 scripts/reddit/02_clean.py --study studies/eugene_bakersfield.json
    python3 scripts/reddit/02_clean.py --study studies/boston_heat_2026.json --force

Input:   the raw files listed under each city's "raw" in the study file, anywhere on disk
         (default: data/raw/reddit/arctic-shift/<city>_*.jsonl). Formats: .jsonl/.ndjson (Arctic
         Shift download tool), .json lists (Arctic Shift web search), .zst dumps (needs zstandard).
         Posts and comments can be in the same or separate files; downloads can overlap
         (duplicates are dropped by id).
Output:  data/processed/reddit/<study>/step02_clean/
           items.csv          one row per kept post or comment per window (text, no usernames)
           removed.csv        removed/deleted comments: window, id, thread id only (no text),
                              used by step 03's removal check
           summary.csv        per window and kind: raw rows in window, removed, bot, empty, kept
           per_day.csv        kept rows per local day
           bots_found.txt     bot accounts dropped, for audit

Rules (unchanged from the Eugene/Bakersfield run; log as decisions):
    C1  Window = local midnight on its start date to local midnight after its last day,
        in the city's own time zone (from the study file). Default 7 days.
    C2  Removed or deleted = _meta.removal_type set, _meta.was_deleted_later true,
        removed_by_category set, author "[deleted]", or text "[removed]"/"[deleted]".
    C3  Bots = the explicit list below, "<sub>-ModTeam" accounts, and comments
        distinguished as "moderator".
    C4  Usernames are not carried over; "u/name" in text becomes "u/[user]".
    C5  Text cleaning: HTML entities decoded; quoted lines (">") removed; markdown links kept
        as text; URLs removed; markdown symbols removed; whitespace collapsed.
    C6  A post's text = title + body.
    C7  Comments are judged on their own time and status, whatever happened to their post.
    C8  thread_id = the post's id, or the parent post id from link_id for comments.
    C9  (study version) A post or comment inside several overlapping windows is kept once
        per window. A file's kind is read from each row (rows with a title are posts).
"""

import argparse
import csv
import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study, raw_files, WindowIndex   # noqa: E402

GONE_TEXT = {"[removed]", "[deleted]"}
BOTS = {"automoderator", "sneakpeekbot", "haikusbot", "sokkahaikubot", "amputatorbot", "vettedbot",
        "wikisummarizerbot", "remindmebot", "savevideo", "savevideobot", "repostsleuthbot"}
MODTEAM = re.compile(r"-modteam$", re.IGNORECASE)
URL = re.compile(r"https?://\S+|www\.\S+")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
USER = re.compile(r"(?<![\w/])/?u/[A-Za-z0-9_-]+")
MD_SYMBOLS = re.compile(r"[*_~`#]+")
SPACES = re.compile(r"\s+")
COLS = ["window", "city", "group", "week_type", "kind", "id", "thread_id", "parent_id", "created_utc",
        "created_local", "local_date", "score", "num_comments", "text_clean", "n_chars"]
csv.field_size_limit(10**9)


def is_removed(x, kind):
    meta = x.get("_meta") or {}
    body = (x.get("selftext") if kind == "post" else x.get("body")) or ""
    return bool(meta.get("removal_type") or meta.get("was_deleted_later") or x.get("removed_by_category")
                or x.get("author") == "[deleted]" or body.strip() in GONE_TEXT)


def is_bot(x, kind):
    a = x.get("author") or ""
    return a.lower() in BOTS or bool(MODTEAM.search(a)) or (kind == "comment" and x.get("distinguished") == "moderator")


def clean(text):
    t = html.unescape(text or "")
    t = "\n".join(line for line in t.split("\n") if not line.lstrip().startswith(">"))
    t = MD_LINK.sub(r"\1", t)
    t = URL.sub(" ", t)
    t = USER.sub("u/[user]", t)
    t = MD_SYMBOLS.sub(" ", t)
    t = t.replace("\u200b", " ")
    return SPACES.sub(" ", t).strip()


def iter_rows(path):
    """Yields one dict per post/comment from .jsonl / .ndjson (one object per line), a .json file
    holding a list (Arctic Shift web search download), or a .zst dump (Arctic Shift / Academic
    Torrents; needs `pip3 install zstandard`). Lines that cannot be read are counted, not fatal."""
    p = str(path)
    if p.endswith(".zst"):
        import io
        import zstandard
        with open(p, "rb") as fh:
            stream = io.TextIOWrapper(zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(fh), encoding="utf-8")
            for line in stream:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        yield None
        return
    with open(p, encoding="utf-8") as fh:
        first = fh.read(1)
        while first and first.isspace():
            first = fh.read(1)
        fh.seek(0)
        if first == "[":
            data = json.load(fh)
            for x in (data.get("data", data) if isinstance(data, dict) else data):
                yield x
            return
        for line in fh:
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    yield None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True, help="study file, e.g. studies/eugene_bakersfield.json")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = ap.parse_args()
    S = load_study(args.study)
    OUT = S["out"] / "step02_clean"
    if (OUT / "items.csv").exists() and not args.force:
        raise SystemExit(f"{OUT/'items.csv'} exists; use --force to overwrite")
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"study {S['name']}: {len(S['windows'])} windows in {len(S['cities'])} cities")

    stats = defaultdict(Counter)          # (window, kind) -> reasons
    bots = defaultdict(Counter)
    f_items = open(OUT / "items.csv", "w", newline="", encoding="utf-8")
    f_rem = open(OUT / "removed.csv", "w", newline="", encoding="utf-8")
    wi, wr = csv.writer(f_items), csv.writer(f_rem)
    wi.writerow(COLS)
    wr.writerow(["window", "id", "thread_id"])

    for city, info in S["cities"].items():
        cw = [w for w in S["windows"] if w["city"] == city]
        if not cw:
            continue
        idx = WindowIndex(cw)
        files = raw_files(S, city)
        print(f"\n{city}: r/{info['subreddit']}, {len(cw)} windows, {len(files)} raw files")
        if not files:
            print("    MISSING: no raw files matched", info.get("raw"))
            continue
        seen, n_dup, n_out, n_bad, tmin, tmax = set(), 0, 0, 0, None, None
        subs = Counter()
        for path in files:
            n_file = 0
            for x in iter_rows(path):
                    if x is None:
                        n_bad += 1
                        continue
                    n_file += 1
                    if x.get("id") in seen:
                        n_dup += 1
                        continue
                    seen.add(x.get("id"))
                    t = int(float(x["created_utc"]))
                    tmin, tmax = (t if tmin is None else min(tmin, t)), (t if tmax is None else max(tmax, t))
                    subs[str(x.get("subreddit", "")).lower()] += 1
                    hits = idx.find(t)
                    if not hits:
                        n_out += 1
                        continue
                    kind = "post" if "title" in x else "comment"
                    removed, bot = is_removed(x, kind), is_bot(x, kind)
                    if kind == "post":
                        text, thread, parent = clean((x.get("title") or "") + "\n" + (x.get("selftext") or "")), x["id"], ""
                    else:
                        text, thread, parent = clean(x.get("body")), (x.get("link_id") or "").replace("t3_", ""), x.get("parent_id") or ""
                    for w in hits:
                        st = stats[(w["name"], kind)]
                        st["raw_in_window"] += 1
                        if removed:
                            st["removed_deleted"] += 1
                            if kind == "comment":
                                wr.writerow([w["name"], x["id"], thread])
                            continue
                        if bot:
                            st["bot"] += 1
                            bots[w["name"]][x.get("author") or "(none)"] += 1
                            continue
                        if not text:
                            st["empty_after_clean"] += 1
                            continue
                        local = datetime.fromtimestamp(t, w["tz"])
                        wi.writerow([w["name"], city, w["group"], w["type"], kind, x["id"], thread, parent, t,
                                     local.strftime("%Y-%m-%d %H:%M"), local.strftime("%Y-%m-%d"), x.get("score"),
                                     x.get("num_comments") if kind == "post" else "", text, len(text)])
                        st["kept"] += 1
            print(f"    {path}: {n_file} rows")
        print(f"    raw rows {len(seen) + n_dup}: duplicates {n_dup}, outside every window {n_out}, unreadable {n_bad}")
        if set(subs) - {info["subreddit"].lower()}:
            print(f"    WARNING: unexpected subreddits {dict(subs)}")
        if tmin is not None:
            first, last = min(w["t0"] for w in cw), max(w["t1"] for w in cw)
            if tmin > first + 3600 or tmax < last - 3600:
                print(f"    WARNING: raw data covers {datetime.fromtimestamp(tmin, timezone.utc):%Y-%m-%d %H:%M} -> "
                      f"{datetime.fromtimestamp(tmax, timezone.utc):%Y-%m-%d %H:%M} UTC, but the windows run "
                      f"{datetime.fromtimestamp(first, timezone.utc):%Y-%m-%d} -> {datetime.fromtimestamp(last, timezone.utc):%Y-%m-%d}; "
                      f"some windows may be incomplete")
    f_items.close()
    f_rem.close()

    rows = []
    for w in S["windows"]:
        for kind in ["post", "comment"]:
            st = stats[(w["name"], kind)]
            inw = st["raw_in_window"]
            rows.append({"window": w["name"], "city": w["city"], "group": w["group"], "week_type": w["type"],
                         "start": w["start"].isoformat(), "end": w["end"].isoformat(), "kind": kind,
                         "raw_in_window": inw, "removed_deleted": st["removed_deleted"], "bot": st["bot"],
                         "empty_after_clean": st["empty_after_clean"], "kept": st["kept"],
                         "removed_share": round(st["removed_deleted"] / inw, 3) if inw else None})
    summ = pd.DataFrame(rows)
    summ.to_csv(OUT / "summary.csv", index=False)
    items = pd.read_csv(OUT / "items.csv", usecols=["window", "local_date", "kind"])
    pd_ = items.groupby(["window", "local_date", "kind"]).size().unstack(fill_value=0).reset_index()
    pd_.to_csv(OUT / "per_day.csv", index=False)
    with open(OUT / "bots_found.txt", "w") as f:
        for name, c in bots.items():
            f.write(f"{name}\n" + "".join(f"  {a}: {n}\n" for a, n in c.most_common()))

    show = summ.pivot_table(index="window", columns="kind", values=["kept", "removed_share"], sort=False)
    print("\nPER WINDOW (kept rows; share removed)")
    many = len(S["windows"]) > 30
    for w in (S["windows"][:10] + [None] + S["windows"][-5:]) if many else S["windows"]:
        if w is None:
            print("    ...")
            continue
        r = show.loc[w["name"]]
        print(f"  {w['name']:32s} {w['type']:8s} {w['start']}..{w['end']}  posts {int(r[('kept','post')]):5d}  "
              f"comments {int(r[('kept','comment')]):6d}  removed posts {r[('removed_share','post')]}  comments {r[('removed_share','comment')]}")
    empty = summ.groupby("window").kept.sum()
    if (empty == 0).any():
        print(f"\nWARNING: {int((empty == 0).sum())} windows have no kept items: {list(empty[empty == 0].index)[:10]}")
    print(f"\noutputs -> {OUT}/")


if __name__ == "__main__":
    main()
