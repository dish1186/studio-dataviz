# Boiling Frog site · where every number comes from

One row per number on the page (`site/`), in page order: what it means, how it is calculated, where the calculation
lives, and the data it starts from. Written 2026-10-07 for the freestanding site (step 5 of `site/README.md`).

**How to read it**
- *Built by* is the script that writes the data file the page reads (`scripts/site/NN_*.py`, run from the repo root).
  Each data file's header lists its inputs with their SHA-256; `python3 site/tools/check.py` confirms they still match.
- *Drawn by* is the page code that turns the data into what you see. Formulas there are marked `CALCULATION` in the code.
- Upstream steps (OpenAQ, Reddit, tone correction) are explained in full in their own scripts and in `logs/data-log-gina.md`
  and `logs/data-log-dish.md`; this page gives each in one line.
- **COPIED** = not computed by any repo script yet (see the end).

---

## Shared definitions

| Term | Definition | Made by | Source data |
|---|---|---|---|
| **Worst week** | the Monday–Sunday week with the highest average PM2.5, 2019–2026, among weeks with at least 5 days of readings, leaving out fireworks weeks (July 4th, New Year) | `scripts/openaq/07_city_screening.py` | OpenAQ reference monitors, `data/processed/openaq/step05_averages` |
| **PM2.5 (worst week)**, `pm` | mean of the city's daily reference-monitor PM2.5 in the worst week, µg/m³ | `07_city_screening.py` → `step08_pm_normals/pm_normals.csv` (`event_week_pm25`) | same |
| **Normal PM2.5**, `pm_normal` | median of the weekly averages for the same calendar month, 2019–2025, leaving out the worst week (a week counts toward the month of its Thursday and needs ≥ 5 days) | `scripts/openaq/08_pm_normals_and_pairs.py` (`pm25_normal`) | `step07_screening/weekly_all.csv` |
| **× normal**, `ratio` | `pm ÷ pm_normal`, 2 decimals | `08_pm_normals_and_pairs.py` (`ratio_to_normal`) | as above |
| **Unhealthy days a year**, `bad_days` | for each year 2019–2025, the days with daily PM2.5 ≥ 35.5 µg/m³; the median of those 7 counts | `07_city_screening.py` (`median_days_ge_35_5_2019_2025`) | `step05_averages` |
| **Used to it** | `bad_days ≥ 8` (Bakersfield 12, Fairbanks 8, Fresno 8) | `site/js/map-dots.js` `BF_USED` | `data/pm25.js` |
| **Air talk share** | % of a week's kept posts + comments (bots, deleted, duplicates removed) that match the air lexicon `data/lexicons/lexicon_air_v1.csv` | `scripts/reddit/analysis_01_event_rise.py` (`air_share_pct`) | Reddit (Arctic Shift), usernames removed |
| **Normal air talk**, `share_normal` | median air-talk share of the city's usable normal weeks (same month 2019–2025; dropped: PM2.5 > 35.5 or missing, fireworks, < 100 kept items, comments on < 5 of 7 days) | `analysis_01_event_rise.py` (`normal_share_pct`) | as above |
| **× more air talk**, `rise` | `share_event ÷ share_normal` | `analysis_01_event_rise.py` (`rise_ratio`) | as above |
| **Tone groups** | A Alarm, J Adjusting (Reacting = A + J); E Enduring, N Normalizing (Living with it = E + N); X not about the air (never counted in shares) | codebook `data/processed/reddit/spectrum_02_labels/codebook.md` | — |
| **Corrected tone counts** | hand-checked items (436) keep Gina and Dish's agreed label; every other item is spread over the groups by how often its Claude label turned out to be each agreed label in the check (one table for all nine cities); sampled weeks (Eugene, Seattle, Pittsburgh: 400 of ~1,150–1,200 each) weighted back to the full week | `scripts/reddit/spectrum_07_corrected_shares.py` → `city_shares.csv` | `spectrum_03_outputs` (Claude labels), Air Talk Check export |

All of these reach the page through `site/data/pm25.js` (built by `05_pm25.py`, which runs `viz/pm25-scrolly/build.py --full`)
and `site/data/tone-counts.js` (built by `02_tone_counts.py`).

---

## Thresholds plate

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| WHO 15, EPA 35 | 24-hour PM2.5 guideline (WHO 2021) and standard (US EPA) | none (reference values) | text in `index.html` | WHO, EPA |
| 3 rotating Reddit posts | example quotes, excerpted | none | text in `index.html` (item ids in a comment) | `spectrum_01_air_items` (oyhy3nt, g4rihme, oyfzo86) |

