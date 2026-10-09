#!/usr/bin/env python3
"""
scripts/reddit/spectrum_07_corrected_shares.py

Correct Claude's draft tone labels with Gina and Dish's hand check (the Air Talk Check, Oct 4 2026), and write
each city's corrected tone shares.

Why: in the hand check, Claude's label matched the agreed label on about two thirds of items, below the bar set
before the check. Rather than use the drafts as they are, or only the ~50 checked items per city, every item is
counted as follows (hybrid calibration):
  - checked item (436): the agreed label. Same label from both coders, or the label they settled on in
    Reconcile (Gina decided 2026-10-05 to keep these labels as final).
  - unchecked item (1,725): spread over the five groups by how often each Claude label turned out to be each
    agreed label among the checked items. One table pooled over all nine cities (about 50 checked items per city
    is too few for a table per city). Claude's choice, approved by Gina.
Bands: A Alarm, J Adjusting, E Enduring, N Normalizing, X not about the air. Shares leave X out of the denominator
and weight sampled weeks (Eugene, Seattle, Pittsburgh) back to the full week, the same rules as spectrum_03/05.

Ranges: 95% ranges for each corrected share come from a bootstrap that redraws the 436 checked items
(2,000 rounds, seed 7) and rebuilds the table each time. They show the uncertainty from the hand check only,
not from the sampling of the three big weeks. Claude's choice, approved by Gina.

The pair and "used to it" tables are EXPLORATORY: tone was not part of the pre-set pair test
(analysis_01 tested the amount of air talk). "Used to it" = the city's median number of days a year at or above
35.5 µg/m³ (2019-2025) is 8 or more, the default of the slider on Dish's Boiling Frog Pots page.

Input (read only):
  data/raw/reddit/air_talk_check/air_talk_check_codes_2026-10-05.csv     both coders' codes + agreed labels
  data/processed/reddit/spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv   Claude's bands
  data/processed/reddit/spectrum_02_labels/<city>_<week>_to_label.csv    sampling weights
  data/processed/reddit/analysis_01/cities.csv                            PM2.5 ratio, bad days per year
  data/processed/reddit/analysis_01/pairs.csv                             the 9 pairs
Output: data/processed/reddit/spectrum_07_corrected/
  hand_check_items.csv     436 checked items: city, weight, Claude's band, each coder's band, agreed band (codes only)
  confusion_matrix.csv     Claude's band x agreed band: counts and row shares (the correction table)
  agreement.csv            Gina vs Dish, Claude vs agreed: percent agreement and Cohen's kappa, overall and by city
  item_probabilities.csv   all 2,161 items: checked or not, weight, Claude's band, probability of each group
  city_shares.csv          per city, Claude draft vs corrected: weighted counts, 4-group, 3-group and 2-group shares,
                           95% ranges for the corrected shares
  pairs_tone.csv           EXPLORATORY: each pair's "living with it" share, draft and corrected, and the used-to-it check
  summary.md               plain-language summary
Run from the repo root: python3 scripts/reddit/spectrum_07_corrected_shares.py   (local files only)
"""

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path("data/raw/reddit/air_talk_check/air_talk_check_codes_2026-10-05.csv")
LAB = Path("data/processed/reddit/spectrum_03_outputs")
WTS = Path("data/processed/reddit/spectrum_02_labels")
A01 = Path("data/processed/reddit/analysis_01")
OUT = Path("data/processed/reddit/spectrum_07_corrected")
BANDS = ["A", "J", "E", "N", "X"]
AIR = ["A", "J", "E", "N"]
GROUPS = {"four": {"alarm": "A", "adjusting": "J", "enduring": "E", "normalizing": "N"},
          "three": {"alarm": "A", "adjusting": "J", "living": "EN"},
          "two": {"reacting": "AJ", "living": "EN"}}
BOOT, SEED = 2000, 7          # Claude's choice, approved by Gina
USED_TO_IT_DAYS = 8           # Dish's Pots page default; Claude's choice to reuse it, approved by Gina
csv.field_size_limit(10**9)


def read(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] / n * cb[k] / n for k in BANDS)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


# ---------- inputs ----------
items = {}                                   # item_id -> city, week, weight, claude band
for f in sorted(LAB.glob("spectrum_labels_*_claude_draft.csv")):
    if "comparison" in f.name:
        continue
    for r in read(f):
        items[r["item_id"]] = {"city": r["city"], "week": r["week"], "claude": r["band"]}
