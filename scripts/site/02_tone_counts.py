"""Site step 2: comment counts per tone group for every city (the tone hills, talk disks, pair groupings and story disks).

Groups: A Alarm, J Adjusting, E Enduring, N Normalizing. X (not about the air) is counted only in air_items.
  corrected   corrected counts: spectrum_07_corrected/city_shares.csv, method = corrected, count_A..count_N
              (scripts/reddit/spectrum_07_corrected_shares.py: hand-checked items keep the agreed label, the rest are split by
              how often Claude's label matched it; sampled weeks weighted back to the full week). Kept to 2 decimals as in the file.
  draft_read  Claude draft labels, one per labelled item: spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv, band
  draft_est   the same, weighted back to the full week: city_shares.csv, method = claude_draft, count_A..count_N, rounded to 1 decimal
  big_thread  draft counts in the city's biggest thread = the thread with the most labelled items, weighted with the sampling
              weights in spectrum_02_labels/<city>_<week>_to_label.csv (1 where a week was not sampled), rounded to 1 decimal
  air_items   all worst-week air items before sampling, X included: rows in spectrum_01_air_items/<city>_<week>_air_items.csv
              (the three big weeks, Eugene, Seattle and Pittsburgh, were sampled down to 400 items for labelling)
Output: site/data/tone-counts.js, window.TONE = {corrected, draft_read, draft_est, big_thread, air_items}, each {city: ...}.
Replaces CORR and C (js/how-they-talked.js), SPEC (js/plates-shared.js) and DATA.cnt (js/story-same-air.js).
Run from the repo root:  python3 scripts/site/02_tone_counts.py
"""
import collections
import csv
import glob
import sys

sys.path.insert(0, "scripts/site")
from _stamp import write_js

csv.field_size_limit(10**9)
B = "AJEN"
SHARES = "data/processed/reddit/spectrum_07_corrected/city_shares.csv"
DRAFTS = sorted(f for f in glob.glob("data/processed/reddit/spectrum_03_outputs/spectrum_labels_*_claude_draft.csv") if "comparison" not in f)

shares = list(csv.DictReader(open(SHARES, encoding="utf-8")))
corrected = {r["city"]: [round(float(r["count_" + b]), 2) for b in B] for r in shares if r["method"] == "corrected"}
draft_est = {r["city"]: {b: round(float(r["count_" + b]), 1) for b in B} for r in shares if r["method"] == "claude_draft"}

inputs = [SHARES, *DRAFTS]
draft_read, big_thread, air_items = {}, {}, {}
for f in DRAFTS:
    rows = list(csv.DictReader(open(f, encoding="utf-8")))
    city, week = rows[0]["city"], rows[0]["week"]
    weights = {}
    for w in glob.glob(f"data/processed/reddit/spectrum_02_labels/{city}_{week}_to_label.csv"):
        inputs.append(w)
        weights = {r["item_id"]: float(r["weight"] or 1) for r in csv.DictReader(open(w, encoding="utf-8"))}
    n = collections.Counter(r["band"] for r in rows)
    draft_read[city] = {b: n[b] for b in B}
    items_f = f"data/processed/reddit/spectrum_01_air_items/{city}_{week}_air_items.csv"
    inputs.append(items_f)
    air_items[city] = sum(1 for _ in csv.DictReader(open(items_f, encoding="utf-8")))
    biggest = collections.Counter(r["thread_id"] for r in rows).most_common(1)[0][0]
    big = collections.Counter()
    for r in rows:
        if r["thread_id"] == biggest:
            big[r["band"]] += weights.get(r["item_id"], 1)
    big_thread[city] = {b: round(big[b], 1) for b in B}

assert set(corrected) == set(draft_read) == set(draft_est), (sorted(corrected), sorted(draft_read))
out = {"corrected": corrected, "draft_read": draft_read, "draft_est": draft_est, "big_thread": big_thread, "air_items": air_items}
write_js("site/data/tone-counts.js", "TONE", out, "scripts/site/02_tone_counts.py", inputs,
         notes=["biggest thread = most labelled items in one thread (Claude's choice when the page was built; approved by Gina 2026-10-07)."])
for c in sorted(corrected):
    print(c, "corrected", corrected[c], "read", draft_read[c], "big", big_thread[c], "air", air_items[c])
