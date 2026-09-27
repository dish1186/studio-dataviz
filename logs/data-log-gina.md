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
- **Study period:** 2016-03-06 – 2026-09-25, daily (start = first OpenAQ data, Decision OA-D2; end matches Dish's Decision D1)
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

### Decision OA-D6 · OpenAQ · 2026-09-27 · Gina
- **What:** A rule for removing **low-cost** sensor-day readings that are glitches, applied in Step 5 before any average. Reference monitors are not subject to it. Values are checked after negatives are set to 0 (OA-D5). "Reference average" = the mean of the city's valid reference sensor-days that day; "other low-cost median" = the median of the city's other valid low-cost sensor-days that day.

  A low-cost sensor-day is **removed** if it is **> 100 µg/m³** and:

  | Available in the city that day | Removed if… |
  |---|---|
  | Reference data **and** ≥ 3 other low-cost sensors | > 5× the reference average **and** > 5× the other low-cost median |
  | Reference data, < 3 other low-cost sensors | > 5× the reference average |
  | No reference data, ≥ 3 other low-cost sensors | > 5× the other low-cost median |
  | Neither | > 1,000 µg/m³ |

  Also, **any low-cost sensor-day > 1,000 µg/m³ is removed**, whatever the comparison. Removed days stay in the Step 5 audit file with the value, what it was compared to, and which rule applied.
- **Why:**
  - 64 low-cost sensor-days exceed 500 µg/m³ and 35 exceed 1,000; the highest reference value in the study period is 542 (Eugene, 2020-09-12). On every low-cost day above 500, the city's reference average was 3–23.
  - Of 144 days caught by a reference-only version (> 100 and > 5× reference), 140 were also > 5× the median of ≥ 3 other low-cost sensors (median ratio 39×). On those days the other low-cost sensors' median (10.6) matched the reference average (10.8).
  - On 5,530 days with both types, the city's low-cost median and reference average differ by a median of −0.5 µg/m³ and are within ±5 on 84% of days, so the two networks can check each other.
  - Real events pass. Detroit 2026-07-16: low-cost 302–333, reference average ~294.
- **Options considered:**
  - (a) a fixed ceiling of 500 or 1,000. Gina was hesitant about 500 because reference values have exceeded it; 1,000 would keep 29 clearly false days between 500 and 1,000.
  - (b) reference comparison only.
  - (c) reference **and** peer comparison, with a 1,000 ceiling as a safety net.

  **Claude's recommendation (c), approved by Gina.**
- **Caveats for the appendix:**
  - Reference data comes through AirNow, which is preliminary; EPA's validated version is in AQS.
  - A removed low-cost reading may sometimes be real but hyper-local (a sensor next to a local source), not a malfunction. Either way it does not represent the city's air.
  - Expected effect: about 140 of ~302,000 valid low-cost sensor-days (0.05%); the exact count will be in Step 5.

### Decision OA-D5 · OpenAQ · 2026-09-27 · Gina
- **What:** **Negative daily PM2.5 values are set to 0 µg/m³** before any site or city average is calculated. The raw files and Step 4 CSVs keep the original values, and the Step 5 audit file will show both.
- **Why:** 26 sensor-days in the study period have a negative daily mean (24 Fairbanks, 2 San Francisco). Physically, concentration can't be below 0.
- **Options:** Claude suggested keeping them as measured (small negatives are a known instrument quirk in very clean air); the alternatives were set to 0 or drop. **Changed by Gina: set to 0.**
- **Documentation:** noted in `data/descriptions/data_descriptions.csv` on the daily `value` field, at Gina's request.

### Step 4 · OpenAQ · 2026-09-27 · Gina + Claude
- **What:** Downloaded OpenAQ's daily PM2.5 values for all 549 kept sensors (Step 3), 2016-03-06 to 2026-09-25, one calendar year per request. Flattened them into one CSV per city: one row per sensor per local day, with the day's mean, hourly min/median/max/sd, hours observed and flags. `valid_day` = 1 when at least 18 hours were observed. **No values changed, no days removed.**
- **Why:** The data for the site and city averages (Step 5).
- **Input:** `data/processed/openaq/step03_final/openaq_sensors_final.csv` (kept sensors); OpenAQ API v3 `/v3/sensors/{id}/days`. OpenAQ Docs: the daily value is "computed from the hourly average values from 01:00 to 0:00 in local time".
- **Script:** `scripts/openaq/04_download_daily.py`
- **Rows in → out:** 549 sensors → **549 downloaded, 0 failed**, 0 rate-limit errors. **466,458 sensor-days** in the study period (3,856 days), **387,836 valid** (≥ 18 h). 15 sensors have no valid day.

  | City | Days with ≥ 1 valid reference sensor | Low-cost valid days (first day) |
  |---|---|---|
  | Ann Arbor | 3,043 (78.9%) | 752 (2024-06-25) |
  | Bakersfield | 2,949 (76.5%) | 176 (2025-09-30) |
  | Boston | 2,656 (68.9%) | 922 (2023-07-18) |
  | Brownsville | **1,147 (29.7%)** | 12 (2026-09-12) |
  | Delano | 0 | 525 (2025-04-17) |
  | Detroit | 3,042 (78.9%) | 440 (2025-07-10) |
  | Eugene | 3,203 (83.1%) | 0 |
  | Fairbanks | 2,907 (75.4%) | 0 |
  | Fresno | 3,009 (78.0%) | 824 (2024-05-07) |
  | Los Angeles | 3,031 (78.6%) | 1,586 (2022-01-21) |
  | Phoenix | 3,070 (79.6%) | 911 (2024-02-17) |
  | San Diego | 2,428 (63.0%) | 859 (2024-04-26) |
  | San Francisco | 2,729 (70.8%) | 1,649 (2021-10-30) |
  | Springfield | 2,926 (75.9%) | 0 |
  | Warren | 0 | 924 (2023-12-21) |
- **Output:**
  - Raw: `data/raw/openaq/daily_json/sensor_<id>.json.gz` (549 files, 44 MB)
  - Flattened: `data/processed/openaq/step04_daily/openaq_pm25_<city>_daily_sensors.csv` (15 files, 95 MB; Los Angeles alone is 67 MB)
  - `step04_sensor_summary.csv`, `step04_failed.csv` (empty)
  - Descriptions: 9 rows added
- **Checks:**
  - Day alignment: each daily record runs from local midnight to the next local midnight (e.g. 2024-06-24T00:00−04:00 → 2024-06-25T00:00−04:00), so `date_local` is the correct local day.
  - `date_to` is inclusive, so year-boundary days came back twice; one copy is kept per sensor and date.
  - Days with 25 hours are daylight-saving fall-back days (e.g. Bakersfield 2016-11-06).
- **Findings for Step 5:**
  - **Implausible low-cost values.** 35 valid low-cost sensor-days exceed 1,000 µg/m³ and 64 exceed 500; no reference day exceeds 542. Ann Arbor low-cost sensor 13667130 read 3,870–5,330 µg/m³ daily from Nov to Dec 2025, clearly a malfunction. **Open item: an outlier rule for low-cost sensors.**
  - **Reference extremes match known events:** Eugene/Springfield in the Sept 2020 wildfires (up to 542); Phoenix on New Year's Day 2021 and 2025 (fireworks); Fairbanks in summer smoke (2022-06-28, 2024-06-30); Detroit and Ann Arbor on 2026-07-16/17 (7 Detroit monitors 224–327 on the same day). The Detroit event is not yet explained.
  - **Flags:** 10.6% of valid reference sensor-days and 0.1% of low-cost ones have `hasFlags = true`. Meaning not yet checked. **Open item.**
  - **Negative daily means:** 26 sensor-days (24 Fairbanks, 2 San Francisco). **Open item.**
  - **First valid reference day is 2016-03-12** in most cities (2016-03-15 Fairbanks, 2016-03-30 San Francisco), not 2016-03-06. OpenAQ's first days have fewer than 18 hours.
  - **Brownsville's reference coverage is low (29.7%)**, including the 2023–2024 gap found in Step 1.
- **Judgment calls:**
  - **One calendar year per request**, because OpenAQ warns long ranges can time out. **Claude's choice, approved by Gina.**
  - **Flattened CSVs in `processed`, not `raw`** (they are a transformation of the raw JSON). **Claude's choice, approved by Gina.**
  - **Raw JSON gzip-compressed** to keep the repo manageable (content unchanged). **Claude's choice, approved by Gina.**
  - **No filtering in this step;** invalid, negative and extreme values kept and flagged. **Claude's choice, approved by Gina.**
- **Change during the step:** After 32 sensors, the run was stopped and restarted with faster pacing: a 0.3 s pause plus a self-imposed budget of 55 requests/minute and 1,850/hour, under OpenAQ's free-tier limits of 60/minute and 2,000/hour. **Changed by Gina** (chose this from Claude's two options). The run resumed without re-downloading the 32. The Mac was kept awake with `caffeinate` for the run, at Gina's request. Total run time about 35 minutes after the restart.