for f in sorted(WTS.glob("*_to_label.csv")):
    if "comparison" in f.name:
        continue
    for r in read(f):
        if r["item_id"] in items:
            items[r["item_id"]]["weight"] = float(r["weight"])
assert all("weight" in v for v in items.values()), "an item has no sampling weight"

checked = {}                                 # item_id -> agreed band (AMB = no agreed label: treated as unchecked)
hc_rows = []
for r in read(RAW):
    i = r["item_id"]
    assert i in items, f"checked item {i} not in Claude's labels"
    same = r["dish_band"] == r["gina_band"]
    agreed = r["dish_band"] if same else r["reconciled_band"]
    assert agreed, f"item {i}: coders differ and no reconciled label"
    if agreed != "AMB":
        checked[i] = agreed
    v = items[i]
    hc_rows.append({"item_id": i, "city": v["city"], "week": v["week"], "weight": v["weight"], "claude_band": v["claude"],
                    "dish_band": r["dish_band"], "gina_band": r["gina_band"], "agreed_band": agreed,
                    "agreed_by": "same label" if same else "reconciled"})


def table(ids):
    """Row shares: P(agreed band | Claude band), from the checked items given."""
    c = defaultdict(Counter)
    for i in ids:
        c[items[i]["claude"]][checked[i]] += 1
    return {b: {k: c[b][k] / sum(c[b].values()) for k in BANDS} if c[b] else None for b in BANDS}, c


def corrected_counts(P, chk):
    """Weighted counts per city and band: agreed label for checked items, P[Claude band] for the rest."""
    out = defaultdict(lambda: dict.fromkeys(BANDS, 0.0))
    for i, v in items.items():
        if i in chk:
            out[v["city"]][chk[i]] += v["weight"]
        else:
            for k in BANDS:
                out[v["city"]][k] += v["weight"] * P[v["claude"]][k]
    return out


def shares(cnt):
    t = sum(cnt[k] for k in AIR)
    res = {"air_items": t}
    for g, spec in GROUPS.items():
        for name, ks in spec.items():
            res[f"{g}_{name}"] = sum(cnt[k] for k in ks) / t if t else float("nan")
    return res


# ---------- correction table and agreement ----------
P, C = table(checked)
assert all(P[b] for b in BANDS), "a Claude band never appears among the checked items"
write("hand_check_items.csv", hc_rows)
write("confusion_matrix.csv", [{"claude_band": b, "n_checked": sum(C[b].values()),
                                **{f"agreed_{k}": C[b][k] for k in BANDS},
                                **{f"share_{k}": round(P[b][k], 4) for k in BANDS}} for b in BANDS])

agree = []
for scope in ["all"] + sorted({r["city"] for r in hc_rows}):
    rows = [r for r in hc_rows if scope == "all" or r["city"] == scope]
    po, k = kappa([(r["gina_band"], r["dish_band"]) for r in rows])
    agree.append({"comparison": "gina_vs_dish", "scope": scope, "n": len(rows), "agreement": round(po, 3), "kappa": round(k, 3)})
    rows = [r for r in rows if r["agreed_band"] != "AMB"]
    po, k = kappa([(r["claude_band"], r["agreed_band"]) for r in rows])
    agree.append({"comparison": "claude_vs_agreed", "scope": scope, "n": len(rows), "agreement": round(po, 3), "kappa": round(k, 3)})
write("agreement.csv", agree)

write("item_probabilities.csv", [{"item_id": i, "city": v["city"], "weight": v["weight"], "checked": int(i in checked),
                                  "claude_band": v["claude"],
                                  **{f"p_{k}": (1.0 if checked[i] == k else 0.0) if i in checked else round(P[v["claude"]][k], 4)
                                     for k in BANDS}} for i, v in items.items()])

# ---------- city shares, with bootstrap ranges ----------
draft = defaultdict(lambda: dict.fromkeys(BANDS, 0.0))
for v in items.values():
    draft[v["city"]][v["claude"]] += v["weight"]
corr = corrected_counts(P, checked)

rng = random.Random(SEED)
ids = list(checked)
boot = defaultdict(lambda: defaultdict(list))
for _ in range(BOOT):
    pick = [rng.choice(ids) for _ in ids]
    Pb = table(pick)[0]
    Pb = {b: Pb[b] or P[b] for b in BANDS}   # a band missing from a redraw keeps the full-sample row
    for city, cnt in corrected_counts(Pb, checked).items():   # checked items keep their labels; only the table is redrawn
        for k, val in shares(cnt).items():
            boot[city][k].append(val)

