# Data log — Gina

Project 2, MDE Studio ("AI-Augmented Storytelling with Data" · Natural + Artificial).
Running plain-language log of every data step Gina runs with Claude. This log feeds the Algorithmic Forensics Appendix.
Dish keeps her own log (`data-log-dish.md`); the two may be combined later.
**Newest entries are at the top** (Dish's log runs oldest-first).

**Datasets in this log:** Media Cloud news coverage (online news) · American Lung Association *State of the Air 2026* PM2.5 rankings · OpenAQ PM2.5

**City-selection (Media Cloud × ALA)**
- **Cities (36 in 15 ALA metro areas):** Bakersfield-Delano CA · Eugene-Springfield OR · Brownsville-Harlingen-Raymondville TX · Fresno-Hanford-Corcoran CA · Visalia CA · Fairbanks-College AK · Los Angeles-Long Beach CA · Detroit-Warren-Ann Arbor MI · Indianapolis-Carmel-Muncie IN · Pittsburgh-Weirton-Steubenville PA-OH-WV · McAllen-Edinburg TX · San Diego-Chula Vista-Carlsbad CA · Phoenix-Mesa AZ · San Jose-San Francisco-Oakland CA · Houston-Pasadena TX
- **Media window:** 2024-09-25 – 2026-09-25 (24 months, as passed to the Media Cloud API; whether the API counts the end date itself was not checked)
- **Scale:** Media Cloud "State & Local" collection per state; the city is a search term, not a geographic filter.

**OpenAQ PM2.5**
- **Cities (16):** Ann Arbor MI · Bakersfield CA · Boston MA · Brownsville TX · Delano CA · Detroit MI · Eugene OR · Fairbanks AK · Fresno CA · Los Angeles CA · Phoenix AZ · Raymondville TX · San Diego CA · San Francisco CA · Springfield OR · Warren MI
- **Study period:** 2016-01-01 – 2026-09-25, daily (end date matches Dish's Decision D1)
- **Scale:** city limits; nearest-city fallback only where a city has no sensor inside its limits, logged when used (Decision OA-D1).

## Rules
1. One step at a time. Claude explains the step and shows the script, and Gina approves before it runs.
2. Raw downloads in `data/raw/` are never edited. Every change writes a new file to `data/processed/`.
3. Every step saves its exact script to `scripts/<dataset>/NN_<step-name>.py` and gets an entry below.
4. Any threshold, filter or default Gina didn't specify is flagged as **Claude's choice, approved by Gina** or **changed by Gina**.

## Entry format
Step · dataset · date · who ran it | What (plain language) | Why | Input file(s) | Script | Rows/values in → out (and what was removed or changed) | Output file | Judgment calls

**Note on Steps 1–8:** these were run on 2026-09-26/27 before this log existed, and logged retroactively in Step 9. They did not follow Rule 1 (no step-by-step approval before running), and Rule 2/3 files were assembled afterwards. Judgment calls in them are marked **Claude's choice, flagged to Gina in chat; not yet approved**, unless Gina specified or changed them. Gina to review.

---

### Step 1 · OpenAQ · 2026-09-27 · Gina + Claude
- **What:** Read-only inventory of every OpenAQ location with a PM2.5 sensor within 25 km of each city's center (city hall), and each PM2.5 sensor's first and last measurement date. **No measurements downloaded; nothing assigned to a city yet.**
- **Why:** To see which sensors exist near each city, what type they are and how far back they go, before choosing which ones count (Step 2) and downloading data.
- **Input:**
  - **City centers:** 9 from Dish's city hall coordinates (`data/processed/metar/metar_station_distances.csv`: Bakersfield, Boston, Brownsville, Detroit, Eugene, Fairbanks, Fresno, Los Angeles, San Francisco).
  - **6 geocoded:** city hall addresses supplied by Claude, geocoded by the US Census Geocoder (Ann Arbor, Delano, Phoenix, Raymondville, San Diego, Springfield).
  - **Warren:** Gina's Google Maps place pin (42.5118008, −83.0249714), because the Census Geocoder has no match for 1 City Square.
  - **OpenAQ API v3:** `/v3/locations` (radius search, PM2.5 only) and `/v3/locations/{id}/sensors`.
- **Script:** `scripts/openaq/01_sensor_inventory.py` (API key read from `$OPENAQ_API_KEY`; not in any file, checked after the run)
- **Rows in → out:** 16 city searches → **880 location results → 881 city × sensor rows, 821 distinct sensors** (some sensors fall in two cities' circles; one Boston location has 2 PM2.5 sensors). 0 removed.

  | City | Sensors | Reference | Low-cost |
  |---|---|---|---|
  | Ann Arbor | 27 | 1 | 26 |
  | Bakersfield | 10 | 5 | 5 |
  | Boston | 55 | 20 | 35 |
  | Brownsville | 12 | 2 | 10 |
  | Delano | 22 | 0 | 22 |
  | Detroit | 57 | 15 | 42 |
  | Eugene | 8 | 8 | 0 |
  | Fairbanks | 3 | 3 | 0 |
  | Fresno | 12 | 5 | 7 |
  | Los Angeles | 282 | 13 | 269 |
  | Phoenix | 37 | 11 | 26 |
  | Raymondville | **0** | 0 | 0 |
  | San Diego | 35 | 12 | 23 |
  | San Francisco | 258 | 7 | 251 |
  | Springfield | 8 | 8 | 0 |
  | Warren | 55 | 12 | 43 |
- **Output:**
  - Raw, exactly as received: `data/raw/openaq/json/` (`geocode_<city>.json` ×6, `locations_<city>.json` ×16, `location_sensors_<city>.jsonl` ×16)
  - Flattened: `data/processed/openaq/step01_inventory/openaq_cities.csv` (16 rows) and `openaq_sensors_inventory.csv` (881 rows)
  - Descriptions: 30 rows added to `data/descriptions/data_descriptions.csv`, one per JSON field in the three raw file types
- **Findings:**
  - **OpenAQ's data starts on 2016-03-06, not 2016-01-01.** No sensor anywhere has earlier data. The first ~2 months of the study period are missing for every city. **Open item for Gina.**
  - **Low-cost sensors are recent.** 695 of 730 low-cost city × sensor rows with dates started in 2022 or later; only 12 started before 2021. For 2016–2026 trends, only the **reference** (AirNow) monitors cover the whole period.
  - **Raymondville:** no PM2.5 sensor within 25 km.
  - **Delano:** no reference monitor within 25 km; 22 low-cost AirGradient sensors, the earliest from 2024-06-28.
  - **Ann Arbor:** the only reference monitor within 25 km is in **Ypsilanti**, 12.9 km from Ann Arbor City Hall.
  - **Warren:** the nearest reference monitor is 9.2 km away in Detroit (Detroit-E7 Mile, from 2024 only); all others are 14+ km away.
  - **Brownsville:** the reference record has a gap. Brownsville C80 ends 2023-04-04 and Brownsville East 6th starts 2024-02-01.
  - **Shared circles:** Detroit and Warren share 52 sensors; Eugene and Springfield share all 8. Springfield's own city hall has a reference monitor (0.15 km).
  - **Reference sensors that stopped reporting** (city × sensor rows): 14 ended between 2016 and 2021, 11 in 2023, 3 in 2024, 8 in 2025; 85 have data in 2026.
  - 30 sensors (29 low-cost, 1 reference) have no first/last date in OpenAQ. None are mobile.
- **Judgment calls:**
  - **25 km search radius**, the API's maximum, as a search net only; assignment happens in Step 2. **Claude's choice, approved by Gina.**
  - **City hall as the center**, reusing Dish's coordinates where they exist. **Claude's choice, approved by Gina.**
  - **Addresses for the 6 geocoded city halls supplied by Claude.** The Census matched all 6. Gina to spot-check Raymondville, Delano and Springfield. **Claude's choice, approved by Gina; verification pending.**
  - **Warren's coordinates from Gina** (Google Maps place pin, not the map-view center, which was ~200 m west). **Changed by Gina.**
  - **"Reference" vs "low-cost" taken from OpenAQ's `isMonitor` flag.** **Claude's choice, approved by Gina.**
- **Problem during the step:** The first run stopped at Warren (no geocoder match) before contacting OpenAQ, as designed. It had written 7 geocoder files. Claude deleted Warren's empty response before the rerun (a raw file, but a failed lookup); the other 6 were overwritten with identical results by the rerun.
- **Known limitation:** Los Angeles, Phoenix and San Diego extend past 25 km from city hall in places. Step 2 will check city limits and fill any gap with an extra search.

### Decision OA-D1 · OpenAQ · 2026-09-27 · Gina
- **What:** Set the approach for the OpenAQ PM2.5 data before any data was pulled.
  1. **Cities:** the 15 Gina listed plus **Boston** (added by Gina).
  2. **Proximity:** sensors inside **city limits**. Where a city has none, fall back to the **nearest sensors outside its limits that are not inside another listed city**, and log it. A sensor belongs to one city only. **Claude's recommendation, approved by Gina.**
  3. **Sensor types:** download both reference and low-cost sensors, flag them in the inventory, and decide what goes into the city averages later. **Claude's recommendation, approved by Gina.**
  4. **Time resolution: daily** (OpenAQ 24-hour summaries), not hourly. **Changed by Gina** (chose daily from Claude's options).
  5. **Study period ends 2026-09-25**, matching Dish's Decision D1. **Changed by Gina** (from "most recent date in September 2026").
  6. **File layout:** one sensor inventory for all cities, plus one daily file per city; raw API responses saved as received. **Claude's recommendation, approved by Gina.**
- **Open for Step 2:** how far the fallback may reach (Claude suggested a 10–15 km cap beyond city limits, with "no local sensor" beyond that).

### Step 11 · descriptions · 2026-09-27 · Gina + Claude
- **What:** Changed the data descriptions from Markdown to CSV. Each table row from `data_descriptions.md` became a CSV row, with the file name in its own column; the Markdown file was removed. Wording unchanged.
- **Why:** Gina asked for a CSV instead.
- **Input:** `data/descriptions/data_descriptions.md` (Step 10)
- **Script:** none (one-off format conversion by Claude)
- **Rows in → out:** 37 descriptions → 37 CSV rows. Checked again that the columns listed match each raw file's header exactly.
- **Output:** `data/descriptions/data_descriptions.csv` (columns: file, column, description, type_units, source, formula_or_derivation). Blank cells = no formula (shown as "—" in the Markdown).
- **Judgment calls:**
  - **CSV replaces the Markdown**, rather than keeping both. **Changed by Gina.**
  - **The Markdown file's intro text was not carried over.** It said the file covers Gina's raw files only and is updated with every new raw file; both points are recorded in Step 10. **Claude's choice, flagged to Gina in chat; not yet approved.**

### Step 10 · descriptions · 2026-09-27 · Gina + Claude
- **What:** Wrote a column-by-column description of every raw file Gina has added: what each value is, its type or units, its source, and the formula when it's calculated. **Documentation only: no data changed.**
- **Why:** So anyone reading the raw files knows what each column means and where it comes from, without having to trace the scripts.
- **Input:** the 5 files in `data/raw/city-selection/`; the ALA *State of the Air 2026* report (About This Report, pp. 7–12, from `~/Desktop/MDE/dataviz/State-of-the-Air-2026-Report.pdf`) for the ranking methods; the Media Cloud API endpoints used in Steps 2–6.
- **Script:** none (documentation, written by Claude).
- **Rows in → out:** 5 files, 37 columns → 37 descriptions. Checked that the columns described match each file's header exactly.
- **Output:** `data/descriptions/data_descriptions.md`
- **Judgment calls:**
  - **Markdown, one section per raw file**, in a new `data/descriptions/` folder. **Changed by Gina** (Claude proposed a CSV in `data/raw/`).
  - **Only Gina's raw files**, not Dish's METAR files. **Changed by Gina** (Claude asked).
  - **The file will be updated every time a new raw file is added**, with a log entry each time. **Specified by Gina.**
  - **Downstream formulas included** where a raw column feeds one (e.g. coverage index = `relevant_total_stories` ÷ `source_count`). **Claude's choice, approved by Gina.**
  - **ALA method summarized from the report itself.** Short-term: county weighted average of unhealthy 24-hour PM2.5 days in 2022–2024 (orange ×1, red ×1.5, purple ×2, maroon ×2.5, ÷ 3). Year-round: county annual PM2.5 design value. In both, the metro takes its worst county. **Claude's choice, approved by Gina.**

### Step 9 · city-selection · 2026-09-27 · Gina + Claude
- **What:** Started this log and filled in Steps 1–8 retroactively. Created `data/raw/city-selection/`, `data/processed/city-selection/` (one subfolder per step) and `scripts/city-selection/`, and added the scripts and intermediate files from the analysis.
- **Why:** Gina asked for a log in the same format as Dish's, and for the city-selection analysis to be traceable in the repo.
- **Input:** the local files in `~/Desktop/MDE/dataviz/` (`mediacloud_air_pollution_by_state.csv`, `news_coverage_by_city.csv`, `air_pollution_cities_by_state.csv`), Gina's `news_coverage_by_state_cross_pm.numbers`, and the commands and terminal output from this chat session.
- **Script:** `scripts/city-selection/08_top3_by_group.py` was written and run in this step (see Step 8). All other scripts are copies of what ran; see each step for how exact they are.
- **Rows in → out:** no data values changed. Checks run: raw city counts = `news_coverage_by_city.csv` (36/36 match); raw state counts = `mediacloud_air_pollution_by_state.csv` (10/10); ALA transcription = ranks in Gina's `air_pollution_cities_by_state.csv` (15/15).
- **Output:** `data/raw/city-selection/*`, `data/processed/city-selection/step03_…/` to `step08_…/`, `scripts/city-selection/*`, this log.
- **Judgment calls:**
  - **API key removed from all scripts.** Every command originally had Gina's Media Cloud key typed inline; the committed scripts read it from the `MEDIACLOUD_API_KEY` environment variable instead. This is the only edit to the scripts as run. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Raw API responses transcribed from terminal output.** The API responses were printed to the terminal but not saved as files when they ran. The raw CSVs were written from those printed lines. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Some scripts are shell scripts (`.sh`)**, not `.py`, because the steps ran as `curl` loops. Kept as run rather than rewritten. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **`news_coverage_ala_comparison.xlsx` left where Gina asked for it** (`data/processed/city-selection/`, commit `b2a5aab`), not moved into a step subfolder. **Claude's choice, flagged to Gina in chat; not yet approved.**
- **Gaps:**
  - The original script for Step 6 (`cities.py`) and the screenshots from Step 1 were in a scratch folder that was cleared when the chat session restarted. The script was reconstructed from the chat record (Step 6). The ALA list was transcribed into a CSV instead.
  - `mediacloud_air_pollution_US_national_vs_state.csv` (Step 4) is no longer in `~/Desktop/MDE/dataviz/`. The repo copy was regenerated by re-running `04b_write_us_csv.py`, which contains the values as typed in on 2026-09-26.

### Step 8 · city-selection · 2026-09-27 · Gina + Claude
- **What:** Listed the top 3 cities in each pollution × coverage group, for both state-level and city-level coverage (Step 7 groups).
- **Why:** Gina asked for the strongest examples of each group, to compare the two methods.
- **Input:** `data/processed/city-selection/step06_city_coverage/news_coverage_by_city.csv`, `step03_state_coverage/mediacloud_air_pollution_by_state.csv`, `data/raw/city-selection/ala_sota2026_pm25_rankings_transcribed.csv`
- **Script:** `scripts/city-selection/08_top3_by_group.py` (written in Step 9 to reproduce the table; the original was worked out in chat from the Step 7 check output)
- **Rows in → out:** 36 cities → 8 ranked lists (4 groups × 2 methods), every group member ranked, not only the top 3.
- **Output:** `data/processed/city-selection/step08_top3/quadrant_rankings.csv`
- **Result (top 3):**

  | Group | State-level | City-level |
  |---|---|---|
  | High pollution / High coverage | Bakersfield, Delano, Fresno (CA) | Los Angeles (CA), Fairbanks (AK), San Diego (CA) |
  | High pollution / Low coverage | Eugene, Springfield (OR), Brownsville (TX) | Delano (CA), Bakersfield (CA), Raymondville (TX) |
  | Low pollution / High coverage | Detroit, Warren, Ann Arbor (MI) | Detroit (MI), Phoenix (AZ), San Francisco (CA) |
  | Low pollution / Low coverage | Phoenix, Mesa (AZ), McAllen (TX) | Edinburg (TX), Steubenville (OH), McAllen (TX) |
- **Judgment calls:**
  - **Ranking inside each group:** high-coverage groups by index (highest first); high pollution / low coverage by pollution score (worst first), then lower index; low / low by index (lowest first). State-level high / high by pollution score, because all 11 California cities share one state index. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Ties broken by the order of Gina's ALA list** (city row number). **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Only the top 3 shown in chat.** **Changed by Gina** (asked for the top 3 after Claude began listing every member).
- **Correction:** In chat, Claude gave **Houston (TX)** as #3 for state-level low pollution / low coverage. Under the stated tie-break, #3 is **McAllen (TX)**: Houston, Pasadena, McAllen and Edinburg all have Texas's state index (10.92), and McAllen-Edinburg comes before Houston-Pasadena in Gina's list. This was a Claude slip, caught when the script reproduced the table. No data changed.
- **Caveat for the appendix:** Delano is also a surname, so its low count may include unrelated stories. Without it, Harlingen (TX) is #3 in city-level high pollution / low coverage.

### Step 7 · city-selection · 2026-09-27 · Gina + Claude
- **What:** Built one workbook crossing the ALA PM2.5 ranks with state-level and city-level coverage, one row per city (36). Each city gets a **pollution score** (the mean of its metro's available ALA ranks), a coverage index and rank under each method, and a group ("High/Low pollution / High/Low coverage") under each method. It also flags whether the group changes between methods. Indexes, ranks, thresholds and groups are live Excel formulas.
- **Why:** Gina asked to compare how rankings change between state-level and city-level mentions, grouped by pollution and coverage.
- **Input:** Gina's `news_coverage_by_state_cross_pm.numbers` (Step 5; ALA ranks + state-level data) and `news_coverage_by_city.csv` (Step 6)
- **Script:** `scripts/city-selection/07a_rebuild_city_jsonl.py` (rebuilds the Step 6 results file from the CSV, since the original had been cleared with the scratch folder), then `scripts/city-selection/07b_build_comparison_workbook.py` (exact copy of the script run, `build.py`)
- **Rows in → out:** 17 rows in Gina's file (15 metros; Pittsburgh-Weirton-Steubenville split into PA, OH and WV rows) + 36 city rows → **36-row Comparison sheet**, a 10-row States sheet and a Method sheet. No values removed.
- **Checks after running:** LibreOffice isn't installed, so the formulas couldn't be recalculated before saving (the file calculates when opened). The same thresholds, ranks and groups were computed separately in Python, and the table given in chat comes from that check. Thresholds: pollution ≤ 7.5, state coverage ≥ 12.80, city coverage ≥ 0.244. **16 of 36 cities change group** between methods.
- **Output:** `~/Desktop/MDE/dataviz/news_coverage_ala_comparison.xlsx`. Pushed to the repo at Gina's request: `data/processed/city-selection/news_coverage_ala_comparison.xlsx` (commit `b2a5aab`).
- **Judgment calls:**
  - **Pollution score = mean of the ALA short-term and year-round ranks**, "high pollution" = score at or below the median over the 36 city rows. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **San Diego-Chula Vista-Carlsbad and Houston-Pasadena have no short-term rank**; their score uses the year-round rank only. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **State coverage threshold = median of the 10 state indices**, not of the 36 city rows. The latter would give California's 14 cities most of the weight and put Pennsylvania (20.27) just below the line. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **City coverage threshold = median of the 36 city indices.** **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **The fourth group (low pollution / low coverage)** was added. Gina asked for three groups, but some cities fall in none of them. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Ranks: 1 = highest index; ties share a rank** (Excel `RANK`). **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Pittsburgh-Weirton-Steubenville:** each city uses its own state's state-level row (Pittsburgh–PA, Weirton–WV, Steubenville–OH). **Claude's choice, flagged to Gina in chat; not yet approved.**
- **Caveat for the appendix:** "Low pollution" is relative. Every metro here is among the most PM2.5-polluted in the US. Coverage indexes are not comparable across states in absolute terms: the index divides by the collection's source count (77 in Alaska vs 1,283 in California), so small collections inflate it (Fairbanks: 144 stories, index 1.87).

### Step 6 · city-selection · 2026-09-26/27 · Gina + Claude
- **What:** Counted Total Stories for `("air pollution" OR "air quality") AND "[city]"` for each of the **36 cities** in the ALA list, each searched on its own in its state's collection, 2024-09-25 to 2026-09-25.
- **Why:** State-level counts give every city in a state the same number. City-level counts show which places the coverage is actually about. Method specified by Gina.
- **Input:** Media Cloud API (`/api/search/total-count`), collections from Step 2; city list from Step 1
- **Script:** `scripts/city-selection/06_city_counts.py` (**reconstructed**: the original `cities.py` was lost with the scratch folder; rebuilt from the chat record, including the mid-step fix below), then `06b_write_city_csv.py` (exact copy)
- **Rows in → out:** 15 metro entries → 36 city queries → 36 counts (all returned a count). Largest: Los Angeles 6,442; smallest: Raymondville 4.
- **Output:** `data/raw/city-selection/mediacloud_city_counts_responses.csv` (raw responses); `data/processed/city-selection/step06_city_coverage/news_coverage_by_city.csv` (also saved as `~/Desktop/MDE/dataviz/news_coverage_by_city.csv`, file name chosen by Gina)
- **Judgment calls:**
  - **Parentheses added:** `("air pollution" OR "air quality") AND "[city]"`. Gina's text was `"air pollution" OR "air quality" AND "[city]"`, which Media Cloud would read as `"air pollution" OR ("air quality" AND "[city]")`. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Multi-state metro:** Pittsburgh searched in Pennsylvania, Weirton in West Virginia, Steubenville in Ohio (each city's home state only). **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Ambiguous names kept as searched and flagged** in an "Ambiguity note" column: Springfield, College, Pasadena, Warren, Mesa, Carmel, Delano. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Pacing:** 20 s between queries and up to 8 tries 30 s apart, to avoid Media Cloud's rate limit (seen in Step 3). **Claude's choice.**
- **Problem during the step:** The first run (2026-09-26) used Python's `urllib`, which failed the SSL certificate check on this Mac. All 7 requests it made errored and no counts were returned. Claude had told Gina it was running before checking the first result. Claude stopped it, switched the requests to `curl`, deleted the empty results file and reran all 36. The rerun started on 2026-09-26 and finished on 2026-09-27.
- **Caveat for the appendix:** the AND only requires that the city name appear somewhere in a story that mentions air pollution or air quality. It doesn't show the story is about that city's air.

### Step 5 · city-selection · 2026-09-26 · Gina
- **What:** Gina combined the ALA ranks (Step 1) with the state-level Media Cloud results (Step 3) in one table, one row per metro area and state: metro, city_1–3, state, ALA short-term and year-round PM2.5 rank, then all Step 3 columns. The Pittsburgh-Weirton-Steubenville metro has 3 rows (PA, OH, WV). Done by Gina in Numbers, without Claude.
- **Why:** Puts pollution rank and state coverage side by side for each metro.
- **Input:** ALA rankings (Step 1), `mediacloud_air_pollution_by_state.csv` (Step 3)
- **Script:** none (manual, in Numbers)
- **Rows in → out:** 15 metros + 10 states → 17 rows.
- **Output:** `data/processed/city-selection/step05_ala_cross_gina/air_pollution_cities_by_state.csv` (22:11 version) and `news_coverage_by_state_cross_pm.numbers` (22:15 version, columns renamed, e.g. `ala_shortterm_pm25_rank_2026`)
- **Judgment calls:** Gina's own (column layout, one row per state for the multi-state metro).

### Step 4 · city-selection · 2026-09-26 · Gina + Claude
- **What:** Ran the search once in the national collection instead of the state collections: `("air pollution" OR "air quality") AND "[State]"` in **United States - National** (`cs=34412234`, 246 sources), one query per state (10), 2024-09-25 to 2026-09-25.
- **Why:** Gina wanted to see whether results differ from the per-state collections.
- **Input:** Media Cloud API (`/api/sources/collections/`, `/api/search/total-count`)
- **Script:** `scripts/city-selection/04_us_national_counts.sh` (exact copy), then `04b_write_us_csv.py` (exact copy except the output path)
- **Rows in → out:** 10 queries → 10 counts. California 4,953 · Texas 2,153 · Michigan 1,408 · Arizona 1,063 · Pennsylvania 1,032 · Ohio 986 · Oregon 905 · Indiana 720 · Alaska 345 · West Virginia 335.
- **Output:** `data/raw/city-selection/mediacloud_us_national_counts_responses.csv`; `data/processed/city-selection/step04_us_national/mediacloud_air_pollution_US_national_vs_state.csv` (regenerated in Step 9; the local copy is gone)
- **Judgment calls:**
  - **"The US collection" = United States - National (34412234).** The other two collections found (United States (Conspiracies), United States (Far-Right)) were not used. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Parentheses** around the OR, as in Step 6. **Claude's choice, flagged to Gina in chat; not yet approved.**
- **Findings:** Rankings shift a lot between methods. Michigan is #1 by state-collection index but #3 nationally; West Virginia is #2 vs #10; Arizona is #9 vs #4. Every query uses the same 246 sources, so the national index (stories ÷ 246) ranks states in the same order as raw counts.
- **Caveat for the appendix:** state names also match unrelated uses (e.g. "Indiana Jones"), and a national story can list several states.

### Step 3 · city-selection · 2026-09-26 · Gina + Claude
- **What:** Counted Total Stories (Media Cloud "Total Attention") for `"air pollution" OR "air quality"` in each of the 10 state collections, 2024-09-25 to 2026-09-25, and computed **index = total stories ÷ sources in the collection**.
- **Why:** Gina's method, to compare how much each state's local media cover air quality.
- **Input:** Media Cloud API (`/api/search/total-count`), collection IDs and source counts from Step 2
- **Script:** `scripts/city-selection/03_state_counts.sh` (exact copy), then `03b_write_state_csv.py` (exact copy)
- **Rows in → out:** 10 queries → 10 counts. The first attempt returned counts for California and Oregon only; the other 8 were rejected with "rate limited" and succeeded on a paced second attempt. Index: Michigan 23.01 · West Virginia 21.65 · California 20.41 · Pennsylvania 20.27 · Indiana 12.87 · Oregon 12.72 · Ohio 11.76 · Texas 10.92 · Arizona 8.71 · Alaska 7.30.
- **Output:** `data/raw/city-selection/mediacloud_state_counts_responses.csv`; `data/processed/city-selection/step03_state_coverage/mediacloud_air_pollution_by_state.csv` (also `~/Desktop/MDE/dataviz/`, moved there at Gina's request)
- **Judgment calls:**
  - **One query per state, not per metro or city.** The query has no city term, so every city in a state would get the same count. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **"Total Stories" = the API's `relevant` count** (stories matching the query). The API also returns `total`, all stories in the collection for the period, which is kept in the raw file. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - **Source count = the collection's current `source_count`**, which can change if Media Cloud edits the collection. **Claude's choice, flagged to Gina in chat; not yet approved.**
  - Index rounded to 2 decimals in the CSV. **Claude's choice.**

### Step 2 · city-selection · 2026-09-26 · Gina + Claude
- **What:** Found each state's Media Cloud collection and its number of sources, for the 10 states in the ALA list (CA, OR, TX, AK, MI, IN, PA, OH, WV, AZ).
- **Why:** Step 1 of Gina's method ("In Collections, select the specific state").
- **Input:** Media Cloud API (`/api/sources/collections/?name=<state>`)
- **Script:** `scripts/city-selection/02_find_state_collections.sh` (exact copy)
- **Rows in → out:** 10 name searches → 12 collections returned → 10 kept (one "[State], United States - State & Local" collection per state). Sources: California 1,283 · Texas 593 · Ohio 256 · Pennsylvania 249 · Michigan 203 · Indiana 167 · Oregon 145 · Arizona 139 · West Virginia 81 · Alaska 77.
- **Output:** `data/raw/city-selection/mediacloud_collections_lookup.csv` (all collections returned, with a `kept` column; includes the national collections found in Step 4)
- **Judgment calls:**
  - Searching "California" also returned Baja California and Baja California Sur (Mexico); only the US collection was kept. **Claude's choice.**
- **Note:** A first attempt used the `mediacloud` Python client and hung for several minutes with no output. The likely cause is the same SSL problem found in Step 6. Claude switched to `curl`. The client's results arrived later and matched; they weren't used.

### Step 1 · city-selection · 2026-09-26 · Gina
- **What:** Gina supplied the list of metro areas and their ALA *State of the Air 2026* PM2.5 ranks (short-term and year-round) as a screenshot: 15 metro areas, named City1-City2-State, one with three states (PA-OH-WV).
- **Why:** Defines the cities for the city-selection analysis.
- **Input:** screenshot of the ALA ranking table (supplied twice in chat, same content)
- **Script:** none
- **Rows in → out:** 15 metros → 36 individual cities and 10 states.
- **Output:** `data/raw/city-selection/ala_sota2026_pm25_rankings_transcribed.csv`, transcribed by Claude in Step 9 (the screenshots weren't kept). Checked against the ranks Gina typed into her Step 5 file: 15/15 match.
- **Judgment calls:**
  - **The list may be incomplete.** Both screenshots end at Houston-Pasadena, TX, with a scroll arrow below, so rows may be missing. Flagged to Gina twice in chat; not yet confirmed. **Open item.**
  - "—" (not ranked) recorded as blank. **Claude's choice.**

---
**City-selection status (2026-09-27):** Steps 1–8 complete and logged retroactively (Step 9); raw-file descriptions in `data/descriptions/data_descriptions.csv` (Steps 10–11). Open items: (1) Gina to review the judgment calls marked "not yet approved"; (2) confirm whether the ALA list continues past Houston-Pasadena; (3) check whether the Media Cloud API includes the end date (2026-09-25) in its counts; (4) ambiguous city names may inflate some city-level counts.
