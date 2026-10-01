#!/usr/bin/env python3
"""
scripts/reddit/04_mood.py

Step 04 of the Reddit case study. Moore et al. (2019)'s second measure: does
the MOOD of a city's conversation change in a bad-air week, even in posts and
comments that never mention the air? ("Extreme temperatures still make people
miserable, but they stop talking about it.")

Run from the repo root:
    python3 scripts/reddit/04_mood.py

Input:   data/processed/reddit/step02_clean/<window>.csv
         data/processed/reddit/step03_remarkability/lexicon_air_v1/items_flagged.csv
Output:  data/processed/reddit/step04_mood/
           items_scored.csv     every kept item: VADER neg/neu/pos/compound, composite,
                                and whether it is in the mood set (no text)
           mood_by_window.csv   mean mood per window with 95% ranges
           mood_shift.csv       event minus baseline mood, per city, with 95% ranges
           daily_mood.csv       mean mood per local day
           audit_extremes.csv   the 10 most negative and 10 most positive scored items per
                                window, with text, to check VADER's reading by eye
                                (local working file: do not publish)

Claude defaults (log as decisions):
    S1  Tool: VADER 3.3.2 (Hutto & Gilbert 2014), installed from PyPI, run unchanged.
        LIWC (also used by Moore et al.) is not used: it needs a paid licence.
    S2  Main score = mean of (VADER pos - VADER neg) per item, Moore et al.'s composite
        (positive minus negative). VADER compound reported as a second check.
    S3  Mood set = kept items that are NOT air talk on any measure (air_wide or
        air_thread), NOT fire talk, and contain NONE of Moore et al.'s weather words
        (their SI Appendix list, used whole-word). Moore et al. removed weather tweets
        before scoring sentiment so the score picks up mood, not statements about the
        weather; we do the same for air, fire and weather.
    S4  Air items are also scored, separately, to describe the tone of air talk itself.
        That is descriptive only, not the mood test.
    S5  Baseline mood = mean of the two baseline weeks. Shift = event - baseline.
    S6  95% ranges: whole-thread bootstrap, 2,000 draws, seed 20261003 (as in step 03).
    S7  Items VADER scores as fully neutral (pos = neg = 0) stay in: a week where
        people write more neutral text is part of the mood.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

CLEAN = Path("data/processed/reddit/step02_clean")
FLAGS = Path("data/processed/reddit/step03_remarkability/lexicon_air_v1/items_flagged.csv")
OUT = Path("data/processed/reddit/step04_mood")
B, SEED = 2000, 20261003

WINDOWS = [
    ("eugene_event_2026-08-03",      "Eugene",      "event"),
    ("eugene_base_2024-08-05",       "Eugene",      "baseline"),
    ("eugene_base_2025-08-04",       "Eugene",      "baseline"),
    ("bakersfield_event_2024-12-02", "Bakersfield", "event"),
    ("bakersfield_base_2023-12-04",  "Bakersfield", "baseline"),
    ("bakersfield_base_2025-12-01",  "Bakersfield", "baseline"),
]

# S3: Moore et al. (2019) SI Appendix, words excluded before sentiment analysis
MOORE_WEATHER = """blizzard breeze chilly clear clouds cloudy cold damp dew downpour drizzle drought dry
flurry fog freezing frigid frostbite frosty gail gust hail heat hot humid hurricane icy lightning
misty moist monsoon muddy overcast pouring precipitation rain rainbow showers sleet snowflakes
soggy sprinkle sunny thunder thunderstorm typhoon weather wet wind windstorm windy""".split()
WEATHER = re.compile(r"\b(?:" + "|".join(MOORE_WEATHER) + r")\b", re.IGNORECASE)


def boot_mean(df, col, rng):
    g = df.groupby("thread_id")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = rng.integers(0, len(g), size=(B, len(g)))
    return s[idx].sum(1) / n[idx].sum(1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    vader = SentimentIntensityAnalyzer()

    flags = pd.read_csv(FLAGS, dtype={"id": str, "thread_id": str})
    text = pd.concat([pd.read_csv(CLEAN / f"{n}.csv", dtype={"id": str}, usecols=["id", "window", "text_clean"])
                      for n, _, _ in WINDOWS])
    d = flags.merge(text, on=["id", "window"], how="left")
    print(f"scoring {len(d)} items with VADER ...")
    sc = d.text_clean.astype(str).map(vader.polarity_scores)
    for k in ["neg", "neu", "pos", "compound"]:
        d[k] = sc.map(lambda x: x[k])
    d["composite"] = d.pos - d.neg                                     # S2
    d["weather_word"] = d.text_clean.astype(str).str.contains(WEATHER)
    d["mood_set"] = ~(d.air_wide | d.air_thread | d.fire | d.weather_word)   # S3
    d["neutral"] = (d.pos == 0) & (d.neg == 0)
    d.drop(columns=["text_clean"]).to_csv(OUT / "items_scored.csv", index=False)

    rows, draws = [], {}
    for name, city, wtype in WINDOWS:
        w = d[d.window == name]
        m = w[w.mood_set]
        a = w[w.air_wide | w.air_thread]
        row = {"window": name, "city": city, "week_type": wtype, "items": len(w),
               "mood_set": len(m), "left_out_air": int((w.air_wide | w.air_thread).sum()),
               "left_out_fire": int((w.fire & ~(w.air_wide | w.air_thread)).sum()),
               "left_out_weather": int((w.weather_word & ~(w.air_wide | w.air_thread | w.fire)).sum()),
               "share_neutral": m.neutral.mean()}
        for col in ["composite", "compound"]:
            bs = boot_mean(m, col, rng)
            draws[(name, col)] = bs
            row[col] = m[col].mean()
            row[f"{col}_lo"], row[f"{col}_hi"] = np.percentile(bs, [2.5, 97.5])
        row["air_items_scored"] = len(a)
        row["air_composite"] = a.composite.mean() if len(a) else np.nan       # S4
        row["air_compound"] = a.compound.mean() if len(a) else np.nan
        rows.append(row)
    mood = pd.DataFrame(rows)
    mood.to_csv(OUT / "mood_by_window.csv", index=False)

    shifts = []
    for city in ["Eugene", "Bakersfield"]:
        w = [n for n, c, t in WINDOWS if c == city]
        ev, bases = w[0], w[1:]
        for col in ["composite", "compound"]:
            e = mood.set_index("window").loc[ev, col]
            b = np.mean([mood.set_index("window").loc[x, col] for x in bases])
            diff = draws[(ev, col)] - np.mean([draws[(x, col)] for x in bases], axis=0)
            lo, hi = np.percentile(diff, [2.5, 97.5])
            shifts.append({"city": city, "score": col, "event": e, "baseline": b,
                           "shift": e - b, "shift_lo": lo, "shift_hi": hi})
    shift = pd.DataFrame(shifts)
    shift.to_csv(OUT / "mood_shift.csv", index=False)

    daily = d[d.mood_set].groupby(["window", "local_date"]).agg(n=("composite", "size"),
                                                                   composite=("composite", "mean"),
                                                                   compound=("compound", "mean"))
    daily.reset_index().to_csv(OUT / "daily_mood.csv", index=False)

    ext = []
    for name, _, _ in WINDOWS:
        m = d[(d.window == name) & d.mood_set].sort_values("compound")
        ext.append(m.head(10).assign(end="most negative"))
        ext.append(m.tail(10).assign(end="most positive"))
    pd.concat(ext)[["window", "end", "kind", "compound", "composite", "text_clean"]].to_csv(OUT / "audit_extremes.csv", index=False)

    print("\nMOOD BY WINDOW (items with no air, fire or weather words; 95% range)")
    for r in mood.itertuples():
        print(f"  {r.window:30s} scored {r.mood_set:5d} of {r.items:5d}  (left out: air {r.left_out_air}, fire {r.left_out_fire}, "
              f"weather {r.left_out_weather})   pos-neg {r.composite:+.4f} [{r.composite_lo:+.4f} to {r.composite_hi:+.4f}]   "
              f"compound {r.compound:+.3f}   neutral {100*r.share_neutral:.0f}%")
    print("\nMOOD SHIFT (event minus mean of baselines)")
    for r in shift.itertuples():
        print(f"  {r.city:12s} {r.score:9s} event {r.event:+.4f}  baseline {r.baseline:+.4f}  "
              f"shift {r.shift:+.4f} [{r.shift_lo:+.4f} to {r.shift_hi:+.4f}]")
    print("\nTONE OF THE AIR TALK ITSELF (descriptive)")
    for r in mood.itertuples():
        if r.air_items_scored:
            print(f"  {r.window:30s} air items {r.air_items_scored:4d}   pos-neg {r.air_composite:+.4f}   compound {r.air_compound:+.3f}")
    print(f"\noutputs -> {OUT}/   (audit_extremes.csv has text: keep it local)")


if __name__ == "__main__":
    main()
