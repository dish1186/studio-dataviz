# Data descriptions — Gina

Column-by-column description of every raw file Gina has added to `data/raw/`. Updated each time a new raw file is added; each new file gets its own section, and the log (`logs/data-log-gina.md`) records the update.
Covers Gina's files only. Dish's METAR files are not described here.

For each column: what the value is, its type or units, where it comes from, and the formula when the value is calculated (by the source or later in our pipeline).

**Files described:**
- `data/raw/city-selection/ala_sota2026_pm25_rankings_transcribed.csv`: ALA metro areas and their PM2.5 ranks (Step 1).
- `data/raw/city-selection/mediacloud_collections_lookup.csv`: Media Cloud collections found by name search (Steps 2 and 4).
- `data/raw/city-selection/mediacloud_state_counts_responses.csv`: Story counts for "air pollution" OR "air quality" in each state collection (Step 3).
- `data/raw/city-selection/mediacloud_us_national_counts_responses.csv`: Story counts for the query AND each state name in the United States - National collection (Step 4).
- `data/raw/city-selection/mediacloud_city_counts_responses.csv`: Story counts for the query AND each city name in its state's collection (Step 6).

---

## `city-selection/ala_sota2026_pm25_rankings_transcribed.csv`

ALA metro areas and their PM2.5 ranks (Step 1).

| Column | Description | Type / units | Source | Formula / derivation |
|---|---|---|---|---|
| `metro_area` | ALA metropolitan area name exactly as listed in the ranking: City1-City2(-City3), State(s). The area is the largest OMB Metropolitan Statistical Area (as of 2023) containing the ranked counties. | text | American Lung Association, "State of the Air" 2026 report, About This Report, pp. 7-12; ranks transcribed by Claude from Gina's screenshot of the Most Polluted Cities table | — |
| `ala_shortterm_pm25_rank_2026` | Metro area's national rank for short-term (24-hour) particle pollution (PM2.5); 1 = most polluted. Blank = not ranked in the short-term list ("—" in the source). Tied metros share a rank. | integer rank | American Lung Association, "State of the Air" 2026 report, About This Report, pp. 7-12; ranks transcribed by Claude from Gina's screenshot of the Most Polluted Cities table | Per county, 2022-2024: weighted total = orange days×1 + red days×1.5 + purple days×2 + maroon days×2.5 (days by 24-hour PM2.5 AQI category); weighted average = total ÷ 3. Metro rank = rank of the highest county weighted average in the metro. |
| `ala_yearlong_pm25_rank_2026` | Metro area's national rank for year-round (annual) particle pollution (PM2.5); 1 = most polluted. Tied metros share a rank. | integer rank | American Lung Association, "State of the Air" 2026 report, About This Report, pp. 7-12; ranks transcribed by Claude from Gina's screenshot of the Most Polluted Cities table | Metro rank = rank of the highest county annual PM2.5 design value (µg/m³, EPA, 2022-2024) in the metro. A design value is the concentration calculated in the form of the national air quality standard (EPA). |

## `city-selection/mediacloud_collections_lookup.csv`

Media Cloud collections found by name search (Steps 2 and 4).

| Column | Description | Type / units | Source | Formula / derivation |
|---|---|---|---|---|
| `search_name` | Name typed into the collection search. | text | Claude (Step 2 and Step 4 scripts) | — |
| `collection_id` | Media Cloud collection ID. Used as the cs= parameter in searches. | integer ID | Media Cloud Directory API: GET https://search.mediacloud.org/api/sources/collections/?name=<state> | — |
| `collection_name` | Collection name as returned by Media Cloud. | text | Media Cloud Directory API: GET https://search.mediacloud.org/api/sources/collections/?name=<state> | — |
| `source_count` | Number of news sources (outlets) in the collection when looked up on 2026-09-26. | count of sources | Media Cloud Directory API: GET https://search.mediacloud.org/api/sources/collections/?name=<state> (field source_count) | Used as the denominator of the coverage index downstream: index = relevant_total_stories ÷ source_count |
| `kept` | Whether the collection was used in the analysis, and why not if not. | yes / no (reason) | Claude (Step 2 judgment call) | — |

## `city-selection/mediacloud_state_counts_responses.csv`

Story counts for "air pollution" OR "air quality" in each state collection (Step 3).

