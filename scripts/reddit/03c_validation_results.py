#!/usr/bin/env python3
"""
scripts/reddit/03c_validation_results.py  (study version)

Scores one coder's sheet against the word list, group by group.

Run from the repo root:
    python3 scripts/reddit/03c_validation_results.py --study studies/boston_heat_2026.json --coder dish

Output:  data/processed/reddit/<study>/step03c_validation/<word list name>[_<tag>]/
           stratum_results.csv, corrected_shares.csv, false_positives.csv, missed.csv
Rules: V6 one coder; V7 correct = A (strict) or A/F (lenient), miss = coded A when not flagged;
V8 Wilson 95% intervals; V9 corrected share = (flagged x precision + not flagged x miss rate) / all,
per city and week type; near-miss groups are not used for it.
"""

import argparse
import sys
from math import sqrt
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study, topic_for   # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--lexicon")
    ap.add_argument("--tag", default="")
    ap.add_argument("--coder", default="dish")
    args = ap.parse_args()
    S = load_study(args.study)
    lex, _ = topic_for(S, args.lexicon)
    sub = lex.stem + (f"_{args.tag}" if args.tag else "")
    V, OUT = S["out"] / "step03b_validation" / sub, S["out"] / "step03c_validation" / sub
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = pd.read_csv(V / f"coding_sheet_{args.coder}.csv", encoding="utf-8-sig")
    key = pd.read_csv(V / "answer_key.csv")
    d = key.merge(sheet[["item_no", "text", "code", "unsure", "note"]], on="item_no", how="left")
    d["code"] = d["code"].astype(str).str.strip().str.upper().str[:1]
    bad = d[~d.code.isin(["A", "F", "N"])]
    if len(bad):
        print(f"WARNING: {len(bad)} items without a valid code (A/F/N), left out: item_no {bad.item_no.tolist()[:20]}")
    d = d[d.code.isin(["A", "F", "N"])]
    print(f"{len(d)} coded items")
    items = pd.read_csv(S["out"] / "step03_remarkability" / lex.stem / "items_flagged.csv").drop_duplicates("id")
    sizes = items.groupby(["city", "week_type", "topic"]).size()

    rows = []
    for stratum, g in d.groupby("stratum"):
        city, week, kind = stratum.split("|")
        n, a, f = len(g), (g.code == "A").sum(), (g.code == "F").sum()
        r = {"stratum": stratum, "city": city, "week": week, "group": kind, "n_coded": n, "coded_A": a, "coded_F": f, "coded_N": n - a - f}
        r["strict"], r["strict_lo"], r["strict_hi"] = wilson(a, n)
        r["lenient_AorF"] = (a + f) / n
        rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "stratum_results.csv", index=False)
    ri = res.set_index("stratum")
    corr = []
    for (city, week) in sorted({(r.city, r.week) for r in res.itertuples()}):
        try:
            prec, miss = ri.loc[f"{city}|{week}|flagged", "strict"], ri.loc[f"{city}|{week}|not_flagged", "strict"]
        except KeyError:
            continue
        nf, nn = sizes.get((city, week, True), 0), sizes.get((city, week, False), 0)
        corr.append({"city": city, "week": week, "items": nf + nn, "flagged": nf, "precision": prec, "miss_rate": miss,
                     "share_word_list": nf / (nf + nn), "share_corrected": (nf * prec + nn * miss) / (nf + nn)})
    pd.DataFrame(corr).to_csv(OUT / "corrected_shares.csv", index=False)
    fp = d[d.stratum.str.endswith(("|flagged", "|thread_only")) & (d.code != "A")]
    fp[["item_no", "stratum", "code", "terms", "note", "text"]].to_csv(OUT / "false_positives.csv", index=False)
    miss = d[d.stratum.str.endswith(("|not_flagged", "|near_miss")) & (d.code == "A")]
    miss[["item_no", "stratum", "note", "text"]].to_csv(OUT / "missed.csv", index=False)

    print("\nBY GROUP  (flagged / thread only: share truly about the topic;  not flagged / near miss: share missed)")
    for r in res.itertuples():
        print(f"  {r.stratum:40s} n {r.n_coded:3d}  A {r.coded_A:3d} F {r.coded_F:3d} N {r.coded_N:3d}   "
              f"{100*r.strict:5.1f}% [{100*r.strict_lo:.0f}-{100*r.strict_hi:.0f}]")
    print("\nWORDS BEHIND FALSE ALARMS")
    t = fp.assign(term=fp.terms.fillna("").str.split(";")).explode("term")
    print(t[t.term != ""].groupby(["term", "code"]).size().unstack(fill_value=0).to_string() if len(t) else "  none")
    print(f"\nMISSED: {len(miss)} items -> {OUT/'missed.csv'}")
    for r in miss.itertuples():
        print(f"  #{r.item_no} [{r.stratum}] {str(r.text)[:140]}")
    print(f"\noutputs -> {OUT}/")


if __name__ == "__main__":
    main()
