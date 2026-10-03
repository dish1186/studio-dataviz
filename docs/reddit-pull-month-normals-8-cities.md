# Reddit pull: month normals for the other 7 cities

*Dish is doing these pulls. Written 2026-10-03 by Dish + Claude. Updated the same day: Yakima dropped (its event week has fewer than 100 posts + comments), so it isn't pulled.*

## Why

- **We chose the month normal** (Normals Step 2, Eugene decides; see `data/processed/reddit/normals_02_compare/decision.md`).
  - Each city's normal is the same calendar month as its event, in every year from 2019 to 2025.
- **Eugene and Bakersfield are already done.** This covers the other 7 cities: 7 pulls each, plus 2 event-week re-pulls (Detroit, Pittsburgh). That is 51 pulls, posts and comments each, so **102 files**. Yakima is dropped.
- **Don't look at event-week posts** (inside the month pulls, or the old `event_weeks_no_usernames/` folder) until every normal is in and the analysis script is committed. That way, nothing we see can shape the rules.

## How (same as last time)

- **Same download tool** (Arctic Shift), posts AND comments for every row.
- **Type the dates exactly as written.** They include the extra day on each side for time zones, and they work for Alaska and Eastern time too.
- **Save** in `~/Downloads/<city>/`, the same as Gina's last pull. Then run the check-and-strip step into `data/processed/reddit/normals_no_usernames/<city>/`. That step is Gina's `scripts/reddit/normals_01_check_and_strip_usernames.py`, and it needs these cities and dates added to its `PLAN` (Claude can do that).
- **Why the dates look odd:** a week belongs to the month of its Thursday, so "June" can start in late May or end in early July.
- **Pull every row, even ones that look like they'll be thrown out.** Some weeks get dropped later by the script, so it's on the record:
  - the event week
  - fireworks weeks (most July pulls, plus some late-June and early-July weeks)
  - bad-air weeks
- **Write down** any download that looks empty or tiny compared with the others.

## Two extra pulls: Detroit and Pittsburgh event weeks (added 2026-10-03)

**Why:** the event-week files in `event_weeks_no_usernames/` were downloaded as UTC days (Monday 00:00 → Sunday 23:59 UTC). Our weeks run in each city's **local** time, so those files cut off Sunday evening and include part of the Sunday before.

- **6 cities don't need a re-pull.** Their event week is already inside one of the month pulls below, with the right padding.
- **Detroit and Pittsburgh need a re-pull,** because their events are in 2026, outside the 2019–2025 month pulls.

| City | Subreddit | Event week (Mon → Sun, local) | Download from | Download to | Save as |
|---|---|---|---|---|---|
| Detroit | r/Detroit | 2026-07-13 → 2026-07-19 | 2026-07-12 | 2026-07-21 | `detroit_event_2026-07-13_posts.jsonl` / `_comments.jsonl` |
| Pittsburgh | r/pittsburgh | 2026-07-13 → 2026-07-19 | 2026-07-12 | 2026-07-21 | `pittsburgh_event_2026-07-13_posts.jsonl` / `_comments.jsonl` |

Save these with the month pulls (same folders). The old `event_weeks_no_usernames/` files won't be used.

## What to pull

### Fairbanks · r/Fairbanks · normal = every June, 2019–2025 · event week Mon 2022-06-27

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-06-03 → 2019-06-30 | 2019-06-02 | 2019-07-02 | `fairbanks_month_2019-06-03_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-06-01 → 2020-06-28 | 2020-05-31 | 2020-06-30 | `fairbanks_month_2020-06-01_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-05-31 → 2021-06-27 | 2021-05-30 | 2021-06-29 | `fairbanks_month_2021-05-31_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-05-30 → 2022-07-03 | 2022-05-29 | 2022-07-05 | `fairbanks_month_2022-05-30_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-05-29 → 2023-07-02 | 2023-05-28 | 2023-07-04 | `fairbanks_month_2023-05-29_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-06-03 → 2024-06-30 | 2024-06-02 | 2024-07-02 | `fairbanks_month_2024-06-03_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-06-02 → 2025-06-29 | 2025-06-01 | 2025-07-01 | `fairbanks_month_2025-06-02_posts.jsonl` / `_comments.jsonl` |

### Fresno · r/fresno · normal = every August, 2019–2025 · event week Mon 2020-08-17

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-07-29 → 2019-09-01 | 2019-07-28 | 2019-09-03 | `fresno_month_2019-07-29_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-08-03 → 2020-08-30 | 2020-08-02 | 2020-09-01 | `fresno_month_2020-08-03_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-08-02 → 2021-08-29 | 2021-08-01 | 2021-08-31 | `fresno_month_2021-08-02_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-08-01 → 2022-08-28 | 2022-07-31 | 2022-08-30 | `fresno_month_2022-08-01_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-07-31 → 2023-09-03 | 2023-07-30 | 2023-09-05 | `fresno_month_2023-07-31_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-07-29 → 2024-09-01 | 2024-07-28 | 2024-09-03 | `fresno_month_2024-07-29_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-08-04 → 2025-08-31 | 2025-08-03 | 2025-09-02 | `fresno_month_2025-08-04_posts.jsonl` / `_comments.jsonl` |

