# How the tone labels were made, checked and corrected

How every worst-week Reddit post and comment about the air got a tone (Alarm, Adjusting, Enduring, Normalizing, or
not about the air), how Gina and Dish checked those labels by hand, and how the hand check was used to correct them.
These corrected counts are what the Boiling Frog page shows: the tone hills, the talk disks, the city cards.

Written 2026-10-07 from the scripts, the codebook, both data logs and the Air Talk Check page. Each step names its
script and files so it can be checked.

---

## In one paragraph

Claude labelled 2,161 air posts and comments by reading each one against a codebook Dish wrote. Gina and Dish then
coded a random 436 of them blind and reconciled their disagreements. Claude matched their agreed label 67% of the
time, below the bar set before the check. So instead of using Claude's labels as they are, every comment is counted
with a **correction**: the 436 checked comments keep Gina and Dish's label, and each of the other 1,725 is split
across the groups by how often its Claude label turned out to be each group in the hand check.

---

## The groups

| Code | Group | Meaning | Side |
|---|---|---|---|
| A | Alarm | the air is bad or strange right now | reacting |
| J | Adjusting | changing behaviour, or tools to check or clean the air | reacting |
| E | Enduring | harm told as ongoing or routine, without alarm | living with it |
| N | Normalizing | it's fine, always has been, or others overreact | living with it |
| X | Not about the air | the air word was incidental | never counted in shares |

The full codebook, with examples, edge-case rules and Rule 8, is
`data/processed/reddit/spectrum_02_labels/codebook.md`. Dish wrote the brief (`docs/claude_handoff-air-spectrum-labeling.md`).

---

## Step 1 · Find the air talk (script)

`scripts/reddit/spectrum_01_air_items.py`

- Source: the worst-week posts and comments for the nine cities, usernames removed (`data/processed/reddit/event_weeks_no_usernames/`).
- An item counts as air talk only if **its own text** matches the air word list (`data/lexicons/lexicon_air_v1.csv`,
  include + candidate terms, excludes applied). Being in an air thread doesn't count.
- The unit is one post or one comment. Long items get a short "hover text": the air sentences plus one either side.
- Result: **4,488 air items** across the nine weeks.
- Output: `data/processed/reddit/spectrum_01_air_items/<city>_<week>_air_items.csv`

## Step 2 · Decide which items get labelled (script)

`scripts/reddit/spectrum_02_sample.py`

- Weeks with up to 500 air items: **every item** is labelled (Bakersfield 55, Fairbanks 36, Fresno 82, Indianapolis 127,
  Detroit 319, San Jose 342).
- Weeks with more than 500: a **random sample of 400**, stratified by thread (Eugene 1,171, Seattle 1,213, Pittsburgh 1,143).
  Each thread with at least 5 air items is its own stratum and small threads are pooled; the sample is spread in
  proportion to stratum size. Each sampled item gets a **weight** = stratum size ÷ stratum sample (about 2.9), so shares
  can be scaled back to the full week. Approved by Dish, 2026-10-04.
- A random **10%** of each week's labelled items is set aside for a blind re-label (219 items).
- Seed 20261004 per week, so each draw can be repeated.
- Result: **2,161 items to label.**
- Output: `spectrum_02_labels/<name>_to_label.csv`, `<name>_relabel_ids.csv`, `sample_summary.csv`

## Step 3 · Claude labels every item (by reading, not by script)

This step is not a program. Claude read each item and chose one group, the way a human coder would.

- **One Claude helper (subagent) per city week**, asked to work in batches of about 150 and follow the codebook. For each item:
  the group, an "unsure" flag, and a one-line reason in plain words (paraphrased, no usernames).
- **Blind second pass:** a separate Claude helper re-labelled the 10% set without seeing the first answers.
  The two passes agreed on 182 of 219 items (83%; `spectrum_03_outputs/results.md`, after Rule 8).
- **Rule 8** (Dish, 2026-10-04: forecasts, maps and explanations of the air count as Adjusting): one more blind pass over
  422 keyword-caught candidates said yes to 185; **71 labels moved to Adjusting** (the old label is kept in
  `band_before_rule8`).
- Claude's working notes, flagged to Dish and written into the codebook: COVID masks are X; questions about what to do are J;
  fire news with no word about the air is X.
