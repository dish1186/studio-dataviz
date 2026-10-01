#!/usr/bin/env python3
"""
scripts/reddit/03c_validation_results.py

Scores Dish's hand codes against the word list (lexicon v0), group by group.

Run from the repo root:
    python3 scripts/reddit/03c_validation_results.py

Input:   data/processed/reddit/step03b_validation/coding_sheet_dish.csv   (codes A / F / N)
         data/processed/reddit/step03b_validation/answer_key.csv
         data/processed/reddit/step03_remarkability/items_flagged.csv     (group sizes)
Output:  data/processed/reddit/step03c_validation/
           stratum_results.csv   per group: how often the list was right
           corrected_shares.csv  air-talk share per city and week, before and after correcting
                                 for the list's measured mistakes
           false_positives.csv   flagged items Dish coded N (or F): which words fooled the list
           missed_air.csv        not-flagged items Dish coded A: vocabulary the list is missing

Claude defaults (log as decisions):
    V6  Single coder (Dish). Gina's sheet is not used, so no between-coder agreement is
        reported; this is a stated limitation (Moore et al. used three coders per tweet).
    V7  "Correct" for a flagged item = coded A (strict) or A/F (lenient).
        For a not-flagged item, a miss = coded A.
    V8  95% ranges for proportions are Wilson intervals (behave well with small groups
        and with 0 or 100%).
    V9  Corrected share = (flagged items x strict precision + not-flagged items x miss rate)
        / all items, within each city and week type. Baseline weeks are pooled here, as in
        the sample. Near-miss items are NOT used for this (they were chosen on purpose).
"""

import argparse
from math import sqrt
from pathlib import Path

import pandas as pd




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
    ap.add_argument("--sample", default="data/processed/reddit/step03b_validation", help="folder with the coding sheet and answer key")
    ap.add_argument("--flags", default="data/processed/reddit/step03_remarkability/items_flagged.csv")
    ap.add_argument("--out", default="data/processed/reddit/step03c_validation")
    args = ap.parse_args()
    V, FLAG, OUT = Path(args.sample), Path(args.flags), Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = pd.read_csv(V / "coding_sheet_dish.csv", encoding="utf-8-sig")
    key = pd.read_csv(V / "answer_key.csv")
    d = key.merge(sheet[["item_no", "text", "code", "unsure", "note"]], on="item_no", how="left")
    d["code"] = d["code"].astype(str).str.strip().str.upper().str[:1].replace({"N": "N", "A": "A", "F": "F"})
    bad = d[~d.code.isin(["A", "F", "N"])]
    if len(bad):
        print(f"WARNING: {len(bad)} items without a valid code (A/F/N), left out: item_no {bad.item_no.tolist()[:20]}")
    d = d[d.code.isin(["A", "F", "N"])]
    print(f"{len(d)} coded items; unsure marked on {d.unsure.notna().sum()}")

    # group sizes in the full data
    items = pd.read_csv(FLAG)
    items["week"] = items.week_type.where(items.week_type == "event", "baseline")
    sizes = items.groupby(["city", "week", "air"]).size()

    rows = []
    for stratum, g in d.groupby("stratum"):
        city, week, kind = stratum.split("|")
        n = len(g)
        a, f = (g.code == "A").sum(), (g.code == "F").sum()
        r = {"stratum": stratum, "city": city, "week": week, "group": kind, "n_coded": n,
             "coded_A": a, "coded_F": f, "coded_N": n - a - f}
        if kind in ("flagged", "thread_only"):
            r["measure"] = "precision (share truly about the air)"
            r["strict"], r["strict_lo"], r["strict_hi"] = wilson(a, n)
            r["lenient_AorF"] = (a + f) / n
        else:
            r["measure"] = "miss rate (share of unflagged that were about the air)"
            r["strict"], r["strict_lo"], r["strict_hi"] = wilson(a, n)
        rows.append(r)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "stratum_results.csv", index=False)

    # corrected shares (V9)
    corr = []
    for city in ["Eugene", "Bakersfield"]:
        for week in ["event", "baseline"]:
            try:
                prec = res.set_index("stratum").loc[f"{city}|{week}|flagged", "strict"]
                miss = res.set_index("stratum").loc[f"{city}|{week}|not_flagged", "strict"]
            except KeyError:
                continue
            nf, nn = sizes.get((city, week, True), 0), sizes.get((city, week, False), 0)
            raw = nf / (nf + nn)
            fixed = (nf * prec + nn * miss) / (nf + nn)
            corr.append({"city": city, "week": week, "items": nf + nn, "flagged": nf,
                         "precision": prec, "miss_rate": miss,
                         "share_word_list": raw, "share_corrected": fixed,
                         "est_recall": (nf * prec) / (nf * prec + nn * miss) if (nf * prec + nn * miss) else float("nan")})
    corr = pd.DataFrame(corr)
    corr.to_csv(OUT / "corrected_shares.csv", index=False)

    fp = d[(d.stratum.str.endswith("|flagged") | d.stratum.str.endswith("|thread_only")) & (d.code != "A")][["item_no", "stratum", "code", "terms", "note", "text"]]
    fp.to_csv(OUT / "false_positives.csv", index=False)
    miss = d[(d.stratum.str.endswith("|not_flagged") | d.stratum.str.endswith("|near_miss")) & (d.code == "A")][["item_no", "stratum", "note", "text"]]
    miss.to_csv(OUT / "missed_air.csv", index=False)

    pd.set_option("display.width", 200, "display.max_colwidth", 90)
    print("\nBY GROUP  (flagged: precision = share truly about the air;  not flagged: miss rate)")
    for r in res.itertuples():
        extra = f"   A or F {100*r.lenient_AorF:.0f}%" if r.group in ("flagged", "thread_only") else ""
        print(f"  {r.stratum:34s} n {r.n_coded:3d}  A {r.coded_A:3d} F {r.coded_F:3d} N {r.coded_N:3d}   "
              f"{100*r.strict:5.1f}% [{100*r.strict_lo:.0f}-{100*r.strict_hi:.0f}]{extra}")
    print("\nAIR-TALK SHARE: word list vs corrected for measured mistakes")
    for r in corr.itertuples():
        print(f"  {r.city:12s} {r.week:8s} word list {100*r.share_word_list:5.2f}%   corrected {100*r.share_corrected:5.2f}%   "
              f"(precision {100*r.precision:.0f}%, miss rate {100*r.miss_rate:.1f}%, est. recall {100*r.est_recall:.0f}%)")
    print("\nWORDS BEHIND FALSE ALARMS (flagged but coded N or F)")
    t = fp.assign(term=fp.terms.fillna("").str.split(";")).explode("term")
    print(t[t.term != ""].groupby(["term", "code"]).size().unstack(fill_value=0).to_string() if len(t) else "  none")
    print(f"\nMISSED AIR TALK (not flagged but coded A): {len(miss)} items -> {OUT/'missed_air.csv'}")
    for r in miss.itertuples():
        print(f"  #{r.item_no} [{r.stratum}] {str(r.text)[:140]}")
    print(f"\noutputs -> {OUT}/")


if __name__ == "__main__":
    main()
