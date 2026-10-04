# Handoff to Gina: how people talked about the air

*From Dish (with Claude), Oct 4, 2026. For tomorrow morning, Oct 5. Jury is Oct 7.*

## What we did

We took each city's worst smoke week (9 cities) and pulled every Reddit comment or post that talks about the air. Then each one was sorted into one of four groups:

| Group | What it sounds like | Big-picture side |
|---|---|---|
| **Alarm** (A) | "This is bad right now." "I can't breathe." | reacting |
| **Adjusting** (J) | Doing something about it: buying a purifier, checking an app or forecast, staying inside | reacting |
| **Enduring** (E) | Harm said in a flat, everyday way: "my allergies are always bad here" | living with it |
| **Normalizing** (N) | "It's fine." "It's always been like this." "People are overreacting." | living with it |
| **Not about the air** (X) | The word matched, but the comment is about something else (COVID masks, smoked meat, jokes) | not counted |

The full sorting rules are in `data/processed/reddit/spectrum_02_labels/codebook.md`. One rule we added at the end: smoke forecasts, maps and explanations ("the wind is trapping it") count as **Adjusting**.

**Important:** Claude did all the sorting, and none of it has been checked by a person yet. Every percentage compares a city with itself: "45% Alarm in Eugene" means 45% of Eugene's own air comments.

## Your job tomorrow: try different ways of grouping

I like splitting everything into two sides: **reacting** (Alarm + Adjusting) vs. **living with it** (Enduring + Normalizing). Please test whether that split holds up. **Only change how the groups are combined. Don't re-sort any comments.**

Run this to see every city under a few different groupings:

```
python3 scripts/reddit/spectrum_05_regroup.py
```

Other ways to run it:

```
python3 scripts/reddit/spectrum_05_regroup.py --preset react_live                                 # just my two-side split
python3 scripts/reddit/spectrum_05_regroup.py --groups "reacting=A;adjusting=J;living=E,N"         # make up your own
python3 scripts/reddit/spectrum_05_regroup.py --preset react_live --without-big bakersfield       # Bakersfield without its big thread
python3 scripts/reddit/spectrum_05_regroup.py --band-col band_before_rule8                        # before the forecast rule
```

For each city, the script shows what percentage falls in each side, with cities listed from most unusual smoke week to least. Underneath is a score from −1 to +1 showing how closely each side follows two things: **how unusual** the week was for that city, and **how bad** the air actually was. Near +1 means the two rise together; near 0 means no pattern.

### What we've noticed so far (rough, not checked)

1. **"Reacting vs. living with it" mostly just singles out Bakersfield.** Eight cities are 81–94% reacting. Bakersfield is 39%, or 80% if you leave out its one big thread.
2. **It depends on where Adjusting goes.** With Adjusting on the reacting side, reacting follows how *unusual* the week was (+0.43) more than how *bad* it was (+0.07). Move Adjusting to the "living with it" side and the pattern goes away (−0.13). So the real question is: is buying a purifier a reaction, or a sign that people have learned to live with smoke?
3. **Adjusting, by itself, follows how unusual the week was** (+0.67). Alarm by itself doesn't (−0.13). One possible reading: when smoke is rare, people change what they do more than they sound alarmed. That's a hunch to check, not a result.
4. **Bakersfield depends on one thread.** Almost half its air comments are in a single thread that asked locals how the air affected them growing up. Always show Bakersfield both with and without that thread.

**Please write down** which grouping you'd use and why, and anything that argues against it. Treat the scores as rough. There are only 9 cities, the sorting hasn't been checked, and for 3 big cities we only read a sample.

## Ground rules
- **Don't change any comment's group.** If one looks wrong, write a note in the `dish_review` column of that city's file, and I'll decide.
- **These are real people's words.** They're in our private repo only. Don't paste them into public websites or tools, and keep the repo private. On slides, use short quotes in our own words, never usernames.
- **Results that don't work out still count.** If a grouping makes the pattern disappear, write it down. It goes in the Forensics Appendix.
- **Always mention:** the sorting is Claude's and unchecked; percentages compare each city with itself; Pittsburgh is missing its last 4 hours of comments.

