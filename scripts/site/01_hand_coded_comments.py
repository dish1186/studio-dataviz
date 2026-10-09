"""Site step 1: the 337 hand-coded comments used by the comment, word and word-cloud plates.

Which comments: every item Gina and Dish both labelled in the Air Talk Check
(data/processed/reddit/spectrum_07_corrected/hand_check_items.csv, 436 items) except the ones whose agreed label is
X (not about the air). Group = agreed_band (A Alarm, J Adjusting, E Enduring, N Normalizing).
Text: full_text from data/processed/reddit/spectrum_01_air_items/<city>_<week>_air_items.csv, matched on item_id
(usernames were removed upstream). Texts longer than 1,500 characters are cut to 1,500 plus "…" (as on the page).
Order: city, then group letter, then item id (the order of the published page; the quote layout depends on it).
f = 1 marks the 12 quotes Gina and Dish flagged as interesting (drawn larger). The list is not in a repo file yet, so it is COPIED
below from the published page (snapshot d689e08, site/index.html). To do: save it as a raw file and read it from there.

Output: site/data/hand-coded-comments.js, window.HAND_CODED = [{id, c, b, t}, ...]
Replaces the inline <script id="qdata"> block in site/index.html. Run from the repo root:
    python3 scripts/site/01_hand_coded_comments.py
"""
import csv
import glob
import sys

sys.path.insert(0, "scripts/site")
from _stamp import write_js

csv.field_size_limit(10**9)
HAND = "data/processed/reddit/spectrum_07_corrected/hand_check_items.csv"
ITEMS = sorted(f for f in glob.glob("data/processed/reddit/spectrum_01_air_items/*_air_items.csv") if "comparison" not in f)
MAX_CHARS = 1500   # longest text shown; the page's limit, kept as published
FLAGGED = {"m0saap8", "m0a3ptw", "oxvt5sk", "oxw2rj4", "oy74qw8", "g4g4ytv", "jq214yu", "1uyb92f", "g24cv7o", "g4f8gtk", "g5458t5", "g54yihm"}   # COPIED, see above

hand = [r for r in csv.DictReader(open(HAND, encoding="utf-8")) if r["agreed_band"] != "X"]
text, used = {}, set()
for f in ITEMS:
    for r in csv.DictReader(open(f, encoding="utf-8")):
        text[(r["item_id"], r["city"], r["week"])] = (r["full_text"], f)

rows = []
for r in hand:
    t, f = text[(r["item_id"], r["city"], r["week"])]
    used.add(f)
    row = {"id": r["item_id"], "c": r["city"], "b": r["agreed_band"], "t": t if len(t) <= MAX_CHARS else t[:MAX_CHARS] + "…"}
    if r["item_id"] in FLAGGED:
        row["f"] = 1
    rows.append(row)
rows.sort(key=lambda x: (x["c"], x["b"], x["id"]))

assert len(rows) == 337, len(rows)
assert all(x["b"] in "AJEN" for x in rows)
assert sum("f" in x for x in rows) == len(FLAGGED), "a flagged quote is missing"
cut = [x["id"] for x in rows if x["t"].endswith("…") and len(x["t"]) == MAX_CHARS + 1]
write_js("site/data/hand-coded-comments.js", "HAND_CODED", rows, "scripts/site/01_hand_coded_comments.py", [HAND, *used],
         notes=[f"{len(rows)} comments: the hand-checked items minus agreed label X. Cut to {MAX_CHARS} characters: {', '.join(cut) or 'none'}.",
                f"f = 1 marks the {len(FLAGGED)} quotes Gina and Dish flagged as interesting; the list is COPIED from the published page (not yet in a repo file)."])
print(len(rows), "comments;", "cut:", cut)
