#!/usr/bin/env python3
"""
scripts/reddit/spectrum_01_air_items.py

Alarm -> Normalizing spectrum, Step 1: pick out air talk in each event week, one row per post or comment.
Brief: docs/claude_handoff-air-spectrum-labeling.md (Dish, 2026-10-04). Labeling (Step 2) happens later, by hand.

Rules (Claude's drafts, flagged for Dish):
  S1  Unit = one post or one comment. Item ID = `id`; thread ID = the post's `id`, or `link_id` minus "t3_".
  S2  Air talk = the item's OWN cleaned text matches lexicon_air_v1 include or candidate terms, after the
      excludes are blanked (study.flag_topic). Being in an air thread does not count. "fire"-type terms
      (wildfire, fire, evacuation) are a separate measure in v1 and do not count on their own.
  S3  Source = Gina's event-week pulls with usernames already stripped (option a, Dish 2026-10-04).
      Window = the file as pulled: Monday 00:00 to Sunday 23:59 UTC, not local time.
  S4  Cleaning reuses 02_clean: removed/deleted (C2) and empty-after-cleaning items are dropped; bots =
      moderator-distinguished or "I am a bot" text (as in analysis_01; usernames are already gone).
      Text cleaning C5 (quoted lines dropped, URLs removed, "u/name" -> "u/[user]"). Post text = title + body.
  S5  hover_text = the sentences that match an air term, plus one sentence either side; gaps shown as " … ".
      If no single sentence matches (a phrase split across sentences), the whole text is used.
  S6  Comparison weeks (Forensics Appendix only, not part of the 9): Eugene 2026-08-03 and Bakersfield
      2024-12-02 from step02_clean, the same cleaned local-time items the old passage labels came from.

Input (read only):
  data/processed/reddit/event_weeks_no_usernames/r_<Sub>_{posts,comments}.jsonl
  data/processed/reddit/step02_clean/{eugene_event_2026-08-03,bakersfield_event_2024-12-02}.csv
  data/lexicons/lexicon_air_v1.csv
Output: data/processed/reddit/spectrum_01_air_items/
  <city>_<weekstart>_air_items.csv   one row per air-talk item (no author field)
  summary.csv                        one row per week (rewritten from all week files present)
Run from the repo root:
  python3 scripts/reddit/spectrum_01_air_items.py                 all weeks
  python3 scripts/reddit/spectrum_01_air_items.py --city detroit  one week (others' files untouched)
"""

import argparse
import csv
import importlib.util
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from study import load_topic_lexicon, flag_topic   # noqa: E402
_spec = importlib.util.spec_from_file_location("clean02", HERE / "02_clean.py")
clean02 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(clean02)

SRC = Path("data/processed/reddit/event_weeks_no_usernames")
OLD = Path("data/processed/reddit/step02_clean")
LEX = Path("data/lexicons/lexicon_air_v1.csv")
OUT = Path("data/processed/reddit/spectrum_01_air_items")
BOT_TEXT = "i am a bot"
SENT = re.compile(r"(?<=[.!?…])\s+")
csv.field_size_limit(10**9)

# city -> (subreddit file stem, event week start); the 9 cities of the PM2.5 experiment (Yakima dropped there)
WEEKS = {"eugene": ("Eugene", "2020-09-07"), "bakersfield": ("bakersfield", "2024-12-02"),
         "fresno": ("fresno", "2020-08-17"), "sanjose": ("SanJose", "2020-08-17"),
         "fairbanks": ("Fairbanks", "2022-06-27"), "indianapolis": ("indianapolis", "2023-06-26"),
         "seattle": ("Seattle", "2020-09-07"), "detroit": ("Detroit", "2026-07-13"),
         "pittsburgh": ("pittsburgh", "2026-07-13")}
COMPARE = {"eugene_cmp2026": ("eugene", "eugene_event_2026-08-03"),
           "bakersfield_cmp2024": ("bakersfield", "bakersfield_event_2024-12-02")}
COLS = ["item_id", "thread_id", "kind", "city", "week", "set", "created_utc", "include_hit", "matched_terms",
        "hover_text", "full_text", "n_chars"]
SUM_COLS = ["city", "week", "set", "source", "rows_read", "removed_deleted", "bots", "empty", "total_items",
            "air_items", "air_items_include_only", "air_share_pct", "threads_with_air", "biggest_thread",
            "biggest_thread_air_items", "biggest_thread_share_pct", "over_500", "skew_over_30pct"]


