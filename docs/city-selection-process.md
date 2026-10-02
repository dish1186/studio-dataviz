# City selection process

How the study's cities were chosen, as of 2 October 2026: the American Lung Association's top 25 metros for short-term particle pollution, one city per metro. Every step below is logged in detail in `logs/data-log-gina.md` (step names in brackets).

---

## Selection steps (2 October 2026)

1. **New list.** Gina supplied the ALA *State of the Air 2026* top 25 metros for **short-term particle pollution**. 
2. **Cross-check against OpenAQ (Analysis A45).** The 25 metros name 49 individual cities. We had PM2.5 data for 13 of them.
3. **One city per metro (Gina's decision).** To keep the comparison simple, each metro is represented by **its first-listed city**: 25 cities. 8 were already covered; 17 were missing.
4. **New data pull (OpenAQ Batch 2, Steps 1–6).** The 17 missing cities were pulled with the same pipeline, rules and study period as the 8 already covered (6 Mar 2016 – 25 Sep 2026). One exception: Indianapolis uses the Census boundary for the consolidated city-county ("Indianapolis city (balance)"). The earlier OpenAQ files were left unchanged.
5. **Coverage check.** Each city's coverage is the share of the 3,856 days in the study period with a city daily PM2.5 average. Groups:
   - strong: 70% or more
   - partial: 40–69%
   - limited: 15–39%
   - too thin: under 15%
   
   The group boundaries are Claude's choice, not yet approved.
6. **Subreddit check (Gina's rule).** A city stays in consideration only if it has its own city subreddit (r/[city name]). **El Centro has none** (no r/ElCentro; only the regional r/imperialvalley), so it is marked *not available* and **removed from consideration**. **24 cities remain.**

| Coverage group | Count | Cities (ALA rank) |
|---|---|---|
| Strong: 70% or more | 16 | Pittsburgh (13), Eugene (2), Seattle (8), Indianapolis (15), Phoenix (18), Salt Lake City (22), Yakima (25), Los Angeles (7), Detroit (11), Fresno (6), Bakersfield (3), San Jose (21), Fairbanks (1), Visalia (5), Medford (16), Lancaster (19) |
| Partial: 40–69% | 3 | Logan (24), Bend (20), McAllen (10) |
| Limited: 15–39% | 3 | Bismarck (9), Brownsville (4), Boise City (17) |
| Too thin: under 15% | 2 | Minot (12), Helena (23) |
| **Total in consideration** | **24** | (El Centro, 45% coverage, removed: no city subreddit) |

7. **Final list: 75% coverage or more.** Of the 24 cities with a city subreddit, the 13 with PM2.5 data on at least 75% of the study days form the final list (below).

---

## Final list: 13 cities with 75% or more PM2.5 coverage

All 13 have their own city subreddit. Coverage = share of 6 Mar 2016 – 25 Sep 2026 (3,856 days) with a city daily PM2.5 average; every city's data runs Mar 2016 – Sep 2026. Subreddit figures are from the Arctic Shift archive, 2 Oct 2026.

| ALA rank | City | PM2.5 coverage | Subreddit | Subscribers | Archived posts |
|---|---|---|---|---|---|
| 1 | Fairbanks, AK | 75% | [r/Fairbanks](https://www.reddit.com/r/Fairbanks/) | 14,478 | 10,199 |
| 2 | Eugene, OR | 83% | [r/Eugene](https://www.reddit.com/r/Eugene/) | 76,986 | 101,285 |
| 3 | Bakersfield, CA | 77% | [r/bakersfield](https://www.reddit.com/r/bakersfield/) | 37,935 | 36,653 |
| 6 | Fresno, CA | 78% | [r/fresno](https://www.reddit.com/r/fresno/) | 54,909 | 49,005 |
| 7 | Los Angeles, CA | 79% | [r/LosAngeles](https://www.reddit.com/r/LosAngeles/) | 724,594 | 404,999 |
| 8 | Seattle, WA | 83% | [r/Seattle](https://www.reddit.com/r/Seattle/) | 632,527 | 367,298 |
| 11 (tie) | Detroit, MI | 79% | [r/Detroit](https://www.reddit.com/r/Detroit/) | 214,048 | 120,884 |
| 13 (tie) | Pittsburgh, PA | 84% | [r/pittsburgh](https://www.reddit.com/r/pittsburgh/) | 244,225 | 227,634 |
| 15 (tie) | Indianapolis, IN | 83% | [r/indianapolis](https://www.reddit.com/r/indianapolis/) | 147,506 | 109,100 |
| 18 (tie) | Phoenix, AZ | 80% | [r/phoenix](https://www.reddit.com/r/phoenix/) | 310,042 | 152,515 |
| 21 (tie) | San Jose, CA | 77% | [r/SanJose](https://www.reddit.com/r/SanJose/) | 209,849 | 100,657 |
| 22 | Salt Lake City, UT | 80% | [r/SaltLakeCity](https://www.reddit.com/r/SaltLakeCity/) | 210,983 | 175,547 |
| 25 (tie) | Yakima, WA | 80% | [r/Yakima](https://www.reddit.com/r/Yakima/) | 12,797 | 4,995 |

**Just below the cut-off:** Visalia (74%), Medford (73%) and Lancaster (71%). All three have city subreddits.

---

## The 25 cities, with PM2.5 coverage and subreddits

ALA rank = *State of the Air 2026*, short-term particle pollution (ties as given in the ALA list).

**PM2.5 columns:**
- Coverage = share of 6 Mar 2016 – 25 Sep 2026 with a city daily average (OpenAQ Step 5 / Batch 2 Step 5).
- Data runs = first to last day with data.

**Reddit columns:**
- Subscribers and archived posts come from the Arctic Shift Reddit archive's subreddit records, looked up on 2 Oct 2026. Counts may lag Reddit's live numbers.
- "Since" = the year of the earliest archived post.

| ALA rank | Metro | City | PM2.5 coverage | Data runs | Group | Subreddit | Subscribers | Archived posts | Since |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Fairbanks-College, AK | Fairbanks | 75% | Mar 2016 – Sep 2026 | Strong | [r/Fairbanks](https://www.reddit.com/r/Fairbanks/) | 14,478 | 10,199 | 2010 |
| 2 | Eugene-Springfield, OR | Eugene | 83% | Mar 2016 – Sep 2026 | Strong | [r/Eugene](https://www.reddit.com/r/Eugene/) | 76,986 | 101,285 | 2008 |
| 3 | Bakersfield-Delano, CA | Bakersfield | 77% | Mar 2016 – Sep 2026 | Strong | [r/bakersfield](https://www.reddit.com/r/bakersfield/) | 37,935 | 36,653 | 2010 |
| 4 | Brownsville-Harlingen-Raymondville, TX | Brownsville | 30% | Mar 2016 – Sep 2026 (patchy before 2024) | Limited | [r/Brownsville](https://www.reddit.com/r/Brownsville/) | 13,515 | 2,662 | 2010 |
| 5 | Visalia, CA | Visalia | 74% | Mar 2016 – Sep 2026 | Strong | [r/visalia](https://www.reddit.com/r/visalia/) | 16,013 | 5,287 | 2009 |
| 6 | Fresno-Hanford-Corcoran, CA | Fresno | 78% | Mar 2016 – Sep 2026 | Strong | [r/fresno](https://www.reddit.com/r/fresno/) | 54,909 | 49,005 | 2009 |
| 7 | Los Angeles-Long Beach, CA | Los Angeles | 79% | Mar 2016 – Sep 2026 | Strong | [r/LosAngeles](https://www.reddit.com/r/LosAngeles/) | 724,594 | 404,999 | 2008 |
| 8 | Seattle-Tacoma, WA | Seattle | 83% | Mar 2016 – Sep 2026 | Strong | [r/Seattle](https://www.reddit.com/r/Seattle/) | 632,527 | 367,298 | 2008 |
| 9 | Bismarck, ND | Bismarck | 35% | Oct 2022 – Sep 2026 | Limited | [r/bismarck](https://www.reddit.com/r/bismarck/) | 3,841 | 2,037 | 2011 |
| 10 | McAllen-Edinburg, TX | McAllen | 44% | Mar 2016 – Sep 2026 | Partial | [r/Mcallen](https://www.reddit.com/r/Mcallen/) | 1,446 | 152 | 2012 |
| 11 (tie) | Detroit-Warren-Ann Arbor, MI | Detroit | 79% | Mar 2016 – Sep 2026 | Strong | [r/Detroit](https://www.reddit.com/r/Detroit/) | 214,048 | 120,884 | 2008 |
| 12 (tie) | Minot, ND | Minot | 4% | Oct 2025 – Sep 2026 | Too thin | [r/minot](https://www.reddit.com/r/minot/) | 3,163 | 1,684 | 2011 |
| 13 (tie) | Pittsburgh-Weirton-Steubenville, PA-OH-WV | Pittsburgh | 84% | Mar 2016 – Sep 2026 | Strong | [r/pittsburgh](https://www.reddit.com/r/pittsburgh/) | 244,225 | 227,634 | 2008 |
| 14 (tie) | El Centro, CA | ~~El Centro~~ | 45% | Jul 2018 – Sep 2026 | Partial | **Not available: removed from consideration** (no r/ElCentro; only the regional r/imperialvalley) | – | – | – |
| 15 (tie) | Indianapolis-Carmel-Muncie, IN | Indianapolis | 83% | Mar 2016 – Sep 2026 | Strong | [r/indianapolis](https://www.reddit.com/r/indianapolis/) | 147,506 | 109,100 | 2010 |
| 16 | Medford-Grants Pass, OR | Medford | 73% | Mar 2016 – Sep 2026 | Strong | [r/medford](https://www.reddit.com/r/medford/) | 25,618 | 11,649 | 2011 |
| 17 (tie) | Boise City-Mountain Home-Ontario, ID-OR | Boise City | 19% | Aug 2024 – Sep 2026 | Limited | [r/Boise](https://www.reddit.com/r/Boise/) | 61,890 | 52,497 | 2008 |
| 18 (tie) | Phoenix-Mesa, AZ | Phoenix | 80% | Mar 2016 – Sep 2026 | Strong | [r/phoenix](https://www.reddit.com/r/phoenix/) | 310,042 | 152,515 | 2008 |
| 19 | Lancaster, PA | Lancaster | 71% | Mar 2016 – Sep 2026 | Strong | [r/lancaster](https://www.reddit.com/r/lancaster/) (city and county) | 50,744 | 29,713 | 2011 |
| 20 (tie) | Bend, OR | Bend | 51% | Jun 2020 – Sep 2026 | Partial | [r/Bend](https://www.reddit.com/r/Bend/) | 44,519 | 43,311 | 2011 |
| 21 (tie) | San Jose-San Francisco-Oakland, CA | San Jose | 77% | Mar 2016 – Sep 2026 | Strong | [r/SanJose](https://www.reddit.com/r/SanJose/) | 209,849 | 100,657 | 2010 |
| 22 | Salt Lake City-Provo-Orem, UT-ID | Salt Lake City | 80% | Mar 2016 – Sep 2026 | Strong | [r/SaltLakeCity](https://www.reddit.com/r/SaltLakeCity/) | 210,983 | 175,547 | 2009 |
| 23 | Helena, MT | Helena | 2% | Jan – Mar 2022 only | Too thin | [r/helena](https://www.reddit.com/r/helena/) | 6,482 | 4,126 | 2011 |
| 24 (tie) | Logan, UT-ID | Logan | 64% | Mar 2016 – Sep 2026 | Partial | [r/Logan](https://www.reddit.com/r/Logan/) | 10,543 | 7,788 | 2012 |
| 25 (tie) | Yakima, WA | Yakima | 80% | Mar 2016 – Sep 2026 | Strong | [r/Yakima](https://www.reddit.com/r/Yakima/) | 12,797 | 4,995 | 2009 |

### How the subreddits were chosen

1. **Source.** Each city's subreddit was looked up in the Arctic Shift Reddit archive's subreddit records on 2 Oct 2026. That's the same archive the Reddit pipeline downloads from; the in-app browser is not allowed to open reddit.com. Only names, subscriber counts and archived post counts were read; no posts were downloaded.
2. **Rule (Gina).** A city stays in consideration only if it has its own subreddit named for the city: **r/[city name]**. If it doesn't, the city is marked *not available* and removed from consideration.
3. **Matching the name.** The subreddit name must be the city's name; capitalisation doesn't matter (r/bakersfield, r/SanJose). One case uses the common name rather than the Census name: **Boise City → r/Boise**. Claude's reading, not yet approved.
4. **If several exist,** the most active one is used: Claude's choice, not yet approved.
   - **Logan:** r/Logan over the nearly empty r/LoganUtah.
   - **Helena:** r/helena over r/HelenaMT.
   - **Brownsville:** r/Brownsville over r/BrownsvilleTX.
   - **Lancaster:** r/lancaster over the closed r/LancasterPA.
5. **Result.** 24 of the 25 cities pass. **El Centro is not available:** there is no r/ElCentro, only the regional r/imperialvalley, so it was removed.

**Notes**
- **Regional alternatives not used:** where a regional subreddit also exists (r/imperialvalley, r/RogueValley with 688 subscribers), it was not used; only the city-named subreddit counts. r/lancaster covers both the city and Lancaster County, but it is named for the city, so it meets the rule.
- **Thin subreddits:** McAllen, Minot, Bismarck, Brownsville and Helena have few posts (McAllen: 152 archived posts in total), too few for a weekly analysis. None of them is in the final 75% list.

---

## Rules for any Reddit data

- **How to download:** Reddit posts and comments are downloaded through the Arctic Shift archive's web download tool (`scripts/reddit/00_download_plan.py` prints what to download). Reddit is not scraped directly.
- **Usernames stay out of GitHub:** the raw downloads contain usernames and should not be pushed (Gina). Dish's first batch of raw Reddit files (Eugene and Bakersfield) is already in the repo; Gina and Dish to decide what to do about it.
- **Before any new collection:** check Arctic Shift's and Reddit's terms of use, and whether the course needs an ethics note (`logs/findings-reddit-case-study.md`, "Open before the deck").

---

## Open items

1. **Approvals:** Gina to approve the coverage-group boundaries and the subreddit choices.
2. **Summary files:** decide whether to merge the batch-2 OpenAQ summary files with the earlier ones.
3. **Metros with weak data** (Minot, Helena, Boise City): decide whether to keep them, or to swap in the metro's second city where it has better data.