### Decision OA-D4 · OpenAQ · 2026-09-27 · Gina
- **What:** A fallback sensor must be **closer to its own city's limits than to any other study city's limits**; otherwise no city uses it. Step 3 was rerun with this rule; its outputs were overwritten and the Step 3 entry below is updated.
- **Why:** Step 3's traceability columns showed that 4 of Warren's fallback sensors were much closer to Detroit's limits than to Warren's. **Oak Park** (reference): 2.0 km from Detroit vs 8.1 km from Warren. **HFH CURES 6, 17, 18** (low-cost): 0.2–1.3 km vs 7.4–9.4 km. They measure air at Detroit's edge, not Warren's. (Measured from city hall, Oak Park is closer to Warren, 14.1 km vs 18.7 km, because Detroit's city hall is far south; the rule uses city limits.)
- **Options:** (a) keep the Step 2 rule, "nearest city that needs it"; (b) the stricter rule. **Changed by Gina: chose (b)**, as recommended by Claude.
- **These 4 sensors don't go to Detroit either.** Detroit has its own sensors of both types, and fallbacks are only for cities with none of that type. They're recorded as "fallback closer to another study city". **Claude's explanation, confirmed by Gina's question in chat; not separately approved.**
- **Effect:** Warren: reference 1 → **0** sites; low-cost 7 → **4** sites (Madison Heights, S Campbell Rd & E 3rd St, Royal Oak, Dodge Park & Utica). Ann Arbor unchanged (Ypsilanti has no other study city within 10 km). Totals: 560 → **556 sensors, 496 → 492 sites** (549 at 489 after the Step 3 correction). **Cities with no reference average: Warren, Delano, Raymondville.**

### Step 3 · OpenAQ · 2026-09-27 · Gina + Claude
- **What:** Made the final list of sensors per city and grouped them into sites. Kept sensors inside city limits, plus fallback sensors within the 10 km cap, US only (Decision OA-D3). Sensors of the same type in the same city within 50 m of each other were grouped into one site (chained). Added traceability columns: other study cities within 10 km of each sensor, and the cities whose Step 1 search circle it fell in. **No measurements downloaded.**
- **Why:** Decision OA-D3, and Gina's requirement that it be traceable which sensors go into which calculation, and why.
- **Input:** `data/processed/openaq/step02_assignment/openaq_sensors_assigned.csv` and `city_boundaries.geojson`; `data/processed/openaq/step01_inventory/openaq_sensors_inventory.csv`; country codes from the raw `data/raw/openaq/json/locations_*.json`
- **Script:** `scripts/openaq/03_final_sensors_and_sites.py` (local files only; no API calls)
- **Rows in → out (final, third run):** 948 sensors → **549 kept at 489 sites**. 399 not kept, each with a reason:
  - 358 outside every study city and not needed as fallback
  - 23 with no data in the study period
  - 7 in city limits but with no dates in OpenAQ (see Correction)
  - 7 fallback beyond the 10 km cap
  - 4 fallback closer to another study city (OA-D4)

  Earlier runs: 560 sensors at 496 sites (first), 556 at 492 (after OA-D4).

  | City | Reference sites (sensors) | Low-cost sites (sensors) |
  |---|---|---|
  | Ann Arbor | 1 (1), fallback: Ypsilanti | 14 (16) |
  | Bakersfield | 3 (5) | 2 (2) |
  | Boston | 5 (5) | 10 (11) |
  | Brownsville | 2 (2) | 10 (10) |
  | Delano | 0 | 12 (13) |
  | Detroit | 8 (8) | 33 (34) |
  | Eugene | 3 (4) | 0 |
  | Fairbanks | 2 (2) | 0 |
  | Fresno | 3 (3) | 4 (5) |
  | Los Angeles | 8 (8) | 242 (273) |
  | Phoenix | 7 (7) | 21 (25) |
  | Raymondville | 0 | 0 |
  | San Diego | 9 (12) | 22 (22) |
  | San Francisco | 1 (1) | 61 (72) |
  | Springfield | 2 (4) | 0 |
  | Warren | 0 (Oak Park dropped, OA-D4) | 4 (4), all fallback |
- **Output:** `data/processed/openaq/step03_final/`
  - `openaq_sensors_final.csv`: all 948 sensors, with kept, reason, site_id, us_basis, other_study_cities_nearby, step01_within_25km_of
  - `openaq_sites.csv`: 496 sites, with member sensors, location and spread
  - `city_site_counts.csv`
- **Problem during the step, fixed before this entry:** The first run applied "US only" using OpenAQ's `country` field. That field is wrong near borders: Brownsville's 2 AirNow monitors and 1 Clarity sensor (inside Brownsville city limits) are tagged **MX**, and HFH CURES 24 (inside Detroit) is tagged **CA**. Brownsville lost both reference monitors. Claude changed the rule and reran:
  - Sensors inside a study city's Census boundary count as US.
  - Only fallback sensors are checked against OpenAQ's country (all 9 are "US", and their coordinates confirm it).

  Column `us_basis` records which test each sensor passed. The first run's outputs were overwritten.
- **Correction (found while preparing Step 4):** 7 kept sensors had no first/last measurement date in OpenAQ, so no data in the study period: 5 low-cost in Los Angeles, 1 low-cost in Bakersfield, and the San Diego reference unit "EBAM 0" (sensor 3565930). Step 2's rule, "only sensors with data in the study period count" (Step 2 judgment calls), was applied to fallback candidates but not to sensors inside city limits. Step 3 now drops them with the reason "in city limits, but no data in study period" and was rerun. **Changes:** Bakersfield low-cost sites 3 → 2; Los Angeles low-cost 243 → 242; San Diego reference 10 → 9. The table above is updated. A Claude slip in Step 2, no data affected.
- **Judgment calls:**
  - **Site = same type, same city, within 50 m, chained.** Co-located reference sensors are 0–16 m apart; the nearest distinct stations are ~150 m or more apart. **Claude's choice, approved by Gina.**
  - **Site IDs made by the script:** "S" + the lowest OpenAQ location ID in the site. **Claude's choice, approved by Gina.**
  - **A station that moved more than 50 m counts as two sites**, e.g. San Ysidro (San Diego), 184 m apart, never reporting on the same day. City averages aren't affected, because only sites with data that day are used. **Claude's choice, approved by Gina.**
  - **US test:** in-city sensors count as US by the Census boundary; fallback sensors use OpenAQ's country. **Claude's fix, approved by Gina** after this check:
    - **Brownsville C80:** TCEQ (Texas environmental agency) lists it at 344 Porter Drive, Brownsville (https://www.tceq.texas.gov/cgi-bin/compliance/monops/site_info.pl?cams=80, accessed 2026-09-27). The Census Geocoder places that address in Texas, Cameron County, Brownsville city, 562 m from OpenAQ's coordinates. OpenAQ's position is 326 m inside the city limit.
    - **Brownsville East 6th:** TCEQ lists it at 85 East 6th Street, Brownsville. Census: Texas, Cameron County, Brownsville city, 301 m from OpenAQ's coordinates. OpenAQ's position is 847 m inside the limit, and OpenAQ gives its locality as "CAMERON".
    - The geocoder interpolates positions along address ranges, so gaps of a few hundred metres are expected.
    - The low-cost sensors (Clarity Brownsville Sensor #6, HFH CURES 24 in Detroit) have no agency address. They are 726 m and 608 m inside their city limits, well beyond the boundary file's simplification error.
- **Finding (resolved by Decision OA-D4):** Some of Warren's fallback sensors are much closer to Detroit than to Warren. The "nearest city that needs it" rule (Step 2) gives them to Warren because Detroit doesn't use fallbacks.
  - HFH CURES 6, 17 and 18: 0.2–1.3 km from Detroit's limits, 7.4–9.4 km from Warren's.
  - **Oak Park**, Warren's only reference monitor: 2.0 km from Detroit, 8.1 km from Warren.

  Gina chose to exclude them (OA-D4).

### Decision OA-D3 · OpenAQ · 2026-09-27 · Gina
- **What:**
  1. **Fallback cap: 10 km beyond city limits.** Ann Arbor gets the Ypsilanti reference monitor (6.9 km). Warren gets Oak Park (reference, 8.1 km, from Dec 2024) and 7 low-cost sensors. **Claude's recommendation, approved by Gina** after seeing the Step 2 cap options.
  2. **US monitors only.** Canadian (Windsor) monitors are excluded. **Claude's recommendation, approved by Gina.**
  3. **Average by site, not by sensor.** Each day, the sensors at a site are averaged first, then the sites are averaged into the city value, so a site with several sensors counts once. **Claude's recommendation, approved by Gina.**
  4. **A sensor-day is valid with at least 18 of 24 hours** (EPA's usual completeness rule for a daily average). **Claude's recommendation, approved by Gina.**
  5. **Three city averages** (reference, low-cost, overall), each with the mean, min and max across sites, the number of sites and the site IDs used. **Specified by Gina.** "Overall" = the mean of the reference average and the low-cost average (each type weighted 50%); on days with only one type, overall = that type. **Changed by Gina** (chose option b from Claude's two options).
- **Still open:** min/max are the lowest and highest site value of the day (spread across the city). OpenAQ's within-day hourly min/max will also be kept in the raw daily files. **Claude's choice, not yet approved.**

### Step 2 · OpenAQ · 2026-09-27 · Gina + Claude
- **What:** Checked which city's limits each PM2.5 sensor is inside, and each sensor's distance to the limits of nearby cities. Sensors inside limits were assigned to that city. For each city and sensor type with no sensor inside its limits, listed the fallback options at caps of 5, 10, 15 and 20 km beyond the limits. **No measurements downloaded; no sensors dropped; the cap isn't chosen yet.**
- **Why:** Decision OA-D1 (city limits first, nearest-city fallback). Gina chose to decide the cap after seeing these counts (OA-D2).
- **Input:**
  - `data/raw/census/cb_2024_us_place_500k.zip`: Census 2024 cartographic boundary file for places, 22,957,701 bytes. Downloaded 2026-09-27 with Gina's approval; not modified. SHA-256 `2be68094…6944b3` (full hash in the data descriptions).
  - `data/processed/openaq/step01_inventory/` (Step 1)
  - OpenAQ API v3 `/v3/locations?bbox=…` and `/v3/locations/{id}/sensors`, for the extra searches
- **Script:** `scripts/openaq/02_assign_sensors.py`. Uses the `pyshp` library (installed with Gina's approval) to read the shapefile.
- **Rows in → out:** 821 Step 1 sensors + **127 found by the extra searches** = **948 distinct sensors**. **551 inside the limits** of a study city, **16 fallback candidates**, **381 unassigned** (outside every city and not a candidate).
  - **Extra searches:** 5 cities reach past the 25 km net. Farthest limit from city hall: Phoenix 53.6 km, San Francisco 53.0 km (the Farallon Islands), San Diego 48.1 km, Los Angeles 43.2 km, Brownsville 35.0 km. New sensors found: Los Angeles +114, San Diego +12, Phoenix +1, San Francisco 0, Brownsville 0.
  - **Sensors inside limits with data in the study period (reference / low-cost):** Ann Arbor 0 / 16 · Bakersfield 5 / 2 · Boston 5 / 11 · Brownsville 2 / 10 · Delano 0 / 13 · Detroit 8 / 34 · Eugene 4 / 0 · Fairbanks 2 / 0 · Fresno 3 / 5 · Los Angeles 8 / 273 · Phoenix 7 / 25 · Raymondville 0 / 0 · San Diego 12 / 22 · San Francisco 1 / 72 · Springfield 4 / 0 · Warren 0 / 0.
  - **Fallback candidates** (km beyond the limits):
    - Ann Arbor reference: Ypsilanti 6.9.
    - Warren reference: Oak Park 8.1, Windsor Downtown 14.7 and 14.8, Dearborn 16.5, Windsor West 17.2 and 17.3.
    - Warren low-cost: 9 sensors, 1.0–15.7 km, all from Dec 2023 or later.
    - None within 20 km for Delano reference, Raymondville (either type), or Eugene / Springfield / Fairbanks low-cost.
- **Output:** `data/processed/openaq/step02_assignment/`
  - `openaq_sensors_assigned.csv`: one row per distinct sensor, with inside_city, nearest_city, assigned_city, assignment_rule and distances
  - `fallback_cap_options.csv`
  - `city_boundary_summary.csv`
  - `city_boundaries.geojson`: the 16 boundaries, copied from the Census file, for maps
  - Raw: `data/raw/openaq/json/locations_bbox_<city>.json` and `location_sensors_bbox_<city>.jsonl` (5 cities each)
  - Descriptions: 16 rows added to `data/descriptions/data_descriptions.csv`
- **Checks:** Every city matched exactly one Census "city" (LSAD 25) boundary. No sensor fell inside two cities. The extra searches returned nothing outside their box. Spot checks: the Springfield City Hall monitor is inside Springfield; Ypsilanti is outside Ann Arbor (6.9 km); Detroit-E7 Mile is inside Detroit and so is not available to Warren.
- **Findings for the next decisions:**
  - **Warren's reference fallback includes Windsor, Ontario (Canada)** monitors, across the Detroit River. AirNow reports some Canadian stations. **Open item: keep or exclude non-US monitors.**
  - **Several sensors can share one site.** Springfield City Hall has 3 reference sensors with overlapping dates; Bakersfield's 5 reference sensors are at 2 named sites; San Diego's 12 are at 8. Averaging by sensor would count those sites more than once. **Open item for the averaging step: average by site (location) or by sensor.**
  - **Short-lived or temporary reference monitors** are included, e.g. San Diego's "EBAM" and "MMCA…" units (2020–2024) and a San Ysidro unit reporting for 8 days in 2016.
  - San Francisco has only **1** reference monitor inside its limits (the Step 1 count of 7 included Oakland and other nearby cities).
  - Detroit and Warren: the 52 sensors their 25 km circles shared (Step 1) are now separated. Warren has no sensor of either type inside its own limits.
- **Judgment calls:**
  - **Fallback decided per sensor type** (reference / low-cost). **Claude's choice, approved by Gina.**
  - **Fallback sensors go to the nearest city that needs them.** Sensors inside another listed city's limits are never used as fallback. **Claude's choice, approved by Gina.**
  - **Only sensors with data between 2016-03-06 and 2026-09-25 count** as "inside" or as candidates. **Claude's choice, approved by Gina.**
  - **Extra search only for cities whose limits reach past 25 km**, using the boundary's bounding box. **Claude's choice, approved by Gina.**
  - **NAD83 (Census) vs WGS84 (OpenAQ) difference ignored** (< 2 m). **Claude's choice, approved by Gina.**
- **Known limitation:** The Step 1 net reaches at least 16 km beyond the limits of the small cities (Warren 16.4, Delano 16.5, Ann Arbor 17.7), so the 20 km cap counts may miss sensors 16–20 km out. The 5, 10 and 15 km counts are complete.

### Step 12 · descriptions · 2026-09-27 · Gina + Claude
- **What:** Added OpenAQ's own definitions of reference-grade monitors and low-cost sensors to the `isMonitor` row of `data/descriptions/data_descriptions.csv`, and examples of each type to the `instruments[].name` row. **Documentation only: no data changed.**
- **Why:** Gina asked for the difference between the two sensor types, from the API/OpenAQ documentation, to be in the definitions document.
- **Input:**
  - OpenAQ Docs, Instruments (https://docs.openaq.org/resources/instruments): the field shows whether the device is used for official monitoring.
  - OpenAQ Explorer, Getting started (https://explore.openaq.org/getting-started): reference-grade monitors are the "gold standard", typically run by government agencies for regulatory purposes; air sensors are less sophisticated but small, portable and affordable, used to fill gaps. Both accessed 2026-09-27.
- **Script:** none (documentation, edited by Claude)
- **Rows in → out:** 2 of 67 description rows changed.
- **Output:** `data/descriptions/data_descriptions.csv`
- **Judgment calls:** OpenAQ's wording paraphrased, with the source pages cited. **Claude's choice, approved by Gina.**

### Decision OA-D2 · OpenAQ · 2026-09-27 · Gina
- **What:**
  1. **The PM2.5 series starts on 2016-03-06**, the first date with OpenAQ data at any sensor (Step 1), instead of 2016-01-01. **Changed by Gina** (chose this from Claude's three options; the others were filling Jan–Feb 2016 from EPA's archive, or asking Dish to move her start date).
  2. **Three city averages planned:** reference sensors only, low-cost sensors only, and all sensors. **Specified by Gina.** How the "all sensors" average is weighted is still open (see the Step 1 counts: e.g. Los Angeles has 13 reference vs 269 low-cost sensors).
  3. **The fallback distance cap will be chosen after Step 2**, once its output shows what each cap would keep. **Specified by Gina.**
- **Consequence:** the OpenAQ PM2.5 series is 2 months shorter than Dish's METAR visibility series (2016-01-01 – 2026-09-25). Comparisons between the two should use the shared period.

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
