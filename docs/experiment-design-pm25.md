# Experimental Design: Harm vs. Abnormal (PM2.5)

*Running reference doc for consistency and reproducibility. Last updated 2026-10-02.*

## Our Hypothesis

People react to abnormal rather than harm.

- **Pos** – Reddit rise correlates with ratio to normal PM2.5, not absolute PM2.5.
- **Neg** – Reddit rise correlates with absolute PM2.5, not ratio to normal PM2.5.
- **Mixed** – Reddit rise correlates with both, or with neither. If neither, Reddit may be too noisy a signal for this test.

## Date ranges

- **2019–2026:** the range searched for event weeks and checked for PM2.5 coverage.
- **2019–2025:** the range used for the PM2.5 baseline and the bad-days-per-year measure. 2026 is excluded from these because it is a partial year, but 2026 weeks can still be event weeks.
- **Reddit baseline:** the 6 weeks before and after each city's event week, in the same year.

## How do we pick the cities?

Candidates come from the American Lung Association's State of the Air 2026 list of most polluted cities. ALA ranks metro areas; we use city-level PM2.5 from OpenAQ. The ALA rank is used only to pick candidates, not in any calculation. No cities were added from outside the list.

Candidates (ALA rank): Fairbanks AK (1), Eugene OR (2), Bakersfield CA (3), Fresno CA (6), Los Angeles CA (7), Seattle WA (8), Detroit MI (11), Pittsburgh PA (13), Indianapolis IN (15), Phoenix AZ (18), San Jose CA (21), Salt Lake City UT (22), Yakima WA (25).

A city is included only if it passes all three checks:

