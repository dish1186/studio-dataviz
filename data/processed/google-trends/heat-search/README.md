# Google Trends · heat-related searches (processed)

17 files, one per geography, named as the raw downloads in `data/raw/google-trends/heat-search/`.
Monthly, January 2016 to September 2026 (129 months; September 2026 is a partial month).

**Source:** Google Trends (https://trends.google.com), downloaded by Gina on 2026-09-27. Settings: search terms (not topics), All categories, Web Search, United States. The geography of each file (state, metro area or city) is listed in `data/raw/google-trends/heat-search/trends_sources.csv`.

## Columns
| Column | Meaning |
|---|---|
| `Time` | First day of the month |
| `air conditioner`, `fan`, `AC` | Google Trends interest index for each search term, unchanged from the raw file |
| `total_interest_index` | air conditioner + fan + AC (range 0–300) |
| `avg_interest_index` | total_interest_index ÷ 3 (range 0–100, 2 decimals) |

"cooling center" and "cooling fan" were removed (Google Trends Step 3, `logs/data-log-gina.md`).

## What the 0–100 interest index is
The numbers are **not counts of searches**. Google Trends:
1. takes the share of all Google searches in that place and month that were for the term ("Each data point is divided by the total searches of the geography and time range it represents"), then
2. rescales those shares so that the highest month for any term in the download = **100**. Other months are relative to that peak (50 = half the peak share). 0 means too little search volume to report.

Source: Google Trends Help, FAQ about Google Trends data, https://support.google.com/trends/answer/4365533

## How to compare
- **Within one file (one place): yes.** Months and terms share one scale, so you can see trends over time and which term is searched more.
- **Between files (places): no.** Each file is rescaled to *its own* peak, so 100 in Phoenix and 100 in Detroit are different amounts. Comparing places needs a download with the places compared in the same Google Trends request.

Script: `scripts/google-trends/02_heat_search_three_terms.py`. Column definitions: `data/descriptions/data_descriptions.csv`.
