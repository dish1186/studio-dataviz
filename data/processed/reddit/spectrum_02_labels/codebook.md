# Air-spectrum codebook (Claude drafts; Dish reviews in `dish_review`)

Source: Dish's brief, 2026-10-04 (`docs/claude_handoff-air-spectrum-labeling.md`). The unit is one post or comment. It was picked because its own text matched an air word (lexicon_air_v1, include + candidate). Label what the item says about the air, using `hover_text` (the air sentences ± 1). Read `full_text` when the hover text is ambiguous.

| Band | Code | Meaning | Examples |
|---|---|---|---|
| Alarm | A | The air is bad or strange right now | AQI numbers, "horrible," "can't breathe," red sun, worry about others, "never used to be like this" |
| Adjusting | J | Changing behavior, or tools for checking or cleaning the air | Purifiers, box-fan filters, apps, PurpleAir, staying in, event logistics |
| Enduring | E | Harm told as ongoing or routine, without alarm | "Allergies everyday," "asthma all around," illness stories said flatly, outdoor job "yay" |
| Normalizing | N | It's fine, always has been, or others overreact | "No issues," "born and raised," "used to be worse," "show must go on," mocking maskers |
| Not about the air | X | The air word was incidental | "Hot air," "on air," politics, jokes, COVID masks, pet allergies, cigarette smoke, fire news with no air content |

## Edge-case rules
1. **Past comparisons split by direction.** "It didn't used to be like this" is A. "It used to be as bad or worse" is N. *(Provisional.)*
2. **Event "it's going ahead" logistics are J.** Dismissive versions are N. *(Provisional.)*
3. **"Usually doesn't bother me, but this week it does" is A**, because a threshold was crossed. *(Provisional.)*
4. **Harm stated flatly is E. Harm stated with intensity or surprise is A.**
5. **Climate-change talk is X unless it's tied to this week's air.** If it is tied, it is A. Mark these unsure.
6. **When an item mixes bands, label it by its main point.** Mark it unsure.
7. **When unsure, still pick one band**, set unsure = yes, and say why.

## Claude's working notes (flagged for Dish)
- **Masks:** a mask matched only in the COVID sense is X. If the mask is for smoke (N95 for smoke, "masks don't stop smoke"), use the rules above: getting or wearing one is J, mocking it is N.
- **Questions:** a question about the air ("is it safe to run today?", "what's the AQI?") is J if it is about what to do, and A if it is reacting to how the air looks or feels.
- **Fire news:** a report about a fire, with no word about the air people are breathing, is X.
- **Reason:** one plain line, paraphrased. Don't quote more than a few words, and never include usernames.

## Rule 8 (Dish, 2026-10-04)
**Forecasts and explanations are J.** Smoke forecasts, maps or satellite images, wind or inversion explanations ("the inversion is trapping it", "it should clear Monday") count as J, because tracking or explaining the air is a way of checking it. If the item mainly reacts to how the air is right now ("it's horrible, and the inversion is trapping it"), it stays A. Applied to existing labels in one pass across all weeks (`<name>_labels_rule8.csv`).
