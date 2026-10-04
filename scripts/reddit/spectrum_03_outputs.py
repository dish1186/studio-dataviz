#!/usr/bin/env python3
"""
scripts/reddit/spectrum_03_outputs.py

Alarm -> Normalizing spectrum, Step 3: turn Claude's draft labels into the per-week outputs Dish reviews.
Nothing here decides a band; bands come from the hand-labeled pass files.

Rules:
  O1  Shares = A/J/E/N as a % of air items with X left out of the denominator. Sampled weeks
      (spectrum_02_sample.py) are weighted back to the full week with each item's stratum weight.
  O2  Re-label agreement = share of the 10% re-label items where the blind second pass gave the same band.
  O3  Skew check: if one thread holds > 30% of a week's air items, shares are also given without it.
  O4  Sensitivity: shares from include-term items only (include_hit = 1); a band moving > 10 pts is flagged.
  O5  "Check these first": (a) items whose two passes disagree, (b) unsure items in the week's top two bands
      when the gap between those bands is smaller than the share those unsure items carry (they could
      flip the headline), (c) every other unsure item.
  O7  Rule 8 (Dish 2026-10-04): items a single later pass judged to be mainly a forecast, map or explanation
      (spectrum_02_labels/rule8_decisions.csv, rule8 = yes) become J in both passes; the original band is kept
      in `band_before_rule8`. Pass files are not changed.
  O6  Comparison weeks (Eugene 2026-08-03, Bakersfield 2024-12-02 local) vs the old passage shares; a band
      moving > 10 pts is reported for the Forensics Appendix.

Input (read only): data/processed/reddit/spectrum_02_labels/<name>_{to_label,labels_pass1,labels_pass2,relabel_ids}.csv
                   data/processed/reddit/spectrum_01_air_items/summary.csv
Output: data/processed/reddit/spectrum_03_outputs/
  spectrum_labels_<city>_<weekstart>[_comparison]_claude_draft.csv   (local only: people's words)
  check_first.csv                                                    (local only: hover text)
  summary.csv, skew.csv, sensitivity.csv, passage_comparison.csv, results.md   (no quotes; tracked)
Run from the repo root: python3 scripts/reddit/spectrum_03_outputs.py   (weeks without a pass-1 file are skipped)
"""

import csv
from collections import Counter
from pathlib import Path

L = Path("data/processed/reddit/spectrum_02_labels")
S1 = Path("data/processed/reddit/spectrum_01_air_items/summary.csv")
OUT = Path("data/processed/reddit/spectrum_03_outputs")
BANDS = ["A", "J", "E", "N"]
OLD = {"eugene_2026-08-03_comparison": dict(A=32, J=54, E=6, N=9),
       "bakersfield_2024-12-02_comparison": dict(A=14, J=8, E=57, N=21)}
N_EVENT = 9
csv.field_size_limit(10**9)
DRAFT_COLS = ["item_id", "thread_id", "city", "week", "band", "claude_unsure", "reason", "hover_text", "full_text",
              "dish_review", "band_before_rule8"]


R8 = L / "rule8_decisions.csv"


def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def shares(rows):
    w = Counter()
    for r in rows:
        w[r["band"]] += float(r["weight"])
    d = sum(w[b] for b in BANDS)
    return {b: (round(100 * w[b] / d, 1) if d else None) for b in BANDS}, round(w["X"]), d


