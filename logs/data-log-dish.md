# Data log — Dish

Project 2, MDE Studio ("AI-Augmented Storytelling with Data" · Natural + Artificial).
Running plain-language log of every data step Dish runs with Claude. This log feeds the Algorithmic Forensics Appendix.
Gina keeps her own log; the two may be combined later.

**Datasets in this log:** METAR visibility · gridMET actual temperature · UTCI felt heat
**Cities (10):** Bakersfield CA · Fresno CA · Los Angeles CA · Fairbanks AK · Eugene OR · Brownsville TX · Detroit MI · Pittsburgh PA · San Francisco CA · Boston MA
**Study period:** 2016-01-01 – 2026-09-25, daily (changed from 09-26 on 2026-09-27, see Decision D1) · **Heat baseline:** 1991–2020
**Scale:** city limits. Expanded only when a dataset can't resolve the city, and logged when it is.

## Rules
1. One step at a time. Claude explains the step and shows the script, and Dish approves before it runs.
2. Raw downloads in `data/raw/` are never edited. Every change writes a new file to `data/processed/`.
3. Every step saves its exact script to `scripts/<dataset>/NN_<step-name>.py` and gets an entry below.
4. Any threshold, filter or default Dish didn't specify is flagged as **Claude's choice, approved by Dish** or **changed by Dish**.

## Entry format
Step · dataset · date · who ran it | What (plain language) | Why | Input file(s) | Script | Rows/values in → out (and what was removed or changed) | Output file | Judgment calls

---

### Step 0 · setup · 2026-09-27 · Dish + Claude
- **What:** Created the folder layout (`data/raw/metar/`, `data/processed/metar/`, `scripts/metar/`, `logs/`) and started this log. Added empty `.gitkeep` files so git tracks the empty folders.
- **Why:** Gives raw data, processed data, scripts and the log each a fixed place, so every change can be traced.
- **Input / output:** none (setup only) · **Script:** none (folder setup only)
- **Judgment calls:**
  - Layout proposed in the handoff doc. **Approved by Dish.**
  - Log named `data-log-dish.md` rather than `data-log.md`, because Dish and Gina keep separate logs for now. **Claude's choice, following Dish's decision to keep logs separate.**

### Decision D1 · all datasets · 2026-09-27 · Dish
- **What:** The study period now ends **2026-09-25** instead of 2026-09-26, for all three datasets (METAR, gridMET, UTCI).
- **Why:** All 10 METAR raw downloads end at Sep 25, 23:5x local time. The IEM end date was set to Sep 26, and IEM leaves out the end date itself. Rather than download Sep 26 separately, Dish chose to end the study period a day early and keep the raw files as downloaded. gridMET and UTCI pulls will end at the same date for consistency.
- **Options considered:** (A) download Sep 26 as a separate raw file per city; (B) re-download all 10 files; (C) end at Sep 25. **Changed by Dish: chose C.**
- **Note on commit `50a314b`:** its message says "Set up data folders and Dish's data log (Step 0)", but it also contains the 10 untouched raw METAR CSVs (and two Finder `.DS_Store` files), which were added to `data/raw/metar/` before the commit ran.

### Step 1 · METAR · 2026-09-27 · Dish + Claude
- **What:** Counted what's in each raw METAR file, per station: total reports, first/last report, days with data, blank visibility, "0 mile" visibility, unparseable visibility, blank humidity, reports with weather codes. **Read-only: nothing was removed or changed.**
- **Why:** A "before" headcount, so the removed/kept counts in every later step can be checked against it.
- **Input:** the 10 files `data/raw/metar/metar_<city>_raw.csv` (12 stations)
- **Script:** `scripts/metar/01_inventory.py`
- **Rows in → out:** 1,348,327 raw reports read → 12-row summary table. 0 rows removed.
- **Output:** `data/processed/metar/metar_inventory.csv`
- **Findings:**
  - All 12 stations run from 2016-01-01 to 2026-09-25 local time. The full span is 3,921 days.
  - Days missing entirely: **BFL 5** (3,916 of 3,921), **BRO 1** (3,920). All other stations have every day.
  - Unparseable visibility values: 0 at every station.
  - Blank visibility: 7 (PIT) to 575 (BRO). "0 mile" readings: 0 to 31 (LAX has the most).
  - Blank humidity is high at **Fairbanks (PAFA): 2,638**, vs 64–565 at the other stations. This matters for the RH ≥ 90% filter in Step 5.
  - Fairbanks is filed in IEM as **PAFA**, the 4-letter code for FAI (Fairbanks International).
- **Judgment calls:** none (counting only).

### Step 2 · METAR · 2026-09-27 · Dish + Claude
- **What:** Threw out broken visibility readings: reports with a **blank** visibility value or **exactly 0 miles**. All other reports were copied over unchanged (read and written as text).
- **Why:** A blank carries no information, and "0 miles" reports in IEM are almost always sensor glitches, not real zero visibility (per the handoff procedure).
- **Input:** `data/raw/metar/metar_<city>_raw.csv` (10 files, not modified; checked with `git diff` afterwards: no changes to raw files)
- **Script:** `scripts/metar/02_drop_broken.py`
- **Rows in → out:** 1,348,327 → **1,346,613**. Removed 1,714 (0.13%): **1,626 blank**, **88 zero**. Per station, 0.025% (PIT, SFO) to 0.463% (BRO). Built-in check passed: kept + removed = input.
- **Output:** `data/processed/metar/step02_valid/metar_<city>_valid.csv` (kept), `metar_<city>_removed.csv` (dropped rows with `removed_reason`), `step02_summary.csv` (per-station counts)
- **Judgment calls:**
  - Only **exactly 0.00 mi** counts as a glitch. Small non-zero values (e.g. 1/16, 1/4 mi) are kept, since they could be real smoke or fog; fog is handled in Step 5. **Claude's choice, approved by Dish.**
  - Dropped rows saved to their own files for audit (not in the handoff procedure). **Claude's choice, approved by Dish.**
  - Each step's outputs go in their own subfolder (`step02_valid/`). **Claude's choice, approved by Dish.**
- **Correction:** Before running, Claude estimated ~1,652 blanks from Step 1; the correct Step 1 sum is 1,626, which matches what was removed. The estimate was a Claude arithmetic slip, not a data change.

### Step 3 · METAR · 2026-09-27 · Dish + Claude
- **What:** Collapsed reports to **one row per airport per clock hour**, keeping the report with the **lowest visibility** (the haziest). Each hour also records how many reports it had, every weather code seen in any report that hour (`wx_any_in_hour`), and the highest RH that hour (`relh_max_in_hour`).
- **Why:** Hours with many "special" reports shouldn't count more in the daily average. Keeping the lowest keeps short haze or smoke events. The hour-level codes and RH let Step 5 catch wet hours even when the wet signal wasn't on the haziest report.
- **Input:** `data/processed/metar/step02_valid/metar_<city>_valid.csv`
- **Script:** `scripts/metar/03_one_per_hour.py`
- **Rows in → out:** 1,346,613 reports → **1,125,665 station-hours** (220,948 reports merged into their hour). Built-in check passed. Station-hours per station: 93,169 (BRO) to 94,048 (SFO), out of 94,104 possible (3,921 days × 24), i.e. 99.0–99.9% hourly coverage.
- **Output:** `data/processed/metar/step03_hourly/metar_<city>_hourly.csv` (columns: station, hour, picked_report_time, vsby, relh, wxcodes, n_reports_in_hour, relh_max_in_hour, wx_any_in_hour), `step03_summary.csv`
- **Judgment calls:**
  - A report belongs to the **clock hour it was filed in** (1:53 pm → 1 pm hour), not the nearest hour. **Claude's choice, approved by Dish.**
  - Weather codes and max RH from **all reports in the hour** are carried forward for the Step 5 wet filter. **Claude's choice, approved by Dish.**
  - Ties on lowest visibility go to the **earliest** report. **Claude's choice, approved by Dish.**
- **Known limitation:** Timestamps are local, so on the November daylight-saving fall-back night, the repeated 1am hour is merged into one. This affects 1am only, outside the 8am–6pm daytime window.

### Step 4 · METAR · 2026-09-27 · Dish + Claude
- **What:** Kept only daytime station-hours, **8:00 am–5:59 pm local** (clock hours 8–17, 10 per day). Night hours dropped; kept rows copied unchanged.
- **Why:** Visibility stands in for haze people can see, which happens during waking daylight hours. This also avoids nighttime fog and inversions.
- **Input:** `data/processed/metar/step03_hourly/metar_<city>_hourly.csv`
- **Script:** `scripts/metar/04_daytime_only.py`
- **Rows in → out:** 1,125,665 → **469,366 station-hours**. Removed 656,299 night hours. Built-in check passed. Daytime coverage per station: 99.05% (AGC) to 99.95% (LAX, SFO) of the 39,210 possible (3,921 days × 10).
- **Output:** `data/processed/metar/step04_daytime/metar_<city>_daytime.csv`, `step04_summary.csv`
- **Judgment calls:**
  - "8am–6pm" read as **8:00–17:59** (10 hours), not through 18:59. **Claude's choice, approved by Dish.**
  - **No removed-rows file** for this step: night hours are recoverable exactly from the Step 3 files; counts are in the summary. **Claude's choice, approved by Dish.**
  - **Fairbanks uses the same fixed window** as the other cities, for comparability. **Claude's choice, approved by Dish.**
