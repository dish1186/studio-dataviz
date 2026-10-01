#!/usr/bin/env python3
"""
scripts/reddit/03_remarkability.py

Step 03 of the Reddit case study. Moore et al. (2019)'s first measure,
"remarkability": how much of a city's conversation is about the air in a
week, compared with ordinary weeks in the same city.

Run from the repo root:
    python3 scripts/reddit/03_remarkability.py

Input:   data/processed/reddit/step02_clean/<window>.csv
         data/lexicons/lexicon_air_v1.csv        (the word list; edit this, not the code;
                                                  pick another with --lexicon PATH)
         data/raw/reddit/arctic-shift/<window>_comments.jsonl   (only for the removal check)
Output:  data/processed/reddit/step03_remarkability/<lexicon name>/
           items_flagged.csv      every kept post/comment: air flag, wide flag, matched terms (no text)
           share_by_window.csv    air-talk share per window, with 95% ranges
           lift.csv               event share / mean baseline share, per city, with 95% ranges
           term_counts.csv        how many items each term matched, per window (for auditing the lexicon)
           daily_share.csv        air-talk share per local day
           removal_check.csv      removal rate of comments in air threads vs other threads

How an item is flagged:
    1. Every "exclude" pattern is blanked out of the text first (e.g. "smokehouse",
       "hazy IPA", "smoke weed"), so it cannot trigger a match.
    2. air      = at least one "include" pattern matches          (main measure)
    3. air_wide = at least one "include" or "candidate" matches   (sensitivity measure)

Claude defaults (log these as decisions, change any you disagree with):
    R1  Main measure = air share of all kept posts + comments together (each item
        counts once, as in Moore et al. where each tweet counted once).
        Posts-only and comments-only shares are reported alongside.
    R2  Baseline share for a city = mean of its two baseline weeks' shares.
        Lift = event share / baseline share.
    R3  95% ranges from a bootstrap that resamples whole threads (a post plus its
        comments) with replacement, 2,000 draws, seed 20261001. Each window is
        resampled independently. Thread-level resampling mirrors Moore et al.
        clustering errors by state: comments in one thread are not independent.
    R4  Removal check, using only the removal flags and thread ids, never the text of
        removed items: a thread counts as an "air thread" if its post was kept and
        flagged air. Compares the share of comments removed in air threads vs other
        threads, per window.
    R6  Added after the first run (2026-09-30): the difference in share (event minus
        baseline, percentage points) with its own 95% range. The ratio's range is
        unstable when bootstrap draws give a baseline of zero (Bakersfield, few air
        items); those draws are left out of the ratio's range and their share is reported.
    R7  Added with lexicon v1 (2026-09-30): "fire" words are a separate measure, never
        counted as air talk (validation showed they were mostly fire news). New measure
        air_thread: an item counts if it is air talk itself, or is a comment in a thread
        whose opening post is air talk (validation showed many replies are about the air
        without using any listed word). Results are written to a subfolder named after
        the lexicon file, so v0 and v1 results sit side by side.
    R5  Lexicon v0 is a draft by Claude. It must be validated by hand (next step)
        and frozen before any result is reported.
"""

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

CLEAN = Path("data/processed/reddit/step02_clean")
RAW = Path("data/raw/reddit/arctic-shift")
LEX_DEFAULT = "data/lexicons/lexicon_air_v1.csv"
OUT_ROOT = Path("data/processed/reddit/step03_remarkability")   # results go in a subfolder named after the lexicon file
B, SEED = 2000, 20261001   # R3

WINDOWS = [  # same names and order as 02_clean.py
    ("eugene_event_2026-08-03",      "Eugene",      "event"),
    ("eugene_base_2024-08-05",       "Eugene",      "baseline"),
    ("eugene_base_2025-08-04",       "Eugene",      "baseline"),
    ("bakersfield_event_2024-12-02", "Bakersfield", "event"),
    ("bakersfield_base_2023-12-04",  "Bakersfield", "baseline"),
    ("bakersfield_base_2025-12-01",  "Bakersfield", "baseline"),
]