| Column | Description | Type / units | Source | Formula / derivation |
|---|---|---|---|---|
| `state` | State whose "State & Local" collection was searched. | text | Claude (Step 3 script) | — |
| `collection_id` | Media Cloud collection searched (cs= parameter). | integer ID | Step 2 lookup (mediacloud_collections_lookup.csv) | — |
| `query` | Exact search text sent to Media Cloud (q= parameter), in Media Cloud's query syntax. | text | Query written by Gina; parentheses added by Claude where noted in the log | — |
| `start` | First day of the search window (start= parameter). | date YYYY-MM-DD | Gina (method: last 24 months) | — |
| `end` | Last day of the search window (end= parameter). Whether Media Cloud counts this day itself was not checked. | date YYYY-MM-DD | Gina (method: last 24 months) | — |
| `platform` | Media Cloud data source searched (platform= parameter): Media Cloud's online news archive. | text | Media Cloud (the default platform in Media Cloud's Python client) | — |
| `successful_attempt` | Which run returned the count: 1 = first run; 2 = paced second run (first run was rate limited). | integer | Claude (Step 3 script output) | — |
| `relevant_total_stories` | Number of stories matching the query in the collection and date window. This is "Total Stories" under Total Attention in the Media Cloud web interface. | count of stories | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count (response field count.relevant) | Coverage index downstream = relevant_total_stories ÷ source_count of the collection |
| `total_stories_in_collection` | Number of all stories in the collection over the same window, matching or not. | count of stories | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count (response field count.total) | Not used in the analysis; would give normalized attention = relevant ÷ total |
| `raw_response` | The API response as printed in the terminal when the query ran. | JSON text | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count | — |

## `city-selection/mediacloud_us_national_counts_responses.csv`

Story counts for the query AND each state name in the United States - National collection (Step 4).

| Column | Description | Type / units | Source | Formula / derivation |
|---|---|---|---|---|
| `state_term` | State name used as the AND term in the query. | text | Claude (Step 4 script) | — |
| `collection_id` | Media Cloud collection searched (cs= parameter): United States - National (246 sources). | integer ID | Step 4 lookup (mediacloud_collections_lookup.csv) | — |
| `query` | Exact search text sent to Media Cloud (q= parameter), in Media Cloud's query syntax. | text | Query written by Gina; parentheses added by Claude where noted in the log | — |
| `start` | First day of the search window (start= parameter). | date YYYY-MM-DD | Gina (method: last 24 months) | — |
| `end` | Last day of the search window (end= parameter). Whether Media Cloud counts this day itself was not checked. | date YYYY-MM-DD | Gina (method: last 24 months) | — |
| `platform` | Media Cloud data source searched (platform= parameter): Media Cloud's online news archive. | text | Media Cloud (the default platform in Media Cloud's Python client) | — |
| `relevant_total_stories` | Number of stories matching the query in the collection and date window. This is "Total Stories" under Total Attention in the Media Cloud web interface. | count of stories | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count (response field count.relevant) | Coverage index downstream = relevant_total_stories ÷ source_count of the collection |
| `total_stories_in_collection` | Number of all stories in the collection over the same window, matching or not. | count of stories | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count (response field count.total) | Not used in the analysis; would give normalized attention = relevant ÷ total |
| `raw_response` | The API response as printed in the terminal when the query ran. | JSON text | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count | — |

## `city-selection/mediacloud_city_counts_responses.csv`

Story counts for the query AND each city name in its state's collection (Step 6).

| Column | Description | Type / units | Source | Formula / derivation |
|---|---|---|---|---|
| `state` | Two-letter code of the state whose collection was searched (the city's home state). | text (USPS code) | Claude (Step 6 script) | — |
| `city` | City name used as the AND term in the query; one of the cities in the ALA metro area names. | text | ALA metro area names (ala_sota2026_pm25_rankings_transcribed.csv), split by Claude | — |
| `collection_id` | Media Cloud collection searched (cs= parameter). | integer ID | Step 2 lookup (mediacloud_collections_lookup.csv) | — |
| `query` | Exact search text sent to Media Cloud (q= parameter), in Media Cloud's query syntax. | text | Query written by Gina; parentheses added by Claude where noted in the log | — |
| `start` | First day of the search window (start= parameter). | date YYYY-MM-DD | Gina (method: last 24 months) | — |
| `end` | Last day of the search window (end= parameter). Whether Media Cloud counts this day itself was not checked. | date YYYY-MM-DD | Gina (method: last 24 months) | — |
| `platform` | Media Cloud data source searched (platform= parameter): Media Cloud's online news archive. | text | Media Cloud (the default platform in Media Cloud's Python client) | — |
| `relevant_total_stories` | Number of stories matching the query in the collection and date window. This is "Total Stories" under Total Attention in the Media Cloud web interface. | count of stories | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count (response field count.relevant) | Coverage index downstream = relevant_total_stories ÷ source_count of the collection |
| `total_stories_in_collection` | Number of all stories in the collection over the same window, matching or not. | count of stories | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count (response field count.total) | Not used in the analysis; would give normalized attention = relevant ÷ total |
| `raw_response` | The API response as printed in the terminal when the query ran. | JSON text | Media Cloud Search API: GET https://search.mediacloud.org/api/search/total-count | — |