1. **PM2.5 coverage:** daily PM2.5 data for at least 75% of days, 2019–2026.
2. **Reddit activity:** the city's event week must have at least **100 kept posts + comments**, the same minimum as for a normal week. *(Settled 2026-10-03 by Dish. This replaces the [N_avg] average and the separate screening pull.)*
   - **Yakima fails** (about 50 posts + comments in its event week, from the pull's coverage counts) **and is dropped, leaving 9 cities.**
3. **Real harm:** the city's worst week has an average PM2.5 above the EPA line, 35.5 µg/m³. This makes sure every city in the study actually faced harmful air. Without that, a city that didn't react might just have had nothing worth reacting to. (35.5 is EPA's 24-hour standard. Applying it to a whole week's average is a stricter bar.)

**Screening results (OpenAQ Step 7, reference monitors, 2019-01-01 → 2026-09-25):** `scripts/openaq/07_city_screening.py` → `data/processed/openaq/step07_screening/`.

- **Check 1:** all 13 candidates pass: Eugene 88.7%, Phoenix 88.5%, Indianapolis 88.3%, Salt Lake City 88.3%, Los Angeles 88.0%, Seattle 87.9%, Detroit 87.2%, Fresno 85.0%, Pittsburgh 84.9%, Yakima 84.3%, Bakersfield 83.2%, San Jose 83.2%, Fairbanks 81.6%. (The earlier 75–84% figures counted all sensors over 2016–2026.)
- **Check 3:** 10 pass. Out:
  - **Los Angeles:** worst week 32.95 (Sep 14–20, 2020). A city average over 6 sites dilutes local peaks.
  - **Salt Lake City:** worst valid week 26.24. A higher week (Aug 2–8, 2021, 45.04) has only 2 of 7 days, so it's invalid.
  - **Phoenix:** its two highest weeks are New Year's weeks, excluded by the fireworks rule. Its best remaining week is 34.99.

**Cities that passed checks 1 and 3 (10), with their event weeks.** Yakima later failed check 2, so **9 are in the study**:

| City | Event week (Mon–Sun) | Week avg PM2.5 (µg/m³) | Days with data | Median days ≥ 35.5 / yr | Event |
|---|---|---|---|---|---|
| Bakersfield | Dec 2–8, 2024 | 55.5 | 7/7 | 12 | Winter inversion: stagnant air trapping local pollution (wood burning, traffic). Not smoke. |
| Fairbanks | Jun 27 – Jul 3, 2022 | 91.8 | 7/7 | 8 | Interior Alaska wildfires (lightning-started complexes, plus a nearby tundra fire) |
| Fresno | Aug 17–23, 2020 | 61.2 | 5/7 | 8 | August 2020 Lightning Siege fires (SCU, LNU, August Complex) |
| ~~Yakima~~ (dropped, check 2) | Sep 6–12, 2021 | 53.8 | 7/7 | 3 | Schneider Springs Fire, NW of Naches |
| Detroit | Jul 13–19, 2026 | 91.8 | 7/7 | 2 | Canadian (mostly Ontario) wildfire smoke; record AQI 650 on Jul 16 |
| Seattle | Sep 7–13, 2020 | 51.5 | 5/7 | 1 | 2020 Labor Day fires (Oregon/Washington) |
| Indianapolis | Jun 26 – Jul 2, 2023 | 55.1 | 7/7 | 1 | Canadian (Quebec) wildfire smoke |
| Eugene | Sep 7–13, 2020 | 280.4 | 7/7 | 0 | 2020 Labor Day fires (Holiday Farm and others) |
| Pittsburgh | Jul 13–19, 2026 | 59.2 | 7/7 | 0 | Canadian (mostly Ontario) wildfire smoke; Code Purple Jul 17 |
| San Jose | Aug 17–23, 2020 | 36.3 | 5/7 | 0 | SCU Lightning Complex |

Event causes checked against news coverage, 2026-10-02; sources are in `logs/data-log-dish.md`. The Bakersfield source is weaker (a general California inversion report from Dec 5, 2024).

GINA ADD MORE INFO HERE

## How do we describe the cities? (no chronic/acute grouping)

**The chronic/acute grouping was dropped on 2026-10-03 (Dish), before any event-week Reddit data was opened.** There are no cutoffs and no cities left out.

**Why:**
- **The ratio already measures "used to it."** A city used to bad air has a high monthly normal, so even a bad week gives it a small ratio.
- **The grouping can contradict the ratio.** Fairbanks has 8 bad days a year, mostly winter inversions, so it would be "chronic." But its event is a June smoke week, and its Junes are clean, so its ratio is 17×.
- **Only 3 cities would have been chronic,** too few to compare groups.

**Bad days per year** is kept as a descriptive measure, to characterize the cities (including in the presentation): the median number of days per year with daily PM2.5 ≥ 35.5, 2019–2025.

| Bad days/yr | Cities |
|---|---|
| 12 | Bakersfield |
| 8 | Fairbanks, Fresno |
| 3 | Yakima (dropped, check 2) |
| 2 | Detroit |
| 1 | Seattle, Indianapolis |
| 0 | Eugene, Pittsburgh, San Jose |

- **Days, not average PM2.5,** match what "used to it" means: how often people live through bad air.
- **The median across years** keeps one bad smoke year from dominating.

*Optional robustness check:* also rank Reddit rise against bad days per year. If familiarity matters, cities with more bad days should react less.

## How do we pick the weeks?

Each city's worst week by absolute PM2.5: the Monday–Sunday week with the highest average PM2.5, 2019–2026. 2026 weeks are allowed as event weeks.

**Why absolute and not most abnormal:** picking by abnormality would build the answer into the selection.

**Fireworks rule:** a week containing July 4–5 or Dec 31–Jan 1 can't be an event week, in any city. Fireworks smoke is short and man-made, and Reddit talk that week is about fireworks, not air. Skipped weeks are listed in the screening output. *(Claude's recommendation, approved by Dish, 2026-10-02.)*

Invalid weeks (fewer than 5 of 7 days) can't be event weeks either. Any that average higher than the chosen week are listed. These are mostly September 2020 weeks, in Bakersfield, Seattle, San Jose and Yakima.

## What is the control?

**PM2.5:** the median of Monday–Sunday weekly average PM2.5 for the same calendar month, 2019–2025, excluding the event week.

**Reddit:** the median weekly air-talk share in the weeks around the event (see the Reddit control protocol).

**Why the two controls differ:** the PM2.5 normal defines what counts as abnormal, so it needs a long, same-month baseline that reflects what residents are used to. The Reddit normal only measures how much this community usually talks about air, so the weeks around the event, with the same community, size, and era of Reddit, are a fair reference. This follows the logic of event studies and case-crossover designs: each city is compared against itself, close in time.