meta = {r["city"]: r for r in read(A01 / "cities.csv")}
city_rows = []
for city in sorted(corr, key=lambda c: float(meta[c]["pm25_ratio"])):
    for method, cnt in (("claude_draft", draft[city]), ("corrected", corr[city])):
        s = shares(cnt)
        row = {"city": city, "pm25_ratio": meta[city]["pm25_ratio"], "bad_days_per_year": meta[city]["bad_days_per_year"],
               "method": method, "n_checked": sum(1 for i in checked if items[i]["city"] == city),
               **{f"count_{k}": round(cnt[k], 2) for k in BANDS}, "air_items": round(s.pop("air_items"), 2)}
        for k, val in s.items():
            row[k] = round(val, 4)
            if method == "corrected":
                b = sorted(boot[city][k])
                row[k + "_lo"], row[k + "_hi"] = round(b[int(.025 * BOOT)], 4), round(b[int(.975 * BOOT) - 1], 4)
            else:
                row[k + "_lo"] = row[k + "_hi"] = ""
        city_rows.append(row)
write("city_shares.csv", city_rows)

# ---------- EXPLORATORY: pairs and "used to it" ----------
liv = {(r["city"], r["method"]): r["two_living"] for r in city_rows}
pair_rows = []
for p in read(A01 / "pairs.csv"):
    a, b = p["worse_air_city"], p["other_city"]
    ra, rb = float(meta[a]["pm25_ratio"]), float(meta[b]["pm25_ratio"])
    hi, lo = (a, b) if ra > rb else (b, a)
    used = {c: float(meta[c]["bad_days_per_year"]) >= USED_TO_IT_DAYS for c in (a, b)}
    row = {"type": p["type"], "worse_air_city": a, "other_city": b, "more_unusual_city": hi,
           "used_to_it_cities": ";".join(c for c in (a, b) if used[c]), "exploratory": 1}
    for m in ("claude_draft", "corrected"):
        row[f"living_worse_air_{m}"] = liv[(a, m)]
        row[f"living_other_{m}"] = liv[(b, m)]
        row[f"more_unusual_lives_with_it_less_{m}"] = int(liv[(hi, m)] < liv[(lo, m)])
        if used[a] != used[b]:
            u, n = (a, b) if used[a] else (b, a)
            row[f"used_to_it_lives_with_it_more_{m}"] = int(liv[(u, m)] > liv[(n, m)])
        else:
            row[f"used_to_it_lives_with_it_more_{m}"] = ""
    pair_rows.append(row)
write("pairs_tone.csv", pair_rows)

# ---------- summary ----------
g = {r["scope"] + r["comparison"]: r for r in agree}
L = ["# Corrected tone shares (spectrum_07)", "",
     f"Checked items: {len(checked)} of {len(items)} air items. Gina vs Dish: {g['allgina_vs_dish']['agreement']:.0%} agreement, "
     f"kappa {g['allgina_vs_dish']['kappa']}. Claude vs agreed label: {g['allclaude_vs_agreed']['agreement']:.0%}, "
     f"kappa {g['allclaude_vs_agreed']['kappa']}.", "",
     "| City | x normal | Claude draft: reacting / living | Corrected: reacting / living | Corrected living, 95% range |",
     "|---|---|---|---|---|"]
for city in dict.fromkeys(r["city"] for r in city_rows):
    d = next(r for r in city_rows if r["city"] == city and r["method"] == "claude_draft")
    c = next(r for r in city_rows if r["city"] == city and r["method"] == "corrected")
    L.append(f"| {city} | {float(d['pm25_ratio']):.1f} | {d['two_reacting']:.0%} / {d['two_living']:.0%} | "
             f"{c['two_reacting']:.0%} / {c['two_living']:.0%} | {c['two_living_lo']:.0%}-{c['two_living_hi']:.0%} |")
for m in ("claude_draft", "corrected"):
    k = sum(r[f"more_unusual_lives_with_it_less_{m}"] for r in pair_rows)
    mix = [r for r in pair_rows if r[f"used_to_it_lives_with_it_more_{m}"] != ""]
    L.append(f"\nEXPLORATORY ({m}): more unusual city lives with it less in {k} of {len(pair_rows)} pairs; "
             f"used-to-it city lives with it more in {sum(r[f'used_to_it_lives_with_it_more_{m}'] for r in mix)} of {len(mix)} mixed pairs.")
(OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
print("DONE")
