# Reddit pull for tomorrow: Eugene and Bakersfield

*For Gina. Written 2026-10-02 by Dish + Claude. Goal: pull enough Reddit data for two cities to decide which "normal" to use for the Reddit baseline.*

## Why these two cities

Eugene and Bakersfield are our "crossed" pair:

- **Eugene** almost never has bad air. Its median is 0 bad days a year.
- **Bakersfield** has bad air all the time. Its median is 12 bad days a year.

If one normal works well for both, it should work for everyone.

## The two normals we're comparing

- **Neighbor normal:** the weeks right around the event, in the same year: 6 weeks before and 6 weeks after.
- **Month normal:** the same month in every other year, 2019–2025: every September for Eugene, every December for Bakersfield.

## What to pull

- **Use the same download tool as before** (Arctic Shift).
- **Pull posts AND comments** for every row below.
- **Type the "download from" and "download to" dates exactly as written.** They already include the extra day on each side for the time zone, same as `00_download_plan.py`.
- **Save everything in `data/raw/reddit/arctic-shift/`** with the names below.
- **Don't delete or replace** the older Eugene/Bakersfield files already in that folder. These new names don't clash with them.

### Eugene · r/Eugene · event week Mon Sep 7 – Sun Sep 13, 2020

| Normal | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| Neighbor | 2020-07-27 → 2020-10-25 | 2020-07-26 | 2020-10-27 | `eugene_neighbor_2020-07-27_posts.jsonl` / `_comments.jsonl` |
| Month 2019 | 2019-09-02 → 2019-09-29 | 2019-09-01 | 2019-10-01 | `eugene_month_2019-09-02_posts.jsonl` / `_comments.jsonl` |
| Month 2020 | 2020-08-31 → 2020-09-27 | 2020-08-30 | 2020-09-29 | `eugene_month_2020-08-31_posts.jsonl` / `_comments.jsonl` |
| Month 2021 | 2021-08-30 → 2021-10-03 | 2021-08-29 | 2021-10-05 | `eugene_month_2021-08-30_posts.jsonl` / `_comments.jsonl` |
| Month 2022 | 2022-08-29 → 2022-10-02 | 2022-08-28 | 2022-10-04 | `eugene_month_2022-08-29_posts.jsonl` / `_comments.jsonl` |
| Month 2023 | 2023-09-04 → 2023-10-01 | 2023-09-03 | 2023-10-03 | `eugene_month_2023-09-04_posts.jsonl` / `_comments.jsonl` |
| Month 2024 | 2024-09-02 → 2024-09-29 | 2024-09-01 | 2024-10-01 | `eugene_month_2024-09-02_posts.jsonl` / `_comments.jsonl` |
| Month 2025 | 2025-09-01 → 2025-09-28 | 2025-08-31 | 2025-09-30 | `eugene_month_2025-09-01_posts.jsonl` / `_comments.jsonl` |

### Bakersfield · r/bakersfield · event week Mon Dec 2 – Sun Dec 8, 2024

| Normal | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| Neighbor | 2024-10-21 → 2025-01-19 | 2024-10-20 | 2025-01-21 | `bakersfield_neighbor_2024-10-21_posts.jsonl` / `_comments.jsonl` |
| Month 2019 | 2019-12-02 → 2019-12-29 | 2019-12-01 | 2019-12-31 | `bakersfield_month_2019-12-02_posts.jsonl` / `_comments.jsonl` |
| Month 2020 | 2020-11-30 → 2021-01-03 | 2020-11-29 | 2021-01-05 | `bakersfield_month_2020-11-30_posts.jsonl` / `_comments.jsonl` |
| Month 2021 | 2021-11-29 → 2022-01-02 | 2021-11-28 | 2022-01-04 | `bakersfield_month_2021-11-29_posts.jsonl` / `_comments.jsonl` |
| Month 2022 | 2022-11-28 → 2023-01-01 | 2022-11-27 | 2023-01-03 | `bakersfield_month_2022-11-28_posts.jsonl` / `_comments.jsonl` |
| Month 2023 | 2023-12-04 → 2023-12-31 | 2023-12-03 | 2024-01-02 | `bakersfield_month_2023-12-04_posts.jsonl` / `_comments.jsonl` |
| Month 2024 | 2024-12-02 → 2024-12-29 | 2024-12-01 | 2024-12-31 | `bakersfield_month_2024-12-02_posts.jsonl` / `_comments.jsonl` |
| Month 2025 | 2025-12-01 → 2025-12-28 | 2025-11-30 | 2025-12-30 | `bakersfield_month_2025-12-01_posts.jsonl` / `_comments.jsonl` |

