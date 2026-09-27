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

---
**METAR pipeline status (2026-09-27):** Steps 0–9b complete. Open items: (1) ~~airport distances (Step 8b)~~ done, city-hall coordinates pending Dish's spot-check; in-city-limits check pending shapefiles; (2) review of the Boston 2024-02-23 and Bakersfield 2020-12-17/18 low days; (3) ASOS internal visibility algorithm (M1).

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
