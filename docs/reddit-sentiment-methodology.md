# Heat, haze and what people say: a methodology for Reddit post frequency and sentiment

**Status:** draft methodology, not yet run. No Reddit data has been collected. Prepared 2026-09-30 by Gina Hollenbach with Claude for the MDE studio project "AI-Augmented Storytelling with Data". Items marked **[decision]** are open choices for Gina and Dish; items marked **[Claude's choice, not yet approved]** are defaults proposed here.

**Model study.** The framing and structure follow Moore, Obradovich, Lehner & Baylis (2019), "Rapidly declining remarkability of temperature anomalies may obscure public perception of climate change," *PNAS* 116(11), 4905–4910, https://doi.org/10.1073/pnas.1816541116. That study:
- used 2.18 billion geolocated tweets (March 2014 to November 2016)
- identified weather posts with a **bag-of-words** term list, validated by hand on 6,000 sampled tweets
- measured sentiment with **VADER** and **LIWC**
- regressed log weekly weather-tweet counts on county temperature anomalies relative to a 1981–1990 baseline, with:
  - controls for precipitation, humidity, cloud cover and the number of active users
  - county, state-by-month-of-year and year fixed effects
  - standard errors clustered by state

This document adapts that design to Reddit, to two kinds of environmental events (heat and poor air quality), and to the five cities already in our pipeline. Details of the model study are taken from its open-access version on PubMed Central (PMC6421414).

---

## Significance

People experience heat and smoky air directly, and both carry health risks. But it is unclear which of them prompts people to *talk*, and whether talking comes with distress. Our earlier steps measured action through Google searches for air conditioners and air purifiers. This analysis asks the same question of public conversation.

When a city is unusually hot, or its air is unhealthy, do residents post about it more, and does the tone of what they write change? Comparing heat with air quality tests whether one kind of event is more "remarkable" than the other, measured by how much people post about it and how they feel.

## Abstract (planned)

We will combine posts from city subreddits for Boston, San Francisco, Phoenix, Detroit and San Diego with weekly measures of:
- actual heat (gridMET daily maximum temperature)
- felt heat (UTCI)
- fine-particle pollution (OpenAQ PM2.5)

for January 2022 to May 2026. A bag-of-words classifier, validated by hand, will flag heat-related and air-quality-related posts. Sentiment will be scored with a lexicon-based tool designed for social media (VADER). Panel regressions with city and seasonal fixed effects will estimate how:
- **(i)** the frequency of heat and air-quality posts, and
- **(ii)** the sentiment of those posts and of all other posts

respond to temperature anomalies and to unhealthy-air days. We will then compare the size of the heat and air-quality responses.

## Research questions and hypotheses

- **RQ1. Frequency.** Do weeks with abnormal heat, or with unhealthy air, see more posts about that topic?
  - *H1a:* heat-post share rises with the weekly temperature anomaly.
  - *H1b:* air-quality-post share rises with the number of unhealthy-air days (PM2.5 ≥ 35.5 µg/m³).
- **RQ2. Sentiment.** Is the tone of posts lower in those weeks?
  - *H2a:* the sentiment of topic posts is more negative in event weeks than in other weeks.
  - *H2b:* following Moore et al., the sentiment of *all other* posts is also lower. This is a spillover of mood, not just complaint about the event.
- **RQ3. Heat vs air.** Are the frequency and sentiment responses larger for air-quality events than for heat events of comparable rarity?
  - *H3:* rare, visible smoke events produce a larger posting response than heat. In Google searches, sudden smoke spikes drove the clearest jumps.
- **RQ4 (exploratory). Thresholds.** Does posting about heat increase sharply above the same temperatures at which AC searches take off (Google Trends Step 12)?

## Approach

The design is observational and within-city. Each city is compared with itself across weeks. Seasonal patterns and city differences are absorbed by fixed effects, so the estimates come from weeks that are unusually hot or smoky *for that city and time of year*.

This mirrors the model study's use of anomalies relative to a local climatology, rather than raw temperature.

---

## Data

### Reddit posts

- **Communities:**
  - Boston: r/boston
  - San Francisco: r/sanfrancisco and r/bayarea
  - Phoenix: r/phoenix
  - Detroit: r/detroit
  - San Diego: r/sandiego

  **[decision]** whether to add suburb or neighbourhood subreddits. Adding them increases volume but mixes geographies.
- **Unit:** submissions (title plus body), and optionally top-level comments. **[decision]**
  - Comments add volume and capture reactions.
  - But comment threads are not independent, and one viral thread can dominate a week.
  - Default: submissions plus top-level comments, with a cap per thread as a robustness check. **[Claude's choice, not yet approved]**
- **Period:** 2022-01-02 to 2026-05-31, weekly (Sunday to Saturday). This matches the weekly heat, felt-heat and search panel already built (Google Trends Step 13), so every outcome lines up with an existing exposure measure.
- **Access:**
  - Through Reddit's official Data API under its Data API Terms and Developer Terms. This requires a registered app and has rate limits and use restrictions.
  - Historical archives distributed by third parties may have different terms. Their use must be checked before relying on them. **[decision]**
  - Do not scrape the website.
- **Location assumption:** a post in a city subreddit is treated as being from that city. Reddit offers no geolocation, unlike the geotagged tweets in the model study. This is a key limitation (see below).
- **Volume control:** the total number of posts in each subreddit-week, which plays the role of "number of active users" in the model study.

### Heat exposure

All of these already exist in the repo:
- **Actual heat:** gridMET daily maximum temperature, averaged per week (`data/processed/google-trends/heat-threshold/heat_map_weekly.csv`).
- **Anomaly:** weekly mean high minus the 1991–2020 mean high for the same city and week of year. This is the analogue of the model study's 1981–1990 reference period. The 1991–2020 window is the current climate normal and is already used for the "abnormally high" flag.
- **Abnormal-heat days per week:** days above the 1991–2020 ±7-day 90th percentile.
- **Felt heat:** UTCI daily maximum and its heat-stress category (moderate ≥ 78.8 °F, strong ≥ 89.6 °F). Felt heat ends 2026-06-12 in the current data.
- **Threshold crossing:** weeks above each city's AC-search threshold, the "searchers reach for AC" point from Google Trends Step 12.

### Air-quality exposure

- **PM2.5:** OpenAQ daily site values, under the EPA 18-of-24-hour completeness rule (OpenAQ Step 5).
- **Unhealthy-air days:** days with any site at ≥ 35.5 µg/m³, i.e. AQI "Unhealthy for Sensitive Groups" or worse (OpenAQ Step 6, 40 CFR 58 App. G). Both a strict version and a partial (≥ 12 h) version exist.
- **Weekly measures:**
  - the number of unhealthy days
  - the weekly maximum of the daily city maximum
  - the weekly mean
- **Haze:** the METAR visibility-based haze index, as a check on sensor coverage. **[optional]**

### Controls

- Precipitation and relative humidity (gridMET), to separate heat from humid, stormy weeks.
- Holiday and major-news weeks: a list of US federal holidays. **[decision]** whether to flag city-specific major events (e.g. sports championships), which are known to shift subreddit volume and mood.

---

## Methods

### 1. Identifying heat and air-quality posts (bag of words)

Following the model study, posts are classified with predefined term lists rather than a trained model. This keeps the classification transparent and easy to audit.

- **Heat terms (draft):**
  - heat wave, heatwave, heat advisory, excessive heat, hot (as an adjective about weather)
  - humid, humidity, muggy, sweltering, scorching, record high
  - air conditioner, air conditioning, AC unit, window unit, cooling center, heat stroke, heat exhaustion
- **Air-quality terms (draft):**
  - air quality, AQI, smoke, smoky, wildfire smoke, haze, hazy, smog
  - PM2.5, air purifier, N95, "can't breathe", orange sky, "smells like smoke"
- **Exclusion rules** for known false positives:
  - "hot" in "hot take", "hot dog", "hot sauce"
  - "AC" meaning a video game or a sports team
  - "smoke" in cannabis or tobacco contexts
  - "heat" as the Miami Heat
  - These are matched on whole words and phrases, case-insensitive. Lemmatised variants are included (e.g. "smoking" is excluded unless near "wildfire" or "fire").
- **Validation:**
  - Hand-code a stratified sample: for example, 600 posts flagged as heat, 600 flagged as air quality, and 600 random unflagged posts, drawn across cities and seasons. The model study validated on 6,000 tweets.
  - Two coders label each post as about weather/heat, air quality, or neither. Report agreement (Cohen's κ).
  - Report **precision** (share of flagged posts that are really on topic) and **recall** (estimated from the unflagged sample).
  - Revise the term lists once, then freeze them before the regressions.
  - Sample sizes: **[Claude's choice, not yet approved]**.
- **Outcome (frequency):** for each city-week,
  - log(heat posts + 1) and log(air-quality posts + 1), with log(total posts) as a control, or
  - the topic share of all posts. **[decision]** The model study used log counts with a user-count control.

### 2. Measuring sentiment

- **Primary tool: VADER** (Hutto & Gilbert, 2014). A rule-based lexicon tuned for social-media text, handling negation, intensifiers, capitals and emoticons. Each post gets a compound score from −1 to +1. Free and open source.
- **Secondary tool: LIWC** (Linguistic Inquiry and Word Count). The model study's second measure. It counts words in categories such as positive emotion, negative emotion, anxiety and anger. **LIWC requires a paid licence.** **[decision]** If it isn't available, an open lexicon such as the NRC Emotion Lexicon is a substitute for the emotion categories.
- **Composite score:** as in the model study, positive minus negative sentiment. For VADER, use the mean compound score per city-week. For LIWC, use positive-emotion % minus negative-emotion %.
- **Two sentiment outcomes per city-week:**
  1. the sentiment of **topic posts** (heat or air quality): how people feel when they talk about the event
  2. the sentiment of **all other posts**: whether the event shifts mood more broadly (the model study's main sentiment test)
- **Checks:**
  - Hand-rate the sentiment of 200 of the validation posts and correlate with VADER.
  - Report where VADER misreads sarcasm or Reddit-specific language.

### 3. Exposure definitions (events)

Two parallel sets, so that heat and air quality can be compared on a common footing.

| | Continuous measure | Event indicator |
|---|---|---|
| **Heat** | Weekly temperature anomaly (°F above the 1991–2020 normal for that week) | Week has ≥ 3 abnormal-heat days, or the weekly high is above the city's AC-search threshold |
| **Felt heat** | Weekly UTCI maximum anomaly | Week has ≥ 1 day of "strong" heat stress or worse |
| **Air quality** | Number of unhealthy-air days (0–7); weekly max PM2.5 | Week has ≥ 1 unhealthy-air day |

To compare heat with air quality (RQ3), both continuous measures are also expressed as **percentiles of each city's own distribution**. This puts "a 1-in-20 hot week" and "a 1-in-20 smoky week" on the same scale. **[Claude's choice, not yet approved]**

### 4. Regression models

The baseline specification follows the model study's principal model:

> Y<sub>c,w</sub> = f(Heat<sub>c,w</sub>) + g(Air<sub>c,w</sub>) + β·X<sub>c,w</sub> + α<sub>c</sub> + γ<sub>c,m(w)</sub> + δ<sub>y(w)</sub> + ε<sub>c,w</sub>

- **Y<sub>c,w</sub>:** the outcome for city *c* in week *w* (log topic-post count, or mean sentiment).
- **f(·), g(·):** the heat and air-quality exposures. They enter as linear terms, as bins (e.g. anomaly quintiles, or 0, 1–2 and 3+ unhealthy days), or as event indicators.
- **X<sub>c,w</sub>:** controls: log(total posts), precipitation, humidity, holiday weeks.
- **α<sub>c</sub>:** city fixed effects. These absorb permanent differences between subreddits (size, tone, moderation).
- **γ<sub>c,m(w)</sub>:** city-by-month-of-year fixed effects. They absorb each city's normal seasonal cycle, so that, for example, July posting in Phoenix is compared with other Julys in Phoenix. The model study used state-by-month-of-year.
- **δ<sub>y(w)</sub>:** year fixed effects. They absorb platform-wide trends, such as changes in Reddit's user base, API changes in 2023, or general shifts in tone.
- **Inference:** with only 5 cities, clustering by city (the analogue of clustering by state) is unreliable. Options:
  - wild-cluster bootstrap by city
  - Driscoll–Kraay standard errors, which allow correlation across cities and over time
  - **[Claude's choice, not yet approved]:** report both.
- **Comparisons:**
  - **RQ3 test:** heat vs air-quality coefficients, on the percentile scale, tested with a joint model.
  - **RQ4 (exploratory):** an event study around the weeks a city first crosses its AC-search threshold each year, with leads and lags of −3 to +3 weeks.

**Not attempted:** the model study's central finding about "remarkability" fading over time used a distributed-lag model over 15 years of past exposure. We have about 4.5 years of Reddit data for 5 cities, which is too short to estimate how fast people get used to heat. We can report a simple version: whether the response to heat is smaller later in each summer, or in the second hot week in a row.

### 5. Robustness checks

- Submissions only vs submissions plus comments, and capping posts per thread.
- Strict vs partial unhealthy-air days, and reference-grade sensors only.
- Actual heat vs felt heat as the heat exposure.
- Topic share instead of log counts.
- Excluding the 2-3 largest single events (e.g. the June 2023 eastern wildfire smoke, the September 2022 western heat wave) to check that one week isn't driving the results.
- Term lists with and without the most ambiguous words ("hot", "smoke", "AC").
- LIWC (or the NRC lexicon) in place of VADER.
- Dropping 2023 around Reddit's API change and the subreddit blackouts of June 2023, when posting volumes were unusual.

---

## Ethics and data handling

- **Only public posts, analysed in aggregate.** Store post IDs, timestamps, subreddit, and derived scores and flags. Don't keep usernames in analysis files.
- **Quotes for the visualization's case-study panel** are **paraphrased** or kept very short, without usernames, and linked to the original only where appropriate. This protects privacy and respects authors' copyright.
- Follow Reddit's Data API Terms, including any rules on storage, deletion and non-commercial academic use. If a post is deleted, remove it from stored data at the next refresh. **[decision]** Check with the course instructor whether this needs ethics (IRB) review or exemption.
- **Every step follows the project's data-log rules:**
  - each step is proposed and approved before running
  - each step is logged in `logs/data-log-gina.md`
  - raw files are never edited
  - API keys are kept in environment variables only

## Limitations

- **Location is assumed from the subreddit.** Posters may not live in the city, and locals discuss events elsewhere. Wildfire smoke in particular is a regional, widely covered event.
- **Who posts on Reddit:** Reddit users are not representative of city residents (younger and more male, for example). The results describe online conversation, not the population. The same caution applies to the Google searches.
- **Selection and moderation:** moderators may remove, merge or sticky event threads (e.g. "Heat wave megathread"), which changes post counts. Megathreads should be identified and their comments counted.
- **Lexicon sentiment** misses sarcasm and context, and Reddit humour is often ironic about heat. Hand validation measures, but doesn't remove, this error.
- **News coverage** may drive both posting and searches. We already have Media Cloud heat and air-quality news shares, which could be added as a control or a mediator. **[decision]**
- **Few cities and a short window** limit statistical power and rule out the model study's long-run adaptation analysis.
- **Platform changes in 2023** (API pricing, the June blackouts) may break the series. Year fixed effects absorb level shifts, but not changes in who posts.

## Outputs planned

1. A weekly panel per city: post counts, topic counts and shares, and mean sentiment (topic and other posts), joined to the existing heat and PM2.5 panels.
2. Regression tables for RQ1–RQ3, plus robustness tables.
3. For the visualization: per city, the weekly heat-post and air-post shares for the Find Your Threshold map, plus a small set of paraphrased case-study posts per major event.

## Open decisions (summary)

1. Subreddits: city-only, or add suburbs and neighbourhoods?
2. Submissions only, or submissions plus comments?
3. Data access route (official API vs archives), checked against current terms.
4. LIWC licence, or an open alternative?
5. Frequency outcome: log counts, or share of posts?
6. Whether news coverage enters as a control.
7. Ethics review requirement.

## References

- Moore, F. C., Obradovich, N., Lehner, F., & Baylis, P. (2019). Rapidly declining remarkability of temperature anomalies may obscure public perception of climate change. *Proceedings of the National Academy of Sciences*, 116(11), 4905–4910. https://doi.org/10.1073/pnas.1816541116 (open access: https://pmc.ncbi.nlm.nih.gov/articles/PMC6421414/)
- Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *Proceedings of the International AAAI Conference on Web and Social Media*, 8(1). **[to verify: pages]**
- Pennebaker, J. W., and colleagues. Linguistic Inquiry and Word Count (LIWC). **[to verify: the version used by the model study, and the current LIWC-22 citation]**
- U.S. EPA, 40 CFR Part 58, Appendix G (AQI breakpoints). Used in OpenAQ Step 6.
- Reddit Data API Terms and Developer Terms. **[to read and cite the current versions before any collection]**