## Map of the nine cities (Plate V)

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| dot size | worst-week PM2.5 | radius = `3 + 17 × √(pm / 300)` px | `js/map-plate.js` `rPM` | `pm25.js` |
| dot colour | used to it (green) or not (ink) | `bad_days ≥ 8` | `js/map-dots.js` | `pm25.js` |
| tooltip "about N bad days a year" | days over 15 µg/m³ a year | **COPIED** (`days_over_15`) | `js/map-plate.js` | snapshot `d689e08` |

## Scroll story: Bakersfield and Indianapolis

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| "same level of unhealthy air" | worst-week PM2.5, 55.47 and 55.09 | `pm` | text | `pm25.js` |
| "over 3x the WHO recommendation" | 55.5 ÷ 15 = 3.7 | `pm ÷ 15` | text (checked in a comment) | `pm25.js` |
| "60% higher than EPA standards" | 55.5 ÷ 35 = 1.58, i.e. about 58%, rounded | `pm ÷ 35` | text (checked in a comment) | `pm25.js` |
| "4.4× indianapolis's normal, 2.9× bakersfield's" | how unusual the week was | `ratio` | text | `pm25.js` |
| bars, × more air talk (nine cities) | reaction | `rise`, sorted; bar length = `rise ÷ largest rise`; label 0 decimals at ≥ 10×, else 1 | `js/story-same-air.js` | `pm25.js` |
| tone disks: % per group, "reacting / living with it" | how the air talk sounded | `share = count ÷ (A+J+E+N)`; reacting % = `round(100 × (A+J) ÷ total)` | `js/story-same-air.js` | `tone-counts.js` corrected |
| "4.8× / 9.5× more air talk" under the disks | reaction | `rise` rounded to 1 decimal | `js/story-same-air.js` | `pm25.js` |
| "~51 / ~99 air posts and comments" | corrected comment count, X left out | `round(A+J+E+N)` | `js/story-same-air.js` | `tone-counts.js` corrected |
| "see the numbers" table | the same values | ≈55 = `pm`; × normal = `ratio`; × air talk = `rise`; tone % = corrected counts (Bakersfield 27 / 11 / 62, Indianapolis 46 / 20 / 34) | text (checked in a comment) | `pm25.js`, `tone-counts.js` |

## Study details: nine cities into pairs

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| dot colour (indigo / green) | used to it or not | `bad_days ≥ 8` | `js/pairs-dots.js` | `pm25.js` |
| the nine pairs | matched (PM2.5 within 5%, different × normal) and crossed (higher PM2.5, lower × normal) | `08_pm_normals_and_pairs.py` (`MATCH_TOL = 0.05`) | `js/pairs-dots.js` (layout) | `pm_normals.csv` |

## City explorer map and pair results

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| dot size, colour | as Plate V | as Plate V | `js/pairs-map.js` | `pm25.js` |
| "8 of 9 pairs went the way the study predicted" | pair test | count of pairs whose outcome is "as Pos predicts" = the city with the higher × normal had the higher × air talk | `js/pairs-map.js` (tally); outcome from `analysis_01_event_rise.py` | `analysis_01/pairs.csv` via `pm25.js` |
| per pair: "More unusual", "Reacted more" | which city | higher `ratio`; higher `rise` | `js/pairs-map.js` | `pm25.js` |
| pair chart | air talk up, × normal down | both on a log scale from 1× to 50× | `js/pairs-map.js` | `pm25.js` |

## City card (opens beside the map)

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| timeline 2019–2026 | days over the line | one mark per day with PM2.5 above EPA 35.5 (or WHO 15, by toggle); the worst week's 7 days are marked separately in magenta | `card/card.js` | `cards.js` daily (`step05_averages`, `ref_mean`) |
| AVG PM2.5 "55 µg/m³ worst week (normal 19)" | `pm`, `pm_normal` | rounded | `card/card.js` | `cards.js` ← `pm25.js` |
| "2.9× normal" tag | how unusual | `ratio` | `card/card.js` | `cards.js` |
| "1.6× over EPA" tag | how harmful | `pm ÷ 35.5` (or `pm ÷ 15` for WHO) | `card/card.js` | `cards.js` |
| "used to it" tag, "12 unhealthy days a year" | | `bad_days ≥ 8` | `card/card.js` | `cards.js` |
| air spiral | a typical year | one dot per week at the week's mean daily PM2.5 (the worst week at `pm`); colour by the line crossed; radius `1.4 + 5 × √(min(PM2.5, 60) ÷ 60)` | `card/card.js` | `cards.js` daily |
| "4.8× more air talk", "from 0.34% to 1.6%" | reaction | `rise`, `share_normal`, `share_event` | `card/card.js` | `cards.js` |
| Low / Medium / High response | | rise < 5× Low, 5–15× Medium, ≥ 15× High | `card/card.js` `level()` | `cards.js` |
| "38% reacting, 62% living with it" | tone | reacting = `round(100 × (A+J) ÷ total)`; living = 100 − reacting | `card/card.js` | `cards.js` tone (corrected) |
| "Enduring was the biggest group (43%)" | | largest corrected count ÷ total | `card/card.js` | `cards.js` |
| tone disk | same shares | lobe length `R × min(1.08, 0.18 + 1.9 × share)` (shape only) | `card/card.js` | `cards.js` |
| keywords | most-matched air terms in the worst week | top 5 of `matched_terms`, leaving out "the air" and "air quality" | `03_city_cards.py` | `spectrum_01_air_items` |
| quotes per group | examples | up to 3: hand-checked first, then closest to 140 characters (filters in the script) | `04_card_quotes.py` | `spectrum_03_outputs`, `hand_check_items.csv` |