That's 16 downloads per city: 8 rows, each with posts and comments.

### Why the month dates look odd

- A week belongs to the month that holds most of its days, which is the month of its Thursday. So "September" can start in late August or end in early October.
- The event week is inside the Month 2020 pull for Eugene and the Month 2024 pull for Bakersfield. That's on purpose: it gets dropped later, not at download time.
- Some weeks get dropped later, too:
  - weeks with bad air (above 35.5)
  - fireworks weeks: Bakersfield's Christmas–New Year weeks in 2020–2023

  **Pull everything anyway.** Dropping happens in the script, so it's on the record.
- The Eugene neighbor and Month 2020 pulls overlap. That's fine, because duplicates are removed by id.

### Things to tell Dish

- If any download looks empty or tiny compared with the others, say so. It could be a gap in Arctic Shift.
- Write down the date you pulled each file.

## The one rule for comparing the normals

**Choose the normal without looking at the event week.**

We judge each normal only on its own weeks:

- how many weeks it has
- how steady the weekly air-talk share is from week to week
- how steady the subreddit's size is
- for the neighbor normal, whether the weeks before and after differ a lot

**Don't calculate the Reddit rise (event week vs. normal) until we've picked.** Otherwise we could end up picking the normal that gives the answer we want. We'll write these comparison rules down before Gina's files are opened.

## All 10 study cities (for later; only Eugene and Bakersfield tomorrow)

| City | Subreddit | Event week (Mon–Sun) | Week avg PM2.5 (µg/m³) | Event | PM2.5 file (`data/processed/openaq/step05_averages/`) |
|---|---|---|---|---|---|
| Bakersfield | r/bakersfield | 2024-12-02 → 12-08 | 55.47 | Winter inversion | `pm25_bakersfield_daily.csv` |
| Fairbanks | r/Fairbanks | 2022-06-27 → 07-03 | 91.80 | Interior Alaska wildfires | `pm25_fairbanks_daily.csv` |
| Fresno | r/fresno | 2020-08-17 → 08-23 | 61.16 | August 2020 lightning fires | `pm25_fresno_daily.csv` |
| Yakima | r/Yakima | 2021-09-06 → 09-12 | 53.77 | Schneider Springs Fire | `pm25_yakima_daily.csv` |
| Detroit | r/Detroit | 2026-07-13 → 07-19 | 91.78 | Canadian (Ontario) wildfire smoke | `pm25_detroit_daily.csv` |
| Seattle | r/Seattle | 2020-09-07 → 09-13 | 51.46 | 2020 Labor Day fires | `pm25_seattle_daily.csv` |
| Indianapolis | r/indianapolis | 2023-06-26 → 07-02 | 55.09 | Canadian (Quebec) wildfire smoke | `pm25_indianapolis_daily.csv` |
| Eugene | r/Eugene | 2020-09-07 → 09-13 | 280.40 | 2020 Labor Day fires | `pm25_eugene_daily.csv` |
| Pittsburgh | r/pittsburgh | 2026-07-13 → 07-19 | 59.21 | Canadian (Ontario) wildfire smoke | `pm25_pittsburgh_daily.csv` |
| San Jose | r/SanJose | 2020-08-17 → 08-23 | 36.34 | SCU Lightning Complex | `pm25_sanjose_daily.csv` |

The event weeks come from `data/processed/openaq/step07_screening/city_screening.csv` (reference monitors).