- **Caveat for the appendix:** In Fairbanks winter, much of 8am–6pm is dark (and in summer it's light nearly all night). The ASOS sensor measures visibility the same way in the dark, so values are valid, but "haze people see" is looser there in winter.

### Step 5a · METAR · 2026-09-27 · Dish + Claude
- **What:** Read-only audit of the daytime data: counted station-hours containing each weather code (as written, and by phenomenon with intensity/vicinity/descriptor prefixes stripped, split into "at the airport" vs "vicinity only"), and hours with RH ≥ 90% (haziest report vs any report in the hour) or blank RH. **Nothing removed.**
- **Why:** So the Step 5b "remove water" filter decisions rest on real counts rather than assumptions.
- **Input:** `data/processed/metar/step04_daytime/metar_<city>_daytime.csv` (469,366 station-hours)
- **Script:** `scripts/metar/05a_audit_weather_codes.py`
- **Rows in → out:** 469,366 read → 0 removed. Three summary tables.
- **Output:** `data/processed/metar/step05a_wx_audit/wxcode_counts.csv`, `phenomenon_counts.csv`, `rh_summary.csv`
- **Findings:**
  - **Mist (BR) and rain (RA)** are the most common water codes everywhere (roughly 900–6,700 hours per city each).
  - **Snow (SN)** is large in Fairbanks (4,367), Pittsburgh (3,643), Detroit (3,257) and Boston (809); ~0 in the California cities.
  - **Fog** variants seen: FG, FZFG (freezing), BCFG (patches), MIFG (shallow), PRFG (partial). Vicinity-only fog (VCFG): Fairbanks 139, LA 30, SFO 3.
  - **Ice crystals (IC) never appear**, including at Fairbanks, although the handoff expected them there.
  - **The signals we want to keep do appear:** haze (HZ) is highest in Bakersfield (5,213), Fresno (3,867), Detroit (2,237) and LA (2,172). Smoke (FU) is highest in Fresno (830), Bakersfield (590), Fairbanks (478), Eugene (312).
  - Other codes seen: thunder (TS, VCTS), hail (GR, GS), ice pellets (PL), unknown precip (UP), dust (DU, BLDU), blowing snow (BLSN), squalls (SQ), funnel cloud (FC), sandstorm (SS). There's also a stray bare "-" token (a formatting artifact in the raw codes).
  - **RH ≥ 90%:** using the hour's highest RH flags 4–11% more hours than the haziest report's RH alone (e.g. BOS 3,687 vs 3,471).
  - **Blank RH for the whole hour:** Fairbanks 742, every other station 18–66.
- **Judgment calls:** none (counting only). Code splitting follows the standard METAR present-weather format.

### Step 5b · METAR · 2026-09-27 · Dish + Claude
- **What:** Removed "wet" daytime station-hours: any hour where a report showed fog, mist, rain, drizzle, snow or other frozen precip (FG, BR, RA, DZ, SN, SG, IC, PL, GR, GS, UP, any intensity or descriptor, e.g. FZFG, BCFG, TSRA, FZRA, BLSN), or vicinity fog (VCFG), or where the hour's highest RH was ≥ 90%. Hours with blank RH were kept and flagged `rh_missing = 1`.
- **Why:** Water droplets and ice reduce visibility the same way particles do. Removing wet hours leaves visibility that mainly reflects haze, smoke and dust.
- **Input:** `data/processed/metar/step04_daytime/metar_<city>_daytime.csv`
- **Script:** `scripts/metar/05b_remove_water.py`
- **Rows in → out:** 469,366 → **408,597 station-hours**. Removed 60,769 (12.9%). Per station: BFL 4.5%, SFO 5.7%, FAT 6.3%, LAX 6.5%, BRO 9.9%, DET 13.3%, BOS 15.7%, DTW 16.3%, AGC 17.1%, PIT 18.6%, EUG 19.3%, **PAFA 22.0%**. Built-in check passed.
- **Check after running:** the only codes left in kept hours are HZ, FU, DU, BLDU, TS, VCTS, SQ and one stray "-" artifact (Fresno); no water codes remain. Most haze/smoke hours survived (e.g. BFL haze 5,099 of 5,213; FAT smoke 830 of 830). The haze/smoke hours that were removed also had a wet code or RH ≥ 90% in the same hour.
- **Kept with blank RH (`rh_missing = 1`):** 427 at Fairbanks; 5–55 elsewhere.
- **Output:** `data/processed/metar/step05_dry/metar_<city>_dry.csv` (kept, plus `rh_missing` column), `metar_<city>_removed.csv` (with `removed_reason`), `step05_summary.csv`
- **Judgment calls (all proposed by Claude from the Step 5a counts):**
  1. Fog, mist, rain, drizzle removed at any intensity/type. **Handoff procedure; confirmed by Dish.**
  2. **Snow and all frozen precip removed** (the handoff said "check snow"). **Claude's choice, approved by Dish.**
  3. **Vicinity fog (VCFG) removed.** **Claude's choice, approved by Dish.**
  4. Thunder without precip (TS, VCTS) **kept**. **Claude's choice, approved by Dish.**
  5. Dust, sand, squalls, funnel cloud **kept**. **Claude's choice, approved by Dish.**
  6. RH ≥ 90% tested on the **hour's highest RH**, not just the haziest report. **Claude's choice, approved by Dish.**
  7. **Blank-RH hours kept** and flagged. **Claude's choice, approved by Dish.**
  8. Removed hours saved to their own file for audit. **Claude's choice, approved by Dish.**
- **Caveats for the appendix:** Removing snow means the northern cities' (Fairbanks, Pittsburgh, Detroit, Boston) winter daily values rest on fewer hours. The RH filter may also drop some humid pollution episodes (known caveat from the handoff). Claude's pre-run estimate of "10–25% removed" was too high for the California cities (actual 4.5–6.5%).

### Method note M1 · METAR Step 7 formula · 2026-09-27 · Dish + Claude
- **What:** Documented where the Step 7 conversion comes from, before running it. Light extinction b_ext (km⁻¹) = 3.912 ÷ visual range (km) is the **Koschmieder (1924) relation**, with a 2% contrast threshold (3.912 = ln 50). Full citations and how each was verified are in `docs/references.md`.
- **Who chose it:** The formula was specified by Dish in the handoff procedure. Claude looked up and verified the citations at Dish's request.
- **Why convert at all:** Extinction rises roughly in proportion to the amount of haze or smoke (Pitchford & Malm, 1994), while visual range bunches up near the 10-mile cap on clean days. Averaging extinction and converting back to miles (Step 9) keeps a few clear hours from hiding a smoky morning.
- **Assumptions to state in the appendix:**
  1. **2% contrast threshold.** The WMO meteorological optical range uses 5% (constant ≈ 3.0). That would scale every value by the same ~0.77, changing absolute numbers but not patterns, rankings or anomalies.
  2. **Uniform air along the sight path, daylight viewing.** Partly addressed by the 8am–6pm window (Step 4).
  3. **10-mile ceiling → extinction floor of 3.912 ÷ 16.09 km ≈ 0.243 km⁻¹.** Very clean air can't be told apart.
- **Open item:** the ASOS sensors' internal visibility algorithm has not been checked (see `docs/references.md`, "Not verified").

### Steps 6 + 7 · METAR · 2026-09-27 · Dish + Claude
- **What:** Step 6 checked that no visibility exceeds the 10-mile ceiling (the script was set to stop, without writing anything, if any did) and counted hours at exactly 10 mi. Step 7 converted each hour's visibility to km (× 1.609344) and then to light extinction = 3.912 ÷ km (Koschmieder 1924; see method note M1). Added columns `vsby_km` and `extinction_km`; existing columns unchanged; full precision kept.
- **Why:** Extinction scales with the amount of haze and can be averaged fairly; the daily average happens in Step 9.
- **Input:** `data/processed/metar/step05_dry/metar_<city>_dry.csv`
- **Script:** `scripts/metar/06_07_ceiling_check_and_extinction.py`
- **Rows in → out:** 408,597 → 408,597 station-hours (0 removed, 2 columns added).
- **Step 6 result:** **no values above 10 mi** at any station. Lowest dry-hour visibility is 0.25–0.75 mi depending on station.
- **Share of dry daytime hours at the 10-mi ceiling:** BFL 64.8% · LAX 75.2% · DTW 80.0% · FAT 80.0% · AGC 89.2% · DET 89.9% · SFO 91.6% · EUG 94.9% · BRO 95.2% · PAFA 96.9% · PIT 97.3% · BOS 98.2%.
- **Extinction range:** floor 0.2431 km⁻¹ (= 10 mi) at every station; max 3.24–9.72 km⁻¹. Station means 0.246 (BOS) to 0.309 (BFL).
- **Output:** `data/processed/metar/step07_extinction/metar_<city>_extinction.csv`, `step07_summary.csv`
- **Judgment calls:** none new. Formula specified by Dish (handoff), source documented in M1; exact statute-mile factor; no rounding.
- **Caveat for the appendix (ceiling effect):** In the cleanest cities (Boston 98%, Pittsburgh 97%, Fairbanks 97%), almost every dry daytime hour reads "10 mi", so daily visibility there will sit at the cap on most days and the signal comes from a small number of hazy hours. The San Joaquin Valley cities (Bakersfield 65% at cap, Fresno 80%) and LA (75%) have far more hours below the cap. The metric can show that a place is hazier than 10-mi air, but can't tell clean days from very clean ones.

### Step 8 · METAR · 2026-09-27 · Dish + Claude
- **What:** Combined station-hours into **one value per city per hour**. Detroit (DET + DTW) and Pittsburgh (AGC + PIT): plain mean of the extinction of whichever airports had a dry daytime reading that hour (at least 1 of 2). The other 8 cities have one airport each: value passed through, flagged `point_sample = 1`. Each airport's own value is kept in its own column (`ext_<STATION>`); `rh_missing_any` carries the blank-RH flag forward.
- **Why:** The rest of the pipeline works one city at a time.
- **Input:** `data/processed/metar/step07_extinction/metar_<city>_extinction.csv`
- **Script:** `scripts/metar/08_combine_airports.py`
- **Rows in → out:** 408,597 station-hours → **347,059 city-hours**. No values removed; the two-airport cities' paired hours merged.
  - Detroit: 35,065 city-hours = 31,637 with both airports + 2,271 DET only + 1,157 DTW only.
  - Pittsburgh: 34,173 city-hours = 29,901 with both + 2,276 AGC only + 1,996 PIT only.
  - Accounting check after running: station-hours = 2 × both + only-one, and city-hours = both + only-one, for both cities. Passed.
- **Output:** `data/processed/metar/step08_city_hourly/metar_<city>_cityhour.csv`, `step08_summary.csv`
- **Judgment calls:**
  - **Equal weighting of the two airports**, although DTW and PIT are ~15 mi outside their cities and DET/AGC are at the city edge. **Claude's choice (following the handoff), approved by Dish.**
  - Blank-RH flag carried forward as `rh_missing_any`. **Claude's choice, approved by Dish.**
- **Cosmetic note:** `step08_summary.csv` has empty `hours_only_<STATION>` columns for the single-airport cities (a formatting quirk of the script; no effect on the data).
- **Open item:** airport distances from each city (required by the handoff) not yet measured; planned as the next, read-only step.

### Step 9a · METAR · 2026-09-27 · Dish + Claude
- **What:** Read-only count of how many dry daytime city-hours (0–10) each of the 3,921 study days has, per city, and how many days would remain at minimum-hours thresholds of 1–6. **Nothing removed or averaged.**
- **Why:** So Dish can choose the minimum number of hours a day needs for a valid daily value, knowing what each choice costs.
- **Input:** `data/processed/metar/step08_city_hourly/metar_<city>_cityhour.csv`
- **Script:** `scripts/metar/09a_hours_per_day_audit.py`
- **Output:** `data/processed/metar/step09a_hours_per_day/hours_per_day_distribution.csv`, `min_hours_tradeoff.csv`
- **Findings:**
  - Days with all 10 hours dry: 50% (Eugene) to 85% (Bakersfield).
  - Days with 0 dry hours: 25 (Bakersfield) to 288 (Fairbanks); Boston 197, Eugene 134.
  - % of days kept at minimum 1 / 3 / 6 hours: Fairbanks 92.7 / 87.7 / 79.3; Boston 95.0 / 91.3 / 85.1; Eugene 96.6 / 93.4 / 83.1; Pittsburgh 98.0 / 95.5 / 89.3; Detroit 97.9 / 95.8 / 91.3; the California cities and Brownsville ≥ 98.6 / ≥ 97.5 / ≥ 94.0.
- **Judgment calls:** none (counting only).

### Step 9b · METAR · 2026-09-27 · Dish + Claude
- **What:** Built the **final daily visibility series** per city. For each of the 3,921 days: `n_hours` = dry daytime city-hours; if n_hours ≥ 3, `extinction` = mean of that day's hourly extinction and `visibility_mi` = (3.912 ÷ extinction) ÷ 1.609344; days with fewer than 3 hours are kept as rows with blank extinction/visibility and `valid_day = 0`. `n_stations` = airports contributing ≥ 1 hour that day.
- **Why:** Daily visibility ("embodied air quality") for the viz. Averaging in extinction, not miles, keeps a few clear hours from hiding a hazy morning (M1).
- **Input:** `data/processed/metar/step08_city_hourly/metar_<city>_cityhour.csv` (347,059 city-hours)
- **Script:** `scripts/metar/09b_daily_visibility.py`
- **Rows in → out:** 347,059 city-hours → **10 files × 3,921 days**. Valid days: Bakersfield 3,873 · Fresno 3,847 · SFO 3,850 · LA 3,852 · Brownsville 3,824 · Detroit 3,758 · Pittsburgh 3,745 · Eugene 3,662 · Boston 3,580 · **Fairbanks 3,439**. Blank (short) days: 48 (Bakersfield) to 482 (Fairbanks). Hours in short days (not used): 32–289 per city.
- **Checks after running:** every city has all 3,921 dates. Hours used + hours in short days = all Step 8 city-hours, for every city (total 347,059). Valid-day counts match Step 9a's "minimum 3" counts exactly. (The script's comment mentions the hours check, but its `assert` only checks the day count; the hours check was run separately afterwards.)
- **Plausibility check (worst days):** Eugene 2020-09-11 to 09-13 (0.25–0.45 mi) and Fresno 2020-08-22, 09-13, 09-14 (~1.0 mi) line up with the September 2020 West Coast wildfire smoke; Fairbanks 2019-07-10/11 and 2024-06-30 fall in Alaska summer fire season. **To review:** Boston's lowest day, 2024-02-23 (1.68 mi, 10 hours), and Bakersfield 2020-12-17/18 (~0.55–0.59 mi) have no obvious smoke explanation. Possibly fog or wet haze that the codes and RH < 90% didn't catch. Worth checking in the raw reports before using them as story beats.
- **Output:** `data/processed/metar/final/vis_<city>_daily.csv` (columns: date, visibility_mi, extinction, n_hours, n_stations, valid_day, point_sample, rh_missing_hours), `step09_summary.csv`
- **Judgment calls:**
  - Minimum **3 dry hours** per valid day. **Changed by Dish** (chose 3 from Claude's options, informed by Step 9a).
  - Extra columns `valid_day`, `point_sample`, `rh_missing_hours` beyond the handoff's five. **Claude's choice, approved by Dish.**
  - `n_stations` = airports contributing any hour that day. **Claude's choice, approved by Dish.**
  - Full precision, no rounding (floating point gives some 10-mi days as 10.000000000000002). **Claude's choice, approved by Dish.**
  - Final files in `data/processed/metar/final/`. **Claude's choice, approved by Dish.**
- **Caveat for the appendix:** Days dropped for too few dry hours are mostly rainy/snowy days, which tend to be clean, so the remaining series tilts slightly toward hazier weather in the wet cities (largest for Fairbanks, Boston, Eugene).

### Step 8b · METAR · 2026-09-27 · Dish + Claude
- **What:** Measured the straight-line (great-circle, haversine) distance from each of the 12 airports to its city hall. **Read-only: no visibility data changed.**
- **Why:** The handoff requires logging airport distances, especially for airports outside city limits. This turns "some airports are outside the city" into numbers for the appendix.
- **Input:** airport coordinates transcribed by Claude from each station's IEM page (`mesonet.agron.iastate.edu/sites/site.php?station=<ID>&network=<NET>`). Scripts couldn't download IEM's station list directly: the network proxy blocks mesonet.agron.iastate.edu from both the local and cloud shells. City hall coordinates supplied by Claude (approximately one block); no geocoder was available (OpenStreetMap Nominatim disallows automated access).
- **Script:** `scripts/metar/08b_station_distances.py`
- **Output:** `data/processed/metar/metar_station_distances.csv`
- **Results (miles from city hall):** BOS 2.5 · BFL 4.5 · BRO 4.6 · FAT 4.7 · PAFA 5.2 · DET 5.8 · AGC 7.0 · EUG 7.9 · SFO 11.3 · LAX 11.5 · PIT 12.9 · **DTW 16.1**.
  - LAX is inside Los Angeles city limits but 11.5 mi from City Hall. LA is large, so "in city" ≠ "downtown."
  - Two-airport cities: Detroit's DET is 5.8 mi and DTW 16.1 mi from city hall; Pittsburgh's AGC is 7.0 mi and PIT 12.9 mi. They are weighted equally in Step 8.
- **Judgment calls:**
  - **City hall coordinates supplied by Claude.** Dish to spot-check 2–3 in Google Maps; a one-block error changes distances by < 0.1 mi. **Claude's choice, approved by Dish; verification pending.**
  - **Airport coordinates copied by hand** from IEM pages (source URL pattern in the script). **Claude's choice, approved by Dish.**
  - "In city limits" filled only where the handoff states it; others are "not checked" until city-limits shapefiles are available (gridMET step). **Claude's choice, approved by Dish.**

### Decision D2 · gridMET · 2026-09-27 · Dish
- **What:** gridMET actual temperature will be pulled over **city-limits boundaries** (Census TIGER/Line "Places") for all 9 continental-US cities, not ClimateEngine's built-in county regions.
- **Why:** For most of the cities the county is far larger and takes in mountains or desert: LA County (San Gabriels, Mojave), Kern (Sierra Nevada, Tehachapis, Mojave), Fresno (Sierra peaks near 14,000 ft), Lane (Cascades to the coast). A county average would blend in those cooler or different climates and misstate city highs. City limits also match the handoff's city-scale rule and the METAR airport-nearest-city approach.
- **Options considered:** (A) city limits for all 9; (B) ClimateEngine county regions for all 9 (faster, no download); (C) county only where it matches the city (San Francisco, Suffolk/Boston), city limits elsewhere. **Approved by Dish: chose A** (Claude's recommendation).
- **Consequence:** Dish downloads the TIGER/Line Places state files by hand (the network proxy blocks www2.census.gov from both shells). Per-city shapefiles for upload to ClimateEngine are made in a later step.

### Step 1 · gridMET · 2026-09-27 · Dish (download) + Claude (check)
- **What:** Dish downloaded the Census **TIGER/Line 2025 "Places"** shapefiles by hand for 7 states from census.gov/cgi-bin/geo/shapefiles/index.php (Year 2025 → Layer type: Places → state → Download). Claude checked that each zip is complete. **Files kept exactly as downloaded (not renamed, not unzipped).**
- **Why:** City-limits boundaries for the gridMET pull (Decision D2), plus the "is the airport inside city limits" check for the METAR stations. Alaska is included only for that check at Fairbanks (gridMET doesn't cover Alaska).
- **Output (raw):** `data/raw/gridmet/tiger_places/tl_2025_<FIPS>_place.zip` for FIPS 02 AK · 06 CA · 25 MA · 26 MI · 41 OR · 42 PA · 48 TX
- **Check:** every zip has .shp, .shx, .dbf, .prj, .cpg and the two ISO metadata .xml files (7 files each). Shapefiles dated 2025-09-12/13 by Census.
- **SHA-256 (so anyone can confirm the raw files are unchanged):**
  - 02 `582c37f2fe680af15d7508e222153d5aa163867f47f2d96fbacd05695b0d985d`
  - 06 `2b59dc5d54c69c7a451795401fc2a1c1c68b172f1d912d3486080e04a83e23e8`
  - 25 `950f7d0a669caf721f770d1cc58883560b1cf84f5d7be845e6e3d05a855c86fa`
  - 26 `91cd708b8f9809a50ebed360fe7242969ba357a542481da81d9edc5821d35d3b`
  - 41 `d05814de06701cca35df9e160017cd11d5ffe43a2530a8fa7f4b3a521e9e1f0f`
  - 42 `b9b8a25b906bc0c338cc4cfea45d8e5de12247a913cbd821b93368c55e2e9dc5`
  - 48 `5a0c4d49641f69028ee9f5c343bf09936ec00a378e5e6393115b106bab935e13`
- **Judgment calls:**
  - **TIGER/Line (full-detail legal boundaries), vintage 2025**, rather than the simplified cartographic-boundary files. **Claude's choice, approved by Dish** (Dish picked 2025, the latest listed).
  - Raw folder `data/raw/gridmet/tiger_places/`; the same boundaries will be reused for UTCI. **Claude's choice, approved by Dish.**
  - Downloaded by hand because the network proxy blocks www2.census.gov from both shells.

### Step 2 · gridMET · 2026-09-27 · Dish + Claude
- **What:** Read-only audit of the city-limits boundaries. For each city: Census land and water area, number of separate polygon pieces and distance of the farthest piece, approximate number of gridMET cells inside. Also checked whether each of the 12 METAR airports lies inside its city's limits. **Nothing changed.**
- **Why:** To decide, with real numbers, how to prepare each city's polygon for ClimateEngine; and to close METAR open item 4 (airports in city limits).
- **Input:** `data/raw/gridmet/tiger_places/*.zip` (not modified) · `data/processed/metar/metar_station_distances.csv`
- **Script:** `scripts/gridmet/02_boundary_audit.py` (needs geopandas 1.1.4, installed in the local workspace)
- **Output:** `data/processed/gridmet/step02_boundary_audit/` → `boundary_audit.csv` (10 cities), `boundary_parts.csv` (one row per polygon piece), `airport_in_city.csv` (12 airports)
- **Findings (boundaries):**
  - Land / water km², pieces, approx. gridMET cells: Bakersfield 390 / 4 · 4 pieces · 20 · Fresno 300 / 3 · 4 · 14 · Los Angeles 1,219 / 82 · 1 · 74 · **San Francisco 121 / 480 (80% water) · 2 pieces, second one 248 km² at 30.7 km (Farallon Islands and surrounding ocean)** · 37 · Eugene 116 / 0.2 · **178 pieces** (mostly slivers, largest detached 0.47 km²) · 8 · Brownsville 316 / 17 · 4 · 19 · Detroit 359 / 11 · 1 · 24 · Pittsburgh 143 / 8 · 1 · 10 · **Boston 125 / 107 (46% water)** · 1 · 15 · Fairbanks 82 / 2 · 1 · n/a.
- **Findings (airports in city limits):** **inside:** FAT, BRO, BOS, LAX, DET. **Outside:** BFL 1.9 km · EUG 0.9 km · AGC 1.2 km · PAFA 4.3 km · SFO 10.0 km · PIT 12.1 km · DTW 13.6 km (km beyond the boundary, not from city hall). Handoff notes for LAX, SFO, DET, DTW, AGC, PIT confirmed.
- **Judgment calls:**
  - Checked all 12 airports, not just the 6 Dish listed. **Claude's choice, approved by Dish.**
  - gridMET cell count = cell centres (1/24° grid) inside the boundary; a rough size check, not what ClimateEngine computes. **Claude's choice, approved by Dish.**
  - Places matched by Census NAME + "<name> city"; exactly one match required. **Claude's choice, approved by Dish.**
  - Equal-area projections EPSG:5070 (CONUS) and EPSG:3338 (Alaska) for areas and distances. **Claude's choice, approved by Dish.**
- **Open decision:** how to handle water (SF, Boston), the Farallon piece, and Eugene's slivers before making the ClimateEngine polygons.

### Housekeeping · repo · 2026-09-27 · Claude (approved by Dish)
- Added `.gitignore` (`.DS_Store`, plus `__pycache__/` as Claude's addition) and a full `README.md`. The two `.DS_Store` files already tracked by git (`data/`, `data/raw/`) are to be untracked with `git rm --cached` at commit time (files stay on disk).

### Decision D3 · gridMET · 2026-09-27 · Dish
- **What:** Use the Census city-limits shapes as they are (water included, Eugene's slivers kept), **except San Francisco: drop the detached Farallon Islands piece** (248 km², 30.7 km offshore).
- **Why:** gridMET is a land dataset, so water cells are expected to be blank and skipped in ClimateEngine's average (to be confirmed visually in ClimateEngine). The Farallones are not part of the lived city, and an ocean-cooled island cell could bias SF's average. Eugene's slivers are tiny (largest 0.47 km²) and inside or next to the city.
- **Options considered:** (A) all shapes as-is; (B) as-is but drop SF's Farallon piece; (C) clip every city to land using Census cartographic-boundary files. **Approved by Dish: chose B** (Claude's recommendation).
- **To confirm:** after upload, check in ClimateEngine's gridMET map layer that bay and harbor water (SF, Boston) show no data.

### Step 3 · gridMET · 2026-09-27 · Dish + Claude
- **What:** Pulled each of the 9 continental cities' city-limits shape out of its state file and saved it as its own zipped shapefile for ClimateEngine upload. San Francisco keeps only its main piece (Decision D3). Converted coordinates from NAD83 to WGS84.
- **Why:** ClimateEngine's "Custom Polygon from Shapefile" needs a zip with .shp/.shx/.dbf/.prj; one city per zip avoids ambiguity.
- **Input:** `data/raw/gridmet/tiger_places/tl_2025_{06,25,26,41,42,48}_place.zip` (not modified; `git status` shows no change to raw files)
- **Script:** `scripts/gridmet/03_city_polygons.py`
- **Rows/values in → out:** 9 city shapes → 9 zips. Pieces and area unchanged for 8 cities. **San Francisco: 2 pieces → 1; 600.62 → 352.69 km² (247.92 km² removed, the Farallon Islands piece).** SF's remaining shape still includes bay and ocean water (lat 37.71–37.93, lon −122.61 to −122.28).
- **Output:** `data/processed/gridmet/step03_city_polygons/<city>_citylimits.zip` (9 files: .shp .shx .dbf .prj .cpg), `step03_summary.csv`
- **Judgment calls:**
  - Reprojected NAD83 (EPSG:4269) → WGS84 (EPSG:4326), Earth Engine's standard; shift ≈ 1 m. **Claude's choice, approved by Dish.**
  - SF "main piece" = largest piece by area. **Claude's choice, approved by Dish** (implements D3).
  - Kept columns GEOID, NAME, NAMELSAD, ALAND, AWATER in the upload copies only. **Claude's choice, approved by Dish.**
  - File names `<city>_citylimits.zip`. **Claude's choice, approved by Dish.**

### Decision D4 · all datasets · 2026-09-27 · Dish
- **What:** The study period now ends **2026-09-24** for all three datasets (replaces D1's end date of 2026-09-25).
- **Why:** gridMET's period of record in ClimateEngine currently ends 2026-09-24 (it runs a day or two behind). Ending everything on the 24th keeps all three datasets aligned without waiting for a re-pull.
- **Options considered:** (A) pull gridMET through 09-24 now, add 09-25 later as a separate raw file; (B) end only gridMET on 09-24, one-day mismatch with METAR; (C) move the whole study end to 09-24. **Changed by Dish: chose C** (Claude had leaned A).
- **Follow-on (open, METAR):** the METAR final files (`data/processed/metar/final/vis_<city>_daily.csv`) still run to 2026-09-25 (3,921 days) and need a small trim step to drop 09-25 (→ 3,920 days). Not done in the gridMET work. UTCI will be pulled through 09-24.

### Step 4 · gridMET · 2026-09-27 · Dish (downloads) + Claude (check)
- **Downloads (Dish, ClimateEngine, Boston pilot):** Native Time Series · One Variable Analysis · Region: Custom Polygon from Shapefile → `boston_citylimits.zip` (feature 2507000 selected in the region dropdown) · Climate & Hydrology · GridMET 4km Daily · Maximum Temperature · deg F · 4000 m · Statistic over region: Mean · **Masking: No masking of data** · Custom Date Range. Saved to `data/raw/gridmet/climateengine/` and named at save time `gridmet_tmax_<city>_<period>.csv` (file contents untouched).
  - Troubleshooting on the way (for the record): masking was initially set to "Mask by category → Valley Bottom Extraction Tool" (left over from the Map tab), and ClimateEngine refused to run; switched to No masking. A generic server error ("Expecting value: line 1 column 1") came from no region being selected in the "Pick a Region!" dropdown after the upload.
  - **Mistaken download replaced:** the first baseline file covered 1999-01-01 to 2020-12-31 (start date typed as 1999). Dish re-ran it from 1991-01-01 and saved over it under the same name. The mistaken file was not processed.
- **Water check (for D3):** the gridMET Map layer shows no values over the Atlantic, Massachusetts Bay, Lake Ontario or the Bay of Fundy; colour stops at the coastline in 4 km steps. So water inside city limits is empty in gridMET and doesn't enter ClimateEngine's regional mean. D3 holds.
- **What (check):** read-only check of each raw file: header, date range, day count, gaps, duplicates, blanks, implausible values (outside −60 to 130 °F), and whether the 2016–2020 days common to both pulls have identical values.
- **Input:** `data/raw/gridmet/climateengine/gridmet_tmax_boston_2016-2026.csv` (SHA-256 `8a043cc9317264b2da10cb76778ebcacbc53b58e59251a1a3f9a8f53c89cb394`) · `gridmet_tmax_boston_1991-2020.csv` (SHA-256 `0f682e54c6d4750674d86351a618e0ce904f12221700b607aea345af22a1370c`)
- **Script:** `scripts/gridmet/04_raw_check.py`
- **Output:** `data/processed/gridmet/step04_raw_check/raw_check.csv`
- **Results (Boston):** 2016-2026: 3,920 of 3,920 days (2016-01-01 to 2026-09-24); 1991-2020: 10,958 of 10,958 days. 0 missing, 0 duplicate, 0 blank, 0 implausible. **Overlap 2016–2020: identical values (max difference 0.0 °F)**, so both pulls used the same polygon and settings. Range: 8.2 °F (2019-01-21) to 101.9 °F (2025-06-24, the June 2025 heat wave); baseline 6.5 to 98.9 °F.
- **Judgment calls:**
  - Plausible range −60 to 130 °F (flag only, nothing removed). **Claude's choice, approved by Dish.**
  - Renaming ClimateEngine downloads at save time so the 18 files are distinguishable. **Claude's choice, approved by Dish.**
  - Boston downloaded first as a pilot before the other 8 cities. **Claude's choice, approved by Dish.**

### Step 4 (final) · gridMET · 2026-09-27 · Dish (downloads) + Claude (check)
- **What:** Dish downloaded the remaining 8 cities from ClimateEngine with the Boston pilot settings (one city polygon per request, its GEOID picked in the region dropdown, No masking, 2016-01-01 → 2026-09-24 and 1991-01-01 → 2020-12-31). Claude ran the raw check on all **18 files** after each city came in, then once more on all of them after adding three header checks (below). **Read-only: nothing changed.**
- **Script change (approved by Dish before running):** `scripts/gridmet/04_raw_check.py` now also records `geoid_in_header`, `geoid_matches_city` (header GEOID vs the city in the filename, using the Step 3 GEOIDs) and `header_dates_match` (header date range vs the expected range; would have caught the 1999 mix-up).
- **Output:** `data/processed/gridmet/step04_raw_check/raw_check.csv` (18 rows)
- **Results:** every file has the right GEOID and date range; 3,920 of 3,920 study days and 10,958 of 10,958 baseline days; 0 missing, 0 duplicate, 0 bad dates, 0 blank, 0 implausible, 0 outside range. **2016–2020 overlap identical in all 9 cities (max difference 0.0 °F).**
- **Hottest study-period days (2016-01-01 to 2026-09-24):** Bakersfield 113.8 °F (2022-09-06) · Fresno 113.4 °F (2022-09-06) · Eugene 110.1 °F (2021-06-27, Pacific NW heat dome) · Los Angeles 109.3 °F (2018-07-06) · Brownsville 102.7 °F · Boston 101.9 °F (2025-06-24) · San Francisco 97.9 °F (2020-09-06) · Detroit 97.2 °F · Pittsburgh 96.8 °F. Cold ends match known events (Detroit −1.4 °F on 2019-01-30, polar vortex; Brownsville 34.0 °F, likely the Feb 2021 freeze).
- **Flags for later (nothing changed):**
  - **Detroit 2013-09-10 = 104.8 °F** (baseline). Real hot spell (neighbouring days 89 and 99 °F), but Claude's understanding is that the airport recorded mid-90s that day, so gridMET may run ~8–10 °F hot on this day. Not verified (METAR pulls didn't include temperature). Affects only early-September normals; candidate for an outlier audit before the normals step.
  - **Area averaging flattens extremes (appendix caveat):** San Francisco's hottest gridMET day in 2017 is 95.3 °F (09-02), while downtown SF officially hit ~106 °F on 2017-09-01. The city mean includes the cooler foggy west side.
- **SHA-256 of raw files** (`data/raw/gridmet/climateengine/`):
  - bakersfield 1991-2020 `c09960f59715601a9cd10d0e87148b254c218caed59e3c87cdbff1648eb6b70b` · 2016-2026 `2ae64c2a7830c3e70fa7b18a374d21fbf6ec72287bdff8af720c0de23552480b`
  - boston 1991-2020 `0f682e54c6d4750674d86351a618e0ce904f12221700b607aea345af22a1370c` · 2016-2026 `8a043cc9317264b2da10cb76778ebcacbc53b58e59251a1a3f9a8f53c89cb394`
  - brownsville 1991-2020 `57c129af19bb4a8baea4105c16590852d7a425f373a8f3d7271575069abeed75` · 2016-2026 `44c7be1de0a742b4fd011c16ec0b2f52861a946b075c48c314140046d73ff40c`
  - detroit 1991-2020 `289697e61b46ccd46aba6f88a036414857e6d5a13eadcbfee5c4c602313059cf` · 2016-2026 `23b99a51719cfd46119ae9c216664c5ffd0d99ecff3d84387c34fb1313c7a4b8`
  - eugene 1991-2020 `f4248f0a6e442015b7c2b9bd9ba5390cb77236b406d96bb8634bf706138b56e8` · 2016-2026 `1fc690435505f0013d7557e4c0bc40d771c2078872c4e7d85fe2e3f6974a00d3`
  - fresno 1991-2020 `0378ed17f7c4440d637c80983a8e72f3b49efc82bf4e9f3f8970a3fd5b645c28` · 2016-2026 `58eefa65bffd9c7ea4684f426e726214bdf60db82856fc01d2166add2126632b`
  - losangeles 1991-2020 `fe4b8b45cdcb22e29118be7fead545b2ef92ad6b81dfc0f25b9b0a7451268a34` · 2016-2026 `bb64c2829a1f01b68f556efe447a0588c1b7e063cceef4ced184c1059a6721ea`
  - pittsburgh 1991-2020 `1e384e4fa16d9c623ee2a8bdefdc934bcaf1beb8d7a195575e6d6e4b8352437b` · 2016-2026 `b8920f10078f69e80d352c5aa2c000a9d2127da96091680239a1df00ed396d9d`
  - sanfrancisco 1991-2020 `6ed70bd8bc7fb4e8a0d75c0fe0b288c4babb33e078cd770ca6d24340cc17dd87` · 2016-2026 `d3b51456d12e35ee117a042ff39e1da4d07316da9740f52bd9389097f1c680e0`
- **Judgment calls:**
  - GEOID and header-date checks added. **Claude's choice, approved by Dish.**
  - Detroit 2013-09-10 and the SF smoothing example flagged but not acted on. **Claude's choice, approved by Dish.**

### Note N1 · gridMET vs OpenAQ boundaries · 2026-09-27 · Dish + Claude
- **What:** Found while rebasing onto Gina's commits: the two pipelines use different Census city-limits files. gridMET (Dish): **TIGER/Line 2025 Places** (full detail, legal boundary incl. water). OpenAQ (Gina, `scripts/openaq/02_assign_sensors.py`): **2024 cartographic boundary file** `data/raw/census/cb_2024_us_place_500k.zip` (generalized, clipped to the shoreline).
- **Why it matters:** the handoff asks for the same boundary for every variable of a city. Differences are one boundary vintage (2024 vs 2025 annexations) and edge detail/water. For gridMET the effect is expected to be negligible (water cells are empty in gridMET; the generalized edges are much finer than the 4 km grid). For OpenAQ it could matter for sensors right at the edge.
- **Decision:** none yet. **Logged for Dish and Gina to decide** whether to align on one file (a read-only comparison of the two boundaries per city is possible). No data changed.
- **Also noted:** these gridMET entries (D2, Steps 1–4, D3, D4, housekeeping) were accidentally dropped from this log by the commit "Data log: D5, D6 (amended), Steps 1b-9b reruns for 17 cities" (`2f63eaa` on main; saved from an older copy) and restored verbatim from the gridMET Steps 1-4 commit (`9e12126` on main) in the commit that adds this note. (Hashes are after rebasing onto Gina's commits.) D4's METAR follow-on (trim to 2026-09-24) is done: see the Steps 9a + 9b rerun below.

### Decision D5 · METAR · 2026-09-27 · Dish
- **What:** Added 4 cities to the METAR pipeline. Stations were chosen from IEM station pages by Claude and approved by Dish:
  - **Ann Arbor MI → ARB** (Ann Arbor Municipal), MI_ASOS, America/New_York.
  - **Delano CA → DLO** (Delano Municipal), CA_ASOS, America/Los_Angeles. **Changed by Dish:** kept DLO despite its gaps, rather than PTV (Porterville, ~20 mi, full record).
  - **San Diego CA → SAN** (Lindbergh Field), CA_ASOS, America/Los_Angeles.
  - **Warren MI → VLL** (Troy). Chosen instead of DET so Warren doesn't share Detroit's station. **Claude's choice, approved by Dish.**
- **Added later the same day** (approved by Dish):
  - **Phoenix AZ → PHX** (Sky Harbor), AZ_ASOS. IEM's timezone menu has no America/Phoenix (Arizona stays on MST, UTC−7, with no daylight saving), so it was **downloaded in UTC** as `metar_phoenix_raw_utc.csv`, to be converted with a logged script (local = UTC − 7 h, all year). **Claude's choice, approved by Dish.** Raw check: 96,974 rows, 2016-01-01 00:51 → 2026-09-24 23:51 **UTC**, which in local time is 2015-12-31 17:51 → 2026-09-24 16:51. The Sep 24 5 pm hour is therefore missing, and the Dec 31, 2015 evening rows fall outside the study period.
  - **Raymondville TX → HRL** (Harlingen, ~18 mi; Raymondville has no ASOS), TX_ASOS, America/Chicago. Raw check: 124,319 rows, 2016-01-01 → **2026-09-24** 23:52, 3,920 days; 711 blank visibility, 625 blank RH.
  - **Springfield OR → EUG, shared with Eugene.** Springfield has no ASOS, so its visibility row is Eugene's. `metar_springfield_raw.csv` is a Finder duplicate of `metar_eugene_raw.csv` made by Dish. Verified **byte-identical**: SHA-256 `f2be2750…37e6dd` for both files. Ends 2026-09-25, like Eugene's.
- **Total: 17 cities, 17 raw files** (one per city; Phoenix in UTC), covering **18 distinct stations**: the original 12 plus ARB, DLO, SAN, VLL, PHX and HRL. EUG is used by both Eugene and Springfield.
- **Raw files:** `data/raw/metar/metar_{annarbor,delano,sandiego,warren}_raw.csv`, downloaded by Dish (same IEM settings as the original 10).
- **Raw check (read-only, before processing):**
  - All four end **2026-09-23 23:5x local**. The IEM end date was set to 2026-09-24 and IEM leaves out the end date itself, so Sep 24 is missing. **Changed by Dish:** accepted as is; no re-download.
  - ARB: 134,489 rows from 2016-01-01, 3,906 days with data; 3,267 blank visibility and 3,136 blank RH (much higher than the original 12 stations).
  - DLO: 223,183 rows, **starts 2017-01-15** (IEM lists the archive as beginning 2017-01-05), 3,173 days with data (~10% of days missing after the start), 9,674 blank RH. **Changed by Dish:** DLO accepted with 2016 and early January 2017 missing.
  - SAN: 116,238 rows, 3,919 days with data.
  - VLL: 292,804 rows, 3,910 days with data.

### Decision D6 · METAR · 2026-09-27 · Dish
- **What:** DLO (Delano) and VLL (Warren) are automated stations reporting at **:15, :35 and :55** past each hour (~70–75 reports/day), vs one routine report (~:51–:56) plus occasional specials at the other stations. Keeping the haziest of three reports every hour (Step 3) would make these two cities look slightly hazier than the others, by construction. **Decision: for DLO and VLL, use only the :55 report** (closest to the big airports' routine :5x timing); all other reports from these two stations are set aside before Step 3.
- **Who chose it:** proposed by Claude, **approved by Dish**. Alternative considered: keep the haziest of the three and log the bias.

### Step 1b · METAR (Phoenix) · 2026-09-27 · Dish + Claude
- **What:** Converted Phoenix timestamps from UTC to local time: **local = UTC − 7 hours, fixed all year** (Arizona is on MST with no daylight saving). The original UTC time is kept as a new column `valid_utc`. No rows dropped; other columns unchanged.
- **Why:** Every other city's timestamps are local, and Steps 3–4 (clock hour, 8am–6pm window) need local time. IEM's menu has no America/Phoenix (D5).
- **Input:** `data/raw/metar/metar_phoenix_raw_utc.csv` (not modified)
- **Script:** `scripts/metar/01b_phoenix_utc_to_local.py`
- **Rows in → out:** 96,974 → 96,974. Built-in check passed: every row shifted by exactly 7 h.
- **Result:** local range 2015-12-31 17:51 → 2026-09-24 16:51. 7 rows fall on 2015-12-31 (before the study period; left in, and excluded by Step 9's date range). Routine reports land at :51 local, as expected.
- **Output:** `data/processed/metar/step01b_phoenix_local/metar_phoenix_local.csv`
- **Judgment calls:** none new (UTC download + fixed −7 h approved under D5).

### Step 1 (rerun, 17 cities) · METAR · 2026-09-27 · Dish + Claude
- **What:** Reran the read-only inventory on all 17 cities. **Script edit:** `01_inventory.py` now reads Phoenix from the Step 1b local-time file instead of the UTC raw file, and strips `_local.csv` from the city name. Nothing else changed (see git diff of the script).
- **Input:** 16 raw files in `data/raw/metar/` + `data/processed/metar/step01b_phoenix_local/metar_phoenix_local.csv`
- **Rows in → out:** 2,454,137 reports read → 19-row summary (18 stations; EUG appears under both Eugene and Springfield). 0 rows removed.
- **Check:** compared to the committed version, the original 12 rows are **identical**; git shows 7 rows added, 0 changed.
- **New stations:** ARB 134,489 rows, 3,906 days, **3,267 blank visibility**, 3,136 blank RH · DLO 223,183 rows from 2017-01-15, 3,173 days, **9,674 blank RH** · SAN 116,238 rows, 3,919 days · VLL 292,804 rows, 3,910 days · HRL 124,319 rows, 3,920 days, 711 blank visibility · PHX 96,974 rows, 3,921 local dates (including 2015-12-31).
- **Output:** `data/processed/metar/metar_inventory.csv` (overwritten; the previous version is in git history)
- **Judgment calls:** none (counting only).

### Step 2 (rerun, 17 cities) · METAR · 2026-09-27 · Dish + Claude
- **What:** Reran "throw out broken readings" (blank or exactly 0-mile visibility) on all 17 cities. **Script edit:** `02_drop_broken.py` reads Phoenix from the Step 1b local-time file and strips `_local.csv` from the city name. Rules unchanged.
- **Input:** 16 raw files + `step01b_phoenix_local/metar_phoenix_local.csv`
- **Rows in → out:** 2,454,137 → **2,447,990**. Removed 6,147: 6,035 blank, 112 zero. **New cities only:** 4,409 blank + 24 zero = 4,433 removed. ARB 3,268 (2.43%, the highest of any station), HRL 711 (0.57%), EUG/Springfield 220 (same as Eugene), DLO 97, VLL 98, PHX 23, SAN 16. Built-in check passed.
- **Check:** git shows **no changes** to any of the original 10 cities' `_valid`/`_removed` files; `step02_summary.csv` gained 7 rows, 0 changed; 14 new files added.
- **Output:** `data/processed/metar/step02_valid/` (same file pattern as before)
- **Judgment calls:** none new. Rerun overwrites processed outputs in place; previous versions are in git history. **Claude's choice, flagged to Dish.**
- **Correction:** Claude's pre-run estimate of "~5,500 more rows removed" was high; the actual count is 4,433.

### Step 3 (rerun, 17 cities, D6 rule) · METAR · 2026-09-27 · Dish + Claude
- **What:** Reran "one reading per airport per hour" on all 17 cities. **Script edit (D6):** for DLO and VLL, only reports at minute :55 are used. All other reports from those two stations (routine :15/:35 and specials) are saved to `metar_<city>_awos_set_aside.csv` before hourly grouping. The summary gains an `awos_set_aside` column, and the self-check now includes set-aside rows. All other stations are processed exactly as before.
- **Input:** `data/processed/metar/step02_valid/metar_<city>_valid.csv`
- **Rows in → out:** 2,447,990 reports → **1,745,831 station-hours** (361,088 set aside at DLO/VLL; 341,071 merged into their hour). Built-in check passed.
  - DLO: 223,086 in → 149,144 set aside → 73,933 hours. VLL: 292,706 in → 211,944 set aside → 80,754 hours.
  - New ASOS stations: ARB 90,239 hours · HRL 93,542 · SAN 94,026 · PHX 93,981 · EUG/Springfield 93,691 (same as Eugene).
- **Check:** git shows no changes to the original 10 cities' hourly files. `step03_summary.csv` changed because of the new column and the 7 new rows.
- **Approved side effects:** (1) no fallback when an hour lacks a :55 report; (2) DLO/VLL specials are set aside, so a sudden event between routine reports can register at the other airports but not at these two. **Claude's choices, approved by Dish.**
- **Finding after running (needs a decision):** hours that had reports but no :55 report: **DLO 1,155** (1.5%), **VLL 12,569** (13.5%). The VLL losses cluster in **2016 (3,025), 2017 (5,088) and 2019 (2,085)**, when its schedule ran a minute off (:14/:34/**:54**, sometimes :56). So strict ":55" is dropping real routine reports, not missing data. Claude proposed amending D6 to accept :54–:56 (one report per hour); awaiting Dish's decision. **These Step 3 outputs for Delano and Warren may be rerun.**

### Decision D6 amended + Step 3 rerun (Delano, Warren) · METAR · 2026-09-27 · Dish + Claude
- **Amendment:** for DLO and VLL, accept one report per hour at **:54, :55 or :56**. If an hour has more than one, the one closest to :55 wins (tie → earliest). All other reports are set aside to the audit file. **Proposed by Claude after the Step 3 finding above, approved by Dish.**
- **Script:** `scripts/metar/03_one_per_hour.py` (D6 block and docstring updated; see git diff). Other stations unchanged.
- **Rows in → out (all 17 cities):** 2,447,990 → **1,754,636 station-hours** (352,300 set aside; 341,054 merged). Built-in check passed.
  - **DLO:** 73,938 hours (was 73,933 under strict :55). Picked minutes: :55 × 73,933, :56 × 5. Hours with reports but none at :54–:56: **1,150** (1.5%).
  - **VLL:** **89,554 hours** (was 80,754). Picked minutes: :55 × 80,754, **:54 × 7,606**, :56 × 1,194. Hours still lost: **3,769** (4.0%; those hours had only off-cycle reports, e.g. :14/:34).
  - No hour had more than one accepted report at either station.
- **Check:** original 10 cities' hourly files unchanged (git). Only the Delano/Warren files and `step03_summary.csv` changed vs the previous rerun.
- **Output:** `data/processed/metar/step03_hourly/` (Delano and Warren hourly and set-aside files overwritten)
- **Caveat for the appendix:** Warren and Delano use one routine report per hour with no specials, while the other stations keep the haziest of all reports, specials included. So short events between routine reports are less likely to register at these two.

### Steps 4 + 5a (rerun, 17 cities) · METAR · 2026-09-27 · Dish + Claude
- **What:** Reran Step 4 (daytime only, 8:00–17:59 local) and Step 5a (read-only weather-code and humidity audit) on all 17 cities. **Scripts unchanged** (`04_daytime_only.py`, `05a_audit_weather_codes.py`; no git diff). Run back to back with Dish's approval, pausing before 5b.
- **Step 4 rows in → out:** 1,754,636 → **731,800 daytime station-hours** (1,022,836 night hours removed). Daytime coverage of the 39,210 possible hours (3,921 days × 10): ARB 96.3%, **DLO 78.4%** (record starts 2017-01-15, plus gaps), VLL 95.2%, HRL 99.7%, SAN 99.9%, PHX 99.9%, EUG/Springfield 99.9%.
- **Check:** original 10 cities' daytime files and all three 5a tables are **identical** for the original cities. Only the summaries gained rows for the new cities.
- **Step 5a findings for the new cities** (daytime hours at the airport):
  - **Haze:** ARB 1,253 · DLO 769 · HRL 632 · SAN 571 · VLL 335 · EUG/Springfield 249 · **PHX only 40**.
  - **Smoke:** EUG/Springfield 312 (as Eugene); ≤ 6 elsewhere; DLO 0.
  - **Dust:** PHX 26 hours dust + 2 hours heavy duststorm (+DS); SAN 3. Dust is kept under 5b decision 5.
  - **Wet codes:** mist and rain are the most common everywhere. Snow at ARB 1,574 and VLL 1,404. Fog at ARB 510, EUG/Springfield 878.
  - **RH ≥ 90% (hour max):** HRL 3,825 (~10% of daytime hours), ARB 3,637, VLL 2,876, SAN 550, **PHX 140**.
  - **Blank RH for the whole hour:** **DLO 1,394** (4.5% of its daytime hours); ≤ 106 elsewhere. These are kept and flagged under 5b decision 7.
  - **Codes not seen in the original 10 cities:** `+DS` (heavy duststorm, PHX, 2 hours) → kept as dust; `TSFZRA` (thunderstorm with freezing rain, ARB, 1 hour) → removed as rain. Both are covered by the existing 5b rules; no new decision needed.
- **Output:** `data/processed/metar/step04_daytime/`, `data/processed/metar/step05a_wx_audit/`
- **Judgment calls:** none new.

### Steps 5b, 6–7, 8 (rerun, 17 cities) · METAR · 2026-09-27 · Dish + Claude
- **What:** Reran Step 5b (remove wet hours), Steps 6–7 (10-mi ceiling check and conversion to extinction) and Step 8 (combine airports) on all 17 cities, back to back with Dish's approval, pausing before Step 9. **Scripts unchanged** (no git diff).
- **Rows in → out:**
  - 5b: 731,800 → **643,101** dry daytime station-hours (88,699 removed). New cities: PHX 1.2% removed · SAN 4.3% · DLO 5.3% · HRL 12.3% · VLL 14.0% · ARB 17.2% · EUG/Springfield 19.3% (= Eugene). Kept with blank RH: **DLO 1,373**, HRL 99, ARB 64; ≤ 26 elsewhere among the new cities.
  - 6–7: no values above 10 mi (check passed). 643,101 hours converted.
  - 8: 643,101 station-hours → **581,563 city-hours**. The new cities all have one station, so they pass through as `point_sample = 1`. Detroit and Pittsburgh are unchanged.
- **Check:** for the original 10 cities, all data files in `step05_dry/`, `step07_extinction/` and `step08_city_hourly/` are **unchanged** (git). Only the three summary files changed, by gaining rows for the new cities.
- **Ceiling effect, new cities** (share of dry daytime hours at exactly 10 mi): ARB 84.7% · SAN 91.5% · DLO 93.9% · HRL 94.6% · EUG/Springfield 94.9% · VLL 97.0% · **PHX 99.3%**.
- **Caveat for the story/appendix:** Phoenix's airport visibility almost never drops below 10 mi on dry daytime hours (0.7% of hours; minimum 1.25 mi). Only 40 haze hours and 0 smoke hours are coded. So the METAR "embodied air quality" row will be nearly flat for Phoenix, even though Phoenix has real ozone and dust problems. Ozone doesn't reduce visibility much, and the 10-mi cap hides moderate haze. For Phoenix, the visibility row says little about air quality.
- **Output:** `data/processed/metar/step05_dry/`, `step07_extinction/`, `step08_city_hourly/`
- **Judgment calls:** none new.

### Steps 9a + 9b (rerun, 17 cities, D4 end date) · METAR · 2026-09-27 · Dish + Claude
- **What:** Reran the hours-per-day audit (9a) and the final daily visibility build (9b) on all 17 cities. **Script edit (D4):** the day range in both scripts now ends **2026-09-24** (3,920 days) instead of 2026-09-25; docstrings and comments updated. Minimum-hours rule (3), formulas and columns unchanged.
- **Input:** `data/processed/metar/step08_city_hourly/metar_<city>_cityhour.csv` (581,563 city-hours). City-hours outside the study period (Sep 25 for the original 10 and Springfield; Phoenix's Dec 31, 2015 evening) are not used.
- **Output:** `data/processed/metar/final/vis_<city>_daily.csv` — **17 files × 3,920 days** — plus `step09_summary.csv`; `step09a_hours_per_day/` tables.
- **Valid days (≥ 3 dry daytime hours), new cities:** PHX 3,915 · SAN 3,896 · HRL 3,810 · VLL 3,610 · EUG/Springfield 3,661 (= Eugene) · ARB 3,523 · **DLO 3,079** (78.5%; no data before 2017-01-15 and ~10% of later days missing). Original 10: one fewer day each, the dropped Sep 25.
- **Sep 24:** blank (`valid_day = 0`) for ARB, DLO, SAN and VLL, whose raw data ends Sep 23 (D5); valid for PHX and HRL.
- **Checks after running:**
  - Original 10 cities: each new file equals the previous committed file minus its final Sep 25 row. **Row-for-row identical otherwise.**
  - Hours used + hours in short days = all study-period city-hours, for every city.
  - Valid-day counts match 9a's "minimum 3" counts exactly.
  - `vis_springfield_daily.csv` is identical to `vis_eugene_daily.csv`.
- **Plausibility (worst days, new cities):** Ann Arbor 2023-06-28/29 (1.3–1.4 mi) lines up with the June 2023 Canadian wildfire smoke; San Diego 2020-09-14/15 (3.4–4.0 mi) with the September 2020 West Coast fires. **To review:** Ann Arbor 2016-07-25 (0.66 mi), Warren 2026-07-16/17 (1.05–1.66 mi) and Delano 2024-11-11 (1.69 mi) have no obvious explanation yet. Phoenix's worst valid day is 5.59 mi, and it has **0 days below 5 mi** (see the ceiling caveat above).
- **Judgment calls:** none new (D4 end date was set in the gridMET chat and applied here).


### Step 8b (rerun, D5 stations) · METAR · 2026-09-27 · Dish + Claude
- **What:** Added the 6 D5 airports (ARB, DLO, SAN, VLL, PHX, HRL), plus EUG measured to **Springfield's** city hall, to the airport-to-city-hall distance table and reran it. Same method as before (great-circle/haversine, straight line). **Read-only: no visibility data changed.**
- **Why:** The handoff requires logging each airport's distance from its city, and the new cities were missing.
- **Input:** airport coordinates copied by Claude from each station's IEM page (`mesonet.agron.iastate.edu/sites/site.php?station=<ID>&network=<NET>`, fetched 2026-09-27, values as shown to 5 decimals). City-hall coordinates supplied by Claude.
- **Script:** `scripts/metar/08b_station_distances.py` (7 rows appended to `AIRPORTS` and `CITY_HALLS`, plus one docstring line; the original 12 rows and the formula are unchanged; see git diff)
- **Rows in → out:** 12 → **19 rows**.
- **Output:** `data/processed/metar/metar_station_distances.csv` (overwritten; previous version in git)
- **Results (miles from city hall):** DLO 1.7 · SAN 1.7 · PHX 3.9 · ARB 4.0 · VLL 8.0 (Troy → Warren) · EUG → Springfield 10.9 · **HRL → Raymondville 19.2** (the farthest airport in the study).
- **Checks after running:** git diff shows only 7 rows added to the CSV and 0 changed. All files in `data/processed/metar/final/` are unchanged (checksums before vs after).
- **Judgment calls:**
  - **City-hall coordinates supplied by Claude:** Ann Arbor 301 E Huron St (42.2819, −83.7449) · Delano 1015 11th Ave (35.7686, −119.2476) · San Diego 202 C St (32.7167, −117.1628) · **Warren 1 City Square (42.5106, −83.0267)**, least certain · Phoenix 200 W Washington St (33.4484, −112.0770) · **Raymondville 142 S 7th St (26.4815, −97.7831)**, less certain · Springfield 225 5th St (44.0462, −123.0221). **Claude's choice, approved by Dish; Dish's spot-check pending (also for the original 10).**
  - Springfield gets its own row (EUG measured to Springfield city hall); Eugene's row is unchanged. **Claude's choice, approved by Dish.**
  - In-city note left as "not checked" for the new stations until the city-limits step. The exception is HRL, noted as outside (it's in Harlingen, per D5). **Claude's choice, approved by Dish.**


### Decision D7 · METAR · 2026-09-27 · Dish
- **What:** The "in city limits" check for the 6 new stations (ARB, DLO, SAN, VLL, PHX, HRL) and EUG → Springfield is **deferred**. Their in-city note stays "not checked" in `metar_station_distances.csv`. The Arizona Places file was not downloaded.
- **Why:** The check changes no visibility values; it's documentation only. The Step 8b distances already record how far each airport is from its city (e.g. HRL is 19.2 mi from Raymondville). The low-day review and the Phoenix decision matter more for the story.
- **Options considered:** (A) run the check now (needs the Arizona TIGER file); (B) defer. **Changed by Dish: chose B** (Claude's suggestion). Claude's planned script (`08c_airport_in_city.py`, same method as `scripts/gridmet/02_boundary_audit.py`) was not written.


### Decision D8 · METAR final (frozen) · 2026-09-27 · Dish
- **What:** The METAR visibility pipeline is **closed**. The 17 files `data/processed/metar/final/vis_<city>_daily.csv` (3,920 days each, 2016-01-01 → 2026-09-24) are final as they stand; no further reruns planned. They are unchanged since the Steps 9a + 9b rerun.
- **Options considered:** (A) freeze now; (B) run a read-only review of the 7 unexplained low days first, possibly blanking any that are fog. **Changed by Dish: chose A** (Claude's suggestion).
- **Moved out of the pipeline** (none of these change values): ASOS visibility algorithm citation (M1) → Forensics Appendix; how to use Phoenix's flat row → story work; city-hall spot-check → Dish, any time; in-city check for new stations → deferred (D7).
- **Unreviewed low days**, not to be used as story beats without checking: Boston 2024-02-23 · Bakersfield 2020-12-17/18 · Ann Arbor 2016-07-25 · Warren 2026-07-16/17 · Delano 2024-11-11 (possibly uncoded fog).
- **New finding (read-only check while summarizing):** **Ann Arbor (ARB) has an outage from about 2026-06-17.** Visibility and RH are blank in almost every raw report from then to the end of the file. Valid days: June 2026 20 · July 3 · August 1 (last valid day **2026-08-05**) · September 0. The pipeline handled it correctly (Step 2 dropped blank readings; those days are blank with `valid_day = 0`). **Ann Arbor can't be used for summer 2026.**
- **Caveats carried to the appendix:** 10-mi ceiling (65% of dry daytime hours at the cap for Bakersfield, up to 99% for Phoenix); Phoenix row nearly flat (0 days < 5 mi); airports are point samples, some outside the city (HRL 19.2 mi, DTW 16.1, PIT 12.9); removing wet hours tilts wet cities' series toward hazier weather; DLO/VLL use one routine report per hour (D6); ARB, DLO, SAN, VLL end 2026-09-23 (Sep 24 blank); DLO starts 2017-01-15.
- **SHA-256 of the final files** (so anyone can confirm they're unchanged):
  - annarbor `8fc6c471fdf2493bb2dd86a21663aea568c761739c743023b593e9d83948abce`
  - bakersfield `e422f6a0a9913d9c462e1e5d189b73d2a15c7d20349de8a4249c22f0518eeeb2`
  - boston `8823c355839c6fbf84bfac9cc3f186fea34c6f298a89b44ade7f4c521ea2585e`
  - brownsville `3594f620b8a19ef65c8636b4eb0b047c9b52f13f2842365556abfb4439dc7c3e`
  - delano `b6dfd24b8167974c8f9a3e107d561a45930b819150ab6894a47526d66ca8b54e`
  - detroit `588f67a423925ae0f4678d0e3e7fe3d209c1379a84f387a477b8187f58550a87`
  - eugene `0c1422b520093a3655a4b541e0e1bac803fdfc3730af417dafcb099d33c29bcb`
  - fairbanks `20d3a61b44332ed8d92e8640d28a089851f5ebec9d7bc89f82d6e873a10d9123`
  - fresno `6d8e01d8b661596af6c0746c7a9be68fa1811cb6ceec86d60b4a16bf2df40030`
  - losangeles `0697fab30dacd04189abb6e75441990c76f33135f970d56926db1c3ffe19f244`
  - phoenix `b9a42f7668ac3c5fd27f0fa09fa74391b6dafca9fc84aab2a16901552df871ca`
  - pittsburgh `3d83e853affb4040e91e1488b68f4cb8ee8ed37758124a48e04aba257a03e4ae`
  - raymondville `492a5f053e6929b173937598b7434b14834b639e4b1436cd07ccaaf17bd5d6f6`
  - sandiego `60c0ac6341496808337e391179dc47226e249a36c4bee10e69777ccd73714e41`
  - sanfrancisco `9123904d918c12300175b79bdb292460ca03ecada658b4b0dfea93da12213b84`
  - springfield `0c1422b520093a3655a4b541e0e1bac803fdfc3730af417dafcb099d33c29bcb`
  - warren `807c8f1520aa9ad8b3c536cda33e11a9cc58ca35c1e4c5a694786cd55c59f2aa`

### Step 1b (7 added cities) · gridMET · 2026-09-27 · Dish (download) + Claude (check)
- **What:** Dish downloaded the Census TIGER/Line 2025 Places file for **Arizona** by hand (census.gov/cgi-bin/geo/shapefiles/index.php → Year 2025 → Places → Arizona → Download), same settings as Step 1. Claude checked the zip. **File kept exactly as downloaded (not renamed, not unzipped).**
- **Why:** gridMET is being extended to the 7 continental cities that METAR added in D5 (Ann Arbor, Warren, Delano, San Diego, Phoenix, Raymondville, Springfield). Phoenix needs the Arizona file; the other 6 are in state files from Step 1 (CA, MI, OR, TX). Springfield OR gets its own city-limits polygon here (in METAR it shares Eugene's airport).
- **Output (raw):** `data/raw/gridmet/tiger_places/tl_2025_04_place.zip`
- **Check (read-only):** zip test passes; 7 files (.shp .shx .dbf .prj .cpg + 2 ISO .xml), dated 2025-09-12 by Census like the other states; 467 places; exactly one "Phoenix city" (GEOID 0455000).
- **SHA-256:** 04 `7c52a87725285cd6e6655daf6cf733c37942256bc7e190ac01ddb174a0acd330`
- **Judgment calls:** none new (same source, vintage and folder as Step 1).

### Step 2b (7 added cities) · gridMET · 2026-09-27 · Dish + Claude
- **What:** Read-only boundary audit for Ann Arbor, Warren, Delano, San Diego, Phoenix, Raymondville and Springfield, same method as Step 2 (areas, polygon pieces, approx. gridMET cells), plus the airport-in-city check for their METAR stations. **Nothing changed in raw data.**
- **Why:** Numbers for preparing the 7 new ClimateEngine polygons (Step 3b), and to close METAR's deferred in-city check (D7) at no extra cost.
- **Input:** `data/raw/gridmet/tiger_places/tl_2025_{04,06,26,41,48}_place.zip` (not modified) · `data/processed/metar/metar_station_distances.csv` (not modified; METAR frozen, D8)
- **Script:** `scripts/gridmet/02_boundary_audit.py` (7 cities added to the city list; nothing else changed)
- **Output:** `data/processed/gridmet/step02_boundary_audit/` → `boundary_audit.csv` (10 → 17 cities), `boundary_parts.csv` (197 → 234 pieces), `airport_in_city.csv` (12 → 19 rows). **Original rows byte-identical to the previous files** (checked against copies taken before the run).
- **Census matches (exactly one each, NAME + "<name> city"):** Ann Arbor 2603000 · Warren 2684000 · Delano 0618394 · San Diego 0666000 · **Phoenix 0455000** · Raymondville 4860836 · Springfield 4169600. The six from the METAR chat are confirmed.
- **Findings (boundaries):** land / water km², pieces, approx. gridMET cells: Ann Arbor 73.6 / 2.3 · 6 (detached total 0.07 km²) · 6 · Warren 89.0 / 0.2 · 1 · 5 · **Delano 38.1 / 0.1 · 3 (largest detached 1.65 km², 0.8 km away)** · 4 · San Diego 844.4 / 42.1 (4.8% water) · 3 (largest detached 0.26 km², 2.7 km) · 50 · Phoenix 1,342.7 / 2.6 · 2 (detached 0.28 km²) · 75 · **Raymondville 10.7 / 0.03 · 1 · ~1 cell** · Springfield 41.6 / 0.0 · 21 (slivers, largest 0.42 km²) · 3.
- **Findings (airports, closes D7):** **inside:** DLO, SAN, PHX. **Outside:** ARB 0.6 km · VLL 7.5 km · EUG→Springfield 13.7 km · HRL→Raymondville 27.6 km beyond the boundary. Recorded here only; `metar_station_distances.csv` keeps "not checked" (frozen, D8).
- **Caveats:** Raymondville's city mean is effectively one gridMET cell; Delano and Springfield 3–4. Springfield borders Eugene, so they share edge cells.
- **Judgment calls:**
  - Rewrote the three Step 2 CSVs with all 17 cities (rather than separate files), after verifying the original rows are unchanged. **Claude's choice, approved by Dish.**
  - Airport check for the 7 new stations included (reopens D7). **Approved by Dish.**

### Step 3b (7 added cities) · gridMET · 2026-09-27 · Dish + Claude
- **What:** Saved each new city's city-limits shape from its state file as its own zipped shapefile for ClimateEngine upload (same method as Step 3: WGS84, columns GEOID/NAME/NAMELSAD/ALAND/AWATER). **All 7 shapes kept as-is**, following D3's rule (water kept, small pieces kept).
- **Why:** ClimateEngine needs one uploadable polygon per city.
- **Input:** `data/raw/gridmet/tiger_places/tl_2025_{04,06,26,41,48}_place.zip` (not modified)
- **Script:** `scripts/gridmet/03_city_polygons.py` (7 cities added; now **never overwrites an existing zip**)
- **Rows/values in → out:** 7 shapes → 7 zips; pieces and area unchanged (Ann Arbor 6 pieces 75.80 km² · Warren 1 · 89.18 · Delano 3 · 38.25 · San Diego 3 · 886.48 · Phoenix 2 · 1,345.28 · Raymondville 1 · 10.68 · Springfield 21 · 41.59). `step03_summary.csv` 9 → 16 rows; original 9 rows byte-identical. **Original 9 zips untouched (SHA-256 unchanged).**
- **Output:** `data/processed/gridmet/step03_city_polygons/<city>_citylimits.zip` for annarbor, warren, delano, sandiego, phoenix, raymondville, springfield
- **D3 review for the new cities (Dish):** no piece comparable to SF's Farallones. Delano has 2 detached pieces (1.65 + 0.29 km²) ~7 km west of downtown (possibly the annexed state-prison area; not verified). San Diego: 0.26 km² piece near Otay Reservoir, 2.7 km from the main shape; water 42 km² (4.8%: bays, reservoirs, near-shore ocean), blank in gridMET. Phoenix, Springfield, Ann Arbor: slivers touching the main shape. **Approved by Dish: keep all as-is** (Claude's suggestion).
- **Judgment calls:**
  - Existing zips are skipped rather than rewritten, because zip timestamps would change their bytes even with identical shapes. **Claude's choice, approved by Dish.**

### Decision D9 · UTCI scope · 2026-09-27 · Dish
- **What:** UTCI felt heat is pulled from Copernicus CDS **"Thermal comfort indices time-series derived from ERA5 reanalysis"** (ERA5-HEAT v1.1, hourly, 0.25°; consolidated data plus intermediate near-real-time days, which the CDS may later replace). The handoff named the gridded ERA5-HEAT dataset, but it ships global daily files; the time-series product gives the same values for one small box per city (max 3×3°) in a single request.
- **Cities:** the 17 METAR cities (D5), **including Fairbanks** (ERA5 is global). Springfield gets its own cell choice.
- **Period:** one continuous request per city, 1991-01-01 UTC → latest available. It covers the 1991–2020 baseline (kept, same as gridMET) and the 2016 → 2026-09-24 study period. The latest UTCI date is expected to lag ~5 days. **Whether all datasets share one end date is to be decided once all three are in** (METAR stays frozen, D8).
- **Boundary:** city limits, TIGER/Line 2025 Places (D2). The UTCI "city" is the city-hall cell or the cells overlapping city limits, chosen per city in a later step.
- **Raw files:** committed to git (~20–30 MB each). SHA-256 logged for each.
- **Judgment calls:** time-series product instead of gridded. **Claude's choice, approved by Dish.** Raw NetCDF committed. **Changed by Dish** (Claude had suggested .gitignore). Download box = cells overlapping city limits plus a 1-cell margin. **Claude's choice, approved by Dish.**

### Step 0 · UTCI · 2026-09-27 · Dish + Claude
- **What:** Created `data/raw/utci/cds_timeseries/`, `data/processed/utci/`, `scripts/utci/` (with `.gitkeep`). Installed xarray 2025.6.1 and netCDF4 1.7.4 (plus geopandas 1.1.4) in the local workspace. **Input / output:** none (setup only) · **Script:** none (folder setup only)
- **Proxy check:** the CDS is blocked (HTTP 403) from both the local workspace and Claude's cloud workspace, so Dish downloads by hand from the CDS website.
- **Judgment calls:** layout proposed by Claude. **Approved by Dish.**

### Decision D10 · all datasets · 2026-09-27 · Dish
- **What:** Final city list for the visualization, **12 cities**, in this order: Los Angeles · Phoenix · San Diego · Detroit · Bakersfield · San Francisco · Fresno · Boston · Eugene · Fairbanks · Brownsville · Ann Arbor. **Dropped at the visualization stage:** Pittsburgh, Raymondville, Springfield, Warren, Delano.
- **Effect on existing files:** none. All data already pulled is kept (METAR finals frozen per D8; gridMET files as they are; UTCI Delano file kept). Extra cities are cut when building the visualizations.
- **Who chose it:** **Dish.**

### Step 1 · UTCI · 2026-09-27 · Dish (downloads) + Claude (check)
- **Downloads (Dish, CDS web form):** "Thermal comfort indices time-series derived from ERA5 reanalysis" · Universal thermal climate index · 1991-01-01 → **2026-06-13 (latest date the form allowed on 2026-09-27)** · Area (the form's field order is **North / South / West / East**) with the per-city boxes from D9 · NetCDF. 13 files, one per city, named `utci_<city>_1991-2026.nc` at save time. Boston was saved without an extension and **renamed** to add `.nc` (name only; SHA-256 identical before and after). File contents untouched.
- **What (check):** read-only check of every raw file: SHA-256; grid vs requested box; hourly continuity; units; empty and implausible values (outside −90 to +60 °C) per cell. Added after the first 10 files (approved by Dish): location check (city-hall cell in the file, every cell touching city limits in the file), hottest 3 days in the city-hall cell, duplicate cells, empty hours by year, and agreement where two cities' boxes share cells.
- **Input:** `data/raw/utci/cds_timeseries/utci_<city>_1991-2026.nc` (13 files, not modified; SHA-256 re-checked after each run) · city limits from `data/processed/gridmet/step03_city_polygons/` and, for Fairbanks, GEOID 0224230 in `data/raw/gridmet/tiger_places/tl_2025_02_place.zip` · city halls from `data/processed/metar/metar_station_distances.csv` (not modified)
- **Script:** `scripts/utci/01_raw_check.py`
- **Output:** `data/processed/utci/step01_raw_check/` → `raw_check.csv` (13 rows), `raw_cells.csv` (232 cells), `raw_extra.csv` (13 rows)
- **Results:** all 13 files: box matches the request, cell centres on 0.25° steps, **310,752 of 310,752 hours** (1991-01-01 00:00 → 2026-06-13 23:00 UTC), 0 missing, 0 duplicate, units K, 0 implausible values. City-hall cell in the file and 0 city-limits cells missing, for every city. Where boxes overlap, the files are identical (Ann Arbor/Detroit 3 cells, Bakersfield/Delano 6 cells).
- **Location sanity check (hottest UTC days, city-hall cell):** Eugene 2021-06-27/28 (Pacific NW heat dome) · Fresno and Bakersfield 2022-09-06 (same day as gridMET's record) · Los Angeles 2022-09-04, 2020-09-05, 2018-07-07 · Phoenix 2017-06-20/21 · Detroit and Ann Arbor 2012-07-06, 1995-07-14 · Boston 2011-07-22 · Fairbanks 2004-06-29 · San Diego 2024-09-08. Brownsville's lowest value (−30.3 °C UTCI) is on 2021-02-15, the Texas freeze.
- **Findings (nothing changed):**
  - **Duplicate cells:** in Boston, Eugene, Fairbanks, Los Angeles and Phoenix, some neighbouring 0.25° cells hold identical values in ≥ 99.99% of hours (e.g. Boston lon −71.00 = −71.25; Eugene −123.00 = −122.75; Fairbanks −147.50 = −147.25; Phoenix lat 33.75 = 34.00; LA several pairs). The Boston, Eugene and LA pairs differ only on 2021-04-29. Likely cause (not verified): regridding from ERA5's native ~31 km grid to 0.25°. So UTCI's true detail is coarser than the 0.25° grid suggests, and some city-hall cells equal their neighbour. Duplicates must be dropped before averaging cells.
  - **Empty hours:** hours with an empty value in any cell: Boston 744, SF 170, Brownsville 119, Detroit 267, LA 89, San Diego 1; 0 in the other 7. Mostly sea or lake cells; in Brownsville also inland cells. Possible cause (not verified): UTCI left blank when inputs are outside the UTCI formula's valid range (e.g. wind > 17 m/s). Days with missing hours to be handled in the daily-max step.
  - **San Francisco:** the city-hall cell (37.75, −122.50) is centred on the ocean side; its hottest day is only 30.1 °C UTCI and it misses the 2017-09-01 heat. Needs a closer look in the cell-choice step.
  - **Gap:** UTCI ends 2026-06-13; METAR and gridMET run to 2026-09-24 (D4). Common end date still to be decided (D9).
  - A Finder `.DS_Store` file appeared in the raw folder; not to be committed.
- **SHA-256 of raw files:**
  - annarbor (13,689,826 bytes) `105c4e11088968f7ddd1b4321266b1e31f97519a1b7dd6811d9b6fab0ab78f72`
  - bakersfield (27,362,914 bytes) `eb5f242af626a2be110e1d03ceddb5fe93be368d0f86fd4c3f4ebac620d9ba3a`
  - boston (27,362,914 bytes) `7c69c5f473c6ba453410768469010ee3a72f5fbbfbb4bcf82ff36d8a2ea3d790`
  - brownsville (33,577,954 bytes) `cebe5957faeb86ffa74b02072c70bbb733ddbf2eeef552e7eea9269e1aa0c7cb`
  - delano (13,689,826 bytes) `22209537e2fd8feb98ffbae96bd9791ff89296d201e6a8cd515d266d649caeef`
  - detroit (22,390,882 bytes) `3d78cd64b0a2b229deff471978599fac514aec87d2de7dd1bbcd77f7bd65ee43`
  - eugene (22,390,882 bytes) `43aa2910e2fe9514a3b354610bebda844a0a4559ee4bd7c5bc18f56cfa12be40`
  - fairbanks (22,390,882 bytes) `8f89828d9afd581b8eda2fe16400504007a33c058e2aaf6239e3eed7c160e281`
  - fresno (22,390,882 bytes) `0d59b2c4313da17f9bdfbccef4ebb1f1cf5e771ed474b8330a84aae85db051be`
  - losangeles (33,577,954 bytes) `e51574d8c7a3cbe90bbf283e95a123142262504b23c26d79182f2f976e6bfdbc`
  - phoenix (32,334,946 bytes) `e3444d94987f6779dcd5336e6129fd63433a60aa8b1ed12af4c12b087344cc9a`
  - sandiego (27,362,914 bytes) `38b4b398aa23b87f4c28f9efbacb2c1b01bb2193ea9fab5bc4025baa085ccdfd`
  - sanfrancisco (22,390,882 bytes) `78a42af438849a288f4d6cf0b127ac23ca4dc383fba2dfb1551e45191f9b1a6a`
- **Judgment calls:**
  - Plausible range −90 to +60 °C, flag only. **Claude's choice, approved by Dish.**
  - Rename of the Boston file to add `.nc`. **Claude's choice, approved by Dish.**
  - Extra checks (location, hottest days, duplicates, empty hours, overlaps) added to the Step 1 script. Duplicate = identical in > 50% of hours. City-hall cell = nearest 0.25° centre. **Claude's choice, approved by Dish.**
  - Script bug caught before logging: the first version of the extra checks overwrote the per-cell table (17 rows instead of 232). Fixed by renaming variables; the re-run table matches the earlier output exactly.

### Decision D11 · UTCI cells · 2026-09-27 · Dish
- **What:** A city's UTCI = **area-weighted average of every 0.25° cell touching city limits** (weight = the cell's share of city area, TIGER/Line 2025 per D2). Applies to all 12 cities (D10). Matches gridMET, which averages over city limits.
- **Options considered:** (A) city-hall cell only; (B) area-weighted average of all touching cells; (C) single cell where it covers ≥ 75%, else B. **Changed by Dish: chose B** (Claude's recommendation).
- **Correction to Step 1:** Step 1 said duplicate cells "must be dropped before averaging." With area weights that is unnecessary: a duplicated pair is one native ERA5 point covering both squares, so weighting each square by its area equals merging them. Duplicates are recorded but not changed (only 2021-04-29 differs within the pairs).
- **Consequence:** San Francisco stays mostly marine (75% of its weight is the ocean-side cell 37.75, −122.50), like gridMET's SF city mean.
- **Rules for the next steps (approved by Dish now):**
  - **Missing cells in an hour:** average the cells that have a value, re-weighted to sum to 1; if those cells cover **< 50% of the city's weight**, the hour is left empty. **Claude's choice, approved by Dish.**
  - **Order:** average the cells hour by hour first, then take the daily maximum (Step 4). **Claude's choice, approved by Dish.**

### Step 2 · UTCI · 2026-09-27 · Dish + Claude
- **What:** For each of the 12 cities, listed every UTCI cell touching city limits and its share of the city's area; the shares are the cell weights for D11. **Read-only on inputs.**
- **Why:** Fixes, in one table, exactly which cells make up each city and how much each counts.
- **Input:** `data/raw/utci/cds_timeseries/utci_<city>_1991-2026.nc` (grid and duplicate check only; not modified) · `data/processed/gridmet/step03_city_polygons/<city>_citylimits.zip`; Fairbanks GEOID 0224230 from `data/raw/gridmet/tiger_places/tl_2025_02_place.zip` · city halls from `data/processed/metar/metar_station_distances.csv`
- **Script:** `scripts/utci/02_cell_weights.py`
- **Output:** `data/processed/utci/step02_cell_weights/cell_weights.csv` (53 rows: city, lat, lon, overlap_km2, weight, is_city_hall_cell, duplicate_of)
- **Results (cells · city-hall cell weight · largest cell if different):** Los Angeles 6 · 23.1% · 34.25,−118.50 35.4% | Phoenix 7 · 30.9% | San Diego 5 · 29.6% | Detroit 4 · 25.5% · 42.50,−83.00 31.6% | Bakersfield 5 · 23.5% · 35.25,−119.00 46.8% | San Francisco 4 · 75.4% | Fresno 3 · 80.0% | Boston 5 · 65.6% | Eugene 3 · 58.2% | Fairbanks 3 · 59.5% | Brownsville 6 · 88.9% | Ann Arbor 1 · 100%. Weights sum to 1 in every city.
- **Checks:** raw UTCI files and Step 1 outputs unchanged (SHA-256).
- **Judgment calls:**
  - Cell footprint = centre ± 0.125°; areas in an equal-area projection (EPSG:6933); weights re-normalized to sum exactly to 1. **Claude's choice, approved by Dish.**
  - Every touching cell kept, however small (smallest: SF 38.00,−122.25 at 0.1%). Follows from D11 (no cutoff).
- **Related (not in the repo yet):** state-by-state map of these cells over gridMET city limits and METAR airports, made for Dish's review in chat (`scripts/utci/02_cell_map.py`, 13 cities incl. Delano). Basemap for its outlines: `data/raw/basemap/ne_50m_admin_1_states_provinces.geojson` (Natural Earth 1:50m, public domain, from GitHub nvkelso/natural-earth-vector commit 117488dc, 2022-05-05; 2,325,694 bytes; SHA-256 `69a0e06e640b2d505858ae1cb63034e4677f3000b35a98e16312932b98c426b9`). Downloaded with Dish's approval; drawing only.

### Step 2a · UTCI map · 2026-09-27 · Dish + Claude
- **What:** State-by-state map of the D11 UTCI cells over the gridMET city-limits polygons and the METAR airports, for the 12 cities (D10). One locator panel per state, then one zoomed panel per city. Cells are shaded and labelled with their weight; the city-hall cell is outlined; dashed "=" links join cells with identical values. **Read-only on all inputs; figure only, no data changed.**
- **Why:** For Dish's visualization work and the Forensics Appendix: shows how coarse UTCI is next to the city limits and the airports.
- **Input:** `data/processed/utci/step02_cell_weights/cell_weights.csv` (weights, duplicates) · UTCI raw files (grid only) · `data/processed/gridmet/step03_city_polygons/` + Fairbanks from `tl_2025_02_place.zip` · `data/processed/metar/metar_station_distances.csv` · `data/processed/gridmet/step02_boundary_audit/airport_in_city.csv` · `data/raw/basemap/ne_50m_admin_1_states_provinces.geojson` (see Step 2) — none modified
- **Script:** `scripts/utci/02_cell_map.py` (drawing style copied from `scripts/maps/01_airport_city_map.py`, which was not modified)
- **Output:** `docs/figures/utci_cells_map.png` (SHA-256 `98c7e9c8c00a5e643b1f5175660751ae83f71adcd6d956c90af2ba0e1dd1f496`) and `.pdf`
- **Layout:** states in order of their first city in Dish's D10 list: California (LA, San Diego, Bakersfield, San Francisco, Fresno) · Arizona · Michigan (Detroit, Ann Arbor) · Massachusetts · Oregon · Alaska · Texas. **Changed by Dish:** state-by-state layout with city zooms; D10 order.
- **Judgment calls:** Natural Earth 1:50m outlines (drawing only; coarser than TIGER); Alaska locator cropped to the mainland (lon −170 to −129); city zoom = cells touching city limits + 0.06° margin; a draft with 13 cities and "= lat,lon" text labels was shown to Dish in chat and replaced by this version. **Claude's choice, approved by Dish.**

### Step 3 · UTCI · 2026-09-27 · Dish + Claude
- **What:** Built one hourly UTCI series per city: in every hour, the area-weighted average of the city's cells (D11 weights from Step 2). Cells without a value in that hour are skipped and the other weights re-normalized; if the cells with a value cover < 50% of the city's weight, the hour is left empty (D11 rules). Times stay in UTC and values in kelvin.
- **Why:** Turns each city's 1–7 cells into the single "city" UTCI that the daily steps use.
- **Input:** `data/raw/utci/cds_timeseries/utci_<city>_1991-2026.nc` (12 cities; Delano's file not used, D10) · `data/processed/utci/step02_cell_weights/cell_weights.csv` — not modified (SHA-256 re-checked)
- **Script:** `scripts/utci/03_city_hourly.py`
- **Output:** `data/processed/utci/step03_city_hourly/utci_<city>_hourly.csv.gz` (columns: time_utc, utci_k, weight_available, n_cells_used, n_cells) and `step03_summary.csv`
- **Rows in → out:** 310,752 hours per city in → 310,752 out. **All cells present in every hour for 11 of 12 cities** (the empty hours seen in Step 1 were all in cells outside city limits). **Brownsville:** 17 hours kept with part of the cells (coverage ≥ 91%) and **10 hours left empty** (coverage 0–4%, because the city-hall cell, 89% of the weight, is blank).
- **Finding (Brownsville empty hours):** they fall on **2005-07-20** (Hurricane Emily), **2008-07-23/24** (Hurricane Dolly), **2010-07-01** (Hurricane Alex) and **2020-07-26** (Hurricane Hanna), all landfalls or near-landfalls in South Texas. This strongly supports the Step 1 guess that ERA5-HEAT leaves UTCI blank when wind is outside the UTCI formula's range (> 17 m/s): **the felt-heat index is undefined in a hurricane.** Possible story/appendix note. (Hurricane dates are Claude's identification, not checked against a storm database.)
- **Checks:** Ann Arbor (1 cell) equals its raw cell to 0.00005 K (rounding to 4 decimals); a hand calculation for Los Angeles 2022-09-06 22:00 UTC matches the file (313.7929 K).
- **Range (°C UTCI, all hours 1991–2026-06-13):** LA −12.0 / 17.1 / 47.6 (min / mean / max) · Phoenix −26.3 / 19.7 / 51.5 · San Diego −15.8 / 16.3 / 42.6 · Detroit −49.3 / 4.5 / 42.4 · Bakersfield −12.0 / 17.8 / 48.0 · San Francisco −22.4 / 8.1 / 32.3 · Fresno −15.3 / 17.2 / 51.6 · Boston −51.6 / 5.3 / 41.4 · Eugene −28.9 / 9.9 / 46.3 · Fairbanks −52.5 / −4.6 / 36.1 · Brownsville −30.2 / 22.2 / 45.3 · Ann Arbor −49.2 / 4.7 / 43.2.
- **Judgment calls:**
  - Output as gzip-compressed CSV (~2 MB per city instead of ~12 MB), values written to 4 decimals of a kelvin. **Claude's choice, approved by Dish.**
  - Missing-cell and 50% coverage rules as decided in D11. **Claude's choice, approved by Dish.**

### Decision D12 · UTCI bad day · 2026-09-27 · Dish
- **What:** All 24 UTC hours of **2021-04-29** are treated as missing in every city. Applied in Step 4; raw files and Step 3 files unchanged.
- **Why:** In all 12 cities that UTC day's hourly pattern runs opposite to the days on either side (correlation −0.71 to −0.96), so UTCI "peaks" in the middle of the night (e.g. Brownsville 45.3 °C at 3 am local, which had become its all-time record; LA 38.0 °C at 3 am). It is also the only day on which the duplicate cells from Step 1 differ, which points to a processing fault in the CDS time series. A scan of every day 1991 → 2026-06-13 (median across cities of each day's correlation with its neighbours) found no other such day; the next-lowest days (0.09–0.26) are winter days with a flat daily cycle.
- **Effect:** with the all-hours rule (Step 4), local days **2021-04-28 and 2021-04-29** become blank in all 12 cities (both contain hours of UTC 2021-04-29). The day is in the study period, not the 1991–2020 baseline.
- **Options considered:** (A) set the day aside; (B) keep it and flag it. **Changed by Dish: chose A** (Claude's recommendation).
- **Follow-up (optional):** report the day to Copernicus/ECMWF support.

### Step 4 · UTCI · 2026-09-27 · Dish + Claude
- **What:** Converted each city's hourly UTCI from UTC to local time, grouped hours into local calendar days (midnight to midnight), took each day's **highest hourly UTCI**, and converted kelvin → °C → °F. Also recorded the local hour of the maximum.
- **Why:** Procedure 3, step 4: daily maximum felt heat in local time, comparable with the daily gridMET high.
- **Input:** `data/processed/utci/step03_city_hourly/utci_<city>_hourly.csv.gz` (12 files, not modified; SHA-256 re-checked)
- **Script:** `scripts/utci/04_daily_max.py`
- **Output:** `data/processed/utci/step04_daily_max/utci_<city>_daily_max.csv` (columns: date, utci_max_c, utci_max_f, hour_of_max_local, n_hours, n_hours_expected, valid) and `step04_summary.csv`
- **Time zones (same as METAR):** America/Los_Angeles (LA, San Diego, Bakersfield, SF, Fresno, Eugene) · America/Phoenix (MST, UTC−7 all year) · America/Chicago (Brownsville) · America/Detroit (Detroit, Ann Arbor) · America/New_York (Boston) · America/Anchorage (Fairbanks).
- **Rows in → out:** 310,752 hours → **12,948 local days per city** (1991-01-01 → 2026-06-13). Valid days: 12,945 in 11 cities, 12,943 in Brownsville. **Blank days:** 2021-04-28 and 2021-04-29 (D12) and 2026-06-13 (data end at 23:00 UTC, mid-afternoon or evening locally), all cities; plus Brownsville 2005-07-20 and 2008-07-23 (hurricane hours missing, Step 3). Last complete day: **2026-06-12**. DST days: 36 with 23 hours, 35 with 25 (none in Phoenix). The UTC hours of 1990-12-31 local are not used.
- **Checks:** typical local hour of the daily max: San Diego 11, SF 12, LA 13, Detroit/Boston/Eugene/Fairbanks/Brownsville/Ann Arbor 14, Phoenix 15, Bakersfield/Fresno 16. Hottest days: LA 2018-07-06 (47.6 °C) · Phoenix 1995-07-28 (51.5) · San Diego 2020-09-06 (42.6) · Detroit 2012-07-06 (42.4) · Bakersfield 2022-09-06 (48.0) · SF 2017-09-02 (32.3) · Fresno 2022-09-06 (51.6) · Boston 2011-07-22 (41.4) · Eugene 2021-06-27 (46.3) · Fairbanks 2004-06-28 (36.1) · Brownsville 2024-05-09 (44.8) · Ann Arbor 2012-07-06 (43.2).
- **Judgment calls:**
  - **A day counts only if every local hour has a value** (Option 1). **Changed by Dish: chose Option 1** over "≥ 20 hours" (Claude's recommendation was Option 1). Reason: a missing hour can be the daily peak (Brownsville 2008-07-23 lacks 3–5 pm).
  - Values rounded to 2 decimals; °F computed from unrounded °C. **Claude's choice, approved by Dish.**
  - Found while checking this step: the corrupt UTC day 2021-04-29 → D12. The first run of this step (before D12) was replaced.

### Decision D13 · UTCI units · 2026-09-27 · Dish
- **What:** UTCI is reported in **°F** from here on (stress-band ranges in Step 5; normal, 10th/90th percentiles and anomaly in Step 6 and later), matching gridMET (°F). `utci_max_c` is kept as a reference column. Stress bands are still assigned on °C, the scale's native unit, so 2-decimal rounding in °F cannot move a day across a band edge.
- **Who chose it:** **Dish** ("I need all of these to be in F"); the classify-on-°C detail is **Claude's choice, approved by Dish.**

### Step 5 · UTCI · 2026-09-27 · Dish + Claude
- **What:** Gave every valid day a heat/cold-stress category from its daily maximum UTCI, using the standard 10-band UTCI assessment scale (Bröde et al. 2012). Edges in °C (°F): −40 (−40.0) · −27 (−16.6) · −13 (8.6) · 0 (32.0) · 9 (48.2) · 26 (78.8) · 32 (89.6) · 38 (100.4) · 46 (114.8). Levels −5 (extreme cold) … 0 (no thermal stress) … +4 (extreme heat).
- **Why:** Procedure 3, step 5: a readable label for how the day felt.
- **Input:** `data/processed/utci/step04_daily_max/utci_<city>_daily_max.csv` (not modified; SHA-256 re-checked)
- **Script:** `scripts/utci/05_stress_category.py`
- **Output:** `data/processed/utci/step05_stress/utci_<city>_stress.csv` (Step 4 columns + stress_level, stress_category, stress_range_f) and `step05_summary.csv`
- **Rows in → out:** 12,948 days per city in and out; every valid day has exactly one category, blank days (3 per city, 5 in Brownsville) stay blank.
- **Results, heat side, valid days 2016-01-01 → 2026-06-12 (moderate / strong / very strong / extreme):** LA 1,592 / 858 / 112 / 5 · Phoenix 903 / 730 / 1,032 / 215 · San Diego 1,506 / 562 / 26 / 0 · Detroit 730 / 358 / 3 / 0 · Bakersfield 933 / 738 / 834 / 5 · San Francisco 103 / 1 / 0 / 0 · Fresno 848 / 684 / 898 / 86 · Boston 660 / 301 / 7 / 0 · Eugene 747 / 257 / 36 / 1 · Fairbanks 329 / 43 / 0 / 0 · Brownsville 998 / 1,504 / 553 / 0 · Ann Arbor 734 / 407 / 5 / 0. Fairbanks also has 8 days of extreme cold stress (warmest hour below −40 °F).
- **Checks:** edge values land as decided (26.00 °C → no thermal stress; 32.00 → moderate heat; 0.00 → moderate cold; 9.00 → slight cold).
- **Judgment calls:**
  - **Each band includes its upper edge** (e.g. moderate heat = above 26 up to and including 32 °C). **Changed by Dish: chose this** (Claude's suggestion). Only 0–9 days per city since 2016 sit exactly on an edge.
  - **Full 10-band scale, including cold-stress bands** (Option A). **Changed by Dish: chose A** (Claude's recommendation). **Caveat for the appendix:** categories come from the day's *warmest* hour, so cold stress is understated ("slight cold stress" = even the warmest hour was slightly cold).

### Step 6 · UTCI · 2026-09-27 · Dish + Claude
- **What:** For each calendar date, built the 1991–2020 "normal" felt heat from the daily maximum UTCI (°F, D13), then compared every 2016+ day with it. Wrote the **final UTCI files**.
- **Method (the recipe gridMET Step 5 should copy for Step 7):**
  1. Pool = every **valid** baseline day (1991-01-01 → 2020-12-31) whose calendar date is within **±7 days** of the target date, across all 30 years; the window wraps around New Year (Jan 1 uses Dec 25 – Jan 8).
  2. Calendar = 365 days; **Feb 29 counts as Feb 28** (in the pool and as a target date). Pools are 450 values, **458** for windows containing Feb 28 (8 leap years in 1991–2020, incl. 2020).
  3. normal_f = mean of the pool; p10_f / p90_f = 10th / 90th percentile (numpy default, linear interpolation).
  4. anomaly_f = utci_max_f − normal_f; **abnormally_high = 1 if utci_max_f > p90_f** (strictly greater), else 0; blank on invalid days.
- **Input:** `data/processed/utci/step05_stress/utci_<city>_stress.csv` (not modified; SHA-256 re-checked) · `data/processed/utci/step02_cell_weights/cell_weights.csv` (for `cells_used`)
- **Script:** `scripts/utci/06_normals_final.py`
- **Output:** `data/processed/utci/final/utci_<city>_daily.csv` (12 files; columns: date, utci_max_f, utci_max_c, stress_level, stress_category, stress_range_f, normal_f, p10_f, p90_f, anomaly_f, abnormally_high, n_baseline_values, valid, cells_used) and `step06_summary.csv`
- **Rows:** **3,920 per city, 2016-01-01 → 2026-09-24** (same days as METAR and gridMET, D4); **3,814 valid**. Blank rows: 2021-04-28/29 (D12) and **2026-06-13 → 2026-09-24** (UTCI data end; **changed by Dish:** keep blank rows so the three datasets line up). Blank rows still carry the date's normal, p10 and p90.
- **Checks:** share of baseline days above their own p90 = 9.2–9.9% per city (≈ 10% expected; slightly lower because "above" is strict). Hand calculation for Phoenix 2023-07-15 matches the file (450 values; normal 110.28 °F, p10 102.75, p90 117.01; that day 120.32 °F → abnormally high, extreme heat stress). 2016-02-29 uses the 458-value Feb 28 pool. Brownsville's smallest pool is 448 (its two hurricane days, 2005-07-20 and 2008-07-23, fall in overlapping windows).
- **Rounding note (added after a read-only check of the final files, 2026-09-27):** on **4 days** the stored `utci_max_f` equals the stored `p90_f` yet `abnormally_high` = 1: San Diego 2021-02-22 (80.71 °F) and 2022-06-08 (86.80), Boston 2024-04-29 (75.40), Brownsville 2025-10-25 (94.99). The flag compares the day's value with the **unrounded** p90, which was just below it; the file shows p90 rounded to 2 decimals. Correct under the strict "above p90" rule; no change made. gridMET Step 5 has the same effect on 5 days. Small method difference: UTCI compares the 2-decimal daily value with the unrounded p90, gridMET compares both unrounded; no visible effect at 2 decimals.
- **Results, valid days 2016-01-01 → 2026-06-12 (share abnormally high / mean anomaly):** LA 11.7% / +0.79 °F · Phoenix 15.7% / +1.40 °F · San Diego 12.3% / +0.79 °F · Detroit 12.2% / +1.29 °F · Bakersfield 16.1% / +1.61 °F · SF 10.5% / +0.59 °F · Fresno 17.7% / +2.19 °F · Boston 11.7% / +1.13 °F · Eugene 12.3% / +0.85 °F · Fairbanks 9.9% / +0.66 °F · Brownsville 17.6% / +1.56 °F · Ann Arbor 12.3% / +1.27 °F. Every city except Fairbanks is above the 10% expected from the baseline, and every city's mean anomaly is positive: felt heat since 2016 runs warmer than 1991–2020.
- **Judgment calls:**
  - Blank baseline days left out of the pool; no minimum pool size (smallest is 448). **Claude's choice, approved by Dish.**
  - Percentile method = numpy default (linear). **Claude's choice, approved by Dish.**
  - Values rounded to 2 decimals; anomaly computed before rounding the normal. **Claude's choice, approved by Dish.**
- **SHA-256 of the final files:**
  - losangeles `53ce50c391848325afc829ca66f98cdb78d94cca67ad081c1e53833aa4c59d53`
  - phoenix `8e91d2730750e88969731441822556926afddb22c1b1674faef95ae784ea62ba`
  - sandiego `e4c676dd341d94264ffc3403c1b69036d77c8270ef493fd4387478f36e98e464`
  - detroit `5018861a6eb8fa6ecf996df1fe46ff5a35317c54f2e7afa0b1d1db0440c22a3d`
  - bakersfield `6e207646e52f33496c5dd457e056d37896e59fc04f0e7682e6d30baa7d598b38`
  - sanfrancisco `eefa156416dcc282a3c8ee279ea1319962b769e60f7439ea1e36f88bfb5b7e56`
  - fresno `f604438a692916aa13ba1a133dcceee6e65d576f6c48e4cef8279260cec6ece7`
  - boston `41c13e1112da822f1570dab664e1c1934ee7b8dfbf61b6c6c2e45f154b00431d`
  - eugene `056e3191eaf4282b32ec73f46d143e9ee9db52a05fac0016560c218cee5dd0ba`
  - fairbanks `713e0d2d2cd6c77fb2374f793236610f65cd138ca56c1d1834d2a08cb1b5d192`
  - brownsville `201dc8107b16962dc11b64df86c9233e145e4c28d17ef311c1a0f76af6f5f689`
  - annarbor `61ce4decf6b10fd5b0d70615c6b102c68225abecd7f4aa78b6ef1e2d63c257e0`

### Step 4b (7 added cities) · gridMET · 2026-09-27 · Dish (downloads) + Claude (check)
- **What:** Dish downloaded 14 ClimateEngine CSVs for the 7 added cities with the Step 4 settings (one city-limits polygon per request, its GEOID picked in the region dropdown, GridMET 4km Daily · Maximum Temperature · deg F · 4000 m · Mean · No masking; 2016-01-01 → 2026-09-24 and 1991-01-01 → 2020-12-31). Claude ran the raw check on all 32 files. **Read-only: nothing changed.**
- **Upload note:** the Step 3b zips showed greyed out in the browser's file picker (likely a macOS attribute on files written by the Claude session). Dish uploaded plain Terminal copies (`cp`) from `~/Desktop/ce_upload/`; a copy is byte-identical, so the polygons are unchanged.
- **Script change (approved by Dish before running):** `scripts/gridmet/04_raw_check.py` — the 7 GEOIDs added to the expected list; nothing else changed.
- **Output:** `data/processed/gridmet/step04_raw_check/raw_check.csv` (18 → 32 rows). **Original 18 rows identical to the previous file; original 18 raw files' SHA-256 unchanged.**
- **Results (new 14):** right GEOID and date range in every header; 3,920/3,920 and 10,958/10,958 days; 0 missing, duplicate, bad-date, blank or implausible; **2016–2020 overlap identical in all 7 (max difference 0.0 °F).**
- **Hottest study-period days:** Phoenix 117.5 °F (2016-06-19) · Delano 112.0 °F (2022-09-06, same day as Bakersfield/Fresno) · Springfield 109.5 °F (2021-06-27, heat dome) · Raymondville 107.4 °F (2026-07-22) · San Diego 102.5 °F (2020-09-06) · Warren 98.4 °F (2026-07-14) · Ann Arbor 96.4 °F (2026-07-01).
- **Note on D10 (decided in the UTCI chat):** the visualization uses 12 cities. Of the 7 added here, **Phoenix, San Diego and Ann Arbor are used; Warren, Delano, Raymondville and Springfield are pulled and checked but dropped at the visualization stage** (files kept, per D10).
- **Flags for later (nothing changed):**
  - **Warren 2013-09-10 = 104.7 °F** (baseline max), the same day as Detroit's flagged 104.8 °F. Neighbouring cities, so most likely the same gridMET feature; supports the Detroit outlier-audit item.
  - Springfield is not a copy of Eugene (mean ~0.4 °F cooler in 2016–2026) despite sharing edge cells.
- **SHA-256 of new raw files** (`data/raw/gridmet/climateengine/`):
  - annarbor 1991-2020 `561168597916315e44de093b528a00b64c64a47a7884f7db21dc4644d4657bb2` · 2016-2026 `9f60d57019555b8332bb294d7fc99390a2f0ca6d88334d356db3cccce4dbeecb`
  - delano 1991-2020 `15a2f3f66baaeac4294915e395a16557c281ccd96a2c3a74c39fff7cc9f248ed` · 2016-2026 `06495a883e5bea2b2a1a8d319347523c3c5ba3f2cd3ba1284eab1a52f917dc5f`
  - phoenix 1991-2020 `39af3dfac0a8617e56efa6fd611990d881215a2d0f0ef92f013f4e7aecc91f02` · 2016-2026 `6304dff1f202be86ac4aa68d21e33eec6e5fa09ddac58cca7eeac79d04ed244c`
  - raymondville 1991-2020 `7b64eaa9576ae6879864747c4309de0d763989d13329fb4528a20d03b1f0afc7` · 2016-2026 `09dbfc8be261e6393cf3fc2c27771a0430236e9ca8a9ea727db3f01943588dd9`
  - sandiego 1991-2020 `d0513df795492cab0f1c4553a43474961359077037d3d81c24e88ffa7552c80b` · 2016-2026 `144f68309dae3687401dc86aa7fc3645ff6074db04ec3e7f5210e3d5be6834d3`
  - springfield 1991-2020 `425d7e0c7a097ff848ac0ed5886147de8d4edcf72b2072ae17dcdcab05c42afa` · 2016-2026 `dff2f5f9751ab46291ca812692b1a5bc0cf0db787465dee3994b0982b1b3aec8`
  - warren 1991-2020 `aa1c3ca4fc675f17602371f31dbf824f6f9130853bd7f2e603bf24314a0a7ded` · 2016-2026 `3dd7225543d8c15ef26a252b9272b8f46970661db72c575d79e182487111351f`
- **Judgment calls:**
  - Original rows compared by file name (the output is sorted by file name, so new rows are interleaved). **Claude's choice, approved by Dish.**
  - Warren 2013-09-10 flagged, not acted on. **Claude's choice, approved by Dish.**

### Step 5 · gridMET · 2026-09-27 · Dish + Claude
- **What:** For each calendar date, built the 1991–2020 "normal" daily high and normal range (p10–p90) per city, then compared every day 2016-01-01 → 2026-09-24 with it. Wrote the **final gridMET actual-temperature files**, one per city, joining row for row with the UTCI finals. **11 cities** (D10 order, gridMET only): Los Angeles, Phoenix, San Diego, Detroit, Bakersfield, San Francisco, Fresno, Boston, Eugene, Brownsville, Ann Arbor. Fairbanks has no gridMET (source still open); Pittsburgh, Warren, Delano, Raymondville, Springfield not processed (D10; their files untouched).
- **Method (copied from UTCI Step 6):** pool = 1991-01-01 → 2020-12-31 highs within **±7 calendar days** of the date, wrapping around New Year; 365-day calendar with **Feb 29 counted as Feb 28** (pools 450, **458** for windows containing Feb 28). normal_f = mean; p10_f / p90_f = numpy default (linear) percentiles; anomaly_f = tmax_f − normal_f; **abnormally_high = 1 if tmax_f > p90_f (strict)**. Column named `abnormally_high` (not the handoff's `abnormally_hot`) to match UTCI. **Decided by Dish** (previous chat).
- **Input:** `data/raw/gridmet/climateengine/gridmet_tmax_<city>_{2016-2026,1991-2020}.csv` (22 files; not modified; SHA-256 re-checked against Step 4 final / 4b before running, and the script stops on any mismatch)
- **Script:** `scripts/gridmet/05_normals_final.py` (SHA-256 `dd4c6ead3baed51277b28bfafba576faf0c5a19b6cae8e342748498b444f2633`)
- **Output:** `data/processed/gridmet/final/temp_<city>_daily.csv` (columns: date, tmax_f, normal_f, p10_f, p90_f, anomaly_f, abnormally_high, n_baseline_values) · `temp_<city>_normals.csv` (365 rows: month_day, normal_f, p10_f, p90_f, n_baseline_values; for drawing the normal band) · `step05_summary.csv`
- **Rows:** in 3,920 study days + 10,958 baseline days per city → out **3,920 rows per city, 2016-01-01 → 2026-09-24, 0 blanks**; nothing removed or changed. Every pool is 450 or 458 (no gaps in the baseline).
- **Checks (read-only):**
  - Dates identical to `data/processed/utci/final/utci_<city>_daily.csv` in all 11 cities (row for row).
  - Share of baseline days above their own p90 = **9.50–9.95%** per city (≈ 10% expected; slightly lower because "above" is strict).
  - Every daily row's normal/p10/p90/pool matches the city's normals table (Feb 29 → Feb 28).
  - **Hand calculation, Phoenix 2023-07-15** (pool rebuilt from real dates Jul 8–22 of 1991–2020, independent of the script's day numbering): 450 values; normal 105.15 °F, p10 99.87, p90 110.50; that day 114.97 °F → anomaly +9.82, abnormally high. Matches the file exactly.
  - Feb 29 and New Year: 2016-02-29 uses the 458-value Feb 28 pool (same normal as 02-28); 2016-01-01 uses a 450-value pool spanning Dec 25 – Jan 8.
  - **Known heat days:** Eugene 2021-06-27 = 110.11 °F vs normal 77.59 (+32.51, p90 87.02) · Bakersfield 2022-09-06 = 113.85 vs 94.94 (+18.90) · Fresno 2022-09-06 = 113.44 vs 94.19 (+19.25). All abnormally high.
  - Existing outputs unchanged: SHA-256 of all 77 files in `data/raw/gridmet/`, `data/processed/gridmet/` (Steps 2–4) and `data/processed/utci/final/` identical before and after.
- **Results, 2016-01-01 → 2026-09-24 (share abnormally high / mean anomaly):** LA 14.6% / −0.21 °F · Phoenix 16.4% / +1.04 · San Diego 11.8% / −0.32 · Detroit 12.4% / +0.88 · Bakersfield 12.8% / +1.03 · SF 15.2% / −0.37 · Fresno 12.9% / +1.29 · Boston 14.4% / +1.15 · Eugene 14.4% / +0.98 · Brownsville 16.6% / +1.12 · Ann Arbor 12.7% / +1.03. Every city is above the ~10% baseline rate. **The three coastal California cities have a slightly negative mean anomaly yet more hot-tail days**: typical days slightly cooler than 1991–2020, extremes more frequent (unlike UTCI, where all means are positive).
- **Detroit 2013-09-10 (104.8 °F, flagged in Step 4 final):** kept in the baseline as decided by Dish. Effect measured, not applied: the Sep 10 pool's normal is 77.08 °F with it vs 77.02 without, p90 87.47 vs 87.37 (the day sits in the pools of Sep 3–17 only).
- **Judgment calls:**
  - `tmax_f` stored rounded to 2 decimals (raw has 4); anomaly and the > p90 test use unrounded values. Consequence: 37 days across the 11 cities show `tmax_f` = `p90_f` after rounding; 5 of them are flagged 1 because the unrounded high was just above p90. **Claude's choice, approved by Dish.**
  - Normals table labelled `month_day` (`MM-DD`), no `02-29` row (Feb 29 uses Feb 28). **Claude's choice, approved by Dish.**
  - Blank baseline days would be left out, no minimum pool size (none occur). **Claude's choice, approved by Dish.**
  - Summary adds `n_blank`, `hottest_day`, `hottest_tmax_f` beyond UTCI's columns. **Claude's choice, approved by Dish.**
  - Script overwrites files in `final/` if re-run (folder was new). **Claude's choice, approved by Dish.**
  - Monthly roll-up (handoff Procedure 2 step 6) not done in this step. **Decided by Dish.**
- **SHA-256 of the final files** (daily · normals):
  - losangeles `a3d05821a0f61e60177faa67823e5d83e2649cdc182e01caea97710d687ee435` · `54c7db36b00069d21faed4a2c40e70dfe51d1816f582e2c3140785d74189cd3e`
  - phoenix `29a715d208ecee730ce6ff836774be1c9949ebdd81f65e2179cfc2f4bf6590d0` · `f4a56a2085dcf4cea21400dbe64a3a3accac029cc1bb37c6c2230726066ff42a`
  - sandiego `6b4cdbd3b047853e9b64cfc89c25135c4d24cff90ab6847c1ff472137150fee0` · `44f0cf9b94b66f22c3cf689a2ac4805ef7332725070f607e1778d998b36585f7`
  - detroit `d80c11384f7b0f41703cacb5e0f9c9c696f74c385b9d73c27b40a3de893dcc3c` · `0ce0849054933045a00cf8749d96ca4a802c75d23966798aaaef99b002ac9643`
  - bakersfield `47dd6fd8b0f8382ef956005cc5822a80f002f5147997a4c42f7df04c15d91d25` · `d94b2e9484fefdc0aae030fb201d275e93c358b993ec1459a5f6aa5f24eb693e`
  - sanfrancisco `37fdd4c95c40adcdc9450a1c0c7db7d40d684c8a7b592d565620d29d1e881121` · `7dae18a3c512ce4321e79f495a1a1c899084cc7ffcce265bf8d95f1c166f08ac`
  - fresno `a7cca208fcd1ea8599b21b3023d8583e860f323202e310049b9aec6d144a716b` · `2ec4f334167cd7caca551fe2b6d3d86b52c3aecc6468b510e489be95582c6b98`
  - boston `4a78adbc0049eca4d5d998743429dc89aab0169976df894825b751d4a9844507` · `68d16f417bbe1bbdbe8053ba02742df46f936042888cd35eefe5dc728998b55b`
  - eugene `f0aa592dd9c2b886012f921b1053c8bb1c685e53812344ba7ad37e00bb44d02a` · `e3b3a852115d997b9598bf298c2cea804c4be0871bcc6a963c1557affbfa6f33`
  - brownsville `57989eb8c550bf8726f207c8860fd20db35234577df8059b17dd6531e4d41c04` · `9e108cba46cd061e71850a0ef7b5032a80909add6b990b2e452037e127c8fc0f`
  - annarbor `e9ea9a0f21c4c941309f455f9ccb147353038d8968a7d1f469884990ca96f9d3` · `6320c6295a0595f95f3961a7216f62f444b8e1359216364e2ea9753733038e00`
  - step05_summary.csv `2f4ec1931a927fccc9a61240881761113428150b6b6f743041a8bb4065946eb8`

### Decision D9 resolved · end date · 2026-09-27 · Dish (Claude's suggestion)
- **All datasets keep the D4 end date, 2026-09-24.** UTCI keeps its blank rows 2026-06-13 → 09-24, so every final file joins on date unchanged. Any direct felt-vs-actual comparison (UTCI Step 7, side-by-side panels) is limited to the common window, **2016-01-01 → 2026-06-12**; the viz marks UTCI as not yet available after that.
- **Why:** cutting everything at 06-12 would drop summer 2026, which gridMET and METAR cover (e.g. Ann Arbor's hottest study day 2026-07-01, Detroit's 2026-09-02). Optional later: top up UTCI from gridded ERA5-HEAT.
- **Claude's suggestion, approved by Dish.**

### Step 5b · gridMET monthly roll-up · 2026-09-27 · Dish + Claude
- **What:** Rolled the Step 5 daily files up to calendar months (handoff Procedure 2, step 6): average high, average normal, average anomaly, count of abnormally hot days, hottest day. 11 cities (D10, gridMET only).
- **Input:** `data/processed/gridmet/final/temp_<city>_daily.csv` (Step 5; not modified)
- **Script:** `scripts/gridmet/05b_monthly.py` (SHA-256 `ef534eb60fcf6398477854f55e5d73c4aab56e8c24c5cc1dee8d2d2390606f9b`)
- **Output:** `data/processed/gridmet/final/temp_<city>_monthly.csv` (columns: month, n_days, days_in_month, tmax_mean_f, normal_mean_f, anomaly_mean_f, n_abnormally_high, hottest_date, hottest_tmax_f, complete) · `step05b_summary.csv`
- **Rows:** 3,920 days → **129 months per city (2016-01 → 2026-09)**; 128 complete, **2026-09 partial (24 of 30 days, complete = 0)**. Nothing removed.
- **Checks (read-only):** month lengths add up to 3,920 days; abnormally hot days add up to the daily totals in every city; each city's hottest month-day equals its Step 5 hottest day; Feb 2016/2020/2024 have 29 days; 0 blanks. **Hand check Eugene 2021-06:** 30 days, mean high 81.72 °F vs normal 73.68 (+8.04), 14 abnormally hot days, hottest 2021-06-27 at 110.11 °F; matches the file. Existing outputs unchanged (SHA-256 of 100 files in `data/raw/gridmet/`, `data/processed/gridmet/` incl. Step 5 finals, `data/processed/utci/final/` identical before and after).
- **Results (month with most abnormally hot days):** **March 2026** in LA (20), Phoenix (25), San Diego (19), SF (19), Fresno (18); it is also the warmest-anomaly month in LA, Phoenix (+14.50 °F), San Diego, Bakersfield, SF and Fresno. Others: Detroit 2024-02 (12) · Bakersfield 2024-07 (17) · Boston 2022-08 (12) · Eugene 2021-06 (14, heat dome) · Brownsville 2023-09 (25) · Ann Arbor 2024-02 (15). **Flag:** the March 2026 values rise and fall smoothly across the month and appear in 6 cities at once (Phoenix 100–103 °F on Mar 18–21 vs normal ~76 °F), so it looks like a real event rather than a data error, but it has **not been checked against station records**.
- **Judgment calls:**
  - Monthly values computed from the Step 5 daily files as saved (2 decimals), not the raw 4-decimal values, so they trace exactly to the dailies (difference < 0.01 °F). **Claude's choice, approved by Dish.**
  - Partial Sep 2026 kept, with n_days / days_in_month / complete columns. **Claude's choice, approved by Dish.**
  - Extra columns normal_mean_f and completeness; no monthly p10/p90 (averaging percentiles isn't a percentile). **Claude's choice, approved by Dish.**
  - Ties: the first day is kept as the hottest; the same rule applies to the summary's "most" columns. **Claude's choice, approved by Dish.**
  - One file per city, matching the dailies. **Claude's choice, approved by Dish.**
- **SHA-256 of the monthly files:**
  - losangeles `f280dd5d6f0e9ca3fd3d897323ad377d2e1ae2c3a3fedb1eda18f24c877ca0a1`
  - phoenix `69cadff361c822c1b3b32d44f84e6353ed04baff467a07989f9632bccc7c5143`
  - sandiego `a5a378d6ae6ba79b83d6d7469d178c3ebe39bd884b93b04f6d3754141e66725d`
  - detroit `a970a4c5cc4c28f5f776bd248d89713d45a5810e7dc73d3aa95cbf548f374347`
  - bakersfield `2328c5856ede18f94cc3d2c8ae5a7f7160b5af7d805e80f06a4159cc5e2568c8`
  - sanfrancisco `71375b060b2b257969e449245aef69fc756b021b7c7280686a8ac2c99b6937e3`
  - fresno `29df3de4f0fe0bb2a9806c639aadd056b755474af05fbc81627ed7669707059c`
  - boston `28adef54ee40d13c36802118260992c7a06010c068465c3ec3396ac2ee433bcf`
  - eugene `260aeb74e132e0558d31e2d40e2f9b81813189fba9786d4aed77ec1e008d21ea`
  - brownsville `e2d3fe226754a64aea76e2d0f85908992b5cea4ea67bbce6e4c9dbcb21fc77f5`
  - annarbor `4843f9397a2be58e522e97dbc604d8469604b92401eb4a855f3682e04ebfeb6a`
  - step05b_summary.csv `cbfcc69d0129222dde6e7b59c95c4f6c5f8969030aa21a0d2e59499bd337f291`

### Decision D14 · felt minus actual (UTCI Step 7) · 2026-09-27 · Dish
- **UTCI Step 7 (felt minus actual, UTCI − gridMET high) is dropped as a pipeline step.** No gap file is produced.
- **Why:** the viz asks which signal prompts action (sensor, body, media), which is shown by the rows side by side, not by their difference. The two sources also differ in method (gridMET 4 km mean over city limits vs UTCI ~28 km reanalysis cells; SF's UTCI is 75% an ocean cell), so a gap would partly measure the method rather than the physics.
- **If needed later:** the gridMET and UTCI finals join on date row for row, so a gap for a single annotation can be computed in the viz code over the common window 2016-01-01 → 2026-06-12 (D9), and noted in the appendix.
- **Possible replacement (later, with the search data):** compare anomalies instead of raw values (abnormally hot by thermometer, abnormally high felt heat, both, or neither) against search spikes.
- **Changed by Dish** (handoff Procedure 3, step 7 had listed it).

---
**gridMET pipeline status (2026-09-27):** Steps 1–5b done. 16 continental cities pulled and checked (Steps 1–4); **final files for the 11 viz cities (D10)** in `data/processed/gridmet/final/`: `temp_<city>_daily.csv` (3,920 rows, 2016-01-01 → 2026-09-24, joins row for row with UTCI), `temp_<city>_normals.csv`, `temp_<city>_monthly.csv` (129 months, Sep 2026 partial), summaries. End date settled (D9 resolved: keep 2026-09-24; felt-vs-actual comparisons use 2016-01-01 → 2026-06-12). Open: Fairbanks (no gridMET in AK), N1 (boundary file vs OpenAQ).

**METAR pipeline status (2026-09-27, final):** **Closed (D8).** 17 cities, Steps 0–9b complete, ending 2026-09-24 (D4); final files frozen. Step 8b distances cover all 18 stations. Not done, by choice: in-city check for the new stations (D7), review of 7 low days, ASOS algorithm citation (appendix), Phoenix story decision; city-hall spot-check pending with Dish. New caveat: Ann Arbor outage from ~2026-06-17 (last valid day 2026-08-05).