def load_lexicon(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    lex = {"include": [], "candidate": [], "exclude": [], "fire": []}
    for r in rows:
        lex[r["type"].strip()].append((r["term"], re.compile(r["pattern"], re.IGNORECASE)))
    print(f"lexicon {path}: " + ", ".join(f"{k} {len(v)}" for k, v in lex.items()))
    return lex


def flag(text, lex):
    t = text or ""
    for _, p in lex["exclude"]:
        t = p.sub(" ", t)
    inc = [term for term, p in lex["include"] if p.search(t)]
    cand = [term for term, p in lex["candidate"] if p.search(t)]
    fire = [term for term, p in lex["fire"] if p.search(t)]
    return bool(inc), bool(inc or cand), bool(fire), inc + [c + "*" for c in cand] + [f + "^" for f in fire]


def boot_share(df, col, rng):
    """Thread-level bootstrap of the share of items with df[col] True."""
    g = df.groupby("thread_id")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = rng.integers(0, len(g), size=(B, len(g)))
    return s[idx].sum(1) / n[idx].sum(1)


def is_removed(x):  # same rule as 02_clean.py C2, comments only
    meta = x.get("_meta") or {}
    return bool(meta.get("removal_type") or meta.get("was_deleted_later") or x.get("removed_by_category")
                or x.get("author") == "[deleted]" or (x.get("body") or "").strip() in {"[removed]", "[deleted]"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexicon", default=LEX_DEFAULT, help="path to the lexicon CSV")
    args = ap.parse_args()
    LEX = Path(args.lexicon)
    OUT = OUT_ROOT / LEX.stem
    OUT.mkdir(parents=True, exist_ok=True)
    lex = load_lexicon(LEX)
    rng = np.random.default_rng(SEED)

    frames = []
    for name, city, wtype in WINDOWS:
        d = pd.read_csv(CLEAN / f"{name}.csv", dtype={"id": str, "thread_id": str})
        f = d["text_clean"].astype(str).map(lambda t: flag(t, lex))
        d["air"], d["air_wide"], d["fire"], d["terms"] = f.str[0], f.str[1], f.str[2], f.str[3].map(lambda x: ";".join(x))
        # R7 thread context: a comment also counts if the post that opened its thread is air talk
        air_posts = set(d[(d.kind == "post") & d.air].id)
        d["air_thread"] = d.air | ((d.kind == "comment") & d.thread_id.isin(air_posts))
        frames.append(d)
    items = pd.concat(frames, ignore_index=True)
    items.drop(columns=["text_clean"]).to_csv(OUT / "items_flagged.csv", index=False)

    # share by window, with bootstrap draws kept for the lift
    rows, draws = [], {}
    for name, city, wtype in WINDOWS:
        d = items[items.window == name]
        row = {"window": name, "city": city, "week_type": wtype, "n_items": len(d),
               "n_threads": d.thread_id.nunique(), "n_air": int(d.air.sum()), "n_air_wide": int(d.air_wide.sum())}
        row["n_air_thread"], row["n_fire"] = int(d.air_thread.sum()), int(d.fire.sum())
        row["fire_share"] = d.fire.mean()
        for col in ["air", "air_wide", "air_thread"]:
            bs = boot_share(d, col, rng)
            draws[(name, col)] = bs
            row[f"{col}_share"] = d[col].mean()
            row[f"{col}_lo"], row[f"{col}_hi"] = np.percentile(bs, [2.5, 97.5])
        for kind in ["post", "comment"]:
            k = d[d.kind == kind]
            row[f"air_share_{kind}s"] = k.air.mean() if len(k) else np.nan
        rows.append(row)
    share = pd.DataFrame(rows)
    share.to_csv(OUT / "share_by_window.csv", index=False)

    # lift = event / mean(baselines)
    lifts = []
    for city in ["Eugene", "Bakersfield"]:
        w = [n for n, c, t in WINDOWS if c == city]
        ev, bases = w[0], w[1:]
        for col in ["air", "air_wide", "air_thread"]:
            e = share.set_index("window").loc[ev, f"{col}_share"]
            b = np.mean([share.set_index("window").loc[x, f"{col}_share"] for x in bases])
            bb = np.mean([draws[(x, col)] for x in bases], axis=0)
            diff = draws[(ev, col)] - bb                                   # R6
            ok = bb > 0
            ratio = draws[(ev, col)][ok] / bb[ok]
            lo, hi = np.percentile(ratio, [2.5, 97.5])
            dlo, dhi = np.percentile(diff, [2.5, 97.5])
            lifts.append({"city": city, "measure": col, "event_share": e, "baseline_share": b,
                          "lift": e / b if b else np.nan, "lift_lo": lo, "lift_hi": hi,
                          "diff_pp": 100 * (e - b), "diff_lo_pp": 100 * dlo, "diff_hi_pp": 100 * dhi,
                          "share_draws_baseline_zero": round(1 - ok.mean(), 4)})
    lift = pd.DataFrame(lifts)
    lift.to_csv(OUT / "lift.csv", index=False)

    # term counts per window (audit)
    tc = (items.assign(term=items.terms.str.split(";")).explode("term")
          .query("term != ''").groupby(["term", "window"]).size().unstack(fill_value=0))
    tc = tc.reindex(columns=[n for n, _, _ in WINDOWS], fill_value=0)
    tc["total"] = tc.sum(axis=1)
    tc.sort_values("total", ascending=False).to_csv(OUT / "term_counts.csv")

    # daily share
    daily = items.groupby(["window", "local_date"]).agg(n=("air", "size"), n_air=("air", "sum"))
    daily["air_share"] = daily.n_air / daily.n
    daily.reset_index().to_csv(OUT / "daily_share.csv", index=False)

    # removal check (R4): flags and thread ids only
    rc = []
    for name, city, wtype in WINDOWS:
        d = items[items.window == name]
        air_threads = set(d[(d.kind == "post") & d.air].id)
        lo, hi = d.created_utc.min(), d.created_utc.max()
        tot = {True: [0, 0], False: [0, 0]}   # air thread? -> [removed, all]
        with open(RAW / f"{name}_comments.jsonl", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                x = json.loads(line)
                t = int(float(x["created_utc"]))
                if not (lo <= t <= hi):
                    continue
                k = (x.get("link_id") or "").replace("t3_", "") in air_threads
                tot[k][1] += 1
                tot[k][0] += is_removed(x)
        rc.append({"window": name, "city": city, "week_type": wtype,
                   "air_thread_comments": tot[True][1], "air_thread_removed_share": tot[True][0] / tot[True][1] if tot[True][1] else np.nan,
                   "other_comments": tot[False][1], "other_removed_share": tot[False][0] / tot[False][1] if tot[False][1] else np.nan})
    pd.DataFrame(rc).to_csv(OUT / "removal_check.csv", index=False)

    # printout
    pd.set_option("display.width", 200)
    print("\nAIR-TALK SHARE BY WINDOW (main measure; 95% range)")
    for r in share.itertuples():
        print(f"  {r.window:30s} items {r.n_items:5d}  air {r.n_air:4d}  share {100*r.air_share:5.2f}%  "
              f"[{100*r.air_lo:.2f}-{100*r.air_hi:.2f}]   wide {100*r.air_wide_share:5.2f}%   thread {100*r.air_thread_share:5.2f}%   fire {100*r.fire_share:5.2f}%   "
              f"posts {100*r.air_share_posts:5.2f}%  comments {100*r.air_share_comments:5.2f}%")
    print("\nLIFT (event share / mean baseline share) and DIFFERENCE (event minus baseline, percentage points)")
    for r in lift.itertuples():
        print(f"  {r.city:12s} {r.measure:9s} event {100*r.event_share:5.2f}%  baseline {100*r.baseline_share:5.2f}%  "
              f"lift {r.lift:5.2f}x [{r.lift_lo:.2f}-{r.lift_hi:.2f}]   "
              f"diff {r.diff_pp:+.2f} pp [{r.diff_lo_pp:+.2f} to {r.diff_hi_pp:+.2f}]   "
              f"(draws with zero baseline: {100*r.share_draws_baseline_zero:.1f}%)")
    print("\nTOP TERMS (items matched; * = candidate, wide measure only; ^ = fire, reported separately, never air talk)")
    print(tc.sort_values("total", ascending=False).head(20).to_string())
    print("\nREMOVAL CHECK (share of comments removed)")
    print(pd.DataFrame(rc)[["window", "air_thread_comments", "air_thread_removed_share", "other_comments", "other_removed_share"]].round(3).to_string(index=False))
    print(f"\noutputs -> {OUT}/")


if __name__ == "__main__":
    main()
