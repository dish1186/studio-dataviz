# Data log — Gina

Project 2, MDE Studio ("AI-Augmented Storytelling with Data" · Natural + Artificial).
Running plain-language log of every data step Gina runs with Claude. This log feeds the Algorithmic Forensics Appendix.
Dish keeps her own log (`data-log-dish.md`); the two may be combined later.
**Newest entries are at the top** (Dish's log runs oldest-first).

**Datasets in this log:** Media Cloud news coverage (online news) · American Lung Association *State of the Air 2026* PM2.5 rankings · OpenAQ PM2.5 · Google Trends (heat-related and air-quality searches) · Media Cloud attention over time (air quality, heat)

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
Step · dataset · date and time · who ran it | What (plain language) | Why | Input file(s) | Script | Rows/values in → out (and what was removed or changed) | Output file | Judgment calls

**Timestamps:** Eastern time (EDT, the Mac's time zone). The time in each heading is when the entry was first committed to the repo, taken from the git history, which is normally within minutes of the step finishing. The retroactive city-selection entries (Steps 1–8) keep their run date in the heading and have a **Time** line with when they ran (from file times, where known) and when they were logged. Timestamps added 2026-09-27 at Gina's request; new entries get them as they are written.

**Note on Steps 1–8:** these were run on 2026-09-26/27 before this log existed, and logged retroactively in Step 9. They did not follow Rule 1 (no step-by-step approval before running), and Rule 2/3 files were assembled afterwards. Judgment calls in them are marked **Claude's choice, flagged to Gina in chat; not yet approved**, unless Gina specified or changed them. Gina to review.

---

### Visualization V2 · version 2: San Francisco threads with 2020 and 2024 · 2026-09-28 12:13 EDT · Gina + Claude
- **What:** Rebuilt the threads page from the re-stitched weekly searches, which now run 2019-12-29 to 2026-09-27 (353 weeks, no 2024 gap). Also:
  - Added a "Sept 2020 wildfire smoke" marker at the week of 2020-09-06, the highest week in the 2020 file.
  - Updated the notes text (seven yearly downloads).
  - Same method as v1. The page is the same link, updated in place.
- **Why:** Gina: "here's the 2024 data, if you can add that to san fran, as well as 2020. please add to the visual".
- **Effect:**
  - ρ now reaches **0.90**: news vs searches in autumn 2020. The fitted scale now runs −0.75 to +1.0.
  - **2020:** news ρ 0.70 (late June), 0.88 (late Sept) and 0.55 (late Dec); haze 0.55 (late June) and 0.64 (late Sept).
  - **2024:** news 0.62 in spring; PM2.5 about 0.3 through the second half.
- **Data note:** San Francisco PM2.5 has no values in the page for mid-2020 to 2021. There are only 222 reference days in 2020 and 190 in 2021, with low-cost from 2021-10, so the PM2.5 thread is broken there. **Not investigated.**

---

### Google Trends · Step 9: 2020 and 2024 weekly San Francisco files; re-stitch · 2026-09-28 12:13 EDT · Gina + Claude
- **What:** Added two more of Gina's downloads to `data/raw/google-trends/air-search-weekly/san-francisco/`, **copied unchanged** (`cmp` identical):
  - `time_series_807_20200101-0000_20260928-1211.csv`: 2019-12-29 to 2020-12-27, 53 weeks, SHA-256 d3547ac1…5ae2
  - `time_series_807_20240101-0000_20260928-1210.csv`: 2023-12-31 to 2024-12-29, 53 weeks, d8bfecd2…1c79
- Reran `scripts/google-trends/05_sf_weekly_stitch.py` (unchanged): 353 weeks.
- Rewrote `trends_sources.csv` (7 rows) and updated 2 rows in `data_descriptions.csv`.
- **Why:** Gina supplied the missing 2024 file and 2020.
- **Result:**
  - New factors: 2020 **1.1614** (fit r 0.999); 2024 **0.1069** (fit r 0.792).
  - 2024's lower fit is because its monthly values are nearly flat (7–9), leaving little to fit; the max residual is 0.83.
  - All six year-boundary overlap weeks agree after scaling (gaps 0.61, 0.10, 0.36, 0.23, 0.48, 0.02 index points).
  - The earlier factors are unchanged.
- **Note:** the 2020 file's values are mostly small integers (4–9) outside the Aug–Sept smoke spike (100 = week of 2020-09-06), so ordinary 2020 weeks carry more rounding error.

---

### Visualization V2 · version 1: San Francisco weekly threads · 2026-09-28 12:07 EDT · Gina + Claude
- **What:** A new, separate page, **"Air-quality threads"**: https://claude.ai/artifact/7UB1ipuuUtX2KEcvCUvxWL
  - San Francisco only; weekly, from 2020-12-27 to 2026-09-27; time runs down the page.
  - Green "air purifier" search thread in the centre (anchor layout). News on the left, haze and PM2.5 on the right.
  - **Distance from the centre = rolling Spearman ρ with searches**, on a **linear ρ scale fitted to this city's range**. ρ runs from −0.63 to 0.74, so guides are at −0.75 … +0.75 in steps of 0.25, and ρ = 0 is dashed. This is Gina's "#1: fit the scale to the range". It replaces the mockup's √(2(1−r)) distance, since a labelled linear ρ axis is easier to read in the anchor layout.
  - A **thickness / colour toggle** shows how unusual each week is.
  - A city dropdown: the other 4 featured cities are listed but disabled until their weekly data exists.
  - Checkboxes for haze, news and PM2.5. Hover shows each value, its percentile, ρ and the number of weeks.
  - A shaded 2024 gap, and a spring 2026 marker.
- **Why:** Gina: "lets start with san francisco. do #1 at the moment to just fit the scale to the range … just to see how this looks".
- **Method:**
  - **Searches:** Step 8 stitched weekly file.
  - **Haze:** SFO weekly mean extinction ÷ 0.24308, weeks with ≥ 3 valid days.
  - **News:** weekly sum ÷ sum, weeks with ≥ 20 city stories.
  - **PM2.5:** reference daily mean, low-cost where none; weeks with ≥ 4 days.
  - **Correlation:** ρ over weeks i−13 … i+12, needing ≥ 18 weeks with both values. Raw weekly values, no seasonal adjustment.
  - **Unusualness:** percentile of the week among all weeks (whole record) whose week_start is in the same calendar month. Thickness = 1.6 + 9 × max(0, (p − 0.5)/0.5) px; colour opacity = 0.14 + 0.86 × the same.
  - Weekly data was computed in a scratch script from the explorer bundle (built from the repo's processed files); not saved in the repo.
- **What it shows (first look):**
  - News is the thread closest to searches in mid-2021 (ρ up to about 0.7) and again in spring 2026 (about 0.7). Haze reaches about 0.5 in mid-2021.
  - In 2022–2023 all threads hover around 0, ranging from −0.3 to +0.35.
  - In spring 2026 haze swings to −0.54, while searches spiked nationwide.
- **Judgment calls (Claude's choices, flagged; not yet approved):**
  - The 26-week window and the 18-week minimum.
  - No seasonal adjustment.
  - Linear ρ scale.
  - Fixed sides.
  - The weekly minimums.
  - The percentile pool (whole record, by calendar month; for searches only the 5 downloaded years).
  - Thickness range.
- **Known issues for v2:**
  - Threads jump when a spike week enters or leaves the 26-week window; a tapered (weighted) window would smooth this.
  - 26 weeks gives ρ an uncertainty of about ±0.35.
  - SFO summer fog leaves some haze weeks blank.
  - Best-fit (all-pairs) layout not built yet.
  - Lead/lag arrows are for later.

---

### Google Trends · Step 8: stitch the weekly San Francisco files · 2026-09-28 12:07 EDT · Gina + Claude
- **What:** New script `scripts/google-trends/05_sf_weekly_stitch.py`, which writes:
  - `data/processed/google-trends/air-search-weekly/sf_air_purifier_weekly.csv` (250 weeks)
  - `sf_air_purifier_weekly_factors.csv`
  - Raw files are unchanged.
- **Why:** each weekly file is scaled 0–100 within its own year, so the files can't be joined as-is. Needed for the threads page.
- **Method:**
  - Each week's value is spread over its 7 days and averaged by calendar month (months with ≥ 20 days).
  - Each file gets one factor: the least-squares scale (through 0) onto the monthly San Francisco-Oakland-San Jose "air purifier" values for the same year.
  - calibrated_index = raw × factor, in the monthly file's units. Weeks in two files are averaged.
- **Result:**
  - Factors: 2021 0.2535 · 2022 0.1446 · 2023 0.1816 · 2025 0.1557 · 2026 0.6391.
  - Fit of weekly-to-monthly averages: r = 0.994 · 0.967 · 0.914 · 0.979 · 0.999; max residual ≤ 1.3 index points.
  - **Independent check:** the three New Year weeks that appear in two files agree after scaling (gaps 0.10, 0.36, 0.02 index points), although the files were scaled separately.
- **Limitation:** the monthly file's values are small integers (about 7–10 most months), so the factors carry some rounding error. 2024 is missing.
- **Judgment call:** calibrating to the monthly file, rather than chaining the one-week overlaps. **Claude's choice, flagged; not yet approved.**

---

### Google Trends · Step 7: weekly San Francisco "air purifier" raw files · 2026-09-28 12:07 EDT · Gina + Claude
- **What:** Added Gina's 5 downloads to `data/raw/google-trends/air-search-weekly/san-francisco/`, **copied unchanged** under their export names. `cmp` identical to ~/Downloads.
  - `time_series_807_20210101-0000_20260928-1200.csv`: 2020-12-27 to 2021-12-26, 53 weeks, SHA-256 1a340e2d…1c05
  - `time_series_807_20220101-0000_20260928-1158.csv`: 2021-12-26 to 2023-01-01, 54 weeks, 7a5b6928…6eef
  - `time_series_807_20230101-0000_20260928-1157.csv`: 2023-01-01 to 2023-12-31, 53 weeks, d8ed0c3f…81e9
  - `time_series_807_20250101-0000_20260928-1156.csv`: 2024-12-29 to 2025-12-28, 53 weeks, 9dd5b455…344
  - `time_series_807_20260101-0000_20260928-1155.csv`: 2025-12-28 to 2026-09-27, 40 weeks, 5caa294a…83fb
- Also wrote `trends_sources.csv` in that folder (5 rows, same columns as the air-search table) and added 10 rows to `data/descriptions/data_descriptions.csv` (4 raw, 6 processed).
- **Why:** Gina: "here's some weekly trends data for san francisco which should span 2021-2026 … make sure to log and put in raw data for air search trends".
- **Findings:**
  - **2024 is missing**: there is no file covering 2024-01 to 2024-12.
  - 807 is the metro code for San Francisco-Oakland-San Jose (the same area as the monthly file), inferred from the file name. **Gina to confirm.**
  - Category and search type were not recorded (marked "assumed" in the sources table).

---

### Visualization V2 · mockups: correlation threads (Eugene) · 2026-09-28 11:47 EDT · Gina + Claude
- **What:** Two inline chat mockups (not saved as repo files or published) for a planned vertical "threads" visual.
  1. **Spearman ρ vs Pearson r**, side by side.
  2. **Thickness vs colour intensity** to show how unusual each variable is.
- **Why:** Gina asked to see how ρ and r look different, and to compare thickness with colour intensity, before writing the spec prompt.
- **Gina's decisions so far:**
  - Both layouts (anchor and best-fit).
  - Default anchor = searches.
  - She will download weekly Trends for the featured cities.
  - Unusualness = colour intensity (comparing with thickness first).
  - Lead/lag arrows: later (**noted for V2 v2**).
  - A city dropdown is required.
- **Mockup method (Eugene; monthly):**
  - **Series:** "air purifier" searches; haze (≥ 15 valid days per month); news share (sum ÷ sum); PM2.5 (reference; ≥ 15 days).
  - **Correlation:** each series has its calendar-month mean removed. Rolling **24-month** window of months m−12 … m+11, needing ≥ 18 months.
  - **Layout:** Spearman ρ and Pearson r of searches vs each variable. Position = correlation distance **d = √(2(1 − r))** from the central search thread, at 62 px per unit. Fixed sides: haze right, news left, PM2.5 right with a 3 px offset.
  - **Unusualness:** (value − that calendar month's median) ÷ (1.4826 × MAD), clipped to 0–4.
- **What it showed:**
  - Pearson r jumps to about 0.98 for every thread in any window containing Sept 2020, so all threads collapse onto searches for 2 years.
  - Spearman stays moderate (haze 0.1–0.3 around 2020; news about 0.5), and rises in 2021–2026 (0.4–0.57).
  - Pearson reflects one event; Spearman reflects ordinary months.
- **Issue found:** haze unusualness saturates (many months at 4+), because most haze months are exactly 1×, so the MAD is tiny. The final version needs a different scale for haze, e.g. a percentile rank within the calendar month. **Not yet decided.**
- **Judgment calls (Claude's choices, flagged; not yet approved):**
  - The 24-month window.
  - Season removal by calendar-month mean.
  - The MAD-based unusualness score.
  - Fixed sides for the threads.
- **No data changed.**

---

### Analysis A8 · Fairbanks annual and seasonal PM2.5 · 2026-09-28 11:25 EDT · Gina + Claude
- **What:** Computed Fairbanks' reference PM2.5 averages by year and season, and clarified the day counts in A7. **No files written**; this was a one-off script in chat, reading the explorer bundle (from `data/processed/openaq/step05_averages/pm25_fairbanks_daily.csv`).
- **Why:** Gina asked for Fairbanks' annual and seasonal average PM2.5, what period the "days above 35" covered, and what drives the winter pollution.
- **Data basis:**
  - 2,907 of 3,921 days have reference data (2016-03-15 to 2026-09).
  - Two in-city sites: S1880 **NCore** (from 2016) and S7089 **A Street** (from 2019-06).
  - The borough's **Hurst Road (North Pole)** monitor is outside the city and not used (Step 3).
- **Results:**
  - **Overall:** mean of all days **9.1 µg/m³**; mean of the 12 calendar-month means 9.0.
  - **Seasonal means:**
    - Winter Dec–Feb **15.5** (median 13.7)
    - Spring Mar–May **5.0**
    - Summer Jun–Aug **9.2** (median 3.5: a few extreme smoke days)
    - Fall Sep–Nov **6.8**
    - Heating season Nov–Feb **14.3**
  - **By year** (mean of days with data; days with data): 2016 8.2 (233) · 2017 9.8 (198) · 2018 6.8 (172) · 2019 11.0 (256) · 2020 8.6 (254) · 2021 11.4 (189) · 2022 11.7 (328) · 2023 8.3 (297) · 2024 9.3 (356) · 2025 8.4 (356) · 2026 through Sept 6.0 (268).
  - **Days > 35:** the A7 counts (36 winter, 47 summer) are **totals over the whole record** (about 10.5 years), counting only days with data.
    - By year: 2016 4 · 2017 11 · 2018 0 · 2019 8 · 2020 3 · 2021 4 · 2022 27 · 2023 6 · 2024 9 · 2025 10 · 2026 1.
    - Winter-season means ranged from 11.9 to 19.9. Winter 2017–18 has only 3 days of data.
- **Caveats:**
  - Missing days are not random: the 2017, 2018 and 2021 gaps cover whole months.
  - These are **not** EPA design values. The annual standard (9.0 µg/m³) and the 24-hour standard (98th percentile of days, averaged over 3 years) need complete-data rules, so these numbers are indicative only.
- **Winter drivers:** background from general knowledge, given in chat, **not from this repo's data**; to be cited from Alaska DEC and EPA sources before use.

---

### Visualization V1 · version 18: US national line in the trend chart · 2026-09-28 11:21 EDT · Gina + Claude
- **What:** Added the whole-US "air purifier" series to the national-trend chart as a bold line labelled "US", divided by its own 2016–2019 average (7.69) like the search areas.
  - The summary line now adds: "Nationally the figure is 2.4×, after 12 flat years: from 2004 to 2015 the US index stayed between 4 and 10."
  - The tooltip shows the US ratio and raw index.
  - The note cites the new raw file.
  - Built with `pm25_bundle_v10.json` (v9 plus `us`, 273 monthly values from 2004-01). **No data changed.**
- **Why:** Gina: "add to the most recent graph we create".
- **Check:** the US 2021–2025 average is **2.41×** its 2016–2019 level, close to the 13-area median (**2.5×**). So the median of our areas is a fair stand-in for the national trend.
- **Readings:**
  - Top US months: 2026-04 (100), 2026-05 (68), 2026-06 (43), 2026-03 (42), 2020-09 (33), 2023-06 (27).
  - The spring 2026 spike is the largest in the national series since 2004.
- **Judgment call:** the line uses the page's ink colour (black in light mode, white in dark), with the median staying green. **Claude's choice, flagged.**

---

### Google Trends · Step 6: US national "air purifier" raw file · 2026-09-28 11:21 EDT · Gina + Claude
- **What:** Added Gina's download to `data/raw/google-trends/us-national/`, **copied unchanged** under its Google Trends export name: `time_series_US_20031231-1900_20260928-1117.csv`.
  - Source: ~/Downloads.
  - `cmp` identical; SHA-256 `0001966d031d789bafc1074c36ef1f0b07ca99c47fdd8a9e4258d921563516eb`.
  - 273 monthly rows, 2004-01 to 2026-09, one term ("air purifier"), index 0–100 with 100 = 2026-04.
- Also wrote `data/raw/google-trends/us-national/trends_sources.csv`: one row, same columns as the air-search table. It was written from the file name and contents, not by a script, since it's a single row.
- Added 4 rows to `data/descriptions/data_descriptions.csv` (the file, its 2 columns, and the sources table).
- **Why:** Gina: "here's the air purifier search data for the US national - can you push to github as raw data and then also add to the most recent graph we create".
- **To confirm (Gina):** category and search type were not recorded at download. They are marked "assumed All categories / Web Search" in the sources table.
- **Note:** this file's 0–100 scale is separate from the state, metro and city files; it is compared only as a ratio to its own 2016–2019 average.

---

### Analysis A7 · Fairbanks case study · 2026-09-28 11:17 EDT · Gina + Claude
- **What:** Profiled Fairbanks' PM2.5 (reference only), haze, news share and Trends by calendar month, by season (winter Nov–Feb vs summer Jun–Aug) and by year. Also listed its top PM2.5, winter-PM2.5 and news days. **No files written**; this was a one-off script in chat, reading the explorer bundle.
- **Why:** Gina: "do a mini case study on fairbanks, alaska. what's happening with its data? what's the story there?"
- **Findings:**
  - **Two pollution seasons:**
    - **Winter:** Jan mean 18.2 µg/m³; 36 winter days > 35. Winter peaks are moderate (max 54 on 2017-01-24).
    - **Summer:** Jun–Jul means ≈ 11; 47 summer days > 35. Summer peaks are extreme: 203 on 2022-06-28 and 196.5 on 2024-06-30.
  - **Only the summer is seen:**
    - **Winter days > 35:** haze valid on 97% of them but averaging **1.02×**; news share **1.0%** (lower than on clean winter days, 1.9%); "air purifier" Trends **0** in every Oct–Dec month.
    - **Summer days > 35:** haze averages **3.96×** and news share **9.0%**.
  - **Summer smoke years:**
    - 2019 (6 days > 35), 2022 (19), 2023 (6), 2024 (7), 2025 (7).
    - 2020 and 2026 were clean.
    - "Air purifier" is non-zero in the summers of 2019 and 2022–2024 only.
  - **Winter trend:** 14 days > 35 in winter 2016–17, then 0–6 per winter. Reference coverage was thin in 2017–2018 (172–198 days per year; winter 2017–18 has 3 days), so the early counts are not comparable. Not investigated.
  - **Top news days** (5/20 on 2018-10-12, 2018-10-30, 2019-10-29, 2020-01-24) fell on **low-PM days**, possibly policy or regulatory coverage. Headlines have not been checked.
  - **Search data:**
    - "Air filter" is the main term (monthly means 5.6–39.4, peaking in May; summer means rise from 16.7 in 2017 to 57.7 in 2025). It is ambiguous (furnace and car filters).
    - "Air purifier" is 0 in 119 of 129 months.
- **Interpretation (Claude's, flagged to Gina):**
  - Winter inversion pollution sits in a range the airport visibility sensor can't register. By a rough rule of thumb, 35–55 µg/m³ of dry fine particles still leaves visibility near or above the 10-mile cap. Summer smoke at 100–200 µg/m³ does not.
  - Fairbanks' "haze" group placement (A6) therefore reflects summer wildfire smoke only.
  - **Context to verify and cite before use:** Fairbanks North Star Borough's PM2.5 nonattainment status (EPA Green Book), and the causes of winter pollution (wood and oil heating under inversions).
- **Caveats:**
  - One reference-monitor series; the airport is 5.2 mi from city hall.
  - Media Cloud's Alaska collection has few Fairbanks stories per day (often 2–20), so the news share is spiky.
  - Trends is city level and low volume.

---

### Visualization V1 · version 17: national air-purifier trend chart · 2026-09-28 11:13 EDT · Gina + Claude
- **What:** Added a section below the coverage table (above "About the data"): **"The national rise in 'air purifier' searches."**
  - One grey line per Google Trends search area, and a bold green line for the median across areas.
  - Each area is divided by its own 2016–2019 monthly average (1× = pre-2020 normal), on a log scale.
  - Event markers: COVID-19 (Mar 2020), Western wildfire smoke (Sep 2020), Canadian smoke (Jun 2023), spring 2026 spike (Apr 2026).
  - Hovering shows every area's value that month and highlights the nearest line.
  - A summary line is computed on the page from the data.
- **Why:** Gina: "mock up option 1 with the real data, and add it at the bottom of this city explorer" (to show the national trend behind the A5/A6 adjustment).
- **Data:** the `ap` series already in the bundle (`data/processed/google-trends/air-search/`).
  - **13 search areas.** The 16 cities map to 14 Trends files, since Michigan covers Ann Arbor and Warren and Harlingen-Weslaco-Brownsville-McAllen covers Brownsville and Raymondville.
  - **Fairbanks is left out:** 0 in 119 of 129 months, so there is no usable baseline.
  - Months at 0 are drawn as gaps; September 2026 is partial. **No data changed.**
- **Result shown on the page:** in all 13 areas, the 2021–2025 average was **1.7× to 4.9×** the 2016–2019 level (**median 2.5×**). The largest single-month peaks were Sept 2020 (median ≈ 7×) and April 2026.
- **Judgment calls (Claude's choices, flagged to Gina):**
  - The 2016–2019 baseline.
  - Log scale.
  - Median rather than mean.
  - Fairbanks left out.
  - Which events to mark and how to label them. The "Western wildfire smoke" and "Canadian smoke" labels are general descriptions of those months, not checked against each area.
  - Placing the section above the notes rather than after them.
- **Not done:** no US-wide Trends file exists yet; the median of our areas stands in for it.

---

### Analysis A6 + Visualization V1 · version 16: season- and year-adjusted groups · 2026-09-28 11:02 EDT · Gina + Claude
- **What:** Recomputed the city groups from correlations with **each series' seasonal pattern and year-to-year level removed**, and put them in the explorer. Each panel's correlations now show the adjusted values; hovering shows the values before adjustment. The Groups footnote was rewritten to match. Built with `pm25_bundle_v9.json` (v8 with the new `assoc` values). **No data files changed**; the correlations came from a one-off script in chat.
- **Why:** Gina: "yes - i also want to add search correlation with pm2.5 (the actual measurement)", after A5 showed the Ann Arbor and Brownsville haze links came from a shared long-term trend.
- **Method:**
  - **Series:** monthly "air purifier" searches vs:
    - PM2.5: reference daily mean, low-cost where no reference; month kept if ≥ 15 days
    - haze: extinction ÷ 0.24308; ≥ 15 valid days
    - news share: sum ÷ sum
  - **Months left out:** 2020-03/04 and 2026-03 to 06.
  - **Adjustment:** for each series, over the months used: value − its calendar-month mean − its year mean + overall mean.
  - **Correlation:** Spearman ρ; a pair needs ≥ 24 months.
  - **Chance check:** the measure was shifted by 6–123 months (circularly) against searches, repeating the adjustment each time. p = share of shifted ρ ≥ actual. In unshifted tests at 12–36 months, chance values reached about ±0.3.
  - **Group rule:** unchanged from V1 v7 (strongest ≥ 0.2, ≥ 0.05 above the next, at least 2 measures).
- **Result (ρ before → after adjustment; * = beats chance, p < 0.05):**

  | City | PM2.5 | Haze | News | Group (was) |
  |---|---|---|---|---|
  | Fairbanks | 0.24 → **0.48*** | 0.24 → **0.73*** | 0.18 → 0.06 | **Haze** (PM2.5) |
  | Ann Arbor | 0.12 → **0.47*** | 0.48 → 0.22* | 0.16 → 0.32* | **PM2.5** (haze) |
  | Bakersfield | 0.25 → **0.34*** | 0.24 → 0.26* | 0.03 → 0.22* | **PM2.5** (other) |
  | Warren | 0.18 → **0.52*** (28 months) | −0.04 → 0.24* | – | **PM2.5** (other) |
  | Detroit | 0.08 → 0.43* | 0.10 → 0.30* | 0.38 → **0.52*** | **Media** (media) |
  | Los Angeles | −0.24 → 0.11 | −0.08 → 0.18* | 0.17 → **0.47*** | **Media** (other) |
  | Phoenix | 0.29 → 0.32* | 0.15 → 0.04 | 0.10 → **0.38*** | **Media** (PM2.5) |
  | San Diego | 0.09 → 0.22* | 0.10 → 0.24* | 0.23 → **0.39*** | **Media** (media) |
  | San Francisco | 0.02 → 0.67* | 0.06 → 0.70* | 0.29 → **0.78*** | **Media** (media) |
  | Eugene | 0.20 → 0.56* | 0.11 → 0.45* | 0.32 → 0.56* | Other: PM2.5 = news (media) |
  | Fresno | 0.26 → 0.61* | −0.00 → 0.58* | 0.29 → 0.36* | Other: PM2.5 ≈ haze (other) |
  | Springfield | 0.27 → 0.58* | 0.12 → 0.58* | – | Other: PM2.5 = haze (PM2.5) |
  | Delano | – | 0.31 → 0.48* | – | Other: one measure only (other) |
  | Boston | −0.16 → 0.18 | −0.04 → 0.09 | 0.37 → 0.12 | Other: none ≥ 0.2 (media) |
  | Brownsville | 0.05 → −0.18 (36 months) | 0.40 → 0.09 | 0.07 → −0.09 | Other: none ≥ 0.2 (haze) |
  | Raymondville | – | 0.00 → 0.08 | – | Other: one measure only (other) |

- **Reading (Claude's interpretation, flagged to Gina):**
  - Once the shared trend and seasons are removed, **most cities' searches move with all three measures** in unusual months. Big smoke events raise PM2.5, haze and news together, so the three measures are hard to separate.
  - The Ann Arbor and Brownsville haze links (A5) disappear.
  - Boston's news link (0.37) also came mostly from the trend.
- **Judgment calls (Claude's choices, flagged; not yet approved):**
  - Additive season + year adjustment applied to both series.
  - The shift-based chance test.
  - Keeping the 0.2 / 0.05 rule.
  - Page notes: Fairbanks (119 of 129 zero-search months) and Warren (PM2.5 only 28 months).
- **Note:** the "before" values differ slightly from V1 v7 for some cities (e.g. Fairbanks PM2.5 0.33 → 0.24). This is because the monthly PM2.5 series was rebuilt here and may not exactly match v7's (which was not saved). The groups use only the new adjusted values.

---

### Analysis A5 · season vs trend check for Ann Arbor and Brownsville · 2026-09-28 10:55 EDT · Gina + Claude
- **What:** Tested the claim that Ann Arbor's and Brownsville's searches–haze link comes from shared seasons. Method: air-purifier searches vs haze, Spearman, 2020-03/04 and 2026-03 to 06 left out, as in V1 v7. **No files written**; this was a one-off script in chat.
- **Why:** Gina asked what "through seasons, not reactions" meant.
- **Method:**
  - **Season removed:** subtract each calendar month's 2016–2026 average from both series.
  - **Season + year removed:** also subtract each year's average (searches).
  - Also computed ρ between the 12 calendar-month averages alone.
- **Result:**

  | City | Raw ρ | ρ of the 12 month-of-year averages | Season removed | Season + year removed |
  |---|---|---|---|---|
  | Ann Arbor | 0.48 | 0.46 | 0.42 | **0.08** |
  | Brownsville | 0.40 | **−0.61** | 0.38 | **0.07** |
  | (Bakersfield, for comparison) | 0.24 | 0.37 | 0.39 | 0.28 |
  | (Boston, for comparison) | −0.04 | −0.25 | 0.14 | 0.12 |

  - **Yearly averages, Ann Arbor:** air-purifier index went from 2.8 in 2016 to 10.7 in 2025; haze from 1.07× to 1.15× (with 2019, 2023 and 2025 highest).
  - **Yearly averages, Brownsville:** index went from 0.4 to 7.2; haze from 1.03× to 1.03×, with 2022 (1.06×) and 2024 (1.08×) highest, all in the later years.
- **Correction (to A4 and the chat reply):** "probably through seasons" was **wrong**.
  - Brownsville's seasons run in opposite directions: haze peaks in Mar–Apr, when searches are at their lowest.
  - Removing seasons barely changes either city.
  - Both links disappear when the year-to-year level is removed. They come from a **shared long-term trend**: searches rose nationally from 2016 to 2026, and both cities happened to have hazier later years. This is a trend coincidence, not evidence of people reacting to haze.
- **Implication:** group 1 ("search follows haze most strongly") currently rests on this trend. **Proposed, not run:** recompute all groupings on season- and year-adjusted series. Waiting for Gina's decision.

---

### Visualization V1 · version 15: groups renamed and reordered · 2026-09-28 10:49 EDT · Gina + Claude
- **What:** Renamed and reordered the city groups (the method from V1 v7 is unchanged):
  1. **Search follows haze most strongly:** Ann Arbor, Brownsville
  2. **Search follows measurement (PM2.5) most strongly:** Fairbanks, Phoenix, Springfield
  3. **Search follows media most strongly:** Boston, Detroit, Eugene, San Diego, San Francisco
  4. **Other:** Bakersfield, Delano, Fresno, Los Angeles, Raymondville, Warren
- **Why:** Gina asked for these four groups.
- **Membership:** unchanged; each city is still in the group of its strongest measure.
  - The old groups 1 and 2 were already "strongest measure" groups; their titles ("haze more than the news", "news more than haze") undersold that.
  - **Delano stays in Other.** It has only haze data (no PM2.5 or news), so there is nothing to compare "most strongly" against. Its reason text was updated, and the footnote now says a city needs at least two of the three measures. **Claude's choice, flagged to Gina in chat; not yet approved.**
- **Built with:** `pm25_bundle_v8.json`, which is v7 with Delano's reason text changed. **No data changed.**
- **Note:** the groups still use the V1 v7 correlations (air purifier only, Spearman, 2020-03/04 and 2026-03 to 06 left out), not the A1–A4 numbers.

---

### Analysis A4 · A1–A3 redone with "air purifier" searches only · 2026-09-28 10:46 EDT · Gina + Claude
- **What:** Reran the three correlation pairs and the drop-the-top-months check using only the **"air purifier"** Trends series, instead of the total of 3 terms. **No files written**; this was a one-off script in chat. The news ↔ haze numbers don't involve searches and are unchanged from A2.
- **Why:** Gina: "can you regenerate these results based just on searches for air purifiers?"
- **Method:** the same as A1–A3. "r−k" = Pearson r after removing the k haziest months (searches vs haze) or the k highest-news months (searches vs news).
- **Result (ρ / r / r−1 / r−3):**

  | City | Searches ↔ Haze | Searches ↔ News | News ↔ Haze (unchanged) |
  |---|---|---|---|
  | Ann Arbor | 0.44 / 0.20 / 0.12 / 0.19 | 0.21 / 0.39 / 0.23 / 0.22 | 0.12 / 0.40 / 0.11 / 0.13 |
  | Bakersfield | 0.18 / 0.13 / 0.13 / 0.14 | 0.00 / −0.03 / 0.03 / 0.02 | −0.12 / −0.13 / −0.12 / −0.08 |
  | Boston | −0.04 / −0.03 / −0.06 / −0.04 | 0.35 / 0.06 / 0.13 / 0.10 | 0.15 / 0.11 / 0.15 / 0.16 |
  | Brownsville | 0.42 / 0.22 / 0.27 / 0.26 | 0.12 / 0.09 / 0.09 / 0.06 | 0.10 / 0.03 / 0.05 / 0.07 |
  | Delano | 0.21 / 0.17 / 0.20 / 0.27 | – | – |
  | Detroit | 0.04 / 0.25 / 0.09 / −0.04 | 0.37 / 0.41 / 0.41 / 0.20 | −0.07 / 0.54 / 0.40 / −0.07 |
  | Eugene | 0.09 / 0.86 / 0.11 / 0.10 | 0.29 / 0.81 / 0.32 / 0.25 | 0.21 / 0.89 / 0.73 / 0.49 |
  | Fairbanks | 0.16 / 0.56 / 0.48 / 0.48 | 0.09 / 0.14 / 0.18 / 0.09 | 0.06 / 0.24 / 0.21 / 0.08 |
  | Fresno | −0.05 / 0.17 / 0.03 / 0.01 | 0.25 / 0.33 / 0.18 / 0.17 | 0.03 / 0.28 / 0.09 / 0.12 |
  | Los Angeles | −0.11 / −0.01 / −0.03 / −0.12 | 0.19 / 0.42 / 0.35 / 0.18 | 0.08 / 0.16 / 0.16 / 0.00 |
  | Phoenix | 0.15 / 0.01 / −0.01 / 0.01 | 0.14 / 0.23 / 0.21 / 0.21 | 0.03 / 0.05 / 0.05 / 0.04 |
  | Raymondville | 0.01 / 0.08 / 0.03 / −0.01 | – | – |
  | San Diego | 0.07 / 0.07 / 0.01 / −0.02 | 0.24 / 0.26 / 0.23 / 0.24 | 0.07 / 0.47 / 0.21 / 0.22 |
  | San Francisco | −0.01 / 0.64 / 0.60 / 0.01 | 0.33 / 0.78 / 0.67 / 0.65 | 0.10 / 0.76 / 0.74 / 0.12 |
  | Springfield | 0.10 / 0.85 / 0.05 / 0.10 | – | – |
  | Warren | −0.08 / 0.24 / −0.15 / −0.12 | – | – |

  Leaving out the 2020-03/04 and 2026-03 to 06 months changes ρ by ≤ 0.09.
- **Searches follow haze more than news:**
  - **Brownsville** and **Fairbanks** on all measures. Brownsville's link rests on ordinary months, most likely shared spring seasons. Fairbanks' link rests on its smoke months.
  - **Ann Arbor** on ordinary months only.
  - **Bakersfield** weakly (0.18 vs 0.00). This is new with air purifier alone.
- **Searches follow news more than haze:** all other cities with news data.
  - **San Francisco's** searches–news link is the most robust in the table: r = 0.65 after removing its 3 biggest news months, while its searches–haze link falls to 0.01.
- **Data caveat:** "air purifier" in Fairbanks is **0 in 119 of 129 months** (Google's low-volume floor), so its correlations rest on 10 non-zero months. Other cities with many zero months: Bakersfield 32, Eugene 23, Brownsville and Raymondville 21 (they share one Trends file). The 1.5×-median hit count from A3 is not meaningful for Fairbanks (median 0).
- **Consistency check:** Ann Arbor searches–haze ρ = 0.44 here, and 0.48 with the COVID-19 and 2026 months left out, matching V1 v7 (0.48).

---

### Analysis A3 · how many events carry the searches–haze link · 2026-09-28 10:37 EDT · Gina + Claude
- **What:** For searches vs haze (as in A1), recomputed Pearson r after removing the 1, 2, … 5 haziest months. Also counted, among each city's 10% haziest months, how many had searches above 1.5× the city's median month. **No files written**; this was a one-off script in chat.
- **Why:** Gina asked what it means that Fairbanks and San Francisco keep a high r with a low ρ, and whether other cities share this.
- **Result (r after removing the 0 / 1 / 2 / 3 / 4 / 5 haziest months; hazy months with high searches):**
  - **Fairbanks:** 0.38 / 0.36 / 0.41 / 0.34 / 0.15 / 0.08. 6 of 12 hazy months had high searches: 2019-07, 2022-06, 2022-07, 2023-08 and 2024-06 were all summer smoke months.
  - **San Francisco:** 0.54 / 0.41 / 0.22 / 0.08 / 0.14 / 0.14. 6 of 12. The link rests on 2018-11 and 2020-08/09.
  - **Eugene:** 0.76 / 0.13 / … 5 of 12. **Springfield:** 0.74 / 0.04 / … 3 of 12. In both, the link rests on 2020-09 alone.
  - **All other cities:** r ≤ 0.24 at every step, and 1–3 of 10–12 hazy months with high searches.
- **Correction to A1/A2 wording:** "keeps r ≈ 0.4 without its top month" overstated San Francisco. Its link rests on **2 events** (Camp Fire Nov 2018; Aug–Sept 2020 fires). **Fairbanks is the only city where the link holds across several separate events** (4 years of summer smoke).
- **Caveats:** same as A1. The 1.5× cutoff and the 10% cutoff are Claude's choices, used only for this check.

---

### Analysis A2 · searches vs news, news vs haze correlations · 2026-09-28 10:27 EDT · Gina + Claude
- **What:** The same exercise as A1 for two more pairs: **searches vs news share** and **news share vs haze**, combined with A1 into one table. **No files written**; this was a one-off script in chat.
- **Why:** Gina: "do the same exercise between searching and news, and then news and haze as two separate correlation exercises. combine the correlations with the previous table into one table".
- **Method:**
  - **News month:** air-quality stories ÷ city stories summed over the calendar month (sum ÷ sum, as in the explorer), in %. The month is blank if it has no city stories.
  - Searches and haze are defined as in A1.
  - A pair needs ≥ 24 months with both values.
  - **"r without top month":** removes the haziest month (pairs with haze) or the highest-news month (searches vs news).
  - News exists for 12 cities; there are no Media Cloud queries for Delano, Raymondville, Springfield or Warren.
  - n = 129 months for all news pairs (126 for Ann Arbor news vs haze).
  - Leaving out the 2020-03/04 and 2026-03 to 06 months changes ρ by ≤ 0.08.
- **Result (ρ = Spearman, r = Pearson, r− = Pearson without top month):**

  | City | Search–Haze ρ / r / r− | Search–News ρ / r / r− | News–Haze ρ / r / r− |
  |---|---|---|---|
  | Ann Arbor | 0.31 / 0.18 / 0.13 | 0.21 / 0.31 / 0.19 | 0.12 / 0.40 / 0.11 |
  | Bakersfield | −0.06 / −0.04 / −0.03 | 0.02 / −0.06 / −0.01 | −0.12 / −0.13 / −0.12 |
  | Boston | 0.11 / 0.03 / 0.06 | 0.40 / 0.05 / 0.10 | 0.15 / 0.11 / 0.15 |
  | Brownsville | 0.31 / 0.11 / 0.14 | 0.15 / 0.06 / 0.06 | 0.10 / 0.03 / 0.05 |
  | Delano | 0.07 / 0.12 / 0.16 | – | – |
  | Detroit | −0.17 / 0.11 / −0.02 | 0.34 / 0.26 / 0.27 | −0.07 / 0.54 / 0.40 |
  | Eugene | 0.02 / 0.76 / 0.13 | 0.28 / 0.72 / 0.26 | 0.21 / 0.89 / 0.73 |
  | Fairbanks | 0.12 / 0.38 / 0.36 | 0.09 / 0.03 / 0.09 | 0.06 / 0.24 / 0.21 |
  | Fresno | −0.27 / 0.01 / −0.08 | 0.31 / 0.30 / 0.22 | 0.03 / 0.28 / 0.09 |
  | Los Angeles | −0.09 / −0.09 / −0.10 | 0.14 / 0.23 / 0.18 | 0.08 / 0.16 / 0.16 |
  | Phoenix | 0.13 / −0.02 / −0.01 | 0.13 / 0.26 / 0.23 | 0.03 / 0.05 / 0.05 |
  | Raymondville | −0.06 / 0.09 / 0.08 | – | – |
  | San Diego | 0.12 / 0.03 / −0.03 | 0.27 / 0.15 / 0.12 | 0.07 / 0.47 / 0.21 |
  | San Francisco | 0.01 / 0.54 / 0.41 | 0.30 / 0.59 / 0.53 | 0.10 / 0.76 / 0.74 |
  | Springfield | 0.00 / 0.74 / 0.04 | – | – |
  | Warren | −0.30 / 0.11 / −0.24 | – | – |

- **Top months removed for r−:**
  - Searches vs news: 2020-09 for Eugene, Fresno, Los Angeles, San Diego and San Francisco; 2026-07 for Ann Arbor and Phoenix; 2023-06 for Detroit.
  - Pairs with haze: as in A1.
- **Reading (Claude's interpretation, flagged to Gina):**
  - On ordinary months (ρ), **searches track news more than haze** in most cities (Boston 0.40, Detroit 0.34, Fresno 0.31, San Francisco 0.30).
  - **News vs haze** is weak on ordinary months (ρ ≤ 0.21) but strong in smoke events (r). It is also the most robust Pearson: Eugene 0.73 and San Francisco 0.74 even without their haziest month.
  - The pattern is consistent with: extreme smoke → news coverage → searches. Everyday haze reaches neither.
- **Caveats:**
  - Same as A1.
  - The news share uses state and local collections, so it is not only local outlets.
  - A monthly correlation can't show which came first.

---

### Analysis A1 · searches vs haze correlations · 2026-09-28 10:18 EDT · Gina + Claude
- **What:** Monthly correlations between **searches (total of air purifier + air filter + n95)** and the **haze index** for all 16 cities. **No files written.** This was a one-off script in chat, reading the explorer bundle (built from `data/processed/google-trends/air-search/` and Dish's frozen `vis_<city>_daily.csv`).
- **Why:** Gina: "can you calculate the correlation coefficients between searching & haze visibility for each city? … which creates a more compelling story?"
- **Method:**
  - **Haze month:** mean extinction of valid days ÷ 0.24308, kept if ≥ 15 valid days (same as the V1 v7 grouping).
  - **Correlations:** Spearman ρ (rank) and Pearson r, first on the raw monthly values, then on the "vs. surrounding year" ratio for both series (month ÷ median of the 6 months before and 6 after, as in v14).
  - **Exclusions:** each run was done with and without the COVID-19 and 2026 spike months (2020-03/04 and 2026-03 to 06).
  - **Outlier check:** Pearson r was also recomputed without each city's single haziest month.
- **Result (all months; n = 129 months for most cities; 106 Delano, 126 Ann Arbor, 128 Warren):**

  | City | Raw ρ | Raw r | r without haziest month | Surrounding-year ρ | Haziest month: haze · search vs median |
  |---|---|---|---|---|---|
  | Eugene | 0.02 | **0.76** | 0.13 | −0.17 | 2020-09 · 7.2× · 8.5× |
  | Springfield | 0.00 | **0.74** | 0.04 | −0.20 | 2020-09 · 7.2× · 8.2× |
  | San Francisco | 0.01 | **0.54** | **0.41** | 0.11 | 2018-11 · 2.0× · 5.7× |
  | Fairbanks | 0.12 | **0.38** | **0.36** | −0.09 | 2019-07 · 2.0× · 2.7× |
  | Ann Arbor | **0.31** | 0.18 | 0.13 | −0.19 | 2023-06 · 1.8× · 1.9× |
  | Brownsville | **0.31** | 0.11 | 0.14 | −0.01 | 2022-04 · 1.4× · 1.0× |
  | Delano | 0.07 | 0.12 | 0.16 | −0.13 | 2017-12 · 1.5× · 0.8× |
  | Detroit | −0.17 | 0.11 | −0.02 | −0.18 | 2026-07 · 1.6× · 3.2× |
  | Warren | −0.30 | 0.11 | −0.24 | −0.36 | 2026-07 · 1.5× · 3.1× |
  | Raymondville | −0.06 | 0.09 | 0.08 | −0.02 | 2024-05 · 1.4× · 1.3× |
  | Boston | 0.11 | 0.03 | 0.06 | 0.17 | 2024-02 · 1.2× · 1.0× |
  | San Diego | 0.12 | 0.03 | −0.03 | 0.01 | 2020-09 · 1.3× · 1.9× |
  | Fresno | −0.27 | 0.01 | −0.08 | **−0.44** | 2020-09 · 2.7× · 2.3× |
  | Phoenix | 0.13 | −0.02 | −0.01 | 0.05 | 2024-01 · 1.0× · 1.0× |
  | Bakersfield | −0.06 | −0.04 | −0.03 | −0.35 | 2021-11 · 2.8× · 0.8× |
  | Los Angeles | −0.09 | −0.09 | −0.10 | 0.18 | 2021-11 · 1.6× · 1.1× |

  Leaving out the COVID-19 and 2026 months changes ρ by ≤ 0.08 in every city.
- **Reading:**
  - Ordinary month-to-month haze barely tracks searches: |ρ| < 0.32 everywhere on raw values.
  - The large Pearson r values in Eugene and Springfield come almost entirely from one month (Sept 2020 smoke) and drop to about 0.1 without it. San Francisco and Fairbanks keep r ≈ 0.4 without their top month (several smoke months each).
  - Central Valley winter haze (Bakersfield Nov 2021 at 2.8×, Fresno and Delano in December) comes with normal or low searches. Hence the negative ρ in Fresno, Bakersfield and Warren (searches and haze peak in different seasons).
  - **Interpretation:** searches respond to rare, extreme smoke events, not to routine haze. This is Claude's interpretation, flagged to Gina.
- **Caveats:**
  - Correlation, not cause.
  - Monthly data only.
  - Pearson is driven by a few months, Spearman by ordinary months; the gap between them is the finding.
  - The 2026-07 haze in Detroit and Warren has not been checked against a known event.
  - Searches are metro-area or state-level (fallbacks), not the city itself.

---

### Visualization V1 · version 14: search shading toggle (dot view) · 2026-09-27 22:55 EDT · Gina + Claude
- **What:** Added a **Search shading: vs. whole period | vs. surrounding year** switch. It appears only in Dots view and affects only the search row's shades. "vs. whole period" (the default) is the existing rule. Graphs view, tooltips and all files are unchanged.
- **"vs. surrounding year" formula:**
  - For each month: ratio = the month's search total (the terms switched on) ÷ the **median of the 6 months before and 6 months after it** (the month itself is excluded).
  - A ratio is computed only when at least 6 of those 12 neighbouring months have data, so the first and last months have no dot.
  - If the median is 0: a 0 month counts as 1× (usual), and a non-zero month gets no dot.
  - Shades: ratio ≤ 1 (at or below usual) is the lightest. The months above 1 are split at their 50th/75th/90th/97th percentiles, the same rule as haze and news.
  - The tooltip shows the ratio, the raw index and the median it was compared with.
- **Why:** Gina: "so the green searching bar is just... dark? what can we do to make this more dynamic".
  - **Cause:** searches stepped up in 2020 and stayed higher. Under whole-period shading, every month from 2016–2019 was in the lowest shade in all 16 cities, and that shade is the darkest in dark mode. The monthly Trends resolution also makes blocks of about 30 identical dots.
  - Gina asked how this keeps the data's integrity. The answer given: it is a display-only derived measure; raw values are unchanged and still shown. It answers "unusual for its time?" instead of "how high overall?", and it **hides the post-2020 level shift**, so it is kept as a toggle and labelled on the page. Gina chose "a as a toggle".
- **Check (all 3 terms):** the darkest months now line up with known events. Eugene 2017-09 and 2020-09, and Springfield 2020-09 (wildfire smoke). San Francisco 2017-10 and 2018-11 (North Bay and Camp fires). Mar–Apr 2020 in 7 cities. Jan 2022 in 7 cities. Apr 2026 in Boston, Los Angeles, Phoenix and San Diego. Fairbanks 2016–2018 stays at the lowest shade, because its Trends months are mostly 0 (low search volume).
- **Judgment calls:** 6 + 6 month window excluding the month itself; median rather than mean; the 6-neighbour minimum; the zero-median rule. **Claude's choice, flagged to Gina in chat; not yet approved.**
- **No data changed.**

---

### Visualization V1 · version 13: hideable controls · 2026-09-27 22:36 EDT · Gina + Claude
- **What:** Added a "Hide controls / Show controls" button to the top of the sticky control panel. When the panel is hidden it becomes a single line summarizing the current settings: number of cities · view · smoothing · date range (for example, "16 cities · Dots · 7-day · 1 Jan 2016 – 25 Sep 2026"). The page remembers the choice in the browser along with the other settings.
- **Why:** Gina: "can i make the top part of cities etc hideable".
- **No data changed.**

---

### Visualization V1 · versions 11–12: dot color key · 2026-09-27 22:32 EDT · Gina + Claude
- **What:** Added a color key to the dot view.
  - **Overall key (in the controls, shown in dot view):** one row per measure with its 6 shades and what the ends mean. For example, PM2.5: "below this city's median day → its top 1%"; haze: "clear (1×) → its haziest 3% of hazy days"; news: "no air-quality stories → its top 3% of days with any". It also explains the middle shades, that shades are relative to each city and follow the smoothing, and that no dot = no data.
  - **Per-city key:** a collapsible "This city's shade values" under each city's dots, giving the actual value range of every shade for that city and smoothing (e.g. Eugene, 7-day: PM2.5 reference "under 5.2 … over 32.1 µg/m³"; news "0% … over 10%").
  - Version 12 added a thin outline to the key swatches, so the lightest (baseline) shade stays visible in dark mode.
- **Why:** Gina: "can you add the color key for the dots to the graph".
- **No data changed.**
- **Note:** a first attempt at the outline stopped at a text check before saving, so version 11 went out without it; version 12 includes it.

---

### Visualization V1 · version 10: dot view · 2026-09-27 22:26 EDT · Gina + Claude
- **What:** Added a **View: Graphs | Dots** switch to the explorer. In **Dots** view, each city panel shows one row per measure with **one dot per day**, darker for higher values. The rows are PM2.5 (two rows, reference and low-cost, in "Reference vs low-cost" mode; one row otherwise), haze, news share and searches. The full period is laid out at 4 px per day (~15,700 px), and the panel **scrolls sideways**. **All panels scroll together**, so dates stay aligned across cities. Row labels stay fixed on the left. Hovering shows the day's values. Graphs view is unchanged. **No data changed.**
- **Why:** Gina wanted the dot "intensity" format (from Dish's heat chart) to compare measures as horizontal lines, and asked for it as a toggle view. She approved a mockup (Eugene, real data) first, then asked for the full period with horizontal scrolling instead of compressed stripes.
- **Shading rule (per city, per measure, over the whole 2016–2026 period, using the current smoothing):**
  - **PM2.5 and searches:** 6 shades split at the city's 50th, 75th, 90th, 97th and 99th percentiles.
  - **Haze and news:** the baseline (haze ≤ 1.005×, clear; news share 0%) is the lightest shade. The other days are split at the 50th, 75th, 90th and 97th percentiles of the non-baseline days.
  - The darkest dots therefore mean "exceptional for this city"; darkness is **not comparable across cities** in absolute terms.
  - No dot = no data.
  - In dark mode the ramps run from dim to bright.
- **Follows the existing controls:** city selection, groups, date slider (only the selected range is drawn), smoothing (shades the smoothed value), sensor mode and the search-term switches (the search row is the total of the terms switched on; the mockup used "air purifier" alone).
- **Judgment calls:**
  - The percentile cut points and 6 shades. **Claude's choice, approved by Gina (mockup).**
  - Per-city relative shading rather than EPA categories. **Claude's recommendation, approved by Gina.**
  - Hues matching the graph rows. **Approved by Gina.**
  - 4 px per day; one canvas per year. **Claude's choice.**
  - The search row follows the term switches. **Claude's choice, flagged to Gina in chat.**

---

### Visualization V1 · version 9: zoom undone · 2026-09-27 22:13 EDT · Gina
- **What:** Reverted version 8. The page is back to version 7: the haze row again uses **one scale across all selected cities**, starting at 1×, as in Dish's handoff rule 3. No ▲ markers or clipping. Everything else from version 7 is unchanged (city groups, news row, search row, monthly option).
- **Why:** Gina: "ok jk undo that please".
- **How:** version 7's page source was restored unchanged and republished (same link). The zoomed version is kept locally in case it's wanted later. **No data changed.**
- **Also:** version 8's note that it covered Gina's earlier per-city haze request no longer applies; the haze axis is shared again.

---

### Visualization V1 · version 8: zoomed haze · 2026-09-27 22:12 EDT · Gina + Claude
- **What:** Each city's haze chart is now **zoomed to its own range**, and single extreme days no longer flatten the rest.
  - **Top of the y-axis:** the 99th percentile of the haze values in view × 1.15 (at least 1.5×, never above the real maximum). It updates with the date range and smoothing.
  - **Days above the top** run off the chart (the line is clipped). Each run of such days gets a **▲** marker at the top edge; up to 4 are labelled with their highest value (e.g. "▲ 40×"), skipping any label within 40 px of one already placed.
  - **Finer ticks:** from 1×, 1.1×, 1.2×, 1.5×, 2×, 3×, 5×, 10×, … with the same 16 px spacing rule.
  - Unreviewed-day circles and the hover dot stay at the top edge when their value is above it. The tooltip still shows the true value.
- **Why:** Gina: "zoom in the haze graph a bit for each of the cities… if there's only one that's 40X… it can just go off the graph", so that movements in haze are visible.
- **Changes Dish's handoff rule 3** (one haze scale across cities). Heights are no longer comparable between cities; the chart label and footnote say so. **Changed by Gina.** (This also covers her earlier, interrupted request for a per-city haze axis.)
- **Check:** Eugene's haze axis now runs 1× to about 2× (it ran to 40×); San Francisco shows ▲ markers for its smoke days (e.g. 6.8×, 4.3×).
- **Judgment calls:** the 99th percentile, the × 1.15 headroom, the 1.5× minimum, the 4-label limit and 40 px spacing. **Claude's choice, flagged to Gina in chat.**
- **No data changed.**

---

### Visualization V1 · version 7: city groups · 2026-09-27 22:05 EDT · Gina + Claude
- **What:** The explorer now groups the city panels by **what each city's air-purifier searches follow most closely**, with a switch to turn grouping off. Each panel shows its three correlations, with the strongest highlighted. The page now opens with all 16 cities selected, so every group shows. **No repo files changed**; the correlations were computed in a one-off script in chat (not saved) and built into the page.
- **Why:** Gina asked for four groups:
  1. searches follow haze more than news
  2. searches follow news more than haze
  3. searches follow PM2.5 most
  4. other
- **Method:**
  - **Series:** monthly Google Trends **"air purifier"** (not the total, which n95 and COVID-19 dominate) vs:
    - monthly PM2.5 (reference daily means, low-cost where no reference; month kept if ≥ 15 days)
    - haze (mean extinction ÷ CLEAR; month kept if ≥ 15 valid days)
    - news share (sum ÷ sum)
  - **Correlation:** Spearman rank.
  - **Months left out:** 2020-03/04 (COVID-19 mask buying) and 2026-03 to 2026-06 (a nationwide air-purifier spike in 13 of 17 Trends files, not tied to local air).
  - **Rule:** a city joins the group of its strongest measure if that correlation is **≥ 0.2** and **≥ 0.05 above the next one**; otherwise **group 4**. A city with haze strongest but no news data also goes to group 4, since "haze more than news" can't be shown.
- **Result:**

  | City | PM2.5 | Haze | News | Group |
  |---|---|---|---|---|
  | Ann Arbor | 0.13 | **0.48** | 0.17 | 1 |
  | Brownsville | 0.06 | **0.42** | 0.08 | 1 |
  | Detroit | 0.10 | 0.11 | **0.40** | 2 |
  | Boston | −0.15 | −0.05 | **0.37** | 2 |
  | Eugene | 0.21 | 0.10 | **0.33** | 2 |
  | San Francisco | 0.03 | 0.07 | **0.29** | 2 |
  | San Diego | 0.10 | 0.11 | **0.23** | 2 |
  | Fairbanks | **0.33** | 0.21 | 0.20 | 3 |
  | Phoenix | **0.32** | 0.17 | 0.11 | 3 |
  | Springfield | **0.28** | 0.11 | – | 3 |
  | Bakersfield | 0.26 | 0.26 | 0.02 | 4 (PM2.5 = haze) |
  | Fresno | 0.27 | 0.00 | 0.29 | 4 (news ≈ PM2.5) |
  | Los Angeles | −0.24 | −0.07 | 0.17 | 4 (none ≥ 0.2) |
  | Delano | – | 0.31 | – | 4 (no news data) |
  | Warren | 0.19 | −0.03 | – | 4 (none ≥ 0.2) |
  | Raymondville | – | 0.00 | – | 4 (none ≥ 0.2) |
- **Judgment calls (all Claude's choices, flagged to Gina in chat):**
  - The 0.2 threshold and the 0.05 margin.
  - "Air purifier" alone as the search measure.
  - Which months are left out.
  - Delano placed in group 4.
- **Caveats (in the page footnote):**
  - Correlation, not cause.
  - Shared seasons (e.g. spring allergy season) can raise a correlation on their own. Brownsville's haze peaks in spring, and its group-1 placement may reflect that.
  - Fairbanks's searches are mostly 0.
  - Groups use the whole 2016–2026 period, whatever the date slider shows.

---

### Step 4 · Media Cloud heat · 2026-09-27 21:47 EDT · Gina + Claude
- **What:** Added **`city_stories`** and **`heat_share`** (heat stories ÷ city stories) to each heat CSV, using the city-mention denominator already downloaded in Step 2. **No new queries.**
- **Why:** Gina asked for a heat share like the air-quality share ("yes!").
- **Input:** `data/processed/heat-media/` (Step 3); `city_stories` from `data/processed/mediacloud-attention/` (Step 2; same collections and dates)
- **Script:** `scripts/mediacloud/04_heat_share.py` (local files only)
- **Checks (built in; the script stops if either fails):** dates identical to Step 2 for every city; heat stories ≤ city stories on every day. Both passed for all 12.
- **Whole-period heat share:** Los Angeles 0.57% · Fresno 0.56% · San Diego 0.53% · San Francisco 0.51% · Bakersfield 0.49% · Phoenix 0.45% · Eugene 0.38% (likely understated, "Eugene" is also a first name) · Brownsville 0.33% · Boston 0.32% · Fairbanks 0.17% · Detroit 0.14% · Ann Arbor 0.10%.
- **Output:** the two new columns in `heat_media_<city>.csv`; `total_city_stories` and `heat_share_overall` in `queries.csv`; description rows as below.
- **Judgment calls:** `heat_share` blank when `city_stories` = 0, and longer periods use the ratio of sums, the same rules as `air_share` (Step 2). **Same rules Gina approved for the air share.**

### Step 3 · Media Cloud heat · 2026-09-27 21:47 EDT · Gina + Claude
- **What:** Downloaded Media Cloud **"Attention over time"** for heat news in the same 12 cities, collections and dates as Step 1 (2016-01-01 → 2026-09-25). Query: `("heat wave" OR "heat advisory") AND "<city>"`. **No values changed.**
- **Why:** Gina is adding a heat media angle alongside the air-quality one.
- **Input:** Media Cloud API; method specified by Gina (same as Step 1). Key read from `$MEDIACLOUD_API_KEY`; not in any file (checked).
- **Script:** `scripts/mediacloud/03_heat_attention_over_time.py` (Step 1's script with the query and folders changed)
- **Rows in → out:**

  | # | City | Collection | Sources | Heat stories |
  |---|---|---|---|---|
  | 1 | Los Angeles | California | 1,283 | 13,491 |
  | 2 | Phoenix | Arizona | 139 | 1,924 |
  | 3 | San Diego | California | 1,283 | 6,211 |
  | 4 | Detroit | Michigan | 203 | 949 |
  | 5 | Bakersfield | California | 1,283 | 736 |
  | 6 | San Francisco | California | 1,283 | 6,975 |
  | 7 | Fresno | California | 1,283 | 1,366 |
  | 8 | Boston | Massachusetts | 307 | 2,907 |
  | 9 | Eugene | Oregon | 145 | 194 |
  | 10 | Fairbanks | Alaska | 77 | 66 |
  | 11 | Brownsville | Texas | 593 | 130 |
  | 12 | Ann Arbor | Michigan | 203 | 123 |

  All have 3,921 days except Fairbanks (3,886; the same 35 empty-collection days as Step 1).
- **Output:** raw `data/raw/heat-media/json/` (12 heat responses + 12 collection records); processed `data/processed/heat-media/heat_media_<city>.csv` (12) and `queries.csv`; 10 description rows added (Steps 3–4).
- **Checks:**
  - `ratio` = stories ÷ collection total on every row.
  - **The busiest days match known heat waves:** Los Angeles and San Francisco **2022-09-07** (the September 2022 California heat wave); Eugene **2021-06-29** (the Pacific Northwest heat dome); Phoenix 2021-06-29 and **2023-07-19**; Fresno 2020-09-06/07; San Diego 2020-08-17; Boston June–August 2018/2019.
  - Rate-limit hits (HTTP 429) on 3 cities were retried successfully.
- **Judgment calls:**
  - **Folders:** Gina asked for a new raw folder "heat-media". Following her rule from Step 1 (JSON is raw; flattened CSVs are processed), the JSON is in `data/raw/heat-media/json/` and the CSVs in `data/processed/heat-media/`. **Claude's proposal, approved by Gina** ("yes do that").
  - **Same collections as Step 1**, including Massachusetts 38381372. **Claude's choice.**
- **Caveat:** "heat advisory" is a National Weather Service product name; stories quoting advisories may cluster in regions where the NWS issues them often. "heat wave" also appears in non-weather uses (e.g. sports, music).

---

### Visualization V1 · version 6: news row · Media Cloud · 2026-09-27 19:16 EDT · Gina + Claude
- **What:** Added an **"In the news"** row to each city panel in the explorer, between "Haze you can see" and "Searching for air-quality help": the percentage of local stories mentioning the city that are about air pollution or air quality (Media Cloud Step 2). Own scale per city (0 to the highest share in view). **No repo files changed**; the calculation runs in the page.
- **Why:** Gina asked to chart the daily `air_share` for each city.
- **Input:** `data/processed/mediacloud-attention/mediacloud_attention_<city>.csv` (`stories`, `city_stories`) for the 12 queried cities. Springfield, Delano, Warren and Raymondville show "No news data for this city (not queried)".
- **Calculation (in the page):**
  - **Daily:** share = stories ÷ city_stories × 100; blank when city_stories = 0.
  - **7-day / 30-day:** trailing window sums, sum(stories) ÷ sum(city_stories).
  - **Monthly:** calendar-month sums, the same ratio.
  - A window is blank only when it has no city story.
  - **Fairbanks's 35 days missing from the file** (the Alaska collection published nothing) count as 0 air and 0 city stories.

  **Approved by Gina** ("% malleable based on the settings of the explorer"; ratio of sums, not an average of daily shares).
- **Tooltip:** e.g. "News: 28% of city stories about air quality (111 of 395)". The coverage table gained a column with the share over the selected period (the same ratio of sums).
- **Checks:**
  - Page vs CSV: Bakersfield 2016-01-04 = 0 of 9; Eugene Sep 2020 monthly = 111 of 395 (28%).
  - Whole-period shares in the table match `queries.csv` (e.g. Bakersfield 1.8%, Fairbanks 1.9%, Detroit 0.42%).
  - Bundle totals equal `total_stories` and `total_city_stories` for all 12.
- **Judgment calls:**
  - **Line in magenta** (Cove slot 5, a darker step for contrast on light backgrounds). **Claude's choice.**
  - **Own y-scale per city**, like the search row, since shares differ a lot between cities. **Claude's choice, flagged to Gina in chat.**
  - A **zero share is shown as "0%"**, not "0.00%". **Claude's choice.**
- **Not done (still open from earlier):** renaming the page to "Air quality: measurement, perception & reaction", and making the haze axis follow the per-city / shared toggle. Gina interrupted that request; not applied.

---

### Step 2 · Media Cloud attention · 2026-09-27 18:55 EDT · Gina + Claude
- **What:** For each of the 12 cities, counted daily stories mentioning the city at all (`"<city>"`), in the **same state collection and dates** as Step 1. Added two columns to each processed CSV:
  - **`city_stories`** (the denominator)
  - **`air_share`** = air-pollution stories ÷ city stories (the numerator is Step 1's `stories`)

  This gives the share of the day's city coverage that is about air pollution or air quality. Existing columns are unchanged.
- **Why:** Gina's design: a percentage of media attention that is independent of how much a city is in the news overall.
- **Input:** Media Cloud API (`/api/search/count-over-time`, query `"<city>"`); `data/processed/mediacloud-attention/` (Step 1)
- **Script:** `scripts/mediacloud/02_city_mentions.py`
- **Rows in → out:** 12 queries; no rows added or removed.

  | City | City stories | Days with 0 | Whole-period air share |
  |---|---|---|---|
  | Los Angeles | 2,363,655 | 0 | 1.18% |
  | Phoenix | 430,944 | 0 | 0.45% |
  | San Diego | 1,173,860 | 0 | 0.76% |
  | Detroit | 670,408 | 0 | 0.42% |
  | Bakersfield | 149,574 | 2 | 1.76% |
  | San Francisco | 1,357,132 | 0 | 1.14% |
  | Fresno | 242,984 | 0 | 1.67% |
  | Boston | 905,399 | 0 | 0.46% |
  | Eugene | 50,689 | 49 | 1.20% (likely understated) |
  | Fairbanks | 38,519 | 374 | 1.93% |
  | Brownsville | 39,093 | 196 | 0.40% |
  | Ann Arbor | 119,442 | 6 | 0.38% |
- **Output:**
  - Raw: `data/raw/mediacloud-attention/json/<city>_city_count_over_time.json` (12)
  - Processed: `mediacloud_attention_<city>.csv` gained `city_stories` and `air_share`; `queries.csv` gained `city_query`, `total_city_stories`, `days_city_stories_0` and `air_share_overall`
  - 4 description rows added
- **Checks (built into the script, which stops if either fails):** the dates are identical to Step 1 for every city (Fairbanks: the same 3,886 days); `city_stories` ≥ `stories` on every day. Both passed for all 12. Rate-limit hits (HTTP 429) on 4 cities were retried successfully.
- **Judgment calls:**
  - **Denominator = the same quoted city phrase as the numerator, in the same state collection**, so the share can't exceed 100%. **Specified by Gina.**
  - **Eugene kept as `"Eugene"`, flagged as likely understated** (the first name inflates the denominator); Phoenix has a smaller version of the same issue. **Claude's recommendation, approved by Gina.**
  - **`air_share` blank when `city_stories` = 0** (undefined, not 0%). **Specified by Gina.**
  - **For 7-day, 30-day and monthly views, the share is to be calculated as sum(stories) ÷ sum(city_stories) over the window,** not an average of daily shares; the explorer will apply this. **Approved by Gina** ("malleable based on the settings of the explorer").
  - **Sports and passing mentions count in the denominator** ("all media mentioning the city"). **Approved by Gina.**
- **Caveat for the appendix:** daily shares are noisy where city mentions are few (Brownsville: 196 days with no city story; Fairbanks 374), e.g. 1 of 2 stories = 50%. Use longer windows for small cities.

---

### Step 1 · Media Cloud attention · 2026-09-27 18:32 EDT · Gina + Claude
- **What:** Downloaded Media Cloud **"Attention over time"** (daily story counts) for 12 study cities. Each query is `("air pollution" OR "air quality") AND "<city>"`, run in the city's state **"State & Local"** collection, 2016-01-01 → 2026-09-25. Saved one CSV per city plus the raw responses. **No values changed.**
- **Why:** Gina is adding a media angle to the city explorer (measurement, perception, reaction, and now coverage).
- **Input:** Media Cloud API (`/api/search/count-over-time`, `/api/sources/collections/{id}/`); method specified by Gina. API key read from `$MEDIACLOUD_API_KEY` (not in any file; checked).
- **Script:** `scripts/mediacloud/01_attention_over_time.py`
- **Rows in → out:**

  | # | City | Collection (ID) | Sources | Stories 2016–2026 | Days |
  |---|---|---|---|---|---|
  | 1 | Los Angeles | California (38380550) | 1,283 | 27,980 | 3,921 |
  | 2 | Phoenix | Arizona (38381317) | 139 | 1,935 | 3,921 |
  | 3 | San Diego | California (38380550) | 1,283 | 8,905 | 3,921 |
  | 4 | Detroit | Michigan (38381374) | 203 | 2,788 | 3,921 |
  | 5 | Bakersfield | California (38380550) | 1,283 | 2,627 | 3,921 |
  | 6 | San Francisco | California (38380550) | 1,283 | 15,523 | 3,921 |
  | 7 | Fresno | California (38380550) | 1,283 | 4,055 | 3,921 |
  | 8 | Boston | Massachusetts (38381372) | 307 | 4,117 | 3,921 |
  | 9 | Eugene | Oregon (38381398) | 145 | 606 | 3,921 |
  | 10 | Fairbanks | Alaska (38381315) | 77 | 743 | **3,886** |
  | 11 | Brownsville | Texas (38381323) | 593 | 158 | 3,921 |
  | 12 | Ann Arbor | Michigan (38381374) | 203 | 451 | 3,921 |
- **Output:**
  - **Raw:** `data/raw/mediacloud-attention/json/` (raw API responses and collection records, exactly as received).
  - **Processed:** `data/processed/mediacloud-attention/`: `mediacloud_attention_<city>.csv` (12) and `queries.csv`.
  - 16 description rows added.
  - **Moved:** the CSVs were first saved in `data/raw/` and moved to `data/processed/` at Gina's request (flattening is a transformation, so only the JSON is raw). Moved with `git mv`, contents unchanged; the script now writes the CSVs to `processed/`. **Changed by Gina.**
- **Checks:**
  - **Totals match an independent query.** For every city with a city-selection Step 6 count (all but Boston), the stories from 2024-09-25 to 2026-09-25 equal Step 6's total exactly (e.g. Los Angeles 6,442, San Francisco 2,422, Brownsville 30). Step 6 used the `total-count` endpoint, not `count-over-time`.
  - `ratio` = stories ÷ collection total on every row, and every returned day has a collection total ≥ 1.
  - The busiest days match known events: Los Angeles 2025-01-10 (127; January 2025 fires), 2017-12-07 (125; Thomas/Creek fires), 2020-09-11 to 09-15 (September 2020 smoke); Detroit and Ann Arbor 2026-07-16 (the same day as the Detroit PM2.5 spike).
- **Fairbanks:** Media Cloud returned 3,886 of 3,921 days. The 35 missing days (2016-01-05 to 2017-08-06) are days when the whole Alaska collection published nothing: every returned day has ≥ 1 collection story, and early 2016–17 days often have only 1. The raw file is left as received; when used, those days count as 0 stories.
- **Judgment calls:**
  - **Massachusetts collection = "Massachusetts, United States - State & Local" (38381372, 307 sources)**, the same kind as the other states (not the "(Faster)" or "Local Papers" collections). **Claude's choice, flagged to Gina in chat.**
  - **Source counts are the collections' counts at download time** (unchanged since 2026-09-26 for the 11 collections looked up then). **Claude's choice.**
  - **Only 12 of the 16 explorer cities**, as listed by Gina: Springfield, Delano, Warren and Raymondville were not requested. **Specified by Gina.**

---

### Visualization V1 · version 5: search row + monthly · Google Trends + METAR + OpenAQ · 2026-09-27 17:45 EDT · Gina + Claude
- **What:** Added a third row to each city panel, **"Searching for air-quality help"**: the monthly Google Trends total of the search terms switched on ("air purifier", "air filter", "n95"; all on by default), with switches to turn terms on and off. Added a **Monthly** option to the smoothing control (Daily / 7-day / 30-day / Monthly). Each panel now reads measured (PM2.5) → perceived (haze) → action (searches). **No repo files created or changed**; calculations run in the page.
- **Why:** Gina wants to see the relationship between measured PM2.5, perceived haze and action taken (searching for mitigation).
- **Input:** `data/processed/google-trends/air-search/*-air-search.csv` (Google Trends Step 5; read only), plus the PM2.5 and METAR inputs of versions 1–4.
- **Search geography per city:**
  - **City files:** Bakersfield, Detroit, Eugene, Fairbanks, Los Angeles, Phoenix, San Diego.
  - **Metro areas:** San Francisco → San Francisco-Oakland-San Jose; Fresno → Fresno-Visalia; Brownsville and Raymondville → Harlingen-Weslaco-Brownsville-McAllen; Boston → Boston MA-Manchester NH.
  - **State files (fallback, no own file):** Ann Arbor and Warren → **Michigan**; Springfield → **Oregon**; Delano → **California**. **Changed by Gina** (Claude had suggested the nearest city files).
- **Checks (read only):** all 16 mapped files have 129 months (2016-01 → 2026-09), and `total_interest_index` = the sum of the three terms in every row. Eugene Sep 2020 = air purifier 100 + air filter 92 + n95 63 = 255, and the page shows the same.
- **Transformation (in the page):**
  - **Search line** = sum of the selected terms' monthly index values, drawn flat across each month on the daily date axis. **Own scale per city**, 0 to the highest value in view, because Trends files aren't comparable across places.
  - **Monthly smoothing** = calendar-month mean of the days with data, shown only if at least half of that month's days (within the date axis) have data. For haze: mean **extinction** first, then ÷ CLEAR (same rule as the 7/30-day options).
  - **Tooltip** shows the month, the total, each selected term's value, and "(partial)" for September 2026. The site count is shown only for daily values, since it is a per-day count.
- **Judgment calls:**
  - **Use the total, with term switches.** **Changed by Gina** (Claude had suggested "air purifier" alone because n95 mostly reflects COVID-19). Claude pointed out that the average is total ÷ 3, so it has the same shape, and that a 0 in Trends means "too little data", not zero searches.
  - **Monthly option added.** **Specified by Gina.**
  - **Search line in green, flat within each month.** **Claude's choice.**
- **Findings (from the checks):**
  - The total peaks in **April 2020** (COVID-19 masks) in most places.
  - **Exceptions:** Eugene and Oregon **Sep 2020** (wildfire smoke; all three rows spike together in Eugene); San Francisco **Nov 2018** (the month of the Camp Fire smoke); Fairbanks **Jun 2022**; Phoenix and San Diego **Apr 2026**.
  - **Fairbanks is mostly 0** for "air purifier" (119 of 129 months) and "n95" (125), so its line mostly follows "air filter"; noted on its panel.

---

### Visualization V1 · version 4: haze row · METAR + OpenAQ · 2026-09-27 17:21 EDT · Gina + Claude
- **What:** Added a **"Haze you can see: times hazier than a clear day"** row under each city's PM2.5 chart in the PM2.5 City Explorer (same link, version 4), using Dish's frozen METAR visibility files. Haze index = daily light extinction ÷ its value on a clear day. **No files in the repo created or changed:** the calculation runs in the page. The METAR files were read only; `git status` shows no changes in `data/processed/metar/`.
- **Why:** Gina's handoff: add the METAR visibility row as Dish's "option C", the haze index.
- **Input:** `data/processed/metar/final/vis_<city>_daily.csv` for the **16 study cities** (Pittsburgh excluded: **changed by Gina**), columns `date`, `extinction`, `valid_day`; plus the Step 5 PM2.5 daily files. Data guide: `docs/metar-status.md` (Dish, commit `aa7d554`); Decision D8 in `logs/data-log-dish.md`.
- **Checks before building (read-only):**
  - All 17 files match the SHA-256 in D8.
  - 3,920 rows each, 2016-01-01 → 2026-09-24.
  - Valid days match `step09_summary.csv` and the table in `docs/metar-status.md` for all 17.
  - No valid day has a blank extinction, and no invalid day has one.
  - Minimum 1.00× everywhere. **Eugene max 40.00× on 2020-09-13** (Springfield identical), **Phoenix max 1.79×**.
  - Checked again in the built page: Eugene 2020-09-13 shows "40.0× a clear day (≈0.25 mi visibility)".
- **Transformation (in the page):**
  - `CLEAR` = 3.912 ÷ (10 × 1.609344) = 0.24308 (extinction at the 10-mile sensor cap).
  - **Daily:** haze = extinction ÷ CLEAR, only `valid_day = 1`; other days are gaps (no zeros, no filling).
  - **7- and 30-day:** trailing mean of the valid days' **extinction** in the window, shown only when at least half the window has valid days, then ÷ CLEAR. Visibility is never averaged, and an index is never averaged. The control is shared with PM2.5 (Daily / 7-day / 30-day). **Changed by Gina** (trailing means, as a toggle).
  - **Tooltip visibility** = 10 ÷ haze index miles (identical to `visibility_mi`).
  - **Date axis** extended to 2016-01-01 → 2026-09-25 so both datasets fit; PM2.5 starts 2016-03-06 and METAR ends 2026-09-24, each shown as gaps outside its range.
- **Drawing (per the handoff):**
  - Linear y from 1×; ticks from 1×, 2×, 5×, 10×, 20×, 40× (80× if needed), dropping any within 16 px of the tick below. **One haze scale across all selected cities**, whatever the PM2.5 "per city / shared" setting.
  - Tooltip: "12.4× a clear day (≈0.8 mi visibility)", or "1× (clear, 10+ mi)" at the floor (index < 1.005).
  - The word "extinction" does not appear in the main UI; the footnote wording is as given in the handoff.
- **Caveats shown on the page:**
  - **Notes on the city panels:** Ann Arbor outage from ~2026-06-17 (last valid day 2026-08-05); Phoenix nearly flat (max ≈ 1.8×), flagged not hidden; Springfield uses Eugene's airport; Raymondville uses Harlingen's (19 mi); Delano starts 2017-01-15 and uses routine reports only; Warren = Troy airport (VLL), routine reports only; Detroit = mean of two airports.
  - **The 7 unreviewed days** (Boston 2024-02-23, Bakersfield 2020-12-17/18, Ann Arbor 2016-07-25, Warren 2026-07-16/17, Delano 2024-11-11) are circled on the chart, with "not yet checked: possibly fog" in the tooltip.
  - **Raymondville is now selectable** (haze only; no PM2.5).
- **Finding:** several unreviewed days are their city's **highest** haze day: Ann Arbor 15.2× (2016-07-25), Bakersfield 18.0× (2020-12-17), Boston 6.0× (2024-02-23), Delano 5.9× (2024-11-11), Warren 9.5× (2026-07-16). Warren's and Detroit's 2026-07-16 highs coincide with the Detroit PM2.5 spike (OpenAQ Step 4), which suggests smoke rather than fog there, but it is still unreviewed.
- **Judgment calls:**
  - **Visibility computed as 10 ÷ index**, not read from `visibility_mi` (identical, smaller page). **Claude's choice, flagged to Gina in chat.**
  - **"1×" shown when the index is below 1.005.** **Claude's choice.**
  - **Haze line in violet**, a separate chart (no second axis on the PM2.5 chart). **Claude's choice.**
  - `metar-pipeline-status.md` was not available at first; the repo copy `docs/metar-status.md` was used once Gina added it. Dish's "Haze Scale Options" artifact is not shared with Gina, so it was not consulted.
- **Log fix:** the separator line above the Visualization V1 entry had been cut to `--` by an earlier edit of Claude's; restored to `---`.

---

### Visualization V1 · OpenAQ · 2026-09-27 17:00 EDT · Gina + Claude
- **What:** Built an exploratory chart page, **"PM2.5 City Explorer"** (private Claude artifact: https://claude.ai/artifact/NRvuFdqDZZioQHkL1RnB8Q). One panel per selected city, with the date on the horizontal axis and daily PM2.5 on the vertical.
  - **Controls:** select or unselect cities; sensors (reference vs low-cost overlaid, reference, low-cost, overall); smoothing (daily, 7-day, 30-day trailing mean); linear or log scale; per-city or shared y axis; date range (with drag to zoom); optional site min–max band; optional EPA 35 µg/m³ line.
  - Hover shows each day's values, number of sites and the low-cost − reference difference. A table gives days with data per type and the median low-cost − reference difference in the selected period.
- **Why:** Gina wanted to get a feel for the shape of the data and compare reference and low-cost sensors, with cities she can switch on and off. (She asked for no calendar view.)
- **Input:** `data/processed/openaq/step05_averages/pm25_<city>_daily.csv` (16 files), bundled into the page (mean, min, max and site counts, rounded to 0.1 µg/m³). **No data files changed or added in the repo.**
- **Judgment calls:**
  - **Smoothing** is a trailing mean of the available days, shown only when at least half the window has data. **Claude's choice, flagged to Gina in chat.**
  - **Log scale** uses a symmetric log (so 0 can be shown). **Claude's choice.**
  - **EPA line:** 35 µg/m³ is the level of the 24-hour PM2.5 standard (40 CFR 50.13, https://www.law.cornell.edu/cfr/text/40/50.13, checked 2026-09-27). The page notes that the standard is judged on the 98th percentile over three years, so one day above it is not a violation. **Claude's choice, flagged to Gina in chat.**
  - **Default view:** 6 cities (Bakersfield, Fresno, Los Angeles, Eugene, Fairbanks, Detroit), reference vs low-cost, 7-day smoothing, per-city y axis. **Claude's choice.**
- **Note:** the page is a view of the Step 5 files, not a new dataset. Numbers read from it are rounded to 0.1 µg/m³.
- **Version 2 (2026-09-27 17:06 EDT):** the two date boxes were replaced with a **two-handle date slider** (start and end, minimum 7 days apart), with year marks and the selected range and day count shown above it. The presets and drag-to-zoom on the charts still work and move the slider. **Changed by Gina.** Same link; no data changed.
- **Version 3 (2026-09-27 17:11 EDT):** hover labels rebuilt with HTML character codes (µg/m³, ·, −, –) and set in the sans-serif face, so they display correctly however the page is loaded; the low-cost − reference difference now shows its unit. Gina had seen garbled characters in the labels (likely the first local preview, which ran before the characters were escaped). **Requested by Gina.** No data changed.


### Step 16 · descriptions · 2026-09-27 15:14 EDT · Gina + Claude
- **What:** Added two columns to `data/descriptions/data_descriptions.csv`: **`name`** (who added the row) = `gina` for all 206 existing rows, and **`date-added`** (date the row was first added).
- **Why:** So Gina's and Bidisha's (Dish's) entries can be told apart if both add to the file, and so each row's age is visible.
- **Script:** none (documentation). `date-added` was taken from the git history: for each row (file + column), the date of the first commit containing it. All 206 rows were added on 2026-09-27. Rows renamed later (e.g. `total_searches` → `total_interest_index`) carry the date of the rename.
- **Judgment calls:**
  - **Columns and value `gina`:** **specified by Gina.**
  - **`date-added` as a date only (YYYY-MM-DD)**, as asked; exact times are in the git history. **Claude's choice, flagged to Gina in chat.**
  - **Columns added at the end** of each row. **Claude's choice.**
- **From now on:** every row Claude adds for Gina gets `name` = `gina` and that day's `date-added`.

### Step 5 · Google Trends · 2026-09-27 15:01 EDT · Gina + Claude
- **What:** Made processed copies of the 17 air-search files. Each keeps `Time`, "air purifier", "air filter" and "n95" unchanged (all three kept) and adds `total_interest_index` (their sum) and `avg_interest_index` (their average, 2 decimals). Added a `README.md` defining the 0–100 index. **Raw files not modified.**
- **Why:** Gina asked to repeat the heat-search process for the air-quality searches.
- **Input:** `data/raw/google-trends/air-search/*-air-search.csv` (17 files)
- **Script:** `scripts/google-trends/04_air_search_processed.py`
- **Rows in → out:** 17 files × 129 months → 17 files × 129 months; 2 columns added, none removed. Checked: dates and the three terms identical to raw, and the total equals their sum in every row.
- **Output:** `data/processed/google-trends/air-search/` (17 CSVs + `README.md`); 5 description rows added
- **Judgment calls:**
  - **All three terms kept.** **Specified by Gina** (after Claude flagged that "air filter" includes furnace, HVAC and car filters, and that "n95" peaks with COVID-19).
  - **Column names and README as for heat search** (Google Trends Step 3). **Specified by Gina** ("repeat this process").
- **Caveats for the appendix:**
  - **What sets the 100:** in **15 of 17 files it is "n95" in March or April 2020** (COVID-19 onset), or January 2022 in San Francisco-Oakland-San Jose. Every other month and term is scaled against that spike, so air-quality-related searches in other months look small. Dropping n95 afterwards would not undo this, because Google's scaling is built into the download.
  - In **Eugene and Oregon the 100 is "air purifier" in September 2020**, the month of the Oregon wildfire smoke (compare OpenAQ: Eugene reference PM2.5 up to 468 µg/m³ that month).
  - As for heat search, the files are not comparable across places.

### Step 4 · Google Trends · 2026-09-27 15:01 EDT · Gina + Claude
- **What:** Added Gina's 17 Google Trends air-quality search downloads to the repo **unchanged** (checked byte-for-byte), and wrote `trends_sources.csv` with each file's source, geography, level, date range, terms and settings. The hidden Mac file `.DS_Store` in the folder was not copied. **No data values changed.**
- **Why:** Same as Google Trends Step 1, for the air-quality searches.
- **Input:** `~/Desktop/MDE/dataviz/trends-air/*.csv` (17 files, downloaded by Gina 2026-09-27, file times 10:51–13:41)
- **Script:** `scripts/google-trends/03_air_sources_table.py`
- **Rows in → out:** 17 files, each 129 months (2016-01 to 2026-09) × 3 terms ("air purifier", "air filter", "n95"), all values whole numbers → 17 files unchanged + a 17-row sources table.
- **Geographies:** the same 17 as the heat search, with the same levels: 6 US states; 4 metro areas; 7 cities (per Gina). Checked in code: geographies and levels identical to the heat-search `trends_sources.csv`.
  - File names differ from the heat search in places: `boston-ma` (heat: `boston MA-Manchester-NH`), `la-ca`, `san diego-ca`, `fresno-visalia-ca`, `oregon`, `tx`.
- **Output:** `data/raw/google-trends/air-search/` (17 CSVs + `trends_sources.csv`); 6 description rows added
- **Judgment calls:**
  - **Same levels as the heat search.** **Specified by Gina.**
  - **Boston recorded as the Boston MA-Manchester NH metro**, although this file is named just `boston-ma`. **Confirmed by Gina.**
  - **Settings as for heat search** (search terms, All categories, Web Search, downloaded 2026-09-27). **Confirmed by Gina.**

### Step 3 · Google Trends · 2026-09-27 14:51 EDT · Gina + Claude
- **What:** Made processed copies of the 17 heat-search files. Each keeps `Time`, "air conditioner", "fan" and "AC" unchanged, removes "cooling center" and "cooling fan", and adds `total_interest_index` (sum of the three terms) and `avg_interest_index` (their average, 2 decimals). **Raw files not modified** (checked with `git status`).
- **Why:** Gina asked for the three main heat-related terms, with a total and an average per month.
- **Input:** `data/raw/google-trends/heat-search/*-heat-search.csv` (17 files)
- **Script:** `scripts/google-trends/02_heat_search_three_terms.py`
- **Rows in → out:** 17 files × 129 months → 17 files × 129 months; 2 columns removed, 2 added. Checked after running: dates and the three kept terms are identical to the raw files, and the total equals their sum in every row.
- **Output:** `data/processed/google-trends/heat-search/` (17 files, same names as the raw files); 7 rows added to `data/descriptions/data_descriptions.csv`
- **Judgment calls:**
  - **Columns removed, terms kept and the two new columns:** **specified by Gina.**
  - **Column names:** first `total_searches` / `avg_searches` as Gina specified. After Claude pointed out these are index values, not numbers of searches, they were **renamed `total_interest_index` / `avg_interest_index`** and the files rewritten. **Changed by Gina.**
  - **A `README.md` added to the processed folder** defining the 0–100 interest index (with the Google Trends Help source) and when files can and can't be compared; a CSV has no room for a title or description. **Claude's suggestion, requested by Gina.**
  - **`avg_searches` rounded to 2 decimals;** kept columns written as numbers. **Claude's choice, flagged to Gina in chat.**
  - **Same file names as the raw files**, in a parallel processed folder. **Claude's choice.**
- **Problem during the step:** The first run wrote the three kept columns as quoted text (e.g. `"2"`), which spreadsheet or charting tools could read as text. Fixed (written as numbers) and rerun; the first run's output was overwritten.
- **Caveats for the appendix:**
  - **Each file is scaled separately** (0–100 within that file), so `total_interest_index` can be compared across months within a city, but not between cities or states.
  - **The three terms are summed with equal weight.** In each file, "fan" and "AC" are usually much higher than "air conditioner", so they dominate the total.

### Step 2 · Google Trends · 2026-09-27 14:48 EDT · Gina + Claude
- **What:** Added one more Google Trends download, `boston MA-Manchester-NH-heat-search.csv` (metro area **Boston MA-Manchester NH**), the same way as Step 1: copied **unchanged** (checked byte-for-byte), added to `trends_sources.csv` (now 17 rows), and the file count updated in the data descriptions. **No data values changed.**
- **Why:** Gina added the Boston file to `~/Desktop/MDE/dataviz/trends-heat-search/` after Step 1.
- **Input:** `~/Desktop/MDE/dataviz/trends-heat-search/boston MA-Manchester-NH-heat-search.csv` (file time 2026-09-27 14:45)
- **Script:** `scripts/google-trends/01_sources_table.py` (one line added to its geography list; rerun rewrites `trends_sources.csv` for all 17 files)
- **Rows in → out:** 1 file, 129 months (2016-01 to 2026-09) × the same 5 terms → copied unchanged; `trends_sources.csv` 16 → 17 rows.
- **Output:** `data/raw/google-trends/heat-search/boston MA-Manchester-NH-heat-search.csv`; `trends_sources.csv`; descriptions row updated (17 files: 6 states, 4 metro areas, 7 cities)
- **Judgment calls:**
  - **Level recorded as "metro area"**, from the name (it matches the Google Trends metro naming, like the other 3 metros). **Claude's reading, confirmed by Gina.**
  - **Same settings as Step 1** (search terms, All categories, Web Search, downloaded 2026-09-27 by Gina). **Confirmed by Gina.**
- **Correction:** Steps 1 and 2 first said each file has 128 months; the correct count is **129** (Jan 2016 to Sep 2026 = 10 × 12 + 9). Claude had read the number from a line count (`wc -l`) that misses the files' last line, which has no line ending. `trends_sources.csv` was always correct (n_months = 129 for all 17 files); only the log and description text were wrong, now fixed.
- **Note:** Boston is covered by a **metro** file, while most other study cities are covered by city (or state) files, so the geographic level differs.

### Step 1 · Google Trends · 2026-09-27 14:46 EDT · Gina + Claude
- **What:** Added Gina's 16 Google Trends downloads to the repo **unchanged**, and wrote `trends_sources.csv` next to them, with one row per file: source, geography selected, level, date range, search terms and settings. **No data values changed.**
- **Why:** Gina asked for the files to be in the raw data folder, labelled with their source (Google Trends), date range and geography. The files themselves contain no metadata, so the geography is only in the file name.
- **Input:** `~/Desktop/MDE/dataviz/trends-heat-search/*.csv` (16 files, downloaded by Gina from Google Trends on 2026-09-27)
- **Script:** `scripts/google-trends/01_sources_table.py` (writes `trends_sources.csv`); the files were copied with `cp -p` and checked byte-for-byte against the originals (16/16 identical).
- **Rows in → out:** 16 files, each 129 months (2016-01 to 2026-09) × 5 terms ("air conditioner", "cooling center", "fan", "AC", "cooling fan") → 16 files unchanged + a 16-row sources table.
  - **US states (6):** Arizona, California, Alaska, Michigan, Oregon, Texas
  - **Metro areas (3):** Fresno-Visalia CA; Harlingen-Weslaco-Brownsville-McAllen TX; San Francisco-Oakland-San Jose CA
  - **Cities, per Gina (7):** Bakersfield CA, Detroit MI, Eugene OR, Fairbanks AK, Los Angeles CA, Phoenix AZ, San Diego CA
- **Output:** `data/raw/google-trends/heat-search/` (16 CSVs + `trends_sources.csv`; a 17th file, Boston, added in Step 2); 19 rows added to `data/descriptions/data_descriptions.csv`
- **Settings (from Gina):** search terms (not topics), All categories, Web Search, downloaded 2026-09-27.
- **Judgment calls:**
  - **Metadata in a companion file, not inside the CSVs**, because Rule 2 says raw files are never edited and title rows would break the CSV format. Gina had asked for "a page in the csv or a title". **Claude's proposal; Gina did not object.**
  - **Folder `data/raw/google-trends/heat-search/`**, leaving room for other Trends downloads (e.g. `trends-air`). **Claude's choice, flagged to Gina in chat.**
  - **The 7 city-named files are recorded as cities, per Gina.** Claude had expected them to be metro areas and couldn't confirm from Google's help pages which levels the "interest over time" view offers. **Specified by Gina; level not independently verified.**
- **Caveats for the appendix:**
  - **Values are relative (0–100), scaled within each file**, not search counts, and not comparable across files. Google normalizes each point by total searches in that geography and time range, then scales 0–100 (Google Trends Help FAQ, https://support.google.com/trends/answer/4365533).
  - **2026-09 is a partial month.**
  - **"fan" and "AC" are ambiguous terms** (e.g. sports fans, other meanings of AC).
  - **"cooling center" is mostly 0** (too little search volume).

### Step 15 · descriptions · 2026-09-27 14:35 EDT · Gina + Claude
- **What:** Added a **key terms** section at the top of `data/descriptions/data_descriptions.csv`: 21 rows with `file` = "KEY TERM", one per term (PM2.5, reference monitor, low-cost sensor, AirNow, sensor, location, site, city limits, city center, fallback sensor, study period, sensor-day, valid day, flag, negative values, low-cost outlier rule, counted sensor-day, site-day, city daily mean, overall city daily mean, min / max). Each has a plain definition, units, source (with links), formula where relevant, and pointers to the detailed rows, steps and decisions. **Documentation only: no data changed.**
- **Why:** Gina asked where reference vs low-cost is defined. The definition existed, but only under the raw field `isMonitor`, and other key terms were spread across rows and log entries.
- **Script:** none (documentation, written by Claude).
- **Judgment calls:** Key terms placed as rows at the top of the same CSV (not a separate file), so the definitions file stays one document. **Claude's choice, flagged to Gina in chat.**
- **Sources checked after writing:**
  - The AirNow definition (preliminary data, validated data in EPA's AQS) was checked against AirNow's "About the Data" page (https://www.airnow.gov/about-the-data/) and the link added.
  - The first version of "low-cost sensor" said these sensors "can read high, especially in humid air"; this is widely reported but was not sourced here, so Claude removed it. It can be restored with a citation (e.g. EPA material on low-cost sensor corrections) if the appendix needs it.

### Step 14 · descriptions · 2026-09-27 14:21 EDT · Gina + Claude
- **What:** Added the Step 5 audit files and coverage summary to `data/descriptions/data_descriptions.csv`, each with description, units, source and formula. **Documentation only: no data changed.**
  - `audit/sensor_day_audit_<city>.csv`: 1 file row + 16 columns
  - `audit/site_daily_<city>.csv`: 1 + 7
  - `pm25_city_coverage_summary.csv`: 1 + 6 (first_day and last_day in one row)
- **Why:** Gina asked for the audit files to be in the definitions document too. The coverage summary was added with them, since it was the other Step 5 file not yet described. **Claude's choice, flagged to Gina in chat.**
- **Script:** none (documentation). Checked that the columns described match each file's header exactly.

### Step 13 · descriptions · 2026-09-27 14:20 EDT · Gina + Claude
- **What:** Added the columns of the final daily city files (`data/processed/openaq/step05_averages/pm25_<city>_daily.csv`) to `data/descriptions/data_descriptions.csv`: 1 file row + 18 column rows, each with description, units, source and formula. **Documentation only: no data changed.**
- **Why:** Gina asked for the definitions document to cover the daily results, not only raw files.
- **Script:** none (documentation, written by Claude). Checked that the 18 columns described match the file header exactly.
- **Judgment calls:**
  - **The descriptions file now covers this processed file as well as raw files.** Its `file` column gives the path under `data/` (`processed/...`) to tell them apart. **Changed by Gina** (Step 10 had scoped it to raw files).
  - **Audit and coverage files** were added in Step 14.

### Step 5 · OpenAQ · 2026-09-27 14:17 EDT · Gina + Claude
- **What:** Built **daily PM2.5 averages per city**: reference, low-cost and overall. Each is built from site averages, with the min and max across sites, the number of sites, and the site and sensor IDs used each day. Every sensor-day is recorded in an audit file as included or excluded, with the reason.
- **Why:** Gina needs one value per city per day that combines all the sites and sensors measuring in the city, fully traceable.
- **Input:** `data/processed/openaq/step04_daily/openaq_pm25_<city>_daily_sensors.csv`; site IDs from Step 3
- **Script:** `scripts/openaq/05_site_and_city_averages.py` (local files only; no API calls)
- **Order of operations** (OA-D3, OA-D5, OA-D6, OA-D7):
  1. sensor-day valid if ≥ 18 h
  2. negatives set to 0
  3. flagged low-cost days removed
  4. low-cost outlier rule
  5. site-day = mean of the site's included sensor-days
  6. city-day per type = mean / min / max across site-days
  7. overall mean = mean of the reference and low-cost means (one type only → that type); overall min / max / sites = across all site-days
- **Rows in → out:** **466,458 sensor-days → 387,270 included**. Excluded:

  | Reason | Sensor-days |
  |---|---|
  | Fewer than 18 hours observed | 78,622 |
  | Low-cost day flagged by OpenAQ | 269 |
  | No value | 255 |
  | Low-cost outlier, rule "ref+peer" | 35 |
  | Low-cost outlier, rule "peer" | 1 |
  | Above 1,000 µg/m³ | 6 |

  Negative daily values set to 0: 26. Most extreme low-cost days were removed by the flag rule (OA-D7) before the outlier rule (OA-D6) ran, so OA-D6 removed 42 days, not the ~140 estimated beforehand.

  **About the 78,622 short days** (fewer than 18 of 24 hours; the threshold is EPA's standard for a valid 24-hour PM2.5 average, 40 CFR Part 50 Appendix N §3.0(c), see Decision OA-D3):
  - **Both types lose days at about the same rate:** 16,618 of 101,883 reference sensor-days (16%) and 62,004 of 364,575 low-cost sensor-days (17%). Routine data loss, not a problem with one type.
  - **Most are near misses:** 48,609 had 12–17 hours, 22,471 had 6–11, and 7,542 had 0–5. Likely causes are partial-day outages, maintenance or calibration hours, power or connection drops, and a sensor's first or last day. The cause is not recorded in the data.
  - **Most are in Los Angeles** (47,683), which has by far the most sensors (276 used), then Phoenix 7,055, San Francisco 6,033 and Detroit 3,344.
  - **A short day loses one sensor's reading, not usually the city's day.** Where a city has several sites, the others still give that day's value. A city-day is blank only when no site has a valid sensor-day.
  - **Trade-off, if the threshold is revisited:** 12 hours would bring back ~48,600 sensor-days, but daily values would then rest on half a day and could miss a smoky afternoon (cf. Springfield 2020-09-12). Kept at 18 (OA-D3).
- **Days with data per city** (of 3,856; reference / low-cost / overall; days with both types):

  | City | Reference | Low-cost | Overall | Both |
  |---|---|---|---|---|
  | Ann Arbor | 3,043 | 752 | 3,049 | 746 |
  | Bakersfield | 2,949 | 176 | 2,954 | 171 |
  | Boston | 2,656 | 922 | 2,663 | 915 |
  | Brownsville | 1,147 | 12 | 1,150 | 9 |
  | Delano | 0 | 502 | 502 | 0 |
  | Detroit | 3,042 | 440 | 3,043 | 439 |
  | Eugene | 3,203 | 0 | 3,203 | 0 |
  | Fairbanks | 2,907 | 0 | 2,907 | 0 |
  | Fresno | 3,009 | 824 | 3,016 | 817 |
  | Los Angeles | 3,031 | 1,586 | 3,051 | 1,566 |
  | Phoenix | 3,070 | 911 | 3,076 | 905 |
  | Raymondville | 0 | 0 | 0 | 0 |
  | San Diego | 2,428 | 859 | 2,429 | 858 |
  | San Francisco | 2,729 | 1,649 | 2,947 | 1,431 |
  | Springfield | 2,926 | 0 | 2,926 | 0 |
  | Warren | 0 | 924 | 924 | 0 |
- **Output:** `data/processed/openaq/step05_averages/`
  - **`pm25_<city>_daily.csv`** (16 files, 3,856 rows each; days without data are blank): date; for reference (`ref_`) and low-cost (`lowcost_`): mean, min, max, n_sites, site_ids, sensor_ids; then all_mean, all_mean_basis, all_min, all_max, all_n_sites
  - `pm25_city_coverage_summary.csv`: per city and average, days with data, share of study days, first/last day, sites used. **Coverage only, no whole-period averages** (changed by Gina).
  - `audit/sensor_day_audit_<city>.csv`: every sensor-day, with raw value, value used, negative_set_to_zero, hours, flag, included, exclusion_reason, and for low-cost the rule applied, the reference average and the peer median it was compared to
  - `audit/site_daily_<city>.csv`: every site-day, with site mean, n_sensors and sensor IDs
- **Checks:**
  - Every city file has 3,856 rows. Sensor-day totals match Step 4 (466,458).
  - **Trace example:** Springfield 2020-09-12 → ref_mean 105.0 from 1 site (S1857) = 1 sensor (3278), 18 h.
  - Largest values after the rules: reference 468 (Eugene), low-cost 289 (Warren, 2026-07-16 event). No city value above 500.
- **Judgment calls:**
  - **Days with no data kept as blank rows.** **Claude's choice, approved by Gina.**
  - **The low-cost outlier test compares against the mean of reference *sensor*-days,** not site-days, as OA-D6 is worded. **Claude's choice, approved by Gina.**
  - **No whole-period averages in the summary.** **Changed by Gina** (she needs daily values per city; Claude had proposed period, yearly and shared-period means).
- **For review:**
  - **Springfield 2020-09-10 to 09-14 (wildfire smoke).** Springfield's only reference monitor read 105 on 09-12 (hourly 48–220) while Eugene's three monitors read 372–542 (hourly 156–742), 5 km away. Its 09-13 and 09-14 days have 6 and 16 hours (invalid). It could be a real local dip or an instrument problem at extreme levels. **Open item for Gina.**
  - **Overall average composition changes over time:** reference only until low-cost sensors appear (2021–2025 depending on city), mixed after. The column `all_mean_basis` records which, day by day.
  - **Files:** `sensor_day_audit_losangeles.csv` is 29 MB and `site_daily_losangeles.csv` 14 MB (below GitHub's 50 MB warning).

### Decision OA-D7 · OpenAQ · 2026-09-27 14:12 EDT · Gina
- **What:** How OpenAQ-flagged days are treated in Step 5.
  - **Reference sensor-days with `hasFlags = true` are kept.** The flagged hour (negative) is already excluded from OpenAQ's daily value (Step 5a); the rest of the day is valid. Dropping them would remove 9,009 mostly clean-air days and bias reference averages upward.
  - **Low-cost sensor-days with `hasFlags = true` are removed.** The flagged hour is above 1,000 µg/m³ and is still inside OpenAQ's daily value (Step 5a), a sign of malfunction. This affects 523 valid sensor-days (0.2% of valid low-cost sensor-days), overlapping with OA-D6.
- **Who:** **Claude's recommendation, approved by Gina.**
- **Order in Step 5:** valid-day check (≥ 18 h) → negatives set to 0 (OA-D5) → flagged low-cost removed (OA-D7) → outlier rule (OA-D6, using only sensor-days still included) → site average → city averages.

### Step 5a · OpenAQ · 2026-09-27 14:08 EDT · Gina + Claude
- **What:** Read-only audit of what OpenAQ's `hasFlags` means. Downloaded all flags for the 95 kept sensors with at least one flagged day, counted flag types, and checked 2 flagged days hour by hour against the daily value. **Nothing removed or changed.**
- **Why:** 10.6% of valid reference sensor-days are flagged (Step 4); Gina asked to understand what that means before deciding whether flagged days count.
- **Input:** `data/processed/openaq/step04_daily/`; OpenAQ API v3 `/v3/sensors/{id}/flags` and, for the 2 checks, `/v3/sensors/{id}/measurements`
- **Script:** `scripts/openaq/05a_flags_audit.py`. The 2 hour-by-hour checks were run as one-off commands in chat, not saved as a script; their results are below.
- **Rows in → out:** 95 sensors → **55,531 flags** (16,470 reference, 39,061 low-cost). Valid flagged sensor-days: **9,009 reference, 523 low-cost**.
- **Output:** raw `data/raw/openaq/flags_json/sensor_<id>_flags.json` (95); `data/processed/openaq/step05a_flags/flags_list.csv`, `flag_types_summary.csv`; 5 description rows added and the `hasFlags` description updated.
- **Findings:**
  - **Every flag is "Limits exceeded" (level ERROR)**, one flag per hour.
  - **Reference:** all flags with values are **negative hours** (−0.1 to −10). **Low-cost:** all flags with values are hours **above 1,000 µg/m³** (1,000.32 to 7,242.94), or have the note "Added as part of ingestion". This implies OpenAQ treats 0–1,000 µg/m³ as the plausible hourly range; that is inferred from the notes, not stated in the docs.
  - **Check 1, reference sensor 890, 2016-08-17:** the flagged hour is blank in the hourly data; the daily value (3.23) equals the mean of the 10 remaining hours. `observedCount` is 11, so the blanked hour is still counted as observed.
  - **Check 2, low-cost sensor 13667130, 2025-12-09:** all 51 raw values that day are blank and flagged, but the daily value is still 5,330 µg/m³. OpenAQ did not recompute the daily value.
  - Flagged reference days have a median daily mean of 6.2 µg/m³; they are ordinary clean-air days with one or two slightly negative hours.
- **Correction:** Earlier in chat, Claude said OpenAQ "still included those hours in the daily mean". Check 1 shows that for reference monitors the flagged hour is **excluded**. The earlier statement was a Claude assumption, not checked at the time.
- **Judgment calls:** Only 2 days were checked hour by hour; the pattern is consistent with all 55,531 flag notes but not verified on every day. **Claude's choice, flagged to Gina in chat.**
- **Problem during the step:** The flags endpoint ignores `limit` and `page` and returns all flags every time (sensor 2436: 1,130 flags returned for page 1, 2 and 50). The first run treated a full page as "more pages to come" and looped on the 14th sensor for ~25 minutes. Claude stopped it, changed the script to one request per sensor (checked against `meta.found`), and reran, reusing the 13 files already saved (all under 1,000 flags, so complete).

### Decision OA-D6 · OpenAQ · 2026-09-27 14:03 EDT · Gina
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

### Decision OA-D5 · OpenAQ · 2026-09-27 14:03 EDT · Gina
- **What:** **Negative daily PM2.5 values are set to 0 µg/m³** before any site or city average is calculated. The raw files and Step 4 CSVs keep the original values, and the Step 5 audit file will show both.
- **Why:** 26 sensor-days in the study period have a negative daily mean (24 Fairbanks, 2 San Francisco). Physically, concentration can't be below 0.
- **Options:** Claude suggested keeping them as measured (small negatives are a known instrument quirk in very clean air); the alternatives were set to 0 or drop. **Changed by Gina: set to 0.**
- **Documentation:** noted in `data/descriptions/data_descriptions.csv` on the daily `value` field, at Gina's request.

### Step 4 · OpenAQ · 2026-09-27 13:29 EDT · Gina + Claude
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

### Decision OA-D4 · OpenAQ · 2026-09-27 12:44 EDT · Gina
- **What:** A fallback sensor must be **closer to its own city's limits than to any other study city's limits**; otherwise no city uses it. Step 3 was rerun with this rule; its outputs were overwritten and the Step 3 entry below is updated.
- **Why:** Step 3's traceability columns showed that 4 of Warren's fallback sensors were much closer to Detroit's limits than to Warren's. **Oak Park** (reference): 2.0 km from Detroit vs 8.1 km from Warren. **HFH CURES 6, 17, 18** (low-cost): 0.2–1.3 km vs 7.4–9.4 km. They measure air at Detroit's edge, not Warren's. (Measured from city hall, Oak Park is closer to Warren, 14.1 km vs 18.7 km, because Detroit's city hall is far south; the rule uses city limits.)
- **Options:** (a) keep the Step 2 rule, "nearest city that needs it"; (b) the stricter rule. **Changed by Gina: chose (b)**, as recommended by Claude.
- **These 4 sensors don't go to Detroit either.** Detroit has its own sensors of both types, and fallbacks are only for cities with none of that type. They're recorded as "fallback closer to another study city". **Claude's explanation, confirmed by Gina's question in chat; not separately approved.**
- **Effect:** Warren: reference 1 → **0** sites; low-cost 7 → **4** sites (Madison Heights, S Campbell Rd & E 3rd St, Royal Oak, Dodge Park & Utica). Ann Arbor unchanged (Ypsilanti has no other study city within 10 km). Totals: 560 → **556 sensors, 496 → 492 sites** (549 at 489 after the Step 3 correction). **Cities with no reference average: Warren, Delano, Raymondville.**

### Step 3 · OpenAQ · 2026-09-27 12:38 EDT · Gina + Claude
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

### Decision OA-D3 · OpenAQ · 2026-09-27 12:38 EDT · Gina
- **What:**
  1. **Fallback cap: 10 km beyond city limits.** Ann Arbor gets the Ypsilanti reference monitor (6.9 km). Warren gets Oak Park (reference, 8.1 km, from Dec 2024) and 7 low-cost sensors. **Claude's recommendation, approved by Gina** after seeing the Step 2 cap options.
  2. **US monitors only.** Canadian (Windsor) monitors are excluded. **Claude's recommendation, approved by Gina.**
  3. **Average by site, not by sensor.** Each day, the sensors at a site are averaged first, then the sites are averaged into the city value, so a site with several sensors counts once. **Claude's recommendation, approved by Gina.**
  4. **A sensor-day is valid with at least 18 of 24 hours.** This is EPA's completeness rule for a daily PM2.5 average: EPA, 40 CFR Part 50, Appendix N (Interpretation of the National Ambient Air Quality Standards for PM2.5), section 3.0(c): "A 24-hour average concentration shall be considered valid if at least 75 percent of the hourly averages (i.e., 18 hourly values) for the 24-hour period are available." https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-50/appendix-Appendix%20N%20to%20Part%2050 (text checked 2026-09-27 via https://www.law.cornell.edu/cfr/text/40/appendix-N_to_part_50). **Claude's recommendation, approved by Gina.**
  5. **Three city averages** (reference, low-cost, overall), each with the mean, min and max across sites, the number of sites and the site IDs used. **Specified by Gina.** "Overall" = the mean of the reference average and the low-cost average (each type weighted 50%); on days with only one type, overall = that type. **Changed by Gina** (chose option b from Claude's two options).
- **Still open:** min/max are the lowest and highest site value of the day (spread across the city). OpenAQ's within-day hourly min/max will also be kept in the raw daily files. **Claude's choice, not yet approved.**

### Step 2 · OpenAQ · 2026-09-27 12:05 EDT · Gina + Claude
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

### Step 12 · descriptions · 2026-09-27 11:06 EDT · Gina + Claude
- **What:** Added OpenAQ's own definitions of reference-grade monitors and low-cost sensors to the `isMonitor` row of `data/descriptions/data_descriptions.csv`, and examples of each type to the `instruments[].name` row. **Documentation only: no data changed.**
- **Why:** Gina asked for the difference between the two sensor types, from the API/OpenAQ documentation, to be in the definitions document.
- **Input:**
  - OpenAQ Docs, Instruments (https://docs.openaq.org/resources/instruments): the field shows whether the device is used for official monitoring.
  - OpenAQ Explorer, Getting started (https://explore.openaq.org/getting-started): reference-grade monitors are the "gold standard", typically run by government agencies for regulatory purposes; air sensors are less sophisticated but small, portable and affordable, used to fill gaps. Both accessed 2026-09-27.
- **Script:** none (documentation, edited by Claude)
- **Rows in → out:** 2 of 67 description rows changed.
- **Output:** `data/descriptions/data_descriptions.csv`
- **Judgment calls:** OpenAQ's wording paraphrased, with the source pages cited. **Claude's choice, approved by Gina.**

### Decision OA-D2 · OpenAQ · 2026-09-27 11:06 EDT · Gina
- **What:**
  1. **The PM2.5 series starts on 2016-03-06**, the first date with OpenAQ data at any sensor (Step 1), instead of 2016-01-01. **Changed by Gina** (chose this from Claude's three options; the others were filling Jan–Feb 2016 from EPA's archive, or asking Dish to move her start date).
  2. **Three city averages planned:** reference sensors only, low-cost sensors only, and all sensors. **Specified by Gina.** How the "all sensors" average is weighted is still open (see the Step 1 counts: e.g. Los Angeles has 13 reference vs 269 low-cost sensors).
  3. **The fallback distance cap will be chosen after Step 2**, once its output shows what each cap would keep. **Specified by Gina.**
- **Consequence:** the OpenAQ PM2.5 series is 2 months shorter than Dish's METAR visibility series (2016-01-01 – 2026-09-25). Comparisons between the two should use the shared period.

### Step 1 · OpenAQ · 2026-09-27 10:58 EDT · Gina + Claude
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

### Decision OA-D1 · OpenAQ · 2026-09-27 10:58 EDT · Gina
- **What:** Set the approach for the OpenAQ PM2.5 data before any data was pulled.
  1. **Cities:** the 15 Gina listed plus **Boston** (added by Gina).
  2. **Proximity:** sensors inside **city limits**. Where a city has none, fall back to the **nearest sensors outside its limits that are not inside another listed city**, and log it. A sensor belongs to one city only. **Claude's recommendation, approved by Gina.**
  3. **Sensor types:** download both reference and low-cost sensors, flag them in the inventory, and decide what goes into the city averages later. **Claude's recommendation, approved by Gina.**
  4. **Time resolution: daily** (OpenAQ 24-hour summaries), not hourly. **Changed by Gina** (chose daily from Claude's options).
  5. **Study period ends 2026-09-25**, matching Dish's Decision D1. **Changed by Gina** (from "most recent date in September 2026").
  6. **File layout:** one sensor inventory for all cities, plus one daily file per city; raw API responses saved as received. **Claude's recommendation, approved by Gina.**
- **Open for Step 2:** how far the fallback may reach (Claude suggested a 10–15 km cap beyond city limits, with "no local sensor" beyond that).

### Step 11 · descriptions · 2026-09-27 10:12 EDT · Gina + Claude
- **What:** Changed the data descriptions from Markdown to CSV. Each table row from `data_descriptions.md` became a CSV row, with the file name in its own column; the Markdown file was removed. Wording unchanged.
- **Why:** Gina asked for a CSV instead.
- **Input:** `data/descriptions/data_descriptions.md` (Step 10)
- **Script:** none (one-off format conversion by Claude)
- **Rows in → out:** 37 descriptions → 37 CSV rows. Checked again that the columns listed match each raw file's header exactly.
- **Output:** `data/descriptions/data_descriptions.csv` (columns: file, column, description, type_units, source, formula_or_derivation). Blank cells = no formula (shown as "—" in the Markdown).
- **Judgment calls:**
  - **CSV replaces the Markdown**, rather than keeping both. **Changed by Gina.**
  - **The Markdown file's intro text was not carried over.** It said the file covers Gina's raw files only and is updated with every new raw file; both points are recorded in Step 10. **Claude's choice, flagged to Gina in chat; not yet approved.**

### Step 10 · descriptions · 2026-09-27 10:09 EDT · Gina + Claude
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

### Step 9 · city-selection · 2026-09-27 10:00 EDT · Gina + Claude
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
- **Time:** 2026-09-27, in chat between 09:28 and 09:47 EDT (no file at the time). Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
- **Time:** ran 2026-09-27, workbook written 09:28 EDT; pushed to the repo 09:47 EDT. Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
- **Time:** ran 2026-09-26/27, output file written 2026-09-27 00:19 EDT. Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
- **Time:** done by Gina 2026-09-26: CSV saved 22:11 EDT, Numbers file 22:15 EDT. Logged retroactively 2026-09-27 10:00 EDT (Step 9).
- **What:** Gina combined the ALA ranks (Step 1) with the state-level Media Cloud results (Step 3) in one table, one row per metro area and state: metro, city_1–3, state, ALA short-term and year-round PM2.5 rank, then all Step 3 columns. The Pittsburgh-Weirton-Steubenville metro has 3 rows (PA, OH, WV). Done by Gina in Numbers, without Claude.
- **Why:** Puts pollution rank and state coverage side by side for each metro.
- **Input:** ALA rankings (Step 1), `mediacloud_air_pollution_by_state.csv` (Step 3)
- **Script:** none (manual, in Numbers)
- **Rows in → out:** 15 metros + 10 states → 17 rows.
- **Output:** `data/processed/city-selection/step05_ala_cross_gina/air_pollution_cities_by_state.csv` (22:11 version) and `news_coverage_by_state_cross_pm.numbers` (22:15 version, columns renamed, e.g. `ala_shortterm_pm25_rank_2026`)
- **Judgment calls:** Gina's own (column layout, one row per state for the multi-state metro).

### Step 4 · city-selection · 2026-09-26 · Gina + Claude
- **Time:** ran 2026-09-26, time not recorded (local output file no longer exists). Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
- **Time:** ran 2026-09-26, output file written 21:59 EDT. Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
- **Time:** ran 2026-09-26, time not recorded (before Step 3). Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
- **Time:** ran 2026-09-26, time not recorded (before Step 2). Logged retroactively 2026-09-27 10:00 EDT (Step 9).
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