## Definitions

- **City daily PM2.5:** the mean of all reporting reference sites in the city for that day, with at least one required (a site = same-type sensors within 50 m, already averaged). A sensor-day counts only with at least 18 of 24 hours (EPA's rule, Gina's OA-D3). Input: OpenAQ Step 5 (`pm25_<city>_daily.csv`). *(Approved by Dish, 2026-10-02.)*
- **Harmful day:** daily PM2.5 ≥ 35.5 µg/m³, on the unrounded value. *(Approved by Dish.)* In 2020–21, coverage is below 75% in most cities, so those years' counts are likely undercounts. The median is kept over all 7 years anyway: dropping those years would drop the biggest smoke years and understate cities with frequent bad air.
- **Day:** the city's local calendar day.
- **Week:** Monday–Sunday, in the city's local time. If a week spans two months, it belongs to the month holding most of its days.
- **Valid week:** at least 5 of 7 days have PM2.5 data. Weeks that fail are listed in the output, not silently dropped. Days outside 2019-01-01 → 2026-09-25 count as missing. *(Approved by Dish, 2026-10-02.)*
- **Ratio to normal:** event-week PM2.5 ÷ PM2.5 baseline.
- **Air-talk share:** posts and comments matching the air keyword list ÷ all posts and comments in the subreddit that week.
- **Reddit rise (ratio):** event-week air-talk share ÷ the median baseline-week share.
- **Reddit rise (percentage points):** event-week share − median baseline-week share. This keeps a near-zero normal from creating a huge, misleading ratio.
- **Reddit percentile:** where the event week ranks among the up to 10 baseline weeks, e.g., "higher than all 10 normal weeks." This is how we tell a real rise from a normal week.
- **Event type:** smoke, inversion, or other, assigned by [rule, e.g., checking news coverage for that week].

## Reddit control protocol

*Status: **decided 2026-10-03: month normal.** The Reddit normal is the median weekly air-talk share for the same calendar month, 2019–2025, excluding the event week, like the PM2.5 normal.*
- *It was chosen by the pre-set rules below ("Choosing the normal") on Eugene, which is blind. Eugene split (neighbor steadier, month far less drift), and a split goes to the month normal. Results: `data/processed/reddit/normals_02_compare/decision.md`.*
- *The Bakersfield check (not blind) favored neighbor. That's reported, not acted on.*
- *Steps 2, 3, 11 and 12 below describe the neighbor design. They're kept for the record. The before/after sensitivity check is replaced by the neighbor normal itself, which can be reported as the alternative.*
- *Pull plan for the other 8 cities: `docs/reddit-pull-month-normals-8-cities.md`.*

1. **Order:** PM2.5 event weeks are found first. Reddit is pulled only after, except for the check 2 screening pull.
2. **What we pull:** for each city, one continuous range from 6 weeks before to 6 weeks after the event week, padded by 1 day on each end for the time zone conversion. Example: event week Mon Sep 7 – Sun Sep 13, 2020 → pull Jul 26 – Oct 26, 2020.
3. **Baseline weeks:** the 12 surrounding weeks, minus the week directly before and directly after the event (talk there may be elevated by lead-up or aftermath), minus any week with average PM2.5 above 35.5. This leaves up to 10 weeks.
4. **Time zone:** all Reddit timestamps are converted from UTC to the city's local time before assigning posts to weeks, so Reddit weeks match PM2.5 weeks.
5. **Subreddit:** one main city subreddit per city, listed in this doc, chosen before looking at the event week.
6. **Data:** posts and comments from Arctic Shift (arctic-shift.photon-reddit.com). Remove bot accounts, deleted or removed text, and duplicates.
7. **Air keyword list:** written once, frozen, and used for every city. **Frozen 2026-10-03: `data/lexicons/lexicon_air_v1.csv`.**
   - **What counts:** `include` terms count as air talk. `candidate` terms count only in a wider secondary measure. `fire` terms are a separate fire measure. `exclude` patterns are blanked first.
   - **Hand-check:** no new one. The earlier hand-check of 216 items from the Eugene/Bakersfield study is used instead *(changed by Dish)*.
   - **Caveats** (see `logs/data-log-dish.md`):
     - Only Eugene and Bakersfield were tested, and v1 itself was not re-checked.
     - The list was partly tuned on Bakersfield's event week, which likely inflates Bakersfield's rise (a conservative bias for Pos).
