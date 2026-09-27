# Google Trends · air-quality searches (processed)

17 files, one per geography, named as the raw downloads in `data/raw/google-trends/air-search/`.
Monthly, January 2016 to September 2026 (129 months; September 2026 is a partial month).

**Source:** Google Trends (https://trends.google.com), downloaded by Gina on 2026-09-27. Settings: search terms (not topics), All categories, Web Search, United States. The geography of each file (6 states, 4 metro areas, 7 cities; same as the heat-search files) is listed in `data/raw/google-trends/air-search/trends_sources.csv`.

## Columns
| Column | Meaning |
|---|---|
| `Time` | First day of the month |
| `air purifier`, `air filter`, `n95` | Google Trends interest index for each search term, unchanged from the raw file |
| `total_interest_index` | air purifier + air filter + n95 (range 0–300) |
| `avg_interest_index` | total_interest_index ÷ 3 (range 0–100, 2 decimals) |

## What the 0–100 interest index is
The numbers are **not counts of searches**. Google Trends:
1. takes the share of all Google searches in that place and month that were for the term ("Each data point is divided by the total searches of the geography and time range it represents"), then
2. rescales those shares so that the highest month for any term in the download = **100**. Other months are relative to that peak (50 = half the peak share). 0 means too little search volume to report.

Source: Google Trends Help, FAQ about Google Trends data, https://support.google.com/trends/answer/4365533

## How to compare
- **Within one file (one place): yes.** Months and terms share one scale.
- **Between files (places): no.** Each file is rescaled to *its own* peak, so 100 in Phoenix and 100 in Detroit are different amounts.

## Important for these files: what sets the 100
- In **15 of 17 files the 100 is "n95" in March or April 2020** (the start of COVID-19), or January 2022 in San Francisco-Oakland-San Jose. All other months and terms are scaled against that mask-buying spike, which compresses them.
- In **Eugene and Oregon the 100 is "air purifier" in September 2020** (the month of the Oregon wildfire smoke).
- "air filter" also covers furnace, HVAC and car filters, not only air-quality concerns.

Script: `scripts/google-trends/04_air_search_processed.py`. Column definitions: `data/descriptions/data_descriptions.csv`.