- Output: `spectrum_02_labels/<name>_labels_pass1.csv`, `_labels_pass2.csv`, `rule8_candidates.csv`, `rule8_decisions.csv`

**What can't be repeated exactly:** the instructions each helper was given were not saved beyond the brief and the
codebook, and a language model may not give the same label twice. What is saved is every label, every reason and
the codebook, so the labels can be checked, which is what Step 5 does.

## Step 4 · Turn the labels into shares (script)

`scripts/reddit/spectrum_03_outputs.py`

- Share of each group = its count ÷ (A + J + E + N). X is left out. The three sampled weeks use each item's weight.
- Also written: a skew check when one thread holds over 30% of a week (Bakersfield 47%, Fairbanks 36%), a sensitivity check
  using include-terms only, and a "check these first" list of uncertain items.
- Output: `spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv` (each item's Claude label), `results.md`, `summary.csv`

Claude's draft shares (A / J / E / N %): Bakersfield 29 / 10 / 43 / 18 · Detroit 57 / 36 / 2 / 6 · Eugene 45 / 50 / 2 / 4 ·
Fairbanks 37 / 49 / 0 / 14 · Fresno 61 / 19 / 14 / 6 · Indianapolis 66 / 24 / 1 / 10 · Pittsburgh 48 / 38 / 3 / 11 ·
San Jose 45 / 48 / 2 / 5 · Seattle 38 / 50 / 5 / 7.

## Step 5 · Gina and Dish check the labels by hand (the Air Talk Check)

Page: claude.ai/artifact/CTiUZAAjnXS2QfmYwor28i (private to Gina and Dish). Export of the codes:
`data/raw/reddit/air_talk_check/air_talk_check_codes_2026-10-05.csv`.

**The sample.** A simple random sample of 50 labelled items per city (all 36 in Fairbanks): **436 items**, every group
included, "not about the air" too. For the three sampled weeks the 50 come from the 400 Claude labelled. Drawn with seed
20261005 by `scripts/reddit/spectrum_06_validation_sample.py`. **That script is not in the repo yet** (possibly on Dish's computer).

**The rules, fixed on 2026-10-04 before anyone coded a card:**
1. Practice together on 15 cards that are not in the sample (Claude's label shown after each pick).
2. Code alone and blind: the same 436 cards in each coder's own random order, **Claude's label hidden**, no looking at
   each other's codes until both are done.
3. Reconcile together: only the cards coded differently; agree on one label or mark it Ambiguous.
4. Read the results against the bars:

| Check | Bar | Result | |
|---|---|---|---|
| Gina vs Dish, Cohen's κ (five groups) | ≥ 0.60 | **0.44** (56% agreement before reconciling) | below |
| Claude vs agreed label, reacting vs living with it | ≥ 80% overall | **75%** (likely range 71–79%) | below |
| same, Bakersfield only | ≥ 80% | **80%** (67–89%) | meets |
| Claude on items agreed to be Alarm or Adjusting | ≥ 80% | **74.5%** (68–80%) | below |
| Claude vs agreed label, all five groups | (reported) | **67%**, κ 0.57 | |

**Agreed labels:** 245 cards got the same label from both coders, and 191 were settled in Reconcile. None were marked
Ambiguous. Gina decided on 2026-10-05 to **keep these labels as final** (no relabelling after seeing results).

Per-city agreement is in `data/processed/reddit/spectrum_07_corrected/agreement.csv`
(e.g. Claude vs agreed: Fresno 82%, Bakersfield 78%, Indianapolis 58%).

**What this meant.** By the rules set beforehand, Claude's labels were not good enough to use as they were. Rather than
use only the ~50 checked items per city (too few), the hand check was used to correct all of Claude's labels (Step 6).
Gina chose this; Dish agreed the method on 2026-10-05.

## Step 6 · Correct every label with the hand check (script)

`scripts/reddit/spectrum_07_corrected_shares.py` (logged in `logs/data-log-gina.md`, "Reddit · tone, Step 1")

**The correction table.** From the 436 checked items: for each label Claude gave, how often the agreed label turned out
to be each group (pooled over all nine cities, because ~50 items per city is too few for a table each):

| When Claude said… | agreed Alarm | Adjusting | Enduring | Normalizing | Not about the air | (items checked) |
|---|---|---|---|---|---|---|
| Alarm | 61% | 5% | 28% | 2% | 4% | 137 |
| Adjusting | 18% | 68% | 9% | 1% | 5% | 130 |
| Enduring | 17% | 8% | 71% | 4% | 0% | 24 |
| Normalizing | 6% | 12% | 9% | 61% | 12% | 33 |
| Not about the air | 10% | 5% | 9% | 1% | 75% | 112 |

(`spectrum_07_corrected/confusion_matrix.csv`. The biggest pattern: Claude often called Enduring comments Alarm.)

**How each item counts:**
- **Checked item (436):** its agreed label, counted as 1.
- **Unchecked item (1,725):** split by its Claude label's row in the table. A comment Claude called Alarm counts as
  0.61 Alarm, 0.05 Adjusting, 0.28 Enduring, 0.02 Normalizing and 0.04 not about the air.
- **Sampled weeks:** each item also counts for its weight (about 2.9), so the 400 stand for the full week.
- A city's corrected count for a group = the sum over its items. X is then left out of the shares.

**Worked example, Eugene:** 400 labelled items (50 checked) → about 331 of them about the air after the correction →
× the weights ≈ **969** air comments in Eugene's hill, split across the four groups by the same table.

**Uncertainty.** 95% ranges come from a bootstrap: redraw the 436 checked items 2,000 times (seed 7), rebuild the table,
recompute. They show the uncertainty from the hand check only, not from the sampling of the big weeks.
Claude's choice, approved by Gina.

**Result, "living with it" share (Enduring + Normalizing), Claude draft → corrected (95% range):**

| City | Draft | Corrected |
|---|---|---|
| Bakersfield | 61% | 62% (61–64) |
| Indianapolis | 11% | 34% (31–38) |
| San Jose | 7% | 24% (21–28) |
| Pittsburgh | 14% | 31% (27–35) |
| Fresno | 19% | 35% (31–38) |
| Seattle | 12% | 28% (24–32) |
| Detroit | 8% | 27% (24–31) |
| Fairbanks | 14% | 16% (all items checked) |
| Eugene | 6% | 24% (21–28) |

The correction moves every city except Bakersfield and Fairbanks toward "living with it", mostly because Claude's
Alarm labels were often Enduring by Gina and Dish's reading. Bakersfield stays the clear outlier.

Output: `spectrum_07_corrected/city_shares.csv` (counts and shares, draft and corrected, with ranges),
`hand_check_items.csv`, `confusion_matrix.csv`, `agreement.csv`, `item_probabilities.csv`, `pairs_tone.csv`, `summary.md`.

---

## Where the page uses this

| On the page | Uses |
|---|---|
| tone hills, talk disks, city card tone shares, story disks | corrected counts (`city_shares.csv` → `scripts/site/02_tone_counts.py` → `site/data/tone-counts.js`) |
| quotes, words and word cloud plates | the 337 checked items not labelled X, with their agreed group (`scripts/site/01_hand_coded_comments.py`) |
| city card quotes | checked items first (agreed label), then Claude-labelled ones, marked "draft" (`scripts/site/04_card_quotes.py`) |

## Caveats

- **Tone is exploratory.** The pre-set test was about how much people talked about the air, not how they sounded.
- The hand check failed its own bars; the correction makes the counts more trustworthy but is a model, not a measurement.
- Gina and Dish themselves agreed only moderately (κ 0.44), so the codebook leaves room for judgment, especially between
  Alarm and Enduring and between Alarm and Adjusting.
- One correction table is used for all nine cities. It assumes Claude makes the same kinds of mistakes everywhere.
- Small cities rest on few comments: Fairbanks 32, Fresno 39, Bakersfield 51 (corrected, X left out).
- Bakersfield's profile leans on one thread ("how did the air affect you growing up", 47% of its air items).
- Weeks are UTC Monday–Sunday. Pittsburgh's comments miss the last 4.1 hours; Detroit's miss Sunday 8 pm–midnight.
- Not yet in the repo: the hand-check sampling script (`spectrum_06_validation_sample.py`), and the exact instructions
  given to the Claude labelling helpers.
