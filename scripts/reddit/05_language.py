#!/usr/bin/env python3
"""
scripts/reddit/05_language.py  (study version)

Step 05: what KIND of topic talk each window produced. Registers (comfort, safety,
meaning) and markers (normalizing, alarm, institution) from the register word list;
pronoun counts and "too ___" phrases kept for completeness (negative results in the
Eugene/Bakersfield run). Descriptive, no ranges.

Run from the repo root:
    python3 scripts/reddit/05_language.py --study studies/eugene_bakersfield.json --set wide

Output:  data/processed/reddit/<study>/step05_language/<word list name>/<set>/
           register_summary.csv, pronoun_summary.csv, register_terms.csv, too_phrases.csv
           LOCAL ONLY (people's words): fragments.csv, concordance.csv
Rules: L1 set: wide = the item itself contains a topic word (include or candidate), strict =
include words only, thread = wide plus comments in topic threads. "Other talk" = everything else
in the same window. L2 register list v0 unvalidated: read register_terms.csv and the fragments
before trusting a register (Institutions failed this check in Eugene). L3 "US" is not "us".
L4 "too" + next word, skipping "too" = "also". L5 no ranges. L6 concordance and fragments only
from sentences that mention the topic.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study, load_topic_lexicon, topic_for   # noqa: E402

SEED = 20261004
REGISTERS = ["comfort", "safety", "meaning", "normalizing", "alarm", "institution"]
PRON = {
    "I":    re.compile(r"\b(?:i|me|my|mine|myself|i'm|im|i've|ive|i'd|i'll)\b", re.IGNORECASE),
    "we":   re.compile(r"\b(?:we|our|ours|ourselves|we're|we've|we'd|we'll|let's)\b|(?<![A-Za-z])(?:us|Us)\b"),
    "they": re.compile(r"\b(?:they|them|their|theirs|themselves|they're|they've|they'd|they'll)\b", re.IGNORECASE),
    "you":  re.compile(r"\b(?:you|your|yours|yourself|yourselves|you're|you've|you'd|you'll|ya|y'all|yall)\b", re.IGNORECASE),
}
TOO = re.compile(r"\btoo\s+([a-z']+)(?:\s+to\s+([a-z']+))?", re.IGNORECASE)
TOO_SKIP = {"lol", "lmao", "haha", "and", "but", "i", "im", "i'm", "so", "though", "tbh", "honestly", "btw", "the", "a", "an",
            "is", "was", "it", "lmfao", "imo", "now", "or", "if", "my", "this", "that", "please", "kekw", "fr", "lmk", "xd",
            "you", "we", "they", "he", "she"}
SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def load_registers(path):
    lex = {r: [] for r in REGISTERS}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        lex[row["register"].strip()].append((row["term"], re.compile(row["pattern"], re.IGNORECASE)))
    return lex


def has_topic(sentence, tl):
    t = sentence
    for _, p in tl["exclude"]:
        t = p.sub(" ", t)
    return any(p.search(t) for _, p in tl["include"] + tl["candidate"])


def frag(text, m, n=8):
    return " ".join(text[:m.start()].split()[-n:]), text[m.start():m.end()], " ".join(text[m.end():].split()[:n])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--set", choices=["wide", "strict", "thread"], default="wide")
    ap.add_argument("--lexicon")
    args = ap.parse_args()
    S = load_study(args.study)
    lexp, S["topic"] = topic_for(S, args.lexicon)
    OUT = S["out"] / "step05_language" / lexp.stem / args.set
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    reg, tl = load_registers(S["lex_registers"]), load_topic_lexicon(lexp)

    flags = pd.read_csv(S["out"] / "step03_remarkability" / lexp.stem / "items_flagged.csv", dtype={"id": str, "thread_id": str})
    text = pd.read_csv(S["out"] / "step02_clean" / "items.csv", dtype={"id": str}, usecols=["id", "window", "text_clean"])
    d = flags.merge(text, on=["id", "window"], how="left")
    d["text_clean"] = d.text_clean.astype(str).str.replace("\u2019", "'").str.replace("\u2018", "'")
    mask = {"wide": d.topic_wide, "strict": d.topic, "thread": d.topic_wide | d.topic_thread}[args.set]
    d["set"] = np.where(mask, "topic", "other")
    print(f"{S['topic']}-talk set = {args.set}: {int(mask.sum())} items")

    hits = {r: [] for r in REGISTERS}
    prons = {p: [] for p in PRON}
    terms, frags, toos, conc = [], [], [], []
    for row in d.itertuples():
        t = row.text_clean
        for r in REGISTERS:
            h = False
            for term, p in reg[r]:
                if p.search(t):
                    h = True
                    terms.append((row.window, row.set, r, term))
            hits[r].append(h)
        for p, rx in PRON.items():
            prons[p].append(len(rx.findall(t)))
        if row.set != "topic":
            continue
        for sent in SENT.split(t):
            if not has_topic(sent, tl):
                continue
            for r in REGISTERS:
                for term, p in reg[r]:
                    for m in list(p.finditer(sent))[:1]:
                        l, w, rt = frag(sent, m)
                        frags.append({"window": row.window, "city": row.city, "week_type": row.week_type, "register": r,
                                      "term": term, "left": l, "match": w, "right": rt, "sentence": sent})
            if row.week_type == "event":
                for p, rx in PRON.items():
                    for m in list(rx.finditer(sent))[:3]:
                        l, w, rt = frag(sent, m)
                        conc.append({"window": row.window, "city": row.city, "pronoun": p, "left": l, "word": w, "right": rt})
        for m in TOO.finditer(t):
            if m.group(1).lower() in TOO_SKIP:
                continue
            ph = m.group(0).lower()
            rs = [r for r in ["comfort", "safety", "meaning"] if any(p.search(ph) for _, p in reg[r])]
            toos.append({"window": row.window, "city": row.city, "phrase": ph, "register": ";".join(rs) or "unassigned"})
    for r in REGISTERS:
        d[r] = hits[r]
    for p in PRON:
        d[f"n_{p}"] = prons[p]

    g = d.groupby(["window", "city", "group", "week_type", "set"])
    rs = g[REGISTERS].mean().add_suffix("_share")
    rs.insert(0, "items", g.size())
    rs = rs.reset_index()
    rs.to_csv(OUT / "register_summary.csv", index=False)
    pr = g[[f"n_{p}" for p in PRON]].sum()
    pr["items"] = g.size()
    pr["we_share"] = pr.n_we / (pr.n_I + pr.n_we)
    pr["they_share"] = pr.n_they / (pr.n_I + pr.n_we + pr.n_they)
    pr.reset_index().to_csv(OUT / "pronoun_summary.csv", index=False)
    pd.DataFrame(terms, columns=["window", "set", "register", "term"]).groupby(["register", "term", "set", "window"]).size() \
        .rename("items").reset_index().to_csv(OUT / "register_terms.csv", index=False)
    pd.DataFrame(toos).to_csv(OUT / "too_phrases.csv", index=False)
    pd.DataFrame(frags).to_csv(OUT / "fragments.csv", index=False)
    c = pd.DataFrame(conc)
    if len(c):
        c = c.sample(frac=1, random_state=int(rng.integers(1e9))).groupby(["city", "pronoun"]).head(60).sort_values(["city", "pronoun"])
    c.to_csv(OUT / "concordance.csv", index=False)

    print(f"\nEVENT WINDOWS: {S['topic']} talk vs other talk in the same week (share of items)")
    ev = rs[rs.week_type == "event"]
    for w in ev.window.unique():
        a, o = ev[(ev.window == w) & (ev.set == "topic")], ev[(ev.window == w) & (ev.set == "other")]
        if not len(a):
            continue
        a, o = a.iloc[0], o.iloc[0]
        print(f"  {w:32s} {S['topic']} items {int(a['items']):5d}   " + "   ".join(
            f"{r} {100*a[f'{r}_share']:4.1f}% ({100*o[f'{r}_share']:.1f}%)" for r in REGISTERS))
    if (rs.week_type != "event").any():
        print("  (baseline and period windows are in register_summary.csv)")
    print(f"\noutputs -> {OUT}/   (fragments.csv and concordance.csv contain people's words: keep local)")


if __name__ == "__main__":
    main()
