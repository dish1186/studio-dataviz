# Boiling Frog · site

The freestanding version of the Boiling Frog page (Dish Chowdhury and Gina Hollenbach, MDE Studio, Oct 2026).

## Status: step 3 of 6 done (2026-10-07)

1. **Snapshot** (commit `d689e08`): an unchanged copy of the published artifact, version 94
   (claude.ai/artifact/J3fSoj9QZQjDP9RPoJHmiV, version id 1791318584-8639). `tools/snapshot-d689e08.sha256` holds the
   checksum of every file in that commit. To check the snapshot:
   `mkdir /tmp/snap && git archive d689e08 site | tar -x -C /tmp/snap && cd /tmp/snap/site && shasum -a 256 -c MANIFEST.sha256`
2. **Split** (this commit): the page's style and script blocks moved into their own files by `tools/split_page.py`,
   which reads the snapshot straight from git, so the split can be re-run and checked. Behaviour is unchanged:
   - with reduced motion, screenshots of the old and new page at 45 positions from top to bottom are pixel-identical,
     and the city card is pixel-identical for Bakersfield, Indianapolis and Eugene;
   - with full motion, the only differences are the trembling and drifting words in the comment and word plates,
     which move on the clock; page height, element count (±12 animated specks) and errors (none) match.

The only edits `split_page.py` makes, all needed because code moved into files:
- `url("img/…")` in CSS now reads `url("../img/…")` (CSS paths resolve from the CSS file);
- the libraries load from `js/lib/` (pinned copies of the same cdnjs versions) instead of cdnjs;
- the data files load from `data/` (moved, contents unchanged).

**Comments on calculations and sources** (separate commit, 2026-10-07). 145 comment lines were added on top of the split;
no code changed (checked line by line against the `split_page.py` output, and again pixel-identical with the snapshot).
Search the code for these markers:
- `CALCULATION` — the formula behind a number on the page, with the upstream script and column it comes from;
- `DATA` — numbers or text typed into the code or markup, with the file they were copied from;
- `No data calculations in this file` — files that only do layout and motion.

The source of the 337 hand-coded comments is written above `<script id="qdata">` in `index.html`: which items
(`spectrum_07_corrected/hand_check_items.csv` minus the 99 marked X), which label (`agreed_band`) and where the text
comes from (`spectrum_01_air_items/<city>_<week>_air_items.csv`, `full_text`), checked item by item.

## Run it locally

```
cd site
python3 -m http.server 8000
```
then open http://localhost:8000. Only the fonts still come from the internet (Google Fonts).

## Layout

```
index.html               markup; links each stylesheet and script at the place its block used to be
css/                     00-host-reset (the wrapper the artifact host added), 01-layout, 02-type-roles,
                         03-pairs-dots, 04-how-they-talked, 05-how-they-talked-brand
js/                      one file per section of the page, in the order the page loads them (below)
js/lib/                  d3 7.9.0, GSAP 3.12.5, ScrollTrigger 3.12.5 (unmodified copies from cdnjs)
data/                    pm25.js, cards.js, quotes.js, states.js (see "Where the data comes from")
card/                    the city card: index.html, card.css, card.js, embed.js
img/                     Dish's artwork, paper texture, logos, animation frames
tools/split_page.py      the step 2 split
_unused/                 city-panel.js and city-panel-data.js: published with the artifact, loaded by neither page
```

### Scripts, in load order

| File | What it does |
|---|---|
| `js/skip-to.js` | the sticky "skip to" buttons |
| `js/map-dots.js` | map dot colours and legend. **Calculation:** a city is "used to it" if `bad_days >= 8` |
| `data/pm25.js`, `data/states.js` | data (see below) |
| `js/plates-shared.js` | text filled from the data, tooltips, the safe-level ruler, pair results, table, air-talk groupings. **Holds data inline:** `SPEC`, tone counts per city (Claude draft labels) |
| `js/hero.js` | title plate: pot, frog, bubbles (decoration) |
| `js/door-walk.js` | the figure walking past the doors |
| `js/map-plate.js` | the fixed map of the nine cities |
| `js/pairs-map.js` | the interactive city explorer map |
| `js/scope.js` | "We followed nine U.S. cities" reveal |
| `js/story-same-air.js` | the Bakersfield vs. Indianapolis scroll story |
| `js/see-numbers-rule.js` | matches one rule's width to the plates |
| `js/pairs-dots.js` | the nine dots moving into pairs |
| `js/study-details.js` | study details reveal |
| `js/city-cards.js` | opens a city card beside the map |
| `js/outro.js` | the closing pot of frogs |
| `js/air-layer.js` | the haze that thickens as you scroll (decoration) |
| `js/reddit-posts.js` | rotating Reddit posts on the thresholds plate |
| `js/how-they-talked.js` | the comment, word and word-cloud plates and the tone hills. **Holds data inline:** `CORR`, corrected tone counts. **Calculations:** the hills are a Gaussian smoothing (`kde`) of each city's tone counts; the dot marks its peak |
| `card/card.js`, `card/embed.js` | the city card and how it sits inside the page |

### Where the data comes from

Step 3 (2026-10-07): every data file is now built by a script in `scripts/site/`, run from the repo root. Each output starts
with a header naming the script, the time it ran, the git commit and the SHA-256 of every input. Nothing is typed into the
code any more. Each rebuilt file was checked against the snapshot: all identical (pm25.js apart from its "built" date).
The steps are logged in `logs/data-log-gina.md` ("Site · Step 1–5").

| File | Script | Built from |
|---|---|---|
| `data/hand-coded-comments.js` | `01_hand_coded_comments.py` | `spectrum_07_corrected/hand_check_items.csv` (minus agreed X) + `spectrum_01_air_items` text |
| `data/tone-counts.js` | `02_tone_counts.py` | `spectrum_07_corrected/city_shares.csv`, `spectrum_03_outputs`, `spectrum_02_labels` weights, `spectrum_01_air_items` |
| `data/cards.js` | `03_city_cards.py` | `data/pm25.js`, `city_shares.csv`, `openaq/step05_averages`, `spectrum_01_air_items` keywords |
| `data/quotes.js` | `04_card_quotes.py` | `spectrum_03_outputs`, `hand_check_items.csv` |
| `data/pm25.js` | `05_pm25.py` | runs `viz/pm25-scrolly/build.py --full` (`analysis_01`, `step08_pm_normals`, …) |
| `data/states.js` | none yet | US state outlines: source to be recorded |

To rebuild everything: `for s in 05_pm25 01_hand_coded_comments 02_tone_counts 03_city_cards 04_card_quotes; do python3 scripts/site/$s.py; done`
(05 first, because 03 reads `pm25.js`).

**Copied, not computed (to be confirmed by Dish):**
- `days_over_15` in `pm25.js` ("about N bad days a year" in the map tooltip): no repo file reproduces it.
- `f = 1` on 12 of the hand-coded comments (drawn larger as "interesting"): the flags are in no repo file.
Both are copied from the snapshot and labelled COPIED in their file headers.

## Next steps

4. `check.py`: compare every rebuilt number with the snapshot; explain any difference.
5. `docs/site-methods.md`: one row per number on the page, with formula, script and source file.
6. Host on GitHub Pages.

Until the switch-over, the artifact stays the place where edits happen. Any artifact edit after version 94 has to be
carried over here by hand (or by re-running the snapshot and split).
