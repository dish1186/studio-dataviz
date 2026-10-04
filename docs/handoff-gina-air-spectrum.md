# Handoff to Gina: air-spectrum labels (Alarm → Normalizing)

*Dish + Claude, 4 Oct 2026, for the morning of 5 Oct. Jury is 7 Oct.*

## What this is

For each city's worst PM2.5 week, every Reddit comment or post that mentions the air has one band:

| Band | Meaning | Side of the line |
|---|---|---|
| **A**, Alarm | It's bad or strange right now | reacting |
| **J**, Adjusting | Changing what they do; purifiers, apps, forecasts, staying in | reacting |
| **E**, Enduring | Harm told as routine, without alarm | living with it |
| **N**, Normalizing | It's fine, always has been, others overreact | living with it |
| **X** | Matched an air word but isn't about the air | left out of all shares |

The full rules are in `data/processed/reddit/spectrum_02_labels/codebook.md`, including Rule 8: forecasts, maps and explanations count as J.

**Status:** all 9 event weeks are labeled. **Every label is a Claude draft.** The `dish_review` column is empty, and Dish decided not to hand-audit for now. Shares are **within-city** (each city against its own air talk).

## Your task: play with the buckets

Dish likes the two-bucket reading, **reacting (A + J) vs living with it (E + N)**. Your job is to test how much that framing holds up. Regroup the bands; don't relabel anything.

```
python3 scripts/reddit/spectrum_05_regroup.py                          # all four presets
python3 scripts/reddit/spectrum_05_regroup.py --preset react_live
python3 scripts/reddit/spectrum_05_regroup.py --groups "reacting=A;adjusting=J;living=E,N"
python3 scripts/reddit/spectrum_05_regroup.py --preset react_live --without-big bakersfield
python3 scripts/reddit/spectrum_05_regroup.py --band-col band_before_rule8   # before the forecast rule
```

The script prints each city's bucket shares, ordered by how unusual its week was (× normal PM2.5). It also prints exploratory Spearman ρ against "how unusual" and "how bad". The presets are:
- `four`
- `react_live`: Dish's split
- `j_as_living`: Adjusting counted as living with it
- `three`: Alarm / Adjusting / Living

### What we already see (draft labels, exploratory)

1. **Reacting vs living is close to a ceiling.** Eight cities are 81–94% reacting. Bakersfield is 39%, or 80% without its "how did the air affect you growing up" thread. So, for now, this split mostly separates Bakersfield from everyone else.
2. **Everything depends on where Adjusting goes.** With J on the reacting side, reacting tracks how unusual the week was (ρ +0.43) much more than how bad it was (+0.07). With J on the living side, the pattern disappears (ρ −0.13). Is buying a purifier a reaction, or a sign of living with it? That's the question to think through.
3. **Band by band (`--preset four`), Adjusting is the one that tracks "how unusual"** (ρ +0.67; +0.08 with "how bad"). Alarm doesn't (−0.13), even though it varies more, from 29% in Bakersfield to 66% in Indianapolis. Enduring and Normalizing lean the other way (−0.47, −0.40). One possible reading: rare smoke makes people change what they do, more than it makes them sound alarmed. Treat that as a lead to check, not a finding.
4. **Bakersfield rests on one thread** that holds 47% of its air talk. Always show it both ways (Dish's decision).

Please write down which grouping you'd use and why, plus any counter-reading. The ρ values are not the analysis of record: there are 9 cities, the labels are drafts, and three weeks are sampled.

## Rules that stay fixed
- **Don't change any band.** If a label looks wrong, note its `item_id` in `dish_review` in the draft CSV. Dish decides what changes.
- **The data contains people's words.** Item-level files are gitignored and must stay local: never commit them, and never paste them into a public tool. On slides, use short paraphrased quotes only, with no usernames.
- **Negative results go to the Forensics Appendix.** If a grouping kills the pattern, that is a result.
- Keep the caveats on everything: Claude drafts, shares within-city, Pittsburgh comments miss the last 4.1 hours, weeks are UTC.

## Where things are

| What | Where | In git? |
|---|---|---|
| Codebook (bands + rules) | `data/processed/reddit/spectrum_02_labels/codebook.md` | yes |
| Shares per city, skew check, sensitivity, passage comparison | `data/processed/reddit/spectrum_03_outputs/results.md`, `summary.csv`, `skew.csv`, `sensitivity.csv`, `passage_comparison.csv` | yes |
| Draft labels with text (one per week) | `spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv` | **no**: local only |
| Items worth checking first | `spectrum_03_outputs/check_first.csv` | no |
| Dot map | https://claude.ai/artifact/YT1pzr2NqFzWgaDusAWxTV (built from `viz/air-spectrum/`) | page yes, `data.js` no |
| Scripts | `scripts/reddit/spectrum_01` … `spectrum_05` | yes |
| Decisions log | `logs/data-log-dish.md`, entries dated 2026-10-04 | yes |

### Getting the local files
The label files aren't in git, because their `reason` column can contain a few quoted words. Dish will send you `data/processed/reddit/spectrum_02_labels/` privately. Put it in the same path, then rebuild everything else:

```
python3 scripts/reddit/spectrum_01_air_items.py      # air talk per item, from the username-stripped event weeks in the repo
python3 scripts/reddit/spectrum_02_sample.py         # same fixed seed, so the same sample
python3 scripts/reddit/spectrum_03_outputs.py        # draft CSVs + results.md (applies Rule 8)
python3 scripts/reddit/spectrum_04_dotmap_data.py    # only if you change the dot map
```

`spectrum_03` stops with an error if the label files don't match the rebuilt items, so you'll know right away if something is off.

## Things you may hit
- **Eugene's event week is Sep 7–13, 2020** (its worst PM2.5 week), not the Aug 2026 case study. The Aug 2026 week appears only as a `_comparison` week for the Forensics Appendix.
- **Eugene, Seattle and Pittsburgh are samples** of 400 items. Always use the `weight` column. The regroup script does this for you; a plain count of rows doesn't.
- **"mask"** pulls in a lot of COVID talk in the 2020 weeks. It's all labeled X and left out of the shares.
- **Re-label agreement** (a blind second reading of 10%) is 183 of 219 (84%). Eugene Aug 2026 is the weakest at 16 of 24.