## Where things are

Everything is in git, so `git pull` gets you all of it.

| What | Where |
|---|---|
| Sorting rules | `data/processed/reddit/spectrum_02_labels/codebook.md` |
| Percentages for every city (easy to read) | `data/processed/reddit/spectrum_03_outputs/results.md` |
| Every comment with its group (one file per city) | `data/processed/reddit/spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv` |
| Comments Claude was least sure about | `data/processed/reddit/spectrum_03_outputs/check_first.csv` |
| Interactive dot map | https://claude.ai/artifact/YT1pzr2NqFzWgaDusAWxTV |
| Scripts | `scripts/reddit/spectrum_01` to `spectrum_05` |
| Notes on every decision | `logs/data-log-dish.md` (entries from Oct 4) |

If you change anything and need to rebuild the files:

```
python3 scripts/reddit/spectrum_03_outputs.py        # rebuilds the city files and results.md
python3 scripts/reddit/spectrum_04_dotmap_data.py    # only if you change the dot map
```

## Things that might trip you up
- **Eugene's week is Sep 7–13, 2020**, its worst smoke week, not the August 2026 week from our earlier case study. The 2026 week only shows up as a "comparison" file for the Forensics Appendix.
- **Eugene, Seattle and Pittsburgh had too many comments to read them all**, so Claude read a random 400 from each. Each one has a `weight` column that scales it back up to the full week. The regroup script handles this; simply counting rows won't.
- **"mask" picks up lots of COVID talk** in the 2020 weeks. Those comments are all marked "not about the air" and left out.
- **How consistent the sorting is:** Claude re-sorted 1 in 10 comments a second time without looking at the first answer. The two matched 84% of the time (183 of 219). The August 2026 Eugene comparison week was the least consistent (16 of 24).

---

## gina-response 10/4/2026

*Gina → Dish, Oct 4, 2026 (written with Claude). All numbers come from `scripts/reddit/spectrum_05_regroup.py` on Claude's draft labels (9 cities, not yet checked by a person).*

**Interactive chart:** https://claude.ai/artifact/Q9dn7YgTCE4WxQZJ8Da542
- It shows each city's air comments by group, and where each group's comments come from.
- You can switch between two groups, three groups, four groups, and Adjusting as living.
- You can switch between comments read and estimated full week.
- You can show Bakersfield with or without its biggest thread.

### My proposal: start simple, then add a layer

**Start with your two groups: reacting (Alarm + Adjusting) vs living with it (Enduring + Normalizing).** It's the cleanest story, and it's safe from the hardest judgment call in the sorting.

**Then, as the visualization develops, add a toggle between "two levels" and "three levels"** to see which ends up most relevant. Three levels means Alarm / Adjusting / Living with it.

The three-level layer depends on one thing: **we manually check the comments and confirm that the line between Alarm and Adjusting is solid.** If we can do that in a reasonable amount of time, I think it's worth adding. If we can't, we stay with the two groups and call it a day.

### Why start with two groups

- **It's a cleaner story.** One number per city, with an easy headline.
- **It's safe from the Alarm–Adjusting call.** Your Rule 8 (forecasts and explanations count as Adjusting) moved Adjusting by up to 8 points in some cities; for example, Fresno went from 11% to 19%, and Indianapolis from 17% to 24%. The two-group totals didn't change at all.
- **It depends heavily on Bakersfield, but we can make that work.**
  - Across the 8 other cities, reacting barely varies (81–94%). The contrast is Bakersfield (39% reacting).
  - Much of Bakersfield's "living with it" comes from one thread: 26 of its 31 living-with-it comments come from the "how did the air affect you growing up" thread.
  - We can make Bakersfield the story, as long as we always show it with and without that thread.
- **It can still answer a "how" question** by highlighting Bakersfield as the city where people live with it.

### Why add three groups as the next layer

- **Two groups lose a lot of the nuance in the sentiment analysis.** Across the 8 cities other than Bakersfield:
  - Adjusting rises with how unusual the week was (+0.56).
  - Alarm falls (−0.55).
  - Merged into "reacting", the two cancel out (+0.14). The two-group view hides that pattern.
