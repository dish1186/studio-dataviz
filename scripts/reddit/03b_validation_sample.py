#!/usr/bin/env python3
"""
scripts/reddit/03b_validation_sample.py  (study version)

Exports a blind hand-coding sample to check the topic word list for one study.
Groups (strata) = city x week type (event / baseline / period) x flagged or not,
plus comments counted only through their thread, plus optional near-miss groups.

Run from the repo root:
    python3 scripts/reddit/03b_validation_sample.py --study studies/boston_heat_2026.json --n 25
    python3 scripts/reddit/03b_validation_sample.py --study ... --n 10 --exclude <earlier answer_key.csv>

Output:  data/processed/reddit/<study>/step03b_validation/<word list name>[_<tag>]/
           coding_sheet_dish.csv, coding_sheet_gina.csv  (same items, shuffled, no labels)
           answer_key.csv  (open only after coding)     CODING_GUIDE.txt

Rules: V1 strata as above, up to --n each (all if fewer). V2 near-miss: --near not-flagged
items from the event windows of the cities listed in the study's "near_miss_cities", containing
a hint word (study file "near_miss_hint"). V3 codes A (about the topic) / F (the separate measure,
e.g. fire, not the topic) / N (neither). V4 comments show their thread's post title. V5 shuffled,
seed 20261002. V10 --exclude skips items in earlier answer keys. V11 thread-only group.
V12 broad definition of topic talk.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study, topic_for   # noqa: E402

GUIDE = """CODING GUIDE  (topic: {topic}; word list {lex})

Code each row in the column "code" with ONE letter:

  A  = the text talks about the {topic}: its condition, how it feels, looks or smells,
       what people do because of it, symptoms the writer links to it.
       ANY cause, ANY place, ANY time, even in passing. (Decision V12: broad, like the
       Moore et al. weather-tweet definition, which counted any mention of weather.)
  F  = about the separate measure only ({seps}), not the {topic} itself.
  N  = neither (jokes that only borrow the words, sports teams, food, drugs, slang).

Rules
  - Code what THIS text is about. Use the thread title only to understand short replies.
  - If you cannot tell, write "?" in "unsure" and still pick your best letter.
  - Do not look at the other coder's sheet, the answer key, or the raw data.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--lexicon", help="word list whose step 03 results to sample (default: the study's)")
    ap.add_argument("--tag", default="", help="suffix for the output folder, e.g. v1check")
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--near", type=int, default=25)
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--seed", type=int, default=20261002)
    args = ap.parse_args()
    S = load_study(args.study)
    lex, S["topic"] = topic_for(S, args.lexicon)
    OUT = S["out"] / "step03b_validation" / (lex.stem + (f"_{args.tag}" if args.tag else ""))
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    flags = pd.read_csv(S["out"] / "step03_remarkability" / lex.stem / "items_flagged.csv", dtype={"id": str, "thread_id": str})
    text = pd.read_csv(S["out"] / "step02_clean" / "items.csv", dtype={"id": str}, usecols=["id", "window", "text_clean"])
    d = flags.merge(text, on=["id", "window"], how="left")
    d = d.drop_duplicates("id")          # an item in overlapping windows is coded once
    posts = d[d.kind == "post"].set_index("id")["text_clean"]
    d["thread_title"] = np.where(d.kind == "comment", d.thread_id.map(posts).fillna("(post not available)").str[:160], "")
    d["week"] = d.week_type
    seen = set()
    for k in args.exclude:
        seen |= set(pd.read_csv(k, dtype={"id": str}).id)
    if seen:
        d = d[~d.id.isin(seen)]
        print(f"  left out items already coded in {args.exclude}")

    picks = []
    for (city, week, flag), g in d.groupby(["city", "week", "topic"]):
        n = min(args.n, len(g))
        picks.append(g.sample(n=n, random_state=int(rng.integers(1e9))).assign(stratum=f"{city}|{week}|{'flagged' if flag else 'not_flagged'}"))
        print(f"  {city:14s} {week:8s} {'flagged' if flag else 'not flagged':12s} available {len(g):6d}  sampled {n}")
    for (city, week), g in d[d.topic_thread & ~d.topic].groupby(["city", "week"]):
        n = min(args.n, len(g))
        picks.append(g.sample(n=n, random_state=int(rng.integers(1e9))).assign(stratum=f"{city}|{week}|thread_only"))
        print(f"  {city:14s} {week:8s} thread only  available {len(g):6d}  sampled {n}")
    taken = set(pd.concat(picks).id) if picks else set()
    for city in S["near_miss_cities"]:
        near = d[(d.city == city) & (d.week == "event") & (~d.topic) & (~d.id.isin(taken))
                 & d.text_clean.str.contains(S["near_miss_hint"], case=False, regex=True, na=False)]
        nn = min(args.near, len(near))
        picks.append(near.sample(n=nn, random_state=int(rng.integers(1e9))).assign(stratum=f"{city}|event|near_miss"))
        print(f"  {city:14s} event    near-miss    available {len(near):6d}  sampled {nn}")

    sample = pd.concat(picks).sample(frac=1, random_state=args.seed).reset_index(drop=True)
    sample.insert(0, "item_no", range(1, len(sample) + 1))
    sheet = sample[["item_no", "kind", "thread_title", "text_clean"]].rename(columns={"text_clean": "text"}).assign(code="", unsure="", note="")
    for who in ["dish", "gina"]:
        sheet.to_csv(OUT / f"coding_sheet_{who}.csv", index=False, encoding="utf-8-sig")
    seps = [c for c in flags.columns if c not in {"window", "city", "group", "week_type", "kind", "id", "thread_id", "parent_id",
            "created_utc", "created_local", "local_date", "score", "num_comments", "n_chars", "topic", "topic_wide", "topic_thread", "terms"}]
    keep = ["item_no", "id", "window", "city", "week", "kind", "stratum", "topic", "topic_wide", "topic_thread"] + seps + ["terms"]
    sample[keep].to_csv(OUT / "answer_key.csv", index=False)
    (OUT / "CODING_GUIDE.txt").write_text(GUIDE.format(topic=S["topic"], lex=lex.name, seps=", ".join(seps) or "none"))
    print(f"\n{len(sample)} items -> {OUT}/coding_sheet_dish.csv and coding_sheet_gina.csv  (answer key: open after coding)")


if __name__ == "__main__":
    main()
