#!/usr/bin/env python3
"""
scripts/reddit/03b_validation_sample.py

Exports a sample of posts and comments for Dish and Gina to hand-code, so the
air-talk word list (lexicon v0) can be checked before it is frozen. Follows the
logic of Moore et al. (2019, SI Table S1): sample separately within each group
being compared, so we can see whether the classifier makes MORE mistakes in one
city or week type than another (that would bias the comparison; even mistakes
only add noise).

Run from the repo root:
    python3 scripts/reddit/03b_validation_sample.py

Input:   data/processed/reddit/step02_clean/<window>.csv
         data/processed/reddit/step03_remarkability/items_flagged.csv
Output:  data/processed/reddit/step03b_validation/
           coding_sheet_dish.csv    items to code, shuffled, NO classifier labels
           coding_sheet_gina.csv    same items, same order
           answer_key.csv           item_no -> id, window, stratum, classifier flag, matched terms
                                    (do not open until both sheets are coded)
           CODING_GUIDE.txt         the rules for coding

Sample design (Claude defaults, log as decisions):
    V1  Strata = city x week type (event; baselines pooled) x classifier flag (air / not air).
        8 strata, 25 items each, or every item if a stratum has fewer than 25
        (Bakersfield's flagged strata are small, so all of them are checked).
    V2  Near-miss sample: 25 extra NOT-flagged items from Bakersfield's event week that
        contain a broad hint word (air, outside, breathe, burn, haze, fog, cough, visib,
        allerg, asthma, pollut, inversion, valley). This hunts for air talk the word list
        missed in the city where missing it would matter most. It is reported separately
        and not used to estimate overall error rates.
    V3  Three codes: A = about the air (smoke, haze, air quality, breathing, purifiers,
        masks for smoke); F = about fire but not the air (evacuations, fire news);
        N = neither. Precision is reported two ways: A only, and A or F.
    V4  For comments, the title of the thread's post is shown as context when the post
        was kept, because people read comments in their thread.
    V10 (added for the v1 check) --exclude leaves out every item in earlier answer keys, so
        a fresh sample never re-tests items that were used to revise the word list.
    V11 (added for the v1 check) when the flags include the thread-context measure, one
        more group per city and week: comments counted ONLY because of their thread
        (air_thread but not air), to test whether the thread rule is accurate.
    V5  Seed 20261002. The order is shuffled so coders cannot tell which stratum an
        item came from.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CLEAN = Path("data/processed/reddit/step02_clean")
N_PER, N_NEAR, SEED = 25, 25, 20261002
HINT = r"\b(?:air|outside|breath\w*|burn\w*|haz\w*|fog\w*|cough\w*|visib\w*|allerg\w*|asthma\w*|pollut\w*|inversion\w*|valley)\b"

GUIDE = """CODING GUIDE  (air-talk validation, lexicon v0)

Code each row in the column "code" with ONE letter:

  A  = the text talks about the condition of the AIR: smoke, haze, smog,
       air quality, AQI, breathing, air purifiers or filters, masks worn because
       of smoke or bad air, how the sky or air looks or smells, symptoms the
       writer links to the air.
       ANY cause (wildfire, inversion, traffic, trucks, field burning), ANY place,
       ANY time, and even in passing ("great view when the air quality allows it").
       (Rule clarified 2026-09-30 for the v1 check, decision V12: broad, like the
        Moore et al. weather-tweet definition, which counted any mention of weather.)
  F  = about FIRE but not the air: fire news, evacuations, fire locations,
       firefighters, without saying anything about the air or smoke.
  N  = neither (everything else, including jokes that only borrow the words,
       cannabis or cigarette smoke, food, beer, sports slang).

