#!/usr/bin/env python3
"""
scripts/reddit/05_language.py

Step 05 of the Reddit case study: WHAT KIND of air talk each city produced.
Descriptive, no hand coding. Feeds the computational-poetry visuals.

Run from the repo root:
    python3 scripts/reddit/05_language.py

Input:   data/processed/reddit/step02_clean/<window>.csv
         data/processed/reddit/step03_remarkability/lexicon_air_v1/items_flagged.csv
         data/lexicons/lexicon_registers_v0.csv
Output:  data/processed/reddit/step05_language/<set>/
           register_summary.csv   share of items in each register / marker, air talk vs other talk
           pronoun_summary.csv    I / we / they / you counts and shares, air talk vs other talk
           register_terms.csv     which register words matched, per window (audit the lexicon)
           too_phrases.csv        every "too ___" phrase in air talk, with its register
           LOCAL ONLY (contain short fragments of people's words; paraphrase before publishing):
           fragments.csv          up to 8 words either side of each register match in air talk
           concordance.csv        pronoun lines from air talk, aligned on the pronoun

Measures
    Registers (an item can be in several):
      comfort      coping with daily life: staying in, windows, fans, sleep, runs, dogs, plans,
                   purifiers, looking up apps and maps
      safety       risk to the body: breathing, symptoms, asthma, kids, masks, AQI numbers
      meaning      what this is: climate, every year, used to, never like this, what is happening
    Markers:
      normalizing  "grew up here", "always been", "doesn't bother me", "that's just the valley"
      alarm        fear and extreme words
      institution  looking to someone else to act: agencies, city or county, "someone should",
                   policy, industry
    Pronouns: I-words, we-words, they-words, you-words, counted per item.
      we_share   = we / (I + we)          how often speakers talk as a group rather than alone
      they_share = they / (I + we + they)

Claude defaults (log as decisions):
    L1  Air talk = air_wide OR air_thread from lexicon air v1 (the broadest air set, so
        replies in air threads and body vocabulary are included). "Other talk" = every
        other kept item in the same window, the reference point for each city's ordinary
        way of speaking (Eugene and Bakersfield may simply use "we" at different rates).
    L2  Register lexicon v0 is a draft by Claude, not validated. Results are descriptive.
        Check register_terms.csv: broad words ("outside", "plans", "show", "kids") may
        inflate a register.
    L3  "us" is not counted when written "US" (the country). "y'all" counts as you.
        Curly apostrophes are straightened before matching.
    L4  "too ___" = "too" + the next word (+ "to" + a verb if present). Skipped when the
        next word shows "too" means "also" (lol, and, but, i, haha ...).
    L1 revised (2026-09-30, after reading the concordance): the default air set is now
        "wide" = the post or comment itself contains an air word (include or candidate).
        Comments counted only because of their thread are left out: threads drift off topic
        (concert ads, politics) and that group was never validated. --set strict (include
        words only) and --set thread (the old broad set) are kept as checks.
    L6  concordance.csv now takes pronoun lines only from SENTENCES that mention the air,
        so every line in it is air talk. The pronoun counts in pronoun_summary.csv are still
        per item (whole comment).
    L5  No ranges are attached: counts in Bakersfield are small, so these are patterns
        to look at, not tests. Compare shapes, not decimals.
"""

import argparse
import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd

CLEAN = Path("data/processed/reddit/step02_clean")
FLAGS = Path("data/processed/reddit/step03_remarkability/lexicon_air_v1/items_flagged.csv")
LEX = Path("data/lexicons/lexicon_registers_v0.csv")
AIRLEX = Path("data/lexicons/lexicon_air_v1.csv")
OUT_ROOT = Path("data/processed/reddit/step05_language")   # results go in a subfolder named after --set
SEED = 20261004

WINDOWS = [
    ("eugene_event_2026-08-03",      "Eugene",      "event"),
    ("eugene_base_2024-08-05",       "Eugene",      "baseline"),
    ("eugene_base_2025-08-04",       "Eugene",      "baseline"),
    ("bakersfield_event_2024-12-02", "Bakersfield", "event"),
    ("bakersfield_base_2023-12-04",  "Bakersfield", "baseline"),
    ("bakersfield_base_2025-12-01",  "Bakersfield", "baseline"),
]
REGISTERS = ["comfort", "safety", "meaning", "normalizing", "alarm", "institution"]