def hover(text, lex):
    sents = [s for s in SENT.split(text) if s.strip()]
    hits = [i for i, s in enumerate(sents) if flag_topic(s, lex)[1]]
    if not hits:
        return text
    keep = sorted({j for i in hits for j in (i - 1, i, i + 1) if 0 <= j < len(sents)})
    out, prev = [], None
    for j in keep:
        if prev is not None and j != prev + 1:
            out.append("…")
        out.append(sents[j]); prev = j
    if keep[0] > 0:
        out.insert(0, "…")
    if keep[-1] < len(sents) - 1:
        out.append("…")
    return " ".join(out)


def items_new(stem):
    """Yields (kind, id, thread_id, created_utc, text) or a drop reason, from Gina's stripped files."""
    for kind, fname in (("post", f"r_{stem}_posts.jsonl"), ("comment", f"r_{stem}_comments.jsonl")):
        for x in clean02.iter_rows(SRC / fname):
            if x is None:
                yield "unreadable"; continue
            raw = ((x.get("title") or "") + "\n" + (x.get("selftext") or "")) if kind == "post" else (x.get("body") or "")
            if clean02.is_removed(x, kind):
                yield "removed"; continue
            if x.get("distinguished") == "moderator" or BOT_TEXT in raw.lower():
                yield "bot"; continue
            text = clean02.clean(raw)
            if not text:
                yield "empty"; continue
            th = x["id"] if kind == "post" else str(x.get("link_id", "")).split("_", 1)[-1]
            yield (kind, x["id"], th, int(float(x["created_utc"])), text)


def items_old(window):
    for r in csv.DictReader(open(OLD / f"{window}.csv", encoding="utf-8")):
        yield (r["kind"], r["id"], r["thread_id"], int(float(r["created_utc"])), r["text_clean"])


def run_week(key, lex):
    if key in WEEKS:
        stem, week = WEEKS[key]; city, setname, source = key, "event_9", f"{SRC}/r_{stem}_*.jsonl (UTC week)"
        rows = items_new(stem)
    else:
        city, window = COMPARE[key]; week = window.rsplit("_", 1)[-1]
        setname, source = "comparison", f"{OLD}/{window}.csv (local week, already cleaned)"
        rows = items_old(window)
    drops, kept, air, thr = Counter(), 0, [], Counter()
    for r in rows:
        if isinstance(r, str):
            drops[r] += 1; continue
        kept += 1
        kind, iid, th, ts, text = r
        inc, any_hit, _, terms = flag_topic(text, lex)
        if not any_hit:
            continue
        thr[th] += 1
        air.append({"item_id": iid, "thread_id": th, "kind": kind, "city": city, "week": week, "set": setname,
                    "created_utc": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "include_hit": int(inc), "matched_terms": "; ".join(t for t in terms if not t.endswith("^")),
                    "hover_text": hover(text, lex), "full_text": text, "n_chars": len(text)})
    air.sort(key=lambda d: (d["thread_id"], d["created_utc"]))
    name = f"{city}_{week}" + ("_comparison" if setname == "comparison" else "")
    with open(OUT / f"{name}_air_items.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(air)
    big, bign = (thr.most_common(1)[0] if thr else ("", 0))
    n = len(air)
    return {"city": city, "week": week, "set": setname, "source": source,
            "rows_read": kept + sum(drops.values()), "removed_deleted": drops["removed"], "bots": drops["bot"],
            "empty": drops["empty"] + drops["unreadable"], "total_items": kept, "air_items": n,
            "air_items_include_only": sum(d["include_hit"] for d in air),
            "air_share_pct": round(100 * n / kept, 2) if kept else 0, "threads_with_air": len(thr),
            "biggest_thread": big, "biggest_thread_air_items": bign,
            "biggest_thread_share_pct": round(100 * bign / n, 1) if n else 0,
            "over_500": int(n > 500), "skew_over_30pct": int(n > 0 and bign / n > 0.30)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", help="one key: " + ", ".join(list(WEEKS) + list(COMPARE)))
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    lex = load_topic_lexicon(LEX)
    keys = [args.city] if args.city else list(WEEKS) + list(COMPARE)
    sumf = OUT / "summary.csv"
    rows = {(r["city"], r["week"], r["set"]): r for r in csv.DictReader(open(sumf))} if sumf.exists() else {}
    for k in keys:
        if k not in WEEKS and k not in COMPARE:
            raise SystemExit(f"unknown key {k}")
        s = run_week(k, lex)
        rows[(s["city"], s["week"], s["set"])] = s
        print(f"{s['city']:<12} {s['week']} {s['set']:<10} items {s['total_items']:>6}  air {s['air_items']:>5} "
              f"({s['air_share_pct']}%)  biggest thread {s['biggest_thread_share_pct']}%"
              + ("  >500" if s["over_500"] else "") + ("  SKEW" if s["skew_over_30pct"] else ""))
    with open(sumf, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SUM_COLS); w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: (r["set"] != "event_9", r["city"])))


if __name__ == "__main__":
    main()