Rules
  - Code what THIS text is about. Use the thread title only to understand
    short replies ("same here", "it's awful today") - if the thread is about
    the smoke and the reply clearly continues that topic, code A.
  - If you genuinely cannot tell, write "?" in "unsure" and still choose your
    best letter.
  - Do not look at the other coder's sheet, the answer key, or the raw data.
  - Add a short note if a word or phrase fooled the list (e.g. "smoke = vape").
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags", default="data/processed/reddit/step03_remarkability/items_flagged.csv",
                    help="items_flagged.csv from step 03 (for v1: .../step03_remarkability/lexicon_air_v1/items_flagged.csv)")
    ap.add_argument("--out", default="data/processed/reddit/step03b_validation")
    ap.add_argument("--n", type=int, default=N_PER, help="items per group")
    ap.add_argument("--near", type=int, default=N_NEAR, help="Bakersfield near-miss items")
    ap.add_argument("--exclude", nargs="*", default=[], help="answer_key.csv files whose items must NOT be drawn again")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    flags = pd.read_csv(args.flags, dtype={"id": str, "thread_id": str})
    text = pd.concat([pd.read_csv(p, dtype={"id": str, "thread_id": str}, usecols=["id", "window", "text_clean"])
                      for p in sorted(CLEAN.glob("*.csv")) if p.name not in {"summary.csv", "per_day.csv"}])
    d = flags.merge(text, on=["id", "window"], how="left")
    posts = d[d.kind == "post"].drop_duplicates(["window", "id"]).set_index(["window", "id"])["text_clean"]
    keys = pd.MultiIndex.from_arrays([d.window, d.thread_id])
    titles = pd.Series(posts.reindex(keys).to_numpy(), index=d.index).fillna("(post not available)").str[:160]
    d["thread_title"] = np.where(d.kind == "comment", titles, "")
    d["week"] = np.where(d.week_type == "event", "event", "baseline")
    seen = set()
    for k in args.exclude:   # V10: a fresh check sample never reuses items already coded
        kk = pd.read_csv(k, dtype={"id": str})
        seen |= set(zip(kk.window, kk.id))
    if seen:
        before = len(d)
        d = d[~pd.Series(list(zip(d.window, d.id)), index=d.index).isin(seen)]
        print(f"  left out {before - len(d)} items already coded in {args.exclude}")

    picks = []
    for (city, week, air), g in d.groupby(["city", "week", "air"]):
        n = min(args.n, len(g))
        s = g.sample(n=n, random_state=int(rng.integers(1e9)))
        s = s.assign(stratum=f"{city}|{week}|{'flagged' if air else 'not_flagged'}")
        picks.append(s)
        print(f"  {city:12s} {week:8s} {'flagged' if air else 'not flagged':12s} available {len(g):5d}  sampled {n}")

    if "air_thread" in d.columns:   # V11: check the thread-context measure on its own
        for (city, week), g in d[d.air_thread & ~d.air].groupby(["city", "week"]):
            n = min(args.n, len(g))
            picks.append(g.sample(n=n, random_state=int(rng.integers(1e9))).assign(stratum=f"{city}|{week}|thread_only"))
            print(f"  {city:12s} {week:8s} thread only  available {len(g):5d}  sampled {n}")

    taken = set(pd.concat(picks).id)
    near = d[(d.city == "Bakersfield") & (d.week == "event") & (~d.air) & (~d.id.isin(taken))
             & d.text_clean.str.contains(HINT, case=False, regex=True, na=False)]
    nn = min(args.near, len(near))
    picks.append(near.sample(n=nn, random_state=int(rng.integers(1e9))).assign(stratum="Bakersfield|event|near_miss"))
    print(f"  Bakersfield  event    near-miss    available {len(near):5d}  sampled {nn}")

    sample = pd.concat(picks).sample(frac=1, random_state=args.seed).reset_index(drop=True)
    sample.insert(0, "item_no", range(1, len(sample) + 1))

    sheet = sample[["item_no", "kind", "thread_title", "text_clean"]].rename(columns={"text_clean": "text"})
    sheet = sheet.assign(code="", unsure="", note="")
    for who in ["dish", "gina"]:
        sheet.to_csv(OUT / f"coding_sheet_{who}.csv", index=False, encoding="utf-8-sig")
    cols = [c for c in ["item_no", "id", "window", "city", "week", "kind", "stratum", "air", "air_wide", "air_thread", "fire", "terms"] if c in sample.columns]
    sample[cols].to_csv(
        OUT / "answer_key.csv", index=False)
    (OUT / "CODING_GUIDE.txt").write_text(GUIDE)
    print(f"\n{len(sample)} items -> {OUT}/coding_sheet_dish.csv and coding_sheet_gina.csv")
    print(f"answer key -> {OUT}/answer_key.csv  (don't open until both sheets are coded)")


if __name__ == "__main__":
    main()
