#!/usr/bin/env python3
"""
scripts/reddit/spectrum_04_dotmap_data.py

Builds the data file for the "From alarm to acceptance" dot map (viz/air-spectrum/), all 9 event weeks.
Display only: reads the Claude-draft outputs and PM2.5 numbers, changes no label or share.

Rules (Claude's choices, flagged):
  V1  Each dot = one labeled comment or post. In sampled weeks (Eugene, Seattle, Pittsburgh) a dot stands for
      about 3 comments; shares on the page are the weighted shares from spectrum_03_outputs/summary.csv.
  V2  Quotes stay short (Dish: short quotes only): the excerpt is the first sentence that matches an air term,
      cut to at most 30 words around the match. "u/[user]" handles are removed. No item IDs or thread IDs.
  V3  Bakersfield is shown with and without its biggest thread (Dish 2026-10-04: show both).
  V4  Cities are ordered by PM2.5 ratio to normal (how unusual the week was); the page can re-sort by
      absolute event-week PM2.5 (how bad it was).

Input (read only): data/processed/reddit/spectrum_03_outputs/{summary.csv, spectrum_labels_*_claude_draft.csv}
                   data/processed/openaq/step08_pm_normals/pm_normals.csv, data/lexicons/lexicon_air_v1.csv
Output: viz/air-spectrum/data.js   (local only: holds short quotes; gitignored)
Run from the repo root: python3 scripts/reddit/spectrum_04_dotmap_data.py
"""

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from study import load_topic_lexicon, flag_topic   # noqa: E402

O = Path("data/processed/reddit/spectrum_03_outputs")
PMN = Path("data/processed/openaq/step08_pm_normals/pm_normals.csv")
LEX = Path("data/lexicons/lexicon_air_v1.csv")
OUT = Path("viz/air-spectrum/data.js")
SENT = re.compile(r"(?<=[.!?…])\s+")
USER = re.compile(r"\bu/\[user\]\s*")
MAXW = 30
BANDS = ["A", "J", "E", "N"]
csv.field_size_limit(10**9)


def excerpt(hover, lex):
    t = USER.sub("", hover.replace("…", " ")).strip()
    sents = [s for s in SENT.split(t) if s.strip()] or [t]
    s = next((x for x in sents if flag_topic(x, lex)[1]), sents[0])
    words = s.split()
    if len(words) <= MAXW:
        return s, False, False
    pats = [p for _, p in lex["include"] + lex["candidate"]]
    hit = min((m.start() for p in pats for m in [p.search(s)] if m), default=0)
    at = len(s[:hit].split())
    lo = max(0, min(at - MAXW // 2, len(words) - MAXW))
    return " ".join(words[lo:lo + MAXW]), lo > 0, lo + MAXW < len(words)


def marks(text, lex):
    """Character spans of air-term matches, after excludes, for the page to underline."""
    t = text
    for _, p in lex["exclude"]:
        t = p.sub(lambda m: " " * len(m.group()), t)
    spans = sorted({(m.start(), m.end()) for _, p in lex["include"] + lex["candidate"] for m in p.finditer(t)})
    out = []
    for a, b in spans:
        if out and a < out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def main():
    lex = load_topic_lexicon(LEX)
    pm = {r["city"]: r for r in csv.DictReader(open(PMN))}
    summ = [r for r in csv.DictReader(open(O / "summary.csv")) if r["set"] == "event_9"]
    skew = {r["name"]: r for r in csv.DictReader(open(O / "skew.csv"))} if (O / "skew.csv").exists() else {}
    cities = []
    for s in summ:
        c, wk = s["city"], s["week"]
        p = pm[c]
        rows = list(csv.DictReader(open(O / f"spectrum_labels_{c}_{wk}_claude_draft.csv", encoding="utf-8")))
        big = s["biggest_thread"]
        items = []
        for r in rows:
            ex, pre, post = excerpt(r["hover_text"], lex)
            items.append({"b": r["band"], "u": int(r["claude_unsure"] == "yes"), "r": r["reason"], "t": ex,
                          "m": marks(ex, lex), "pre": int(pre), "post": int(post),
                          "big": int(r["thread_id"] == big)})
        un = {}
        for b in BANDS:
            band = [r for r in rows if r["band"] == b]
            un[b] = round(sum(r["claude_unsure"] == "yes" for r in band) / len(band), 3) if band else 0
        k = f"{c}_{wk}"
        cities.append({
            "key": c, "name": p["city_name"], "week_start": p["event_week_start"], "week_end": p["event_week_end"],
            "pm25": float(p["event_week_pm25"]), "pm25_normal": float(p["pm25_normal"]), "ratio": float(p["ratio_to_normal"]),
            "air_items": int(s["air_items"]), "labeled": int(s["labeled"]), "sampled": int(s["sampled"]),
            "shares": {b: float(s[f"share_{b}"]) for b in BANDS}, "unsure_frac": un,
            "x": int(s["x_labeled"]), "relabel": [int(s["relabel_agree"]), int(s["relabel_n"])],
            "big_share": float(s["biggest_thread_share_pct"]),
            "without_big": ({b: float(skew[k][f"without_{b}"]) for b in BANDS} if k in skew else None),
            "items": items})
    cities.sort(key=lambda d: -d["ratio"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Built by scripts/reddit/spectrum_04_dotmap_data.py. Claude-draft labels; short quotes only.\n"
                   "window.SPECTRUM = " + json.dumps({"cities": cities}, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(OUT, f"{OUT.stat().st_size/1e3:.0f} kB", [(d["key"], d["labeled"]) for d in cities])


if __name__ == "__main__":
    main()
