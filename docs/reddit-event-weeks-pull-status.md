# Reddit event-week pulls: what we have

*Gina + Claude, 3 October 2026. Status of the Reddit posts and comments Gina downloaded on 3 Oct for the 10 PM2.5 event weeks.*

## Where the files are

- **Cleaned copies (in the repo):** `data/processed/reddit/event_weeks_no_usernames/`
  - one posts file and one comments file per city, with the same names as the downloads
  - `coverage.csv`: record counts and first/last timestamps per file
  - every username field has been removed (see "What was removed" below)
- **Gina's original downloads:** kept on Gina's computer only (`Downloads/event week/`), unchanged. They are not in the repo because they contain usernames.

## How the files were pulled

- **Tool:** the Arctic Shift download tool (https://arctic-shift.photon-reddit.com/download-tool), run in Chrome.
- **What was pulled:** posts and comments for each city's own subreddit (r/[city name]).
- **Pull dates:** the event week's Monday to the following Monday.
  - The tool's end date is not included in what it returns.
  - So "Dec 2–9" returns Dec 2 00:00 to Dec 8 23:59, the full seven event days.
- **Time zone:** the tool works in UTC. The files therefore run from midnight to midnight UTC, not local time. For example, a Pacific-time week is shifted by 7–8 hours. **Not yet fixed:** trimming to local weeks would need one more day pulled at the start.
- **Earlier try:** the first pull of every city used the event week's own end date (e.g. Dec 2–8) and came back one day short. All 10 cities were then re-pulled with the extra day.

## Status by city

Covered dates are the first and last post or comment in the file, in UTC. "Tries" counts the downloads of that city's week, including the first pull that came back one day short.

| City | Subreddit | Event week | Arctic Shift pull dates | Posts covered (UTC) | Comments covered (UTC) | Posts | Comments | Coverage gaps | Tries |
|---|---|---|---|---|---|---|---|---|---|
| Bakersfield | r/bakersfield | Dec 2–8, 2024 | Dec 2–9, 2024 | Dec 2 02:09 – Dec 8 23:18 | Dec 2 00:02 – Dec 8 23:57 | 123 | 1,625 | None | 2 |
| Fairbanks | r/Fairbanks | Jun 27 – Jul 3, 2022 | Jun 27 – Jul 4, 2022 | Jun 27 07:07 – Jul 3 08:28 | Jun 27 00:09 – Jul 3 08:29 | 15 | 184 | None: nothing after Jul 3 08:29. Checked against the Arctic Shift archive: 0 posts and 0 comments for the rest of Jul 3. Small, quiet subreddit. | 2 |
| Fresno | r/fresno | Aug 17–23, 2020 | Aug 17–24, 2020 | Aug 17 00:22 – Aug 23 23:25 | Aug 17 00:02 – Aug 23 23:55 | 80 | 1,100 | None | 2 |
| Yakima | r/Yakima | Sep 6–12, 2021 | Sep 6–13, 2021 | Sep 7 02:41 – Sep 10 20:29 | Sep 6 04:45 – Sep 11 17:38 | 3 | 47 | None: the archive has 0 posts and 0 comments on Sep 12 and 0 comments on Sep 10. **Very thin week:** 3 posts, 47 comments. | 2 |
| Detroit | r/Detroit | Jul 13–19, 2026 | Jul 13–20, 2026 | Jul 13 00:09 – Jul 19 23:43 | Jul 13 00:06 – **Jul 19 21:11** | 284 | 5,822 | **Comments: last 2.8 h missing** (Jul 19 21:11–24:00 UTC = 5:11–8 pm Detroit time). Posts complete. | 4 (see below) |
| Seattle | r/Seattle | Sep 7–13, 2020 | Sep 7–14, 2020 | Sep 7 00:18 – Sep 13 23:43 | Sep 7 00:00 – Sep 13 23:59 | 678 | 11,663 | None. Last 3 h checked against the archive. | 2 |
| Indianapolis | r/indianapolis | Jun 26 – Jul 2, 2023 | Jun 26 – Jul 3, 2023 | Jun 26 00:49 – Jul 2 23:58 | Jun 26 00:07 – Jul 2 23:59 | 284 | 5,325 | None. Last 3 h checked against the archive. | 2 |
| Eugene | r/Eugene | Sep 7–13, 2020 | Sep 7–14, 2020 | Sep 7 02:13 – Sep 13 23:56 | Sep 7 00:00 – Sep 13 23:54 | 620 | 9,444 | None. Last 3 h checked against the archive. | 2 |
| Pittsburgh | r/pittsburgh | Jul 13–19, 2026 | Jul 13–20, 2026 | Jul 13 00:08 – Jul 19 23:49 | Jul 13 00:00 – **Jul 19 19:52** | 808 | 22,587 | **Comments: last 4.1 h missing** (Jul 19 19:52–24:00 UTC = 3:52–8 pm Pittsburgh time). Posts complete. | at least 4 (see below) |
| San Jose | r/SanJose | Aug 17–23, 2020 | Aug 17–24, 2020 | Aug 17 00:00 – Aug 23 23:58 | Aug 17 00:06 – Aug 23 23:59 | 346 | 3,926 | None. Last 3 h checked against the archive. | 2 |

"Checked against the archive" means that, for the last 3 hours of the pull, the number of posts (and of comments, where the archive returned fewer than its limit of 100) in the file matched the number the Arctic Shift API returned for the same hours. Bakersfield and Fresno could not be cross-checked because the archive was not answering at the time; their files run to within an hour of the end and show no sign of stopping early.

### Detroit tries (comments)

1. **Event-week dates (Jul 13–19):** came back one day short, ending Jul 18 23:59 UTC.
2. **Jul 13–20:** saved 10:26. Ends Jul 19 21:11 UTC. Chrome left an unfinished-download file (`.crswap`) behind, so the download stopped early. **This is the file in the repo.**
3. **"Detroit2":** pulled Aug 13–20 by mistake (wrong month). Deleted.
4. **"Detroit3" (Jul 13–20):** was still downloading at 11:43, when it had reached Jul 19 20:41 UTC with nothing new compared with try 2. It is no longer in the folder.

### Pittsburgh tries (comments)

1. **Event-week dates (Jul 13–19):** ended Jul 18 20:00 UTC, 4 hours short of even its own end date.
2. **Jul 13–20, saved several times under the same name** (11:24–11:27). Successive versions ended Jul 18 17:20, Jul 19 18:24 and Jul 19 19:52 UTC. **The 19:52 version is the file in the repo.**
3. **"pittsburgh2" (Jul 13–20):** had reached Jul 19 19:32 UTC and was still downloading at 11:37. It is no longer in the folder.

**Likely cause:** the Arctic Shift server was overloaded during these downloads ("Timeout. Maybe slow down a bit"). Long comment downloads seem to stop quietly when they hit a timeout.

**Suggested fix (not yet done):** pull only the missing hours, combine them with the existing file, and remove duplicates:
- Detroit comments: Jul 19 21:00 – Jul 20 00:00 UTC
- Pittsburgh comments: Jul 19 19:00 – Jul 20 00:00 UTC

## What was removed from the copies

The script `scripts/reddit/event_weeks_01_strip_usernames.py` copies each file and drops these fields from every post and comment, at every level of nesting:
- every field whose name starts with `author`:
  - username, user ID, account creation date, flair, premium/Patreon status, cakeday
  - the original poster inside crossposts
  - the author name and URL of embedded YouTube or Twitter media
- `link_author`: the username of the post a comment replies to

In total, 764,010 values were removed from 64,964 posts and comments.

Everything else is kept exactly as downloaded, including the post and comment IDs, the text and the timestamps.

**Not removed:** usernames typed inside a post or comment (e.g. "thanks u/…"). Quotes used in the project should still be paraphrased, without usernames, as the methodology says.
