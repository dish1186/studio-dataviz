#!/usr/bin/env python3
"""
scripts/reddit/spectrum_02_sample.py

Alarm -> Normalizing spectrum, Step 2 prep: decide which air-talk items get labeled, and which 10% get
re-labeled blind. Labels themselves are written by hand (Claude drafts) into spectrum_02_labels/.

Rules:
  P1  Weeks with <= 500 air items: every item is labeled (weight 1).
  P2  Weeks with > 500 air items (Dish OK 2026-10-04): random sample of 400, stratified by thread.
      Strata = each thread with >= 5 air items, plus one pooled "small threads" stratum.
      Allocation proportional to stratum size, rounded by largest remainder, at least 1 per stratum.
      weight = stratum size / stratum sample size, so band shares can be weighted back to the full week.
  P3  Re-label check: a random 10% (rounded up) of the labeled items, drawn after P1/P2.
  P4  Seed 20261004 per week (seeded by week name too), so each week can be re-drawn alone later.

Input (read only): data/processed/reddit/spectrum_01_air_items/<city>_<week>[_comparison]_air_items.csv
Output: data/processed/reddit/spectrum_02_labels/
  <name>_to_label.csv     items to label: item_id, thread_id, stratum, weight, matched_terms, include_hit,
                          hover_text, full_text
  <name>_relabel_ids.csv  item_id of the 10% re-label set
  sample_summary.csv      one row per week: air items, labeled, sampled?, strata, re-label n
Run from the repo root: python3 scripts/reddit/spectrum_02_sample.py [--name eugene_2020-09-07]
"""

import argparse
import csv
import math
import random
from collections import defaultdict
from pathlib import Path

IN = Path("data/processed/reddit/spectrum_01_air_items")
OUT = Path("data/processed/reddit/spectrum_02_labels")
SEED, LIMIT, N_SAMPLE, MIN_THREAD = 20261004, 500, 400, 5
csv.field_size_limit(10**9)
KEEP = ["item_id", "thread_id", "stratum", "weight", "matched_terms", "include_hit", "hover_text", "full_text"]


def allocate(sizes, n):
    tot = sum(sizes.values())
    raw = {k: n * v / tot for k, v in sizes.items()}
    alloc = {k: max(1, math.floor(r)) for k, r in raw.items()}
    left = n - sum(alloc.values())
    for k in sorted(raw, key=lambda k: raw[k] - math.floor(raw[k]), reverse=True)[:max(0, left)]:
        alloc[k] += 1
    return {k: min(a, sizes[k]) for k, a in alloc.items()}


def run(name):
    rows = list(csv.DictReader(open(IN / f"{name}_air_items.csv", encoding="utf-8")))
    rng = random.Random(f"{SEED}-{name}")
    by_th = defaultdict(list)
    for r in rows:
        by_th[r["thread_id"]].append(r)
    if len(rows) <= LIMIT:
        chosen = [dict(r, stratum="all", weight=1) for r in rows]
        n_strata = 1
    else:
        strata = defaultdict(list)
        for th, items in by_th.items():
            strata[th if len(items) >= MIN_THREAD else "small_threads"].extend(items)
        alloc = allocate({k: len(v) for k, v in strata.items()}, N_SAMPLE)
        chosen = []
        for k in sorted(strata):
            pick = rng.sample(sorted(strata[k], key=lambda r: r["item_id"]), alloc[k])
            chosen += [dict(r, stratum=k, weight=round(len(strata[k]) / alloc[k], 4)) for r in pick]
        n_strata = len(strata)
    chosen.sort(key=lambda r: (r["thread_id"], r["item_id"]))
    with open(OUT / f"{name}_to_label.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEEP, extrasaction="ignore"); w.writeheader(); w.writerows(chosen)
    rel = sorted(rng.sample([r["item_id"] for r in chosen], math.ceil(0.1 * len(chosen))))
    with open(OUT / f"{name}_relabel_ids.csv", "w", newline="") as fh:
        fh.write("item_id\n" + "".join(i + "\n" for i in rel))
    return {"name": name, "air_items": len(rows), "labeled": len(chosen), "sampled": int(len(rows) > LIMIT),
            "strata": n_strata, "relabel_n": len(rel)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    names = [args.name] if args.name else sorted(p.name[:-len("_air_items.csv")] for p in IN.glob("*_air_items.csv"))
    sf = OUT / "sample_summary.csv"
    rows = {r["name"]: r for r in csv.DictReader(open(sf))} if sf.exists() else {}
    for n in names:
        rows[n] = run(n)
        print(rows[n])
    with open(sf, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["name", "air_items", "labeled", "sampled", "strata", "relabel_n"])
        w.writeheader(); w.writerows(sorted(rows.values(), key=lambda r: r["name"]))


if __name__ == "__main__":
    main()
