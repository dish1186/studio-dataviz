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