PRON = {   # L3
    "I":    re.compile(r"\b(?:i|me|my|mine|myself|i'm|im|i've|ive|i'd|i'll)\b", re.IGNORECASE),
    "we":   re.compile(r"\b(?:we|our|ours|ourselves|we're|we've|we'd|we'll|let's)\b|(?<![A-Za-z])(?:us|Us)\b"),
    "they": re.compile(r"\b(?:they|them|their|theirs|themselves|they're|they've|they'd|they'll)\b", re.IGNORECASE),
    "you":  re.compile(r"\b(?:you|your|yours|yourself|yourselves|you're|you've|you'd|you'll|ya|y'all|yall)\b", re.IGNORECASE),
}
WE_CI = re.compile(r"\b(?:we|our|ours|ourselves|we're|we've|we'd|we'll|let's)\b", re.IGNORECASE)
TOO = re.compile(r"\btoo\s+([a-z']+)(?:\s+to\s+([a-z']+))?", re.IGNORECASE)
TOO_SKIP = {"lol", "lmao", "haha", "and", "but", "i", "im", "i'm", "so", "though", "tbh", "honestly",
            "btw", "the", "a", "an", "is", "was", "it", "lmfao", "imo", "now", "or", "if", "my",
            "this", "that", "please", "kekw", "fr", "lmk", "xd", "lol.", "you", "we", "they", "he", "she"}


def load_lex():
    lex = {r: [] for r in REGISTERS}
    for row in csv.DictReader(open(LEX, encoding="utf-8")):
        lex[row["register"].strip()].append((row["term"], re.compile(row["pattern"], re.IGNORECASE)))
    print(f"register lexicon {LEX}: " + ", ".join(f"{k} {len(v)}" for k, v in lex.items()))
    return lex


def load_air():
    lx = {"include": [], "candidate": [], "exclude": [], "fire": []}
    for row in csv.DictReader(open(AIRLEX, encoding="utf-8")):
        lx[row["type"].strip()].append(re.compile(row["pattern"], re.IGNORECASE))
    return lx


def has_air(sentence, lx):
    t = sentence
    for p in lx["exclude"]:
        t = p.sub(" ", t)
    return any(p.search(t) for p in lx["include"] + lx["candidate"])


SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def straighten(t):
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def fragment(text, m, n=8):
    left = text[:m.start()].split()[-n:]
    right = text[m.end():].split()[:n]
    return " ".join(left), text[m.start():m.end()], " ".join(right)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["wide", "strict", "thread"], default="wide",
                    help="which items count as air talk (L1, revised): wide = the item itself contains an air word "
                         "(include or candidate); strict = include words only; thread = wide plus every comment in an air thread")
    args = ap.parse_args()
    OUT = OUT_ROOT / args.set
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    lex = load_lex()
    airlx = load_air()

    flags = pd.read_csv(FLAGS, dtype={"id": str, "thread_id": str})
    text = pd.concat([pd.read_csv(CLEAN / f"{n}.csv", dtype={"id": str}, usecols=["id", "window", "text_clean"])
                      for n, _, _ in WINDOWS])
    d = flags.merge(text, on=["id", "window"], how="left")
    d["text_clean"] = d.text_clean.astype(str).map(straighten)
    air_mask = {"wide": d.air_wide, "strict": d.air, "thread": d.air_wide | d.air_thread}[args.set]
    d["set"] = np.where(air_mask, "air", "other")          # L1 (revised)
    print(f"air-talk set = {args.set}: {int(air_mask.sum())} items")

    term_rows, frags, toos, conc = [], [], [], []
    reg_hits = {r: [] for r in REGISTERS}
    pron_counts = {p: [] for p in PRON}
    for row in d.itertuples():
        t = row.text_clean
        for r in REGISTERS:
            hit = False
            for term, p in lex[r]:
                ms = list(p.finditer(t))
                if ms:
                    hit = True
                    term_rows.append((row.window, row.set, r, term))
                    if row.set == "air":
                        for m in ms[:2]:
                            l, w, rt = fragment(t, m)
                            frags.append({"window": row.window, "city": row.city, "register": r, "term": term,
                                          "left": l, "match": w, "right": rt})
            reg_hits[r].append(hit)
        for p, rx in PRON.items():
            pron_counts[p].append(len(rx.findall(t)))
        if row.set == "air" and row.week_type == "event":   # L6: concordance only from sentences that mention the air
            for sent in SENT.split(t):
                if not has_air(sent, airlx):
                    continue
                for p, rx in PRON.items():
                    for m in list(rx.finditer(sent))[:3]:
                        l, w, rt = fragment(sent, m, n=8)
                        conc.append({"window": row.window, "city": row.city, "pronoun": p, "left": l, "word": w, "right": rt})
        if row.set == "air":
            for m in TOO.finditer(t):
                nxt = m.group(1).lower()
                if nxt in TOO_SKIP:
                    continue
                phrase = m.group(0).lower()
                regs = [r for r in ["comfort", "safety", "meaning"] if any(p.search(phrase) for _, p in lex[r])]
                toos.append({"window": row.window, "city": row.city, "phrase": phrase,
                             "register": ";".join(regs) if regs else "unassigned"})
    for r in REGISTERS:
        d[r] = reg_hits[r]
    for p in PRON:
        d[f"n_{p}"] = pron_counts[p]

    # register summary
    g = d.groupby(["window", "city", "week_type", "set"])
    reg = g[REGISTERS].mean().add_suffix("_share")
    reg.insert(0, "items", g.size())
    reg = reg.reset_index()
    reg.to_csv(OUT / "register_summary.csv", index=False)

    # pronoun summary
    pr = g[[f"n_{p}" for p in PRON]].sum()
    pr["items"] = g.size()
    pr["we_share"] = pr.n_we / (pr.n_I + pr.n_we)
    pr["they_share"] = pr.n_they / (pr.n_I + pr.n_we + pr.n_they)
    pr["pronouns_per_item"] = pr[[f"n_{p}" for p in PRON]].sum(axis=1) / pr["items"]
    pr = pr.reset_index()
    pr.to_csv(OUT / "pronoun_summary.csv", index=False)

    tr = pd.DataFrame(term_rows, columns=["window", "set", "register", "term"])
    tr.groupby(["register", "term", "set", "window"]).size().unstack(fill_value=0).to_csv(OUT / "register_terms.csv")
    pd.DataFrame(toos).to_csv(OUT / "too_phrases.csv", index=False)
    pd.DataFrame(frags).to_csv(OUT / "fragments.csv", index=False)
    c = pd.DataFrame(conc)
    if len(c):   # keep up to 60 lines per city and pronoun, chosen at random
        c = c.sample(frac=1, random_state=int(rng.integers(1e9))).groupby(["city", "pronoun"]).head(60)
        c = c.sort_values(["city", "pronoun", "word"])
    c.to_csv(OUT / "concordance.csv", index=False)

    # printout
    pd.set_option("display.width", 220)
    print("\nREGISTERS: share of items (air talk vs other talk in the same week)")
    show = reg.copy()
    for r in REGISTERS:
        show[r] = (100 * show[f"{r}_share"]).round(1)
    print(show[["window", "set", "items"] + REGISTERS].to_string(index=False))

    print("\nPRONOUNS")
    show = pr.copy()
    show["we_share"] = (100 * show.we_share).round(1)
    show["they_share"] = (100 * show.they_share).round(1)
    print(show[["window", "set", "items", "n_I", "n_we", "n_they", "n_you", "we_share", "they_share"]].to_string(index=False))

    print("\nEVENT WEEKS, AIR TALK ONLY: the comparison that matters")
    for city in ["Eugene", "Bakersfield"]:
        a = reg[(reg.city == city) & (reg.week_type == "event") & (reg.set == "air")]
        p = pr[(pr.city == city) & (pr.week_type == "event") & (pr.set == "air")]
        o = pr[(pr.city == city) & (pr.week_type == "event") & (pr.set == "other")]
        if len(a):
            a = a.iloc[0]
            print(f"  {city:12s} items {int(a['items']):4d}  " + "  ".join(f"{r} {100*a[f'{r}_share']:4.1f}%" for r in REGISTERS))
            print(f"  {'':12s} we-share {100*p.we_share.iloc[0]:4.1f}% (other talk {100*o.we_share.iloc[0]:4.1f}%)   "
                  f"they-share {100*p.they_share.iloc[0]:4.1f}% (other talk {100*o.they_share.iloc[0]:4.1f}%)")

    t = pd.DataFrame(toos)
    if len(t):
        print("\n\"TOO ___\" IN AIR TALK (top phrases per city)")
        for city, x in t.groupby("city"):
            top = x.groupby(["phrase", "register"]).size().sort_values(ascending=False).head(12)
            print(f"  {city}: " + ", ".join(f"{ph} [{rg}] x{n}" for (ph, rg), n in top.items()))
    print(f"\noutputs -> {OUT}/   (fragments.csv and concordance.csv contain people's words: keep local, paraphrase before publishing)")


if __name__ == "__main__":
    main()