8. **Control:** the median weekly air-talk share across the baseline weeks.

### Choosing the normal: neighbor vs month (rules fixed 2026-10-03, before any share was computed; approved by Dish)

Script: `scripts/reddit/normals_02_compare.py`. It reads only the normal pulls, drops the event week on reading, and never computes a Reddit rise.

- **Usable weeks** (both normals):
  - Weeks are Monday–Sunday, local time.
  - **Neighbor:** ±6 weeks, minus the week directly before and after.
  - **Month:** every week of the event's month (by Thursday), 2019–2025, minus the event week.
  - **Drop** a week if:
    - PM2.5 is > 35.5
    - it has no PM2.5 data
    - it's a fireworks week
    - it has fewer than **100** kept posts + comments *(Claude's choice, approved)*
  - **Keep, but flag:** weeks with 1–4 PM2.5 days, if their average is ≤ 35.5.
- **Air talk:** `include` terms of `lexicon_air_v1`. Removed/deleted items and bots are dropped. Bots are `distinguished = moderator` or "I am a bot" text, because usernames were stripped *(Claude's choice)*.
- **Test 1, enough weeks:** ≥ **6** usable weeks *(Claude's choice, approved)*.
- **Test 2, steady:** interquartile range of the weekly share (percentage points). Smaller wins.
- **Test 3, no drift:** neighbor = before vs after; month = 2019–2021 vs 2023–2025. Measured as the gap between median shares (pp). Smaller wins.
- **Reported only:** volume, PM2.5 per week, smoky weeks (≥ 15).
- **Decision:**
  - **Eugene decides**, because it's the blind city.
  - A normal that fails test 1 loses.
  - Otherwise, the normal smaller on both tests 2 and 3 wins.
  - A split, a tie, or a test 3 that can't be computed goes to the **month normal**, which matches the PM2.5 normal.
  - **Bakersfield is a check only** (not blind). If it disagrees, that's reported, not acted on.
9. **Why share, not counts:** subreddit activity changes week to week. A share keeps a busier week from looking like more air talk.
10. **Minimum volume:** a week counts only if the subreddit had at least [N_min] total posts and comments that week. Weeks below this are listed for review, not silently dropped.
11. **Sensitivity check:** Reddit rise is also computed with before-weeks only, after-weeks only, and a ± 4-week window. These use the same pull. If the before and after medians differ a lot, the city has seasonal drift and is flagged. If city rankings hold across all versions, the result doesn't depend on the window choice.
12. **Spot check:** if a city is flagged for seasonal drift, pull the same Monday–Sunday week from [3–5] other years in 2019–2025 for that city only, and compare its rise against that baseline too.
13. **Known bias:** if neighboring weeks also had elevated air talk, the Reddit normal is inflated and the rise looks smaller. This works against our hypothesis, not for it.

## What we measure for each city

A table with one row per city: city, group, event week dates, event type, event-week PM2.5, PM2.5 baseline, ratio, air-talk share (density for the week), Reddit rise (ratio), Reddit rise (percentage points), Reddit percentile, and the sensitivity-check rises.

## Pairs

Built after the event weeks are found. Two kinds count:

- **Matched:** similar absolute PM2.5, different ratio. "Similar" = event-week PM2.5 within 5% of each other *(Claude's choice)*.
- **Crossed:** one city had worse air but a smaller ratio.

**Pairs fixed 2026-10-03, before any event-week Reddit file was opened** (PM2.5 only; `scripts/openaq/08_pm_normals_and_pairs.py` → `data/processed/openaq/step08_pm_normals/`).

PM2.5 ratio to normal:

| City | Ratio |
|---|---|
| Eugene | 41.9× |
| Fairbanks | 17.4× |
| Detroit | 7.4× |
| Seattle | 7.2× |
| Yakima (dropped) | 6.0× |
| Fresno | 6.0× |
| Pittsburgh | 5.3× |
| San Jose | 5.0× |
| Indianapolis | 4.4× |
| Bakersfield | 2.9× |

*The PM2.5 normal uses only valid weeks (≥ 5 of 7 days), and keeps fireworks and > 35.5 weeks. Claude's choices.*

**No headline pairs (changed by Dish, 2026-10-03; this replaces the earlier Bakersfield–Indianapolis / Bakersfield–Seattle headlines).** All qualifying pairs are reported, with one pre-set summary:
- in how many pairs the higher-ratio city reacted more
- in how many crossed pairs the worse-air city reacted more

**Featured by rule** (only if the presentation needs one example of each kind):
- the matched pair with the biggest ratio gap: currently **Fairbanks vs Detroit**
- the crossed pair with the biggest air gap: currently **Bakersfield vs San Jose**

Any other pair mentioned is labeled as noticed after seeing results.

**Eugene vs Bakersfield is no longer a test pair.** With the Sep 2020 event week, Eugene has both the worse air (280 vs 55) and the bigger ratio (41.9× vs 2.9×), so Pos and Neg predict the same thing. It's kept as an illustration only. (The old August 2026 Eugene event made a crossed pair.)

**All 9 qualifying pairs** (3 matched, 6 crossed) are in `pairs.csv`. Pairs with Yakima were removed when it was dropped; there were 14 before.
- **Fairbanks vs Detroit** is a strong matched pair: 91.8 vs 91.8, with ratios of 17.4× vs 7.4×. But Detroit's week was national news.

## How we decide

1. Across all cities, compare two rankings of Reddit rise: one against the ratio, one against absolute PM2.5. Whichever lines up better is the stronger driver. With this few cities, treat it as a descriptive pattern, not a statistical proof.
2. The ranking uses Reddit rise ([ratio / percentage points]). The other measure is reported as a check.
3. In each pair, does the higher-ratio city show the bigger Reddit rise?
4. Check whether the rankings hold in the sensitivity check.
5. Write down which hypothesis the evidence supports (Pos, Neg, or Mixed), including the cities that don't fit.

## Data sources

- **PM2.5:** OpenAQ. Reference-grade monitors are the default. Low-cost sensors are used only for a city whose reference coverage is below 75%, and only after EPA correction (Barkjohn model, which requires relative humidity). A low-cost city is kept only if, on overlapping days, it agrees closely with reference monitors ([agreement rule TBD]). Otherwise it drops out. The source choice is made before any Reddit data is examined, using only coverage and agreement. Reference vs. low-cost filter: OpenAQ `sensor_class` (`reference` / `low-cost`). Site IDs per city are in `step07_screening/city_screening.csv`.
  - **Outcome (Step 7):** no fallback was needed, because all 10 cities pass on reference alone. Low-cost couldn't have served anyway:
    - OpenAQ has no relative humidity for these sensors.
    - None are PurpleAir (they are Clarity, AirGradient and CMU), so the Barkjohn correction doesn't apply.
    - Low-cost coverage since 2019 is 0–56% in every city.
- **Reddit:** Arctic Shift, with the subreddit listed for each city.
- **Air-talk keywords:** frozen list in `data/lexicons/lexicon_air_v1.csv` (frozen 2026-10-03).

## Known confounds

- **Candidate pool:** all candidates come from a most-polluted list, so cities that aren't used to bad air are under-represented.
- **Event type:** most event weeks are visible wildfire smoke. Bakersfield's is a winter inversion, which people may not see or smell as much.
- **Subreddit size:** small subreddits make the share jumpy. Yakima and Fairbanks are most at risk of failing check 2.
- **News coverage:** a national story, like the 2023 Canadian smoke, can drive talk regardless of local air. Media Cloud can check this.
- **Other local events:** a big local story during the Reddit window could shift what the subreddit talks about. The median protects against one odd week, though not a whole odd season.
- **Seasonal drift:** air talk may rise or fall across the 13-week window. A centered window cancels steady trends. A seasonal peak at the event could make the rise look larger. Checked by comparing before-week and after-week medians and plotting all 13 weeks per city.
- **Low-cost correction:** the EPA correction underestimates at very high smoke levels, so any city using corrected low-cost data is flagged.
- **Shifting normal:** if smoke shows up in more than half of a city's baseline weeks for a month, the PM2.5 median starts treating smoke as normal. Flag it if it happens; it ties to the rolling-baseline question.

## Open decisions

event type rule (news check done for the 10 event weeks; a formal rule is still open), headline Reddit rise measure (ratio or percentage points), screening pull month, spot-check years.

Settled 2026-10-02: valid-week rule (5 of 7), hourly completeness (18 of 24), ≥ 35.5 for counting days, reference/low-cost filter (`sensor_class`), station combining (mean of sites), fireworks rule. The low-cost agreement rule is not needed: no city uses low-cost.

Settled 2026-10-03:
- **Keyword list:** v1 frozen, with no new hand-check.
- **Reddit normal:** month.
- **Pair tolerance:** within 5%.
- **Headline pairs:** none. All pairs are reported, with a pre-set summary and featured-by-rule examples. This replaced the earlier Bakersfield–Indianapolis / Bakersfield–Seattle choice.
- **Chronic/acute grouping:** dropped. Bad days per year is kept as a descriptive measure.
- **[N_min]:** 100 kept posts + comments per week (from the normals rules).
- **Check 2 (Reddit activity):** the event week needs ≥ 100 kept posts + comments. Yakima dropped.

Each one gets settled in the data log, then copied here.

## Changelog

- **2026-10-02:** Hypotheses (Pos, Neg, Mixed) set. Event week = worst Monday–Sunday week by absolute PM2.5, 2016–2026, with 2026 allowed. Coverage threshold 75%. Control = same-month median, excluding the event week. PM2.5 baseline, Reddit baseline, and grouping all use 2019–2025. Reddit rise reported as ratio and percentage points. Percentile kept as a supporting column.
- **2026-10-02 (later):** Event search and coverage check narrowed to 2019–2026, so events and the baseline come from the same era of Reddit. Cities whose worst week was before 2019 use their worst week from 2019 on.
- **2026-10-02 (final check):** Added a UTC-to-local time zone rule to the Reddit protocol. Split the Reddit volume threshold into [N_avg] (city inclusion) and [N_min] (single week). Added a screening pull for check 2. Added open decisions for station combining, event type rule, and headline Reddit rise measure.
- **2026-10-02 (Reddit baseline):** Reddit baseline changed from same month across 2019–2025 to the weeks around the event (± 6 weeks, skipping the weeks directly before and after, and any week above 35.5). This cuts the pull from 7 chunks per city to 1. The PM2.5 baseline is unchanged. Added a sensitivity check (before-weeks only, after-weeks only, ± 4 weeks) using the same pull, a seasonal-drift confound, and a same-week-other-years spot check for flagged cities. Discussion paused.
- **2026-10-02 (cities):** Candidates set to the 13 cities from ALA State of the Air 2026. No cities added from outside the list; limitation noted. PM2.5 restricted to reference monitors by default; low-cost used only as a pre-specified fallback. Check 1 coverage to be recomputed on reference-only data.
- **2026-10-02 (screening):**
  - Checks 1 and 3 run on reference monitors (OpenAQ Step 7). All 13 pass check 1. Los Angeles, Salt Lake City and Phoenix fail check 3, leaving **10 cities**.
  - Fireworks rule added. Valid-week, hourly completeness, ≥ 35.5 and site-combining rules settled.
  - Event weeks set and their causes checked against news.
  - No second grouping median without low-coverage years.
  - Low-cost fallback found unusable (no RH, no PurpleAir, low coverage), and not needed.
- **2026-10-03 (before any event-week Reddit data was opened):**
  - Keyword list frozen (v1).
  - Reddit normal chosen: month.
  - PM2.5 normals, ratios and pairs computed (OpenAQ Step 8). Eugene–Bakersfield dropped as a test pair.
  - Headline pairs set, then replaced by "all pairs + pre-set summary + featured by rule".
  - **Chronic/acute grouping dropped.** Bad days per year kept as a descriptive measure.
  - Event weeks for Detroit and Pittsburgh to be re-pulled in local time; the others come from the month pulls.
  - **Check 2 set** (event week ≥ 100 posts + comments). **Yakima dropped, leaving 9 cities and 9 pairs.**