- **Three groups give a lot more to see without being too complex.**
  - Four groups is a lot, and Enduring alone is too small (67 comments) to compare cities fairly.
  - Three groups keep Enduring and Normalizing together and separate only Alarm and Adjusting.
- **It shows the change from one response to another more clearly:**
  - where smoke is rare, people act: Eugene, Seattle and Fairbanks are about 50% Adjusting
  - in the Midwest's Canadian-smoke weeks, people sound alarmed: Indianapolis 66%, Detroit 57%
  - where smoke is routine, people endure: Bakersfield is 61% living with it
- **It answers Kate's crit.** Kate said she likes "how" research questions and wants us to avoid questions that can be answered with a simple yes or no. The three groups focus on *how* people respond.
- **It opens a question for future analysis:** how have these three groups changed over time in each city? Is a city's mix shifting from alarm toward action or endurance as smoke becomes more common? *(Caveat: normal weeks have very little air talk, so this would need several smoke weeks per city, not normal weeks.)*

### The condition: the Alarm–Adjusting line has to hold

The more interesting pattern sits exactly on the least reliable line in the sorting.

If the hand check agrees with Claude on most of them, the three-group pattern is worth telling. If not, fall back to the two groups and say plainly that the result rests on Bakersfield.

**Proposed check:**
- Read `check_first.csv`, plus a random sample of comments sorted as Alarm or Adjusting from each city.
- Mark only where we disagree, in the `dish_review` column. You decide any changes, per your ground rules.
- **Bar for "solid": [we need to agree on this.** Suggestion: we agree with Claude on at least 8 in 10.**]**

**If we can't validate it in a reasonable amount of time, or the check fails:** we use reacting vs living with it and call it a day. No more regrouping after that.

### The key narrative questions each level asks

#### Two groups (the starting point)

**Main question:** *When smoke fills the air, how do people respond — by reacting to it or by living with it — and how does that depend on whether the smoke is unusual for their city or dangerous?*

1. How does the share of reacting (alarm plus action) change with how unusual the week was, and with how bad the air was?
2. How does Bakersfield, where bad air is routine, talk about smoke differently from cities where it's rare? How much of that rests on a single thread?

**Possible headline:** *"People react to smoke that's unusual for them, not smoke that's dangerous. Bakersfield, where bad air is normal, mostly lives with it."*

#### Three groups (the added layer, if the check holds)

**Main question:** *When smoke fills the air, how do people respond — with alarm, with action, or by living with it — and what shapes which response they choose?*

1. How does the mix of alarm, action and living with it change with how unusual the smoke week was for each city, and with how bad the air actually was?
2. How do people facing rare smoke respond, compared with people for whom smoke is routine? Do they talk more about what to do, while routine-smoke cities talk more about enduring it?
3. *(Exploratory)* How does familiarity with smoke as a kind of event (western fire seasons vs Canadian smoke in the Midwest) shape whether people sound alarmed or practical? The Alarm-heavy cities are mostly the Canadian-smoke cities (Indianapolis, Detroit, Pittsburgh: 48–66% Alarm), not the western fire-season cities (Eugene, Seattle, Fairbanks, San Jose: 37–45%). Fresno is the exception (61%).
4. *(Future)* How have these three responses changed over time in each city?

**Possible headline:** *"Where smoke is rare, people act. Where it's routine, they endure."*

### How the two levels compare

| | Two groups | Three groups |
|---|---|---|
| Safe from the Alarm–Adjusting judgment call | **Yes** | No: Rule 8 shifted results by up to 8 points |
| Shows a pattern among the 8 non-Bakersfield cities | No (+0.14) | **Yes:** Adjusting rises and Alarm falls |
| Depends on Bakersfield's one thread | **Heavily** | Less: Adjusting holds without it (+0.60) |
| Easy to present | **Yes** | Harder |

### Caveats

- The sorting is Claude's and hasn't been checked by a person.
- There are only 9 cities, so the scores are rough.
- Percentages compare each city with itself.
- Fairbanks (35 comments), Fresno (36) and Bakersfield (51) are small.
- Pittsburgh is missing the last 4 hours of comments on Jul 19.
