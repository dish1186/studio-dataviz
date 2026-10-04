# Handoff: Alarm → Normalizing labeling for new event weeks

Paste everything below into the session that holds the raw Reddit data.

---

## Context

I'm Dish, working on "The Moving Normal," an MDE studio data-viz project (jury Oct 7). The question is whether people react to air quality based on harm, or based on how unusual it is for where they live. In the first pair, Eugene (rare smoke) and Bakersfield (chronic bad air) talked about their worst weeks very differently. I want the same language labeling for the new cities' event weeks so all of them sit on one comparable scale.

How we work:
- **My raw data stays read-only.** Write scripts; I audit and run them.
- **Flag every judgment call** as a draft for me to review.
- **Negative results go to the Forensics Appendix.** Don't drop them.
- **The data contains people's words.** Strip usernames, keep files local, and use only short quotes on slides.

## What you already have

Raw Reddit data (Arctic Shift) for each city's **event week and normal weeks**. Labeling is for **event weeks only**; normal weeks are for the volume control, not this.

Right now **6 of 9 event weeks** are in. Work per week, so the last 3 can be added later without redoing anything. Don't report cross-city conclusions until all 9 are done. Until then, label any table "partial (6/9)."

## Step 0: inspect before writing anything

Show me the following, then wait for my go-ahead:
- **For each event week:** the file names, the columns, and the number of posts and comments.
- **The ID fields you'll use:** comment ID, the post/thread it belongs to, and the timestamp. Confirm that event weeks can be told apart from normal weeks.
- **Any week that looks thin or broken.**

## Step 1: pick out air talk (script)

- Use the event-week posts and comments only.
- **An item counts as air talk only if its own text matches the air word list** (`data/lexicons/lexicon_air_v1.csv`, include + candidate, with excludes applied). Being in an air thread doesn't count, because threads drift.
- **The unit is one comment or post,** with its ID and thread ID kept, and the author column dropped. *(This is a change from Eugene/Bakersfield, where the unit was a keyword-window "passage" because we only had `fragments.csv`. See "Comparability" below.)*
- **Report for each week:** total items, air-talk items, and the share of air talk that comes from the single biggest thread.
- **Long comments:** keep the full text for the CSV, but give me the air-mentioning sentences plus one sentence either side as the hover text.

## Step 2: label every air-talk item (you read them, one band each)

| Band | Meaning | Examples |
|---|---|---|
| **Alarm** (A) | The air is bad or strange right now | AQI numbers, "horrible," "can't breathe," red sun, worry about others, "never used to be like this" |
| **Adjusting** (J) | Changing behavior, or tools for checking or cleaning the air | Purifiers, box-fan filters, apps, PurpleAir, staying in, event logistics |
| **Enduring** (E) | Harm told as ongoing or routine, without alarm | "Allergies everyday," "asthma all around," illness stories said flatly, outdoor job "yay" |
| **Normalizing** (N) | It's fine, always has been, or others overreact | "No issues," "born and raised," "used to be worse," "show must go on," mocking maskers |
| **Not about the air** (X) | The air word was incidental | "Hot air," "on air," politics, jokes |

Rules for the edge cases. **Three of these are still provisional:**
1. **Past comparisons split by direction.** "It didn't used to be like this" counts as A. "It used to be as bad or worse" counts as N. *(Provisional.)*
2. **Event "it's going ahead" logistics count as J.** Dismissive versions count as N. *(Provisional.)*
3. **"Usually doesn't bother me, but this week it does" counts as A**, because a threshold was crossed. *(Provisional.)*
4. **Harm stated flatly counts as E. Harm stated with intensity or surprise counts as A.**
5. **Climate-change talk counts as X unless it's tied to this week's air.** If it is tied, it counts as A. Mark these unsure.
6. **When a comment mixes bands, label it by its main point.** Mark it unsure.
7. **When unsure, still pick one band**, set `unsure = yes`, and say why.

For each item, give the band, the unsure flag, and a one-line plain reason. Work in batches of about 150.

If a week has **more than about 500 air-talk items**, tell me before labeling and propose a random sample stratified by thread. Don't sample without my OK.

After each week, re-label a random 10% without looking at your first answers, and report how often the two passes agree. *(Provisional.)*

## Step 3: outputs, one set per event week

1. **`spectrum_labels_<city>_<weekstart>_claude_draft.csv`** with columns `item_id, thread_id, city, week, band, claude_unsure, reason, hover_text, full_text, dish_review`. Leave `dish_review` blank.
2. **A summary row** for each city-week: air items, the share in each band (X excluded from the denominator), the X count, the unsure count, the re-label agreement, and the biggest thread's share.
3. **A skew check.** If one thread is more than about 30% of a week's air items, give the shares with and without it.
4. **A "check these first" list**: the most uncertain items, and any that would flip a headline share.

Don't build or change visuals unless I ask. If I do, extend the "From alarm to acceptance" dot map (`https://claude.ai/artifact/YT1pzr2NqFzWgaDusAWxTV`).

## Comparability (state this in every summary)

Eugene and Bakersfield were labeled as **passages** (keyword windows). The new weeks use **whole comments**. Within-city shares should be roughly comparable, but the units differ.

Before the jury, either:
- **(a)** re-run Eugene and Bakersfield from their raw data with this comment-level protocol, which is preferred, or
- **(b)** note the difference in the Forensics Appendix.

Ask me which.

## Caveats to always state

- **Labels are Claude drafts** until I fill in `dish_review`.
- **Shares are within-city.**
- **Results are partial** until all 9 event weeks are in.
