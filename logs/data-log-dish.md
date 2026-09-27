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

---
**METAR pipeline status (2026-09-27, updated):** 17 cities, Steps 0–9b complete, ending 2026-09-24 (D4). Open items: (1) Step 8b distances for the 6 new stations (ARB, DLO, SAN, VLL, PHX, HRL) and the city-hall spot-check; (2) review of unexplained low days: Boston 2024-02-23, Bakersfield 2020-12-17/18, Ann Arbor 2016-07-25, Warren 2026-07-16/17, Delano 2024-11-11; (3) ASOS internal visibility algorithm (M1); (4) Phoenix visibility row is nearly flat (99.3% of hours at the 10-mi cap); decide how to use it in the story.
