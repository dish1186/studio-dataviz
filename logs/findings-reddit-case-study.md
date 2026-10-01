# Reddit case study: findings summary

**Do people react to air that is harmful, or to air that is unusual for them?**
Status: analysis complete, lexicons frozen (air v1) or descriptive (registers v0). 2026-09-30; corrected 2026-10-01 (institutions moved to negative results after reading the matched quotes). Prepared by Claude for Dish; every number below comes from the step 02–05 outputs in `data/processed/reddit/`.

---

## Design

Two cities, one bad-air week each, each compared with the same calendar week in two adjacent years (method after Moore, Obradovich, Lehner & Baylis 2019, *PNAS* 116(11):4905–4910).

| | Week (local) | Mean PM2.5 | Days > 35.5 µg/m³ | vs a typical week that month | Reading |
|---|---|---|---|---|---|
| **Eugene** | Aug 3–9, 2026 | 41.9 | 3 of 7 (peak 109.4) | **7.3×** | less dangerous, very unusual |
| **Bakersfield** | Dec 2–8, 2024 | **55.5** | **7 of 7** | 2.9× | worst week since 2016, but familiar |

Baselines: Eugene Aug 5–11 2024 and Aug 4–10 2025; Bakersfield Dec 4–10 2023 and Dec 1–7 2025 (no days over the line in any).
Corpus: every post and comment in r/Eugene and r/bakersfield for the six weeks (Arctic Shift archive), after dropping removed/deleted items, bots and mod notices, and stripping usernames. Items kept: Eugene 4,239 (event), 6,892 and 4,818 (baselines); Bakersfield 1,529, 1,052 and 1,001.

---

## What the data supports

**1. Eugene talked about its air much more than usual; Bakersfield's rise was small and uncertain.** *(step 03, lexicon air v1)*

| | Event | Baseline | Change (percentage points) | 95% range |
|---|---|---|---|---|
| Eugene, word list | 4.81% | 0.64% | **+4.17** | +1.56 to +6.90 |
| Eugene, thread measure | 13.99% | 1.45% | **+12.54** | +4.42 to +21.62 |
| Bakersfield, word list | 1.64% | 0.74% | +0.90 | −0.81 to +3.46 |
| Bakersfield, thread measure | 4.84% | 0.74% | +4.10 | −0.84 to +11.89 |

