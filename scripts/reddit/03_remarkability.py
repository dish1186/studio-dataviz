#!/usr/bin/env python3
"""
scripts/reddit/03_remarkability.py  (study version)

Step 03: Moore et al. (2019)'s first measure, "remarkability": what share of a
city's conversation is about the topic (air by default) in each window, and, for
event windows, how much higher that is than the same city's baseline windows.

Run from the repo root:
    python3 scripts/reddit/03_remarkability.py --study studies/eugene_bakersfield.json

Input:   data/processed/reddit/<study>/step02_clean/items.csv and removed.csv
         the topic word list named in the study file (default lexicon_air_v1.csv)
Output:  data/processed/reddit/<study>/step03_remarkability/<lexicon name>/
           items_flagged.csv   every item: topic, topic_wide, topic_thread, separate measures, terms (no text)
           share_by_window.csv topic share per window with 95% ranges (a weekly series for period windows)
           lift.csv            each event window vs the mean of its group's baselines
           term_counts.csv     items each term matched, per window (long format)
           daily_share.csv     topic share per local day
           removal_check.csv   share of comments removed in topic threads vs other threads

Rules (as in the Eugene/Bakersfield run; log as decisions):
    R1  Main measure = topic share of all kept posts + comments. Posts-only and comments-only too.
    R2  Baseline = mean of the group's baseline windows' shares. Lift = event / baseline.
    R3  95% ranges: whole-thread bootstrap, 2,000 draws, seed 20261001.
    R4  Removal check uses removal flags and thread ids only, never removed text.
    R6  Difference (event minus baseline, percentage points) with its own range; bootstrap draws
        with a zero baseline are left out of the ratio's range and counted.
    R7  Word-list types other than include/candidate/exclude (e.g. "fire") are separate measures,
        never counted as topic talk. topic_thread = topic talk, or a comment in a thread whose
        opening post is topic talk.
    R8  (study version) Groups come from the study file: every event window is compared with the
        baseline windows of its own group. Period windows get shares (a series) but no lift.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study, load_topic_lexicon, flag_topic, boot_mean, comparisons, topic_for   # noqa: E402

B, SEED = 2000, 20261001


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--lexicon", help="override the study file's topic word list")
    args = ap.parse_args()
    S = load_study(args.study)
    LEX, TOPIC = topic_for(S, args.lexicon)
    S["topic"] = TOPIC
    OUT = S["out"] / "step03_remarkability" / LEX.stem
    OUT.mkdir(parents=True, exist_ok=True)
    lex = load_topic_lexicon(LEX)
    seps = sorted(lex["separate"])
    print(f"topic '{S['topic']}', word list {LEX}: include {len(lex['include'])}, candidate {len(lex['candidate'])}, "
          f"exclude {len(lex['exclude'])}" + "".join(f", {k} {len(v)} (separate)" for k, v in lex["separate"].items()))
    rng = np.random.default_rng(SEED)

    items = pd.read_csv(S["out"] / "step02_clean" / "items.csv", dtype={"id": str, "thread_id": str})
    f = items["text_clean"].astype(str).map(lambda t: flag_topic(t, lex))
    items["topic"], items["topic_wide"] = f.str[0], f.str[1]
    for k in seps:
        items[k] = f.map(lambda r: r[2][k])
    items["terms"] = f.map(lambda r: ";".join(r[3]))
    tp = items[(items.kind == "post") & items.topic][["window", "id"]]
    tp_set = set(zip(tp.window, tp.id))
    items["topic_thread"] = items.topic | ((items.kind == "comment") &
                                           pd.Series(list(zip(items.window, items.thread_id)), index=items.index).isin(tp_set))
    items.drop(columns=["text_clean"]).to_csv(OUT / "items_flagged.csv", index=False)

    rows, draws = [], {}
    for w in S["windows"]:
        d = items[items.window == w["name"]]
        row = {"window": w["name"], "city": w["city"], "group": w["group"], "week_type": w["type"],
               "start": w["start"].isoformat(), "n_items": len(d), "n_threads": d.thread_id.nunique(),
               "n_topic": int(d.topic.sum()), "n_topic_wide": int(d.topic_wide.sum()), "n_topic_thread": int(d.topic_thread.sum())}
        for k in seps:
            row[f"{k}_share"] = d[k].mean() if len(d) else np.nan
        for col in ["topic", "topic_wide", "topic_thread"]:
            bs = boot_mean(d, col, rng, B) if len(d) else np.full(B, np.nan)
            draws[(w["name"], col)] = bs
            row[f"{col}_share"] = d[col].mean() if len(d) else np.nan
            row[f"{col}_lo"], row[f"{col}_hi"] = (np.nanpercentile(bs, [2.5, 97.5]) if len(d) else (np.nan, np.nan))
        for kind in ["post", "comment"]:
            k = d[d.kind == kind]
            row[f"topic_share_{kind}s"] = k.topic.mean() if len(k) else np.nan
        rows.append(row)
    share = pd.DataFrame(rows)
    share.to_csv(OUT / "share_by_window.csv", index=False)
    si = share.set_index("window")

    lifts = []
    for c in comparisons(S):
        for col in ["topic", "topic_wide", "topic_thread"]:
            e = si.loc[c["event"], f"{col}_share"]
            b = np.mean([si.loc[x, f"{col}_share"] for x in c["baselines"]])
            bb = np.mean([draws[(x, col)] for x in c["baselines"]], axis=0)
            diff = draws[(c["event"], col)] - bb
            ok = bb > 0
            ratio = draws[(c["event"], col)][ok] / bb[ok]
            lo, hi = np.percentile(ratio, [2.5, 97.5]) if ok.any() else (np.nan, np.nan)
            dlo, dhi = np.percentile(diff, [2.5, 97.5])
            lifts.append({"group": c["group"], "event": c["event"], "baselines": ";".join(c["baselines"]), "measure": col,
                          "event_share": e, "baseline_share": b, "lift": e / b if b else np.nan, "lift_lo": lo, "lift_hi": hi,
                          "diff_pp": 100 * (e - b), "diff_lo_pp": 100 * dlo, "diff_hi_pp": 100 * dhi,
                          "share_draws_baseline_zero": round(1 - ok.mean(), 4)})
    lift = pd.DataFrame(lifts)
    lift.to_csv(OUT / "lift.csv", index=False)

    tc = (items.assign(term=items.terms.str.split(";")).explode("term").query("term != ''")
          .groupby(["term", "window"]).size().rename("items").reset_index())
    tc.to_csv(OUT / "term_counts.csv", index=False)
    daily = items.groupby(["window", "local_date"]).agg(n=("topic", "size"), n_topic=("topic", "sum"))
    daily["topic_share"] = daily.n_topic / daily.n
    daily.reset_index().to_csv(OUT / "daily_share.csv", index=False)

    rem = pd.read_csv(S["out"] / "step02_clean" / "removed.csv", dtype={"id": str, "thread_id": str})
    rc = []
    for w in S["windows"]:
        d = items[(items.window == w["name"])]
        tt = set(d[(d.kind == "post") & d.topic].id)
        kept_c = d[d.kind == "comment"]
        r = rem[rem.window == w["name"]]
        kin, kout = kept_c.thread_id.isin(tt), r.thread_id.isin(tt)
        a_all, o_all = kin.sum() + kout.sum(), (~kin).sum() + (~kout).sum()
        rc.append({"window": w["name"], "city": w["city"], "week_type": w["type"],
                   "topic_thread_comments": int(a_all), "topic_thread_removed_share": kout.sum() / a_all if a_all else np.nan,
                   "other_comments": int(o_all), "other_removed_share": (~kout).sum() / o_all if o_all else np.nan})
    pd.DataFrame(rc).to_csv(OUT / "removal_check.csv", index=False)

    print(f"\n{S['topic'].upper()}-TALK SHARE BY WINDOW (main measure; 95% range)")
    many = len(S["windows"]) > 30
    show = share if not many else pd.concat([share.head(5), share.sort_values("topic_share", ascending=False).head(10)])
    if many:
        print(f"  {len(share)} windows; first 5, then the 10 highest weeks:")
    for r in show.itertuples():
        print(f"  {r.window:32s} {r.week_type:8s} items {r.n_items:6d}  {S['topic']} {r.n_topic:5d}  share {100*r.topic_share:5.2f}% "
              f"[{100*r.topic_lo:.2f}-{100*r.topic_hi:.2f}]  wide {100*r.topic_wide_share:5.2f}%  thread {100*r.topic_thread_share:5.2f}%"
              + "".join(f"  {k} {100*getattr(r, k + '_share'):5.2f}%" for k in seps))
    if len(lift):
        print("\nLIFT (event share / mean of its group's baselines) and DIFFERENCE (percentage points)")
        for r in lift.itertuples():
            print(f"  {r.event:32s} {r.measure:12s} event {100*r.event_share:5.2f}%  baseline {100*r.baseline_share:5.2f}%  "
                  f"lift {r.lift:5.2f}x [{r.lift_lo:.2f}-{r.lift_hi:.2f}]  diff {r.diff_pp:+.2f} pp [{r.diff_lo_pp:+.2f} to {r.diff_hi_pp:+.2f}]"
                  f"  (zero-baseline draws {100*r.share_draws_baseline_zero:.1f}%)")
    top = tc.groupby("term")["items"].sum().sort_values(ascending=False).head(15)
    print("\nTOP TERMS (items matched, all windows; * = candidate, ^ = separate measure)")
    print("  " + ", ".join(f"{t} {n}" for t, n in top.items()))
    print(f"\noutputs -> {OUT}/")


if __name__ == "__main__":
    main()
