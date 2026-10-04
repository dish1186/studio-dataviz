#!/usr/bin/env python3
"""
scripts/reddit/spectrum_05_regroup.py

Exploratory: regroup the four spectrum bands (A Alarm, J Adjusting, E Enduring, N Normalizing) into buckets and
print each city's bucket shares. Changes no label; reads the Claude-draft CSVs written by spectrum_03_outputs.py.

Rules (same as spectrum_03): X is left out of the denominator; sampled weeks (Eugene, Seattle, Pittsburgh) are
weighted back to the full week by each item's stratum weight; shares are within-city.
The Spearman correlations are exploratory (9 cities, draft labels), not the analysis of record.

Input (read only): data/processed/reddit/spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv
                   data/processed/reddit/spectrum_02_labels/<city>_<week>_to_label.csv   (weights)
                   data/processed/reddit/spectrum_01_air_items/summary.csv               (biggest thread)
                   data/processed/openaq/step08_pm_normals/pm_normals.csv
Run from the repo root:
  python3 scripts/reddit/spectrum_05_regroup.py                              all presets
  python3 scripts/reddit/spectrum_05_regroup.py --preset react_live
  python3 scripts/reddit/spectrum_05_regroup.py --groups "reacting=A,J;living=E,N"
  python3 scripts/reddit/spectrum_05_regroup.py --preset react_live --without-big bakersfield
  python3 scripts/reddit/spectrum_05_regroup.py --band-col band_before_rule8   (labels before Rule 8)
"""

import argparse
import csv
from pathlib import Path

O = Path("data/processed/reddit/spectrum_03_outputs")
L = Path("data/processed/reddit/spectrum_02_labels")
S1 = Path("data/processed/reddit/spectrum_01_air_items/summary.csv")
PMN = Path("data/processed/openaq/step08_pm_normals/pm_normals.csv")
PRESETS = {
    "four": "alarm=A;adjusting=J;enduring=E;normalizing=N",
    "react_live": "reacting=A,J;living=E,N",          # Dish's current split
    "j_as_living": "reacting=A;living=J,E,N",          # adjusting read as adapting / living with it
    "three": "alarm=A;adjusting=J;living=E,N",
}
csv.field_size_limit(10**9)


def parse(spec):
    groups = {}
    for part in spec.split(";"):
        name, bands = part.split("=")
        groups[name.strip()] = [b.strip() for b in bands.split(",")]
    used = [b for v in groups.values() for b in v]
    if sorted(used) != ["A", "E", "J", "N"]:
        raise SystemExit(f"each of A, J, E, N must be in exactly one group (got {used})")
    return groups


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


def city_shares(city, week, groups, band_col, without_big, big):
    w = {r["item_id"]: float(r["weight"]) for r in csv.DictReader(open(L / f"{city}_{week}_to_label.csv", encoding="utf-8"))}
    tot = {g: 0.0 for g in groups}
    for r in csv.DictReader(open(O / f"spectrum_labels_{city}_{week}_claude_draft.csv", encoding="utf-8")):
        if without_big and r["thread_id"] == big:
            continue
        for g, bands in groups.items():
            if r[band_col] in bands:
                tot[g] += w[r["item_id"]]
    d = sum(tot.values())
    return {g: 100 * v / d for g, v in tot.items()}


def run(name, spec, band_col, without_big):
    groups = parse(spec)
    pm = {r["city"]: r for r in csv.DictReader(open(PMN))}
    s1 = {r["city"]: r for r in csv.DictReader(open(S1)) if r["set"] == "event_9"}
    rows = []
    for c, s in s1.items():
        sh = city_shares(c, s["week"], groups, band_col, c in without_big, s["biggest_thread"])
        rows.append((c, float(pm[c]["ratio_to_normal"]), float(pm[c]["event_week_pm25"]), sh))
    rows.sort(key=lambda r: -r[1])
    print(f"\n## {name}: {spec}" + (f"   (without biggest thread: {', '.join(without_big)})" if without_big else "")
          + (f"   [bands from {band_col}]" if band_col != "band" else ""))
    print(f"{'city':<13}{'× normal':>9}{'µg/m³':>8}  " + "".join(f"{g:>13}" for g in groups))
    for c, ratio, pm25, sh in rows:
        print(f"{c:<13}{ratio:>9.1f}{pm25:>8.0f}  " + "".join(f"{sh[g]:>12.0f}%" for g in groups))
    print("Spearman rho (exploratory, draft labels, 9 cities):")
    for g in groups:
        v = [r[3][g] for r in rows]
        print(f"  {g:<12} with how unusual (ratio) {spearman([r[1] for r in rows], v):+.2f}   "
              f"with how bad (µg/m³) {spearman([r[2] for r in rows], v):+.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS))
    ap.add_argument("--groups", help='e.g. "reacting=A,J;living=E,N"')
    ap.add_argument("--without-big", default="", help="comma-separated cities to show without their biggest thread")
    ap.add_argument("--band-col", default="band", choices=["band", "band_before_rule8"])
    a = ap.parse_args()
    wb = [x for x in a.without_big.split(",") if x]
    if a.groups:
        run("custom", a.groups, a.band_col, wb)
    else:
        for n in ([a.preset] if a.preset else list(PRESETS)):
            run(n, PRESETS[n], a.band_col, wb)


if __name__ == "__main__":
    main()