Eugene's ranges stay above zero on every measure; Bakersfield's include zero on every measure. During its worst week, Bakersfield's air talk was about a third of Eugene's on the word list and thread measures, and about two thirds on the wide measure (which counts body words such as *asthma* and *allergies*, Bakersfield's own vocabulary).

**2. The two cities talked about the air differently.** *(step 05, sets "wide" and "strict" agree)*

| Event week, air talk | Eugene (wide / strict) | Bakersfield (wide / strict) |
|---|---|---|
| Safety (the body) | 39% / 37% | **76% / 52%** |
| Comfort (coping) | **39% / 39%** | 13% / 16% |
| Normalizing | 1.2% / 1.5% | **12.7% / 12.0%** |
| Institutions | 6.7% / 6.4% (mostly misreads, see below) | 1.8% / 0% |
| Meaning | 6.2% / 5.9% | 3.6% / 4.0% |

- **Eugene coped:** windows, purifiers, apps, AQI numbers, where to go.
- **Bakersfield felt it in the body and explained it away:** asthma, allergies, migraines, coughing, "zero energy"; then "grew up here, no issues", "it doesn't bother me". Normalizing appears at about 12× the rate of its other talk. *(About 7 comments, mostly one conversation: present it as what was said, not as a rate.)*
- **Neither city reached "meaning"** (climate, "every year", "never like this"): 4–6% of air talk in both.

**3. Tone of the air talk itself** *(step 04, descriptive)*: Eugene's was mildly positive (+0.045, practical and joking); Bakersfield's was the only negative air talk of any window (−0.023, 79 items).

**4. Validation by hand** *(steps 03b–03c)*: the near-miss sample in Bakersfield was 50% air talk the first word list had missed: the evidence for finding 2, and the reason lexicon v1 added body vocabulary.

---

## What the data does not support

- That Eugene's rise is **significantly larger** than Bakersfield's (the ranges overlap).
- That Bakersfield **did not react** at all (it had one real conversation about the air; it was small and in different words).
- A **mood effect** (boiling frog) in either city: Eugene +0.001 (−0.017 to +0.020); Bakersfield −0.006 (−0.040 to +0.033). The test can only detect large shifts; Moore et al.'s effects were tiny and needed billions of tweets.
- That the unusual event produced a **collective "we"**: Eugene's air talk uses "we" a little more than its other talk in every week, not just the smoke week.
- That Eugene **looked to institutions**: read in context, most institution matches were misreads (EPA and LRAPA named as data sources, "mother-in-law" matching *law*, a venue's "chair policy").
- Exact **error rates** for lexicon v1 (validated on round 1 only; see limitations).

## Negative results (Forensics Appendix)

- **Pronoun turn (I / we / they):** no event-specific change in either city; Bakersfield's "we" was the family ("we haven't had health issues").
- **"Too ___" phrases:** too few to analyze (a handful in Eugene, none in Bakersfield).
- **Institutions register:** Eugene's 6.7% is mostly misreads once the matched sentences are read; no claim either way.
- **Mood spillover (VADER):** null, underpowered (above).
- **First word list (v0):** counted fire news as air talk; Eugene's 2024 baseline precision was 14%. Fixed in v1 by moving fire words to a separate measure.

---

## Limitations

- One pair of weeks; two subreddits; Reddit users are not the cities' residents.
- Single coder (Dish), 216 items; v1 revised on that sample and not re-checked on a fresh one; definition of air talk clarified after round 1 (V12). Bakersfield precision rests on round-1 codes.
- Register lexicon v0 is unvalidated; broad words (*outside, fans, plans*) inflate Eugene's comfort share.
- Different kinds of bad air: wildfire smoke (visible, newsworthy) vs winter inversion haze. Part of the story, but also a confound.
- Bakersfield's event week falls in the holiday season.
- Removed items dropped (Eugene event comments: 15%); the removal check found air threads were not removed more than others.

## Open before the deck

1. Re-run the week selection on the repo's processed PM2.5 files (weeks were chosen from data embedded in the PM2.5 City Explorer).
2. Reconcile Bakersfield's days over the EPA line: 144 (reference monitors) vs 146 on the slide.
3. Weekly Google Trends for the six windows, to put searches next to the Reddit result.
4. Check METAR visibility for both event weeks (smoke vs haze).
5. Arctic Shift terms of use, and whether the instructor needs an ethics (IRB) note.

---

## Wording for the deck

- *Eugene's air was less dangerous but far more unusual, and Eugene talked about it: air talk rose from under 1% of the conversation to about 5%.*
- *Bakersfield's air was worse than any week since 2016, but ordinary for a Bakersfield December. Its air talk barely rose, and what there was came through the body, then the reassurance: "grew up here, no issues."*
- *In neither city did the talk reach the question of what is happening.*

Quotes on slides: paraphrase or keep to short fragments, without usernames.

---

## Decisions behind these numbers

| Step | IDs | Covers |
|---|---|---|
| 01 download | R1–R5 | windows, paging, week selection |
| 02 clean | C1–C8 | local weeks, removed items, bots (C3 revised after audit), username stripping, text cleaning |
| 03 remarkability | R1–R7 | shares, lift, thread bootstrap, removal check, difference measure (R6), fire split and thread measure (R7) |
| 03b–c validation | V1–V12 | strata, near-miss, codes, single coder (V6), broad definition (V12) |
| 04 mood | S1–S7 | VADER 3.3.2, pos−neg composite, Moore weather-word exclusion |
| 05 language | L1–L6 | air set "wide" (L1 revised), registers v0, sentence-level concordance (L6) |

Lexicons: `data/lexicons/lexicon_air_v1.csv` (frozen 2026-09-30), `lexicon_registers_v0.csv` (descriptive).

**Sources.** Moore, F. C., Obradovich, N., Lehner, F., & Baylis, P. (2019). Rapidly declining remarkability of temperature anomalies may obscure public perception of climate change. *PNAS* 116(11), 4905–4910. · Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *ICWSM* 8(1). · Arctic Shift Reddit archive (github.com/ArthurHeitmann/arctic_shift).