## Conclusion and notes

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| "reaction followed how unusual the air was, not how harmful" | the main test | verdict "Pos": ρ(rise, ratio) = 0.53 is higher than ρ(rise, PM2.5) = −0.13 by ≥ 0.2 (Spearman rank correlation, 9 cities) | `js/plates-shared.js` (text); ρ in `build.py`, checked against `analysis_01/results.md` | `pm25.js` |
| rank correlation, reaction vs unhealthy days a year | | ρ(rise, bad_days) = −0.37 | same | `pm25.js` |
| rank correlation of the two air measures | | ρ(ratio, pm) = 0.73 | same | `pm25.js` |
| "about 15% of their worst-week posts mention fire" (San Jose, Eugene) | fire share | % of kept items matching the fire terms: 14.7% and 16.0% | text | `pm25.js` (`fire_event`) |
| Seattle's fire share, Fairbanks's item count | | `fire_event`, `items` | `js/plates-shared.js` (bound) | `pm25.js` |

## How people talked

| Shown | Meaning | Calculation | Drawn by | Source |
|---|---|---|---|---|
| tone hills, one per city | how each city's air talk spreads from Alarm to Normalizing | on an axis 0–4 (one unit per group, group b centred at b + 0.5): `Σ share_b × exp(−(u − (b+0.5))² ÷ (2 × 0.42²))`; every hill divided by the tallest point across the cities, so heights compare | `js/how-they-talked.js` `kde` | `tone-counts.js` corrected |
| the dot on each hill | the city's peak | the highest point of its hill (checked every 0.025) | `js/how-they-talked.js` `peakOf` | same |
| count in the ink disc | corrected comments behind the hill (≈ 3,509 in all) | `round(A+J+E+N)`; the three sampled weeks are weighted back to the full week | `js/how-they-talked.js` | same |
| quotes plate | the 337 hand-coded comments | position: across = the city's average tone from these comments, up = √(bad-air days ÷ 12); each quote leans toward its own group (formula in the code) | `js/how-they-talked.js` | `hand-coded-comments.js` |
| words plate ("most used") | words each city and tone used | comments in that city and group that use the word (each word once per comment; stop words removed) | `js/how-they-talked.js` `cityWords` | `hand-coded-comments.js` |
| words plate ("most distinctive") | | `ln(((n+0.5) ÷ (n_k+1)) ÷ ((o+0.5) ÷ (N−n_k+1))) × √n`, n ≥ 2 (see code) | same | same |
| word cloud | every word once | size `10 + 70 × √(n ÷ n_top)`, n = every occurrence; colour = the group that used it most | `js/how-they-talked.js` `cloudCounts` | same |
| topic filters (Body & health, Protection, Visibility) | word lists | a word belongs to the first list that names it | `js/how-they-talked.js` `CATS` | — |

The 337 hand-coded comments = every item in `spectrum_07_corrected/hand_check_items.csv` (436 checked) except the 99 with
agreed label X; text from `spectrum_01_air_items`. The 436 were drawn as a simple random sample of 50 per city (all 36 in
Fairbanks), seed 20261005, according to the Air Talk Check page.

---

## Open: not yet computed by a repo script

| What | Where | Status |
|---|---|---|
| `days_over_15` (map tooltip) | `site/data/pm25.js` | **COPIED** from the published snapshot. Dish added it outside the repo; 64 candidate definitions did not reproduce it. Ask Dish. |
| `f = 1` on 12 quotes (drawn larger) | `site/data/hand-coded-comments.js` | flagged by Gina and Dish; the list is **COPIED** into `01_hand_coded_comments.py`. To do: save it as a raw file. |
| the draw of the 436 hand-check cards | `scripts/reddit/spectrum_06_validation_sample.py` (named on the Air Talk Check page) | the script is not in the repo; probably on Dish's computer. Gina to check. |
| US state outlines | `site/data/states.js` | source to be recorded |
