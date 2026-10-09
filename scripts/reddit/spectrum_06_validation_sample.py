#!/usr/bin/env python3
"""
scripts/reddit/spectrum_06_validation_sample.py

Air-spectrum human validation, Step 1: draw the blind coding sample for Dish and Gina.

Rules (Dish, 2026-10-04):
  V1  Source = Claude's draft labels for the 9 event weeks (spectrum_03_outputs/*_claude_draft.csv, not the
      comparison weeks). For Eugene, Seattle and Pittsburgh these are the stratified 400 Claude read.
  V2  Simple random sample of 50 comments per city, every band included (X too), so city shares and
      Claude's accuracy can both be estimated. A city with fewer than 50 comments is taken whole (Fairbanks 36).
  V3  15 practice cards for calibration, drawn from comments NOT in the sample, 3 per Claude band where possible.
  V4  Seed 20261005. Each coder sees the sample in their own random order (shuffled in the page).
  V5  The coding file (cards.json) has no Claude labels. Claude's labels go to claude.json, which the page loads
      only on the results view. Practice cards (practice.json) carry Claude's label for discussion.
  V6  full_text is cut to 1,500 characters for the card; no usernames exist in the source files.

Output: viz/air-validation/cards.json, claude.json, practice.json, sample_summary.csv
Run from the repo root: python3 scripts/reddit/spectrum_06_validation_sample.py
"""

import glob
import json
from pathlib import Path

import pandas as pd

SRC = Path("data/processed/reddit/spectrum_03_outputs")
OUT = Path("viz/air-validation")
SEED, PER_CITY, PRACTICE_PER_BAND, CUT = 20261005, 50, 3, 1500
NAMES = {"bakersfield": "Bakersfield", "detroit": "Detroit", "eugene": "Eugene", "fairbanks": "Fairbanks", "fresno": "Fresno",
         "indianapolis": "Indianapolis", "pittsburgh": "Pittsburgh", "sanjose": "San Jose", "seattle": "Seattle"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = [f for f in sorted(glob.glob(str(SRC / "spectrum_labels_*_claude_draft.csv"))) if "comparison" not in f]
    d = pd.concat([pd.read_csv(f, dtype={"item_id": str, "thread_id": str}) for f in files], ignore_index=True)
    assert d.item_id.is_unique

    sample = pd.concat([g if len(g) <= PER_CITY else g.sample(PER_CITY, random_state=SEED)
                        for _, g in d.groupby("city", sort=True)])
    rest = d[~d.item_id.isin(sample.item_id)]
    practice = pd.concat([g.sample(min(PRACTICE_PER_BAND, len(g)), random_state=SEED) for _, g in rest.groupby("band", sort=True)])

    def card(r):
        full = str(r.full_text)
        return {"id": r.item_id, "city": r.city, "cityName": NAMES[r.city], "week": r.week,
                "hover": str(r.hover_text), "full": full[:CUT] + ("…" if len(full) > CUT else "")}

    (OUT / "cards.json").write_text(json.dumps([card(r) for r in sample.itertuples()], ensure_ascii=False))
    (OUT / "claude.json").write_text(json.dumps({r.item_id: {"band": r.band, "unsure": r.claude_unsure == "yes"}
                                                 for r in sample.itertuples()}))
    (OUT / "practice.json").write_text(json.dumps([{**card(r), "claude": r.band, "reason": str(r.reason)}
                                                   for r in practice.sample(frac=1, random_state=SEED).itertuples()],
                                                  ensure_ascii=False))
    summ = (sample.groupby("city").agg(sampled=("item_id", "size"))
                  .join(d.groupby("city").agg(labelled=("item_id", "size")))
                  .join(sample.pivot_table(index="city", columns="band", values="item_id", aggfunc="count", fill_value=0)))
    summ.to_csv(OUT / "sample_summary.csv")
    print(summ.to_string())
    print(f"\nsample {len(sample)} cards · practice {len(practice)} cards -> {OUT}/")


if __name__ == "__main__":
    main()