### Detroit · r/Detroit · normal = every July, 2019–2025 · event week Mon 2026-07-13

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-07-01 → 2019-07-28 | 2019-06-30 | 2019-07-30 | `detroit_month_2019-07-01_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-06-29 → 2020-08-02 | 2020-06-28 | 2020-08-04 | `detroit_month_2020-06-29_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-06-28 → 2021-08-01 | 2021-06-27 | 2021-08-03 | `detroit_month_2021-06-28_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-07-04 → 2022-07-31 | 2022-07-03 | 2022-08-02 | `detroit_month_2022-07-04_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-07-03 → 2023-07-30 | 2023-07-02 | 2023-08-01 | `detroit_month_2023-07-03_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-07-01 → 2024-07-28 | 2024-06-30 | 2024-07-30 | `detroit_month_2024-07-01_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-06-30 → 2025-08-03 | 2025-06-29 | 2025-08-05 | `detroit_month_2025-06-30_posts.jsonl` / `_comments.jsonl` |

### Seattle · r/Seattle · normal = every September, 2019–2025 · event week Mon 2020-09-07

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-09-02 → 2019-09-29 | 2019-09-01 | 2019-10-01 | `seattle_month_2019-09-02_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-08-31 → 2020-09-27 | 2020-08-30 | 2020-09-29 | `seattle_month_2020-08-31_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-08-30 → 2021-10-03 | 2021-08-29 | 2021-10-05 | `seattle_month_2021-08-30_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-08-29 → 2022-10-02 | 2022-08-28 | 2022-10-04 | `seattle_month_2022-08-29_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-09-04 → 2023-10-01 | 2023-09-03 | 2023-10-03 | `seattle_month_2023-09-04_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-09-02 → 2024-09-29 | 2024-09-01 | 2024-10-01 | `seattle_month_2024-09-02_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-09-01 → 2025-09-28 | 2025-08-31 | 2025-09-30 | `seattle_month_2025-09-01_posts.jsonl` / `_comments.jsonl` |

### Indianapolis · r/indianapolis · normal = every June, 2019–2025 · event week Mon 2023-06-26

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-06-03 → 2019-06-30 | 2019-06-02 | 2019-07-02 | `indianapolis_month_2019-06-03_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-06-01 → 2020-06-28 | 2020-05-31 | 2020-06-30 | `indianapolis_month_2020-06-01_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-05-31 → 2021-06-27 | 2021-05-30 | 2021-06-29 | `indianapolis_month_2021-05-31_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-05-30 → 2022-07-03 | 2022-05-29 | 2022-07-05 | `indianapolis_month_2022-05-30_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-05-29 → 2023-07-02 | 2023-05-28 | 2023-07-04 | `indianapolis_month_2023-05-29_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-06-03 → 2024-06-30 | 2024-06-02 | 2024-07-02 | `indianapolis_month_2024-06-03_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-06-02 → 2025-06-29 | 2025-06-01 | 2025-07-01 | `indianapolis_month_2025-06-02_posts.jsonl` / `_comments.jsonl` |

### Pittsburgh · r/pittsburgh · normal = every July, 2019–2025 · event week Mon 2026-07-13

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-07-01 → 2019-07-28 | 2019-06-30 | 2019-07-30 | `pittsburgh_month_2019-07-01_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-06-29 → 2020-08-02 | 2020-06-28 | 2020-08-04 | `pittsburgh_month_2020-06-29_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-06-28 → 2021-08-01 | 2021-06-27 | 2021-08-03 | `pittsburgh_month_2021-06-28_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-07-04 → 2022-07-31 | 2022-07-03 | 2022-08-02 | `pittsburgh_month_2022-07-04_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-07-03 → 2023-07-30 | 2023-07-02 | 2023-08-01 | `pittsburgh_month_2023-07-03_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-07-01 → 2024-07-28 | 2024-06-30 | 2024-07-30 | `pittsburgh_month_2024-07-01_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-06-30 → 2025-08-03 | 2025-06-29 | 2025-08-05 | `pittsburgh_month_2025-06-30_posts.jsonl` / `_comments.jsonl` |

### San Jose · r/SanJose · normal = every August, 2019–2025 · event week Mon 2020-08-17

| Year | Weeks covered (Mon → Sun) | Download from | Download to | Save as |
|---|---|---|---|---|
| 2019 | 2019-07-29 → 2019-09-01 | 2019-07-28 | 2019-09-03 | `sanjose_month_2019-07-29_posts.jsonl` / `_comments.jsonl` |
| 2020 | 2020-08-03 → 2020-08-30 | 2020-08-02 | 2020-09-01 | `sanjose_month_2020-08-03_posts.jsonl` / `_comments.jsonl` |
| 2021 | 2021-08-02 → 2021-08-29 | 2021-08-01 | 2021-08-31 | `sanjose_month_2021-08-02_posts.jsonl` / `_comments.jsonl` |
| 2022 | 2022-08-01 → 2022-08-28 | 2022-07-31 | 2022-08-30 | `sanjose_month_2022-08-01_posts.jsonl` / `_comments.jsonl` |
| 2023 | 2023-07-31 → 2023-09-03 | 2023-07-30 | 2023-09-05 | `sanjose_month_2023-07-31_posts.jsonl` / `_comments.jsonl` |
| 2024 | 2024-07-29 → 2024-09-01 | 2024-07-28 | 2024-09-03 | `sanjose_month_2024-07-29_posts.jsonl` / `_comments.jsonl` |
| 2025 | 2025-08-04 → 2025-08-31 | 2025-08-03 | 2025-09-02 | `sanjose_month_2025-08-04_posts.jsonl` / `_comments.jsonl` |

