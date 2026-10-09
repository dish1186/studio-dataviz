"""Site step 4: the quotes shown in each city card (up to 3 per city and tone group).

This is the code that built the card quotes on 2026-10-06 (run in the chat at the time), saved here so it can be re-run.

From every worst-week air item with a Claude draft label (spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv):
  1. clean the text: drop links, replace "u/name" with "someone", collapse spaces (usernames were already removed upstream)
  2. keep it only if it is 50 to 230 characters long, has none of the words in BAD, and is at most 40% capital letters
  3. group = the agreed label where Gina and Dish hand-checked the item (spectrum_07_corrected/hand_check_items.csv,
     marked "checked"), otherwise Claude's draft label ("draft"); X (not about the air) is dropped
  4. per city and group, sort: hand-checked first, then closest to 140 characters, then alphabetically; keep the first 3
All four rules are Claude's choices from when the card was built (approved by Gina 2026-10-07).
Output: site/data/quotes.js, window.QUOTES = {city: {group: [{t, h}, ...]}}. Run from the repo root:
    python3 scripts/site/04_card_quotes.py
"""
import collections
import csv
import glob
import re
import sys

sys.path.insert(0, "scripts/site")
from _stamp import write_js

csv.field_size_limit(10**9)
HAND = "data/processed/reddit/spectrum_07_corrected/hand_check_items.csv"
DRAFTS = sorted(f for f in glob.glob("data/processed/reddit/spectrum_03_outputs/spectrum_labels_*_claude_draft.csv") if "comparison" not in f)
BAD = re.compile(r"\b(fuck\w*|shit\w*|bitch\w*|damn|ass|asshole|crap|hell|idiot\w*|stupid|hypocrite\w*|retard\w*|dick\w*)\b", re.I)
MIN_LEN, MAX_LEN, TARGET_LEN, MAX_CAPS, PER_GROUP = 50, 230, 140, .4, 3

agreed = {r["item_id"]: r["agreed_band"] for r in csv.DictReader(open(HAND, encoding="utf-8"))}


def clean(t):
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"/?u/[A-Za-z0-9_-]+", "someone", t)
    return re.sub(r"\s+", " ", t).strip()


Q = collections.defaultdict(lambda: collections.defaultdict(list))
for f in DRAFTS:
    for r in csv.DictReader(open(f, encoding="utf-8")):
        t = clean(r["full_text"])
        if not (MIN_LEN <= len(t) <= MAX_LEN) or BAD.search(t) or sum(ch.isupper() for ch in t) > len(t) * MAX_CAPS:
            continue
        b, how = agreed.get(r["item_id"]), "checked"
        if b is None:
            b, how = r["band"], "draft"
        if b not in ("A", "J", "E", "N"):
            continue
        Q[r["city"]][b].append((0 if how == "checked" else 1, abs(len(t) - TARGET_LEN), t, how))

out, src = {}, collections.Counter()
for c, d in Q.items():
    out[c] = {}
    for b, lst in d.items():
        lst.sort()
        out[c][b] = [{"t": x[2], "h": x[3]} for x in lst[:PER_GROUP]]
        src.update(x[3] for x in lst[:PER_GROUP])

write_js("site/data/quotes.js", "QUOTES", out, "scripts/site/04_card_quotes.py", [HAND, *DRAFTS],
         notes=["h = checked (agreed label from the hand check) or draft (Claude's label)."])
print(dict(src))
