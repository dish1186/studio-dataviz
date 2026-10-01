#!/usr/bin/env python3
"""
scripts/reddit/04_mood.py  (study version)

Step 04: Moore et al. (2019)'s second measure. VADER mood of everything people
wrote that is NOT about the topic, the separate measures, or the weather, per window;
each event window compared with its group's baselines.

Run from the repo root:
    python3 scripts/reddit/04_mood.py --study studies/eugene_bakersfield.json

Output:  data/processed/reddit/<study>/step04_mood/<word list name>/
           items_scored.csv, mood_by_window.csv, mood_shift.csv, daily_mood.csv,
           audit_extremes.csv (has text: local working file)
Rules: S1 VADER 3.3.2 unchanged; S2 main score pos - neg (Moore's composite), compound as a check;
S3 mood set = not topic_wide, not topic_thread, not a separate measure, no Moore et al. weather word;
S4 topic items scored separately (descriptive); S5 baseline = mean of the group's baselines;
S6 whole-thread bootstrap, 2,000 draws, seed 20261003; S7 neutral items stay in.
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study, boot_mean, comparisons, topic_for   # noqa: E402

B, SEED = 2000, 20261003
MOORE_WEATHER = """blizzard breeze chilly clear clouds cloudy cold damp dew downpour drizzle drought dry
flurry fog freezing frigid frostbite frosty gail gust hail heat hot humid hurricane icy lightning
misty moist monsoon muddy overcast pouring precipitation rain rainbow showers sleet snowflakes
soggy sprinkle sunny thunder thunderstorm typhoon weather wet wind windstorm windy""".split()
WEATHER = re.compile(r"\b(?:" + "|".join(MOORE_WEATHER) + r")\b", re.IGNORECASE)
BASE = {"window", "city", "group", "week_type", "kind", "id", "thread_id", "parent_id", "created_utc", "created_local",
        "local_date", "score", "num_comments", "n_chars", "topic", "topic_wide", "topic_thread", "terms"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--lexicon")
    args = ap.parse_args()
    S = load_study(args.study)
    lex, _ = topic_for(S, args.lexicon)
    OUT = S["out"] / "step04_mood" / lex.stem
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    vader = SentimentIntensityAnalyzer()

    flags = pd.read_csv(S["out"] / "step03_remarkability" / lex.stem / "items_flagged.csv", dtype={"id": str, "thread_id": str})
    seps = [c for c in flags.columns if c not in BASE]
    text = pd.read_csv(S["out"] / "step02_clean" / "items.csv", dtype={"id": str}, usecols=["id", "window", "text_clean"])
    d = flags.merge(text, on=["id", "window"], how="left")
    print(f"scoring {len(d)} items with VADER ...")
    sc = d.text_clean.astype(str).map(vader.polarity_scores)
    for k in ["neg", "neu", "pos", "compound"]:
        d[k] = sc.map(lambda x: x[k])
    d["composite"] = d.pos - d.neg
    d["weather_word"] = d.text_clean.astype(str).str.contains(WEATHER)
    topic_any = d.topic_wide | d.topic_thread
    sep_any = d[seps].any(axis=1) if seps else False
    d["mood_set"] = ~(topic_any | sep_any | d.weather_word)
    d["neutral"] = (d.pos == 0) & (d.neg == 0)
    d.drop(columns=["text_clean"]).to_csv(OUT / "items_scored.csv", index=False)

    rows, draws = [], {}
    for w in S["windows"]:
        x = d[d.window == w["name"]]
        m, a = x[x.mood_set], x[x.topic_wide | x.topic_thread]
        row = {"window": w["name"], "city": w["city"], "group": w["group"], "week_type": w["type"], "start": w["start"].isoformat(),
               "items": len(x), "mood_set": len(m), "left_out_topic": int(a.shape[0]),
               "left_out_weather": int((x.weather_word & ~(x.topic_wide | x.topic_thread)).sum()),
               "share_neutral": m.neutral.mean() if len(m) else np.nan}
        for col in ["composite", "compound"]:
            bs = boot_mean(m, col, rng, B) if len(m) else np.full(B, np.nan)
            draws[(w["name"], col)] = bs
            row[col] = m[col].mean() if len(m) else np.nan
            row[f"{col}_lo"], row[f"{col}_hi"] = (np.nanpercentile(bs, [2.5, 97.5]) if len(m) else (np.nan, np.nan))
        row["topic_items_scored"] = len(a)
        row["topic_composite"] = a.composite.mean() if len(a) else np.nan
        row["topic_compound"] = a.compound.mean() if len(a) else np.nan
        rows.append(row)
    mood = pd.DataFrame(rows)
    mood.to_csv(OUT / "mood_by_window.csv", index=False)
    mi = mood.set_index("window")

    shifts = []
    for c in comparisons(S):
        for col in ["composite", "compound"]:
            e = mi.loc[c["event"], col]
            b = np.mean([mi.loc[x, col] for x in c["baselines"]])
            diff = draws[(c["event"], col)] - np.mean([draws[(x, col)] for x in c["baselines"]], axis=0)
            lo, hi = np.nanpercentile(diff, [2.5, 97.5])
            shifts.append({"group": c["group"], "event": c["event"], "score": col, "event_mood": e, "baseline_mood": b,
                           "shift": e - b, "shift_lo": lo, "shift_hi": hi})
    shift = pd.DataFrame(shifts)
    shift.to_csv(OUT / "mood_shift.csv", index=False)
    d[d.mood_set].groupby(["window", "local_date"]).agg(n=("composite", "size"), composite=("composite", "mean"),
                                                         compound=("compound", "mean")).reset_index().to_csv(OUT / "daily_mood.csv", index=False)
    ext = []
    for w in S["windows"]:
        m = d[(d.window == w["name"]) & d.mood_set].sort_values("compound")
        ext += [m.head(10).assign(end="most negative"), m.tail(10).assign(end="most positive")]
    pd.concat(ext)[["window", "end", "kind", "compound", "composite", "text_clean"]].to_csv(OUT / "audit_extremes.csv", index=False)

    print("\nMOOD BY WINDOW (items with no topic, separate-measure or weather words; 95% range)")
    show = mood if len(mood) <= 30 else mood.head(10)
    for r in show.itertuples():
        print(f"  {r.window:32s} scored {r.mood_set:6d} of {r.items:6d}   pos-neg {r.composite:+.4f} [{r.composite_lo:+.4f} to {r.composite_hi:+.4f}]"
              f"   compound {r.compound:+.3f}   topic talk tone {r.topic_composite:+.4f} ({r.topic_items_scored} items)")
    if len(mood) > 30:
        print(f"  ... {len(mood)} windows in mood_by_window.csv")
    if len(shift):
        print("\nMOOD SHIFT (event minus mean of its group's baselines)")
        for r in shift.itertuples():
            print(f"  {r.event:32s} {r.score:9s} event {r.event_mood:+.4f}  baseline {r.baseline_mood:+.4f}  shift {r.shift:+.4f} [{r.shift_lo:+.4f} to {r.shift_hi:+.4f}]")
    print(f"\noutputs -> {OUT}/   (audit_extremes.csv has text: keep it local)")


if __name__ == "__main__":
    main()