def fmt(s):
    return " / ".join("–" if s[b] is None else f"{s[b]:.0f}" for b in BANDS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s1 = {(r["city"], r["week"], r["set"]): r for r in read(S1)}
    r8 = {(r["week"], r["item_id"]): r for r in read(R8) if r["rule8"] == "yes"} if R8.exists() else {}
    names = sorted(p.name[:-len("_labels_pass1.csv")] for p in L.glob("*_labels_pass1.csv"))
    summ, skew, sens, comp, check, allrows = [], [], [], [], [], []
    for name in names:
        comparison = name.endswith("_comparison")
        city, week = name.replace("_comparison", "").split("_", 1)
        base = {r["item_id"]: r for r in read(L / f"{name}_to_label.csv")}
        p1 = {r["item_id"]: r for r in read(L / f"{name}_labels_pass1.csv")}
        missing = set(base) - set(p1)
        if missing or set(p1) - set(base):
            raise SystemExit(f"{name}: pass 1 ids do not match the items to label ({len(missing)} missing)")
        bad = {r["band"] for r in p1.values()} - set(BANDS + ["X"])
        if bad:
            raise SystemExit(f"{name}: unknown bands {bad}")
        rows = [dict(base[i], **{k: p1[i][k] for k in ("band", "claude_unsure", "reason")}, band_before_rule8=p1[i]["band"])
                for i in base]
        for r in rows:
            if (name, r["item_id"]) in r8 and r["band"] != "X":
                if r["band"] != "J":
                    r["reason"] = f"Rule 8 (forecast/explanation): {r8[(name, r['item_id'])]['reason']}"
                r["band"] = "J"
        allrows += rows
        with open(OUT / f"spectrum_labels_{name}_claude_draft.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=DRAFT_COLS, extrasaction="ignore"); w.writeheader()
            w.writerows(dict(r, city=city, week=week, dish_review="") for r in rows)

        sh, xw, denom = shares(rows)
        p2p = L / f"{name}_labels_pass2.csv"
        p2 = {r["item_id"]: r for r in read(p2p)} if p2p.exists() else {}
        for i, r in p2.items():
            if (name, i) in r8 and r["band"] != "X":
                r["band"] = "J"
        agree = sum(p2[i]["band"] == p1[i]["band"] for i in p2 if i in p1)
        info = s1[(city, week, "comparison" if comparison else "event_9")]
        top = sorted(BANDS, key=lambda b: -(sh[b] or 0))
        summ.append({"city": city, "week": week, "set": "comparison" if comparison else "event_9",
                     "air_items": info["air_items"], "labeled": len(rows), "sampled": int(len(rows) < int(info["air_items"])),
                     **{f"share_{b}": sh[b] for b in BANDS}, "headline_band": top[0],
                     "x_labeled": sum(r["band"] == "X" for r in rows), "x_weighted": xw,
                     "unsure": sum(r["claude_unsure"] == "yes" for r in rows),
                     "relabel_n": len(p2), "relabel_agree": agree,
                     "relabel_agree_pct": round(100 * agree / len(p2), 1) if p2 else "",
                     "biggest_thread": info["biggest_thread"], "biggest_thread_share_pct": info["biggest_thread_share_pct"]})

        if float(info["biggest_thread_share_pct"]) > 30:
            sw, _, _ = shares([r for r in rows if r["thread_id"] != info["biggest_thread"]])
            skew.append({"name": name, "thread": info["biggest_thread"], "thread_share_pct": info["biggest_thread_share_pct"],
                         **{f"with_{b}": sh[b] for b in BANDS}, **{f"without_{b}": sw[b] for b in BANDS}})

        si, _, di = shares([r for r in rows if r["include_hit"] == "1"])
        moves = {b: (round(si[b] - sh[b], 1) if si[b] is not None and sh[b] is not None else None) for b in BANDS}
        sens.append({"name": name, "include_only_air_not_x": round(di), **{f"all_{b}": sh[b] for b in BANDS},
                     **{f"incl_{b}": si[b] for b in BANDS},
                     "flag_over_10": ";".join(b for b in BANDS if moves[b] is not None and abs(moves[b]) > 10)})

        if name in OLD:
            for b in BANDS:
                comp.append({"name": name, "band": b, "old_passage_pct": OLD[name][b], "new_comment_pct": sh[b],
                             "move_pts": round(sh[b] - OLD[name][b], 1), "over_10": int(abs(sh[b] - OLD[name][b]) > 10)})

        gap = (sh[top[0]] or 0) - (sh[top[1]] or 0)
        uns_top = [r for r in rows if r["claude_unsure"] == "yes" and r["band"] in top[:2]]
        uns_top_pct = 100 * sum(float(r["weight"]) for r in uns_top) / denom if denom else 0
        flip = uns_top_pct >= gap
        for r in rows:
            i = r["item_id"]
            why = []
            if i in p2 and p2[i]["band"] != r["band"]:
                why.append(f"passes disagree ({r['band']} vs {p2[i]['band']})")
            if r["claude_unsure"] == "yes":
                why.append("could flip headline" if (flip and r["band"] in top[:2]) else "unsure")
            if why:
                rank = 0 if "passes disagree" in why[0] else (1 if "could flip headline" in why else 2)
                check.append({"rank": rank, "name": name, "item_id": i, "thread_id": r["thread_id"], "band": r["band"],
                              "why": "; ".join(why), "reason": r["reason"], "hover_text": r["hover_text"]})

    def write(fn, rows):
        if rows:
            with open(OUT / fn, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    check.sort(key=lambda r: (r["rank"], r["name"], r["item_id"]))
    for fn, rows in [("summary.csv", summ), ("skew.csv", skew), ("sensitivity.csv", sens),
                     ("passage_comparison.csv", comp), ("check_first.csv", check)]:
        write(fn, rows)

    ev = [r for r in summ if r["set"] == "event_9"]
    tag = f"{len(ev)}/{N_EVENT} event weeks" + ("" if len(ev) == N_EVENT else " — PARTIAL")
    md = [f"# Air spectrum: Claude draft labels ({tag})", "",
          "Generated by `scripts/reddit/spectrum_03_outputs.py`. **Labels are Claude drafts until Dish fills in "
          "`dish_review`. Shares are within-city** (A / J / E / N as % of air items, X left out). "
          "Pittsburgh comments miss the last 4.1 h of the week. Weeks are UTC Monday–Sunday. "
          f"Rule 8 (forecasts and explanations are J) moved {sum(r['band'] != r['band_before_rule8'] for r in allrows)} items.", "",
          "| City | Week | Air items | Labeled | A / J / E / N % | X (labeled) | Unsure | Re-label agree | Biggest thread |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in summ:
        md.append(f"| {r['city']}{' (comparison)' if r['set'] == 'comparison' else ''} | {r['week']} | {r['air_items']} | "
                  f"{r['labeled']}{' (sample)' if r['sampled'] else ''} | {fmt({b: r['share_' + b] for b in BANDS})} | "
                  f"{r['x_labeled']} | {r['unsure']} | {r['relabel_agree']}/{r['relabel_n']} | {r['biggest_thread_share_pct']}% |")
    if skew:
        md += ["", "## Skew check (one thread > 30% of air items)", "", "| Week | Thread share | With | Without |", "|---|---|---|---|"]
        md += [f"| {s['name']} | {s['thread_share_pct']}% | {fmt({b: s['with_' + b] for b in BANDS})} | "
               f"{fmt({b: s['without_' + b] for b in BANDS})} |" for s in skew]
    md += ["", "## Sensitivity: include-term items only", "", "| Week | All air items | Include-only | Bands moving > 10 pts |", "|---|---|---|---|"]
    md += [f"| {s['name']} | {fmt({b: s['all_' + b] for b in BANDS})} | {fmt({b: s['incl_' + b] for b in BANDS})} | "
           f"{s['flag_over_10'] or '–'} |" for s in sens]
    if comp:
        md += ["", "## Forensics: passages (old) vs whole comments (new)", "", "| Week | Band | Old % | New % | Move |", "|---|---|---|---|---|"]
        md += [f"| {c['name']} | {c['band']} | {c['old_passage_pct']} | {c['new_comment_pct']} | "
               f"{c['move_pts']:+}{' ⚑' if c['over_10'] else ''} |" for c in comp]
    md += ["", f"Check-these-first list: `check_first.csv` ({len(check)} items, local only)."]
    (OUT / "results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
