# Boiling Frog · brand

Visual identity for the Boiling Frog data visualization (Dish Chowdhury and Gina Hollenbach, MDE Studio, Oct 2026).
Applies to the main page (claude.ai/artifact/J3fSoj9QZQjDP9RPoJHmiV) and the city cards embedded in it
(`card/index.html`; mockup at claude.ai/artifact/MBmo5FYaiP61ejv4ppaaNX).

Type roles and colour code set by Gina on 2026-10-06.

---

## Type

### Roles

| Role | Face · size · weight | Use it for |
|---|---|---|
| **Display** | Jost · 74px · 500 · tight (letter-spacing −0.02em, line-height 1) | The one big question ("how do we react to what's harmful vs. what's abnormal?"). One per page. |
| **Header 1** | Jost · 38px · 400, key words 700 | Plate titles: "Meet the cities…", "We followed nine U.S. cities…", the conclusion's verdict, the "threshold" headword, scroll-story captions ("some of these cities are **used to** air pollution."). |
| **Header 2** | Jost · 28px · 400, key words 700, emphasis in italic (e.g. "*familiar*") | The definition gloss, "Thresholds come from others," lines, "which makes us ask:", the pair tally, the talk-disk city names and "4.8× more air talk", the city card's tab titles ("**20×** more air talk"). |
| **Header 2 · story** | Jost · 32px · 400, key words 700, emphasis in italic | The scroll-story frame titles ("we hope to explore how environments drive our responses…", "in its worst week, bakersfield and indianapolis…"). Header 2 plus 15% (Gina, Oct 6). |
| **Header 3** | Cormorant Garamond italic 34px + Jost 14px caps, letter-spacing 0.3em | **City cards only, for now:** the city name with its "worst week · dates" tag. |
| **Text** | Jost · 16px · 400 | Paragraphs, subtitles, figure explanations, legends, table text, notes, the map hint, card chips and "about" lines, quote-panel lead lines. |
| **Quotes** | Reddit Sans · 22px, author line 16px 500 | Every quote from Reddit: the thresholds plate and the city card's quote panel. |
| **Comments** | Jost · 14px · 400 | Small print: "Fig. 1" tags, result tags ("As predicted"), pair "why" lines, source lines, control labels, footnotes, chart axis and group labels, tabs, buttons. Labels may be set in caps with letter-spacing (0.16–0.3em; 0.16em inside charts). |

Bold (600–700) is only for key words inside a role, and for names in lists (pair names, definition terms). Italic is for one emphasised word at a time.

### Sizes on smaller screens

The sizes above are desktop sizes. Display and headers scale down with the window and stop at these minimums:

| Role | CSS |
|---|---|
| Display | `clamp(40px, 6.4vw, 74px)` |
| Header 1 | `clamp(26px, 3.6vw, 38px)` |
| Header 2 | `clamp(20px, 2.7vw, 28px)` (city card: `clamp(22px, 3.2vw, 28px)`) |
| Header 2 · story | `clamp(23px, 3.1vw, 32px)` |
| Text, quotes, comments | fixed: 16, 22, 14px (raised 15% from 14, 19, 12 on Oct 6) |

Text inside drawings is set so it reads at these sizes on screen:
- In the scroll story (viewBox 1000 wide, about 1:1 on a laptop), the CSS sets the role sizes directly, and roughly doubles them on phones (≤700px), where the drawing is shown at about half size.
- In the city card, text in the charts uses `px(n)`, which converts on-screen pixels into the drawing's own units, so labels stay at 14 / 16 / 28px whatever size the chart is drawn at. Gaps between a label and its number are also set in screen px, so bigger type never collides.

### Exceptions (kept as they were)

| Face | Where | Why |
|---|---|---|
| Pinyon Script | the title "boiling frog" (133px) and "thank you" (82px) | title art |
| Old Standard TT italic | the title subtitle (20px) and the credit line (16px) | pairs with the title art |
| IBM Plex Mono | numbers in tables, values in the scroll story ("55", "4.8×"), ticks, card tags ("42× normal") | numbers line up; takes the size of the role it sits in |

Libre Caslon Text is no longer used (`--display` now points to Jost).

### Loading

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Reddit+Sans:wght@400;500&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,400&family=IBM+Plex+Mono:wght@400;500&family=Pinyon+Script&family=Old+Standard+TT:ital,wght@0,400;1,400&display=swap">
```

Fallback stacks: Jost → Futura, Century Gothic, Avenir Next, sans-serif · Cormorant → Didot, Georgia, serif · Plex Mono → ui-monospace, Menlo, monospace.

### CSS tokens

```css
--t-display: clamp(40px, 6.4vw, 74px);
--t-h1: clamp(26px, 3.6vw, 38px);
--t-h2: clamp(20px, 2.7vw, 28px);
--t-h2-story: clamp(23px, 3.1vw, 32px);
--t-text: 16px;
--t-quote: 22px;  --t-quote-who: 16px;
--t-comment: 14px;
```

On the main page these and the role rules sit in one block marked "type roles (Gina, Oct 6; see brand.md)", just before the first script. In the card they're at the end of its stylesheet.

---

## Colour

Colour code set by Gina on 2026-10-06: **"the frog's pot"** (option C in "Boiling Frog Type and Colour",
claude.ai/artifact/1vkFJxUuLMv21hZFWHW978). It is built from Dish's illustration: the flame is harm, the water is
normal, and the frog is the one who's used to it.

### One colour per concept

| Concept | Token | Light | Dark | Use |
|---|---|---|---|---|
| **The worst week** (the event) | `--event` | #c4285c | #ff5e8e | Only the worst week: its shading and ticks on the timeline, its dot in the air disk, the "worst week · dates" tag. Nothing else in a chart is magenta. |
| **Harmful** (how much PM2.5) | `--harm-1` / `-2` / `-3` | #f2b04a / #e07a1f / #a8410f | #a8742e / #ff9a3d / #ffc66b | A flame-orange ramp: up to WHO 15 / WHO 15 to EPA 35.5 / above EPA 35.5. Map dots sized by worst-week PM2.5 use `--harm-2`. Days over the line on the timeline use `--harm-3`. |
| harm numbers and text | `--harm-ink` | #a8410f | #ffb257 | "55 µg/m³" in the story, the "× over EPA" tag |
| **Unusual** (× its normal) | `--unusual-1` / `-2` / `-3` | #c9bde3 / #7764a1 / #3c2a78 | #5a4a90 / #a493dc / #dcd2ff | Water lavender → deep violet. Lines and dots for "× normal" in the pair charts. |
| unusual numbers and text | `--unusual-ink` | #4b3a8c | #c4b6f2 | "2.9× vs. normal" in the story, the "× normal" tag |
| **Reaction** (× air talk) | `--react` | #0d036a | #c9c2ff | Pot indigo. The air-talk bars, the talk lollipops and "4.8× air talk", the "about 2× more" jump, the response ball and tag. The level is shown by **size** (the response ball grows from low to high), not by a second colour. |
| **Used to it** | `--used` | #2f6e4a | #6cc28a | Frog green. The "used to it" tag, Bakersfield in the story, the words "**used to**" in the opening caption. Cities that aren't used to it are plain ink (Indianapolis). |

### Unchanged

- **Air-talk tone (the quadrants)** keeps its own set and the red split. Tone is a fifth kind of meaning, shown only in the talk disks, their legends and the quote panel.

  | Group | Light | Dark |
  |---|---|---|
  | alarm | #f2643c | #ff7a52 |
  | adjusting | #ec4f9a | #ff6fb0 |
  | enduring | #8a4fe0 | #a77bff |
  | normalizing | #2a9d9a | #3fc4c0 |
  | split (`--split`) | #c8201e | #ff6b5e |

- **Pair type** is told by line style, not colour: matched = solid ink, crossed = dashed ink.
- **Selection** (the ring on the clicked city in the map) is ink.

### Ground and ink

| Token | Light | Dark | Use |
|---|---|---|---|
| `--ground` | #f8ebcb | #160d4c | paper |
| `--ground-2` | #f0dfb6 | #1e1460 | panels |
| `--ink` | #1a0f6b | #f8ebcb | text, lines, "not used to it" |
| `--ink-2` | #463d88 | #d9cfb0 | secondary text |
| `--rule` | #cdb88a | #3e3580 | hairlines |

Texture: `img/paper.jpg`, multiply in light mode, inverted and screened in dark mode.

### Exceptions (decoration, not data)

| What | Colour | Note |
|---|---|---|
| title "boiling frog", "thank you", opener script | `--event` magenta | title art |
| door beams on the definition plate | `--event` | illustration |
| definition plate ground | `--green` #2f6e4a | same green as "used to it"; it's a plate background, not a data mark |
| pot / water / frog artwork | #0d036a / #7764a1 / #4f9a51 | Plate I and the outro |
| focus outlines | `--event` | keyboard focus |

Retired: the old tone tokens `--t-alarm`, `--t-adjust`, `--t-endure` and `--t-norm` (still defined on the page, no longer drawn). Also retired: `--cp-norm` / `--cp-mid` and the card's `--norm` / `--mid` / `--r-*` (replaced by `--harm-*` and `--react`).

### Colour-blind note

Magenta (worst week) and frog green (used to it) only just separate for red-green colour blindness. That is acceptable because "used to it" always appears with its text tag. Lavender (unusual) sits close to the enduring violet, but the two are never shown in the same chart.

---

## Rules

- Text inside a visual is at most two lines; shorten it rather than wrap to three.
- Every view must work from phone width (about 375px) up, with no sideways scroll.
- Never use colour alone: every coloured mark has a label, a legend entry or a tag with text.
- Light and dark mode both get designed. Colours are tokens on `:root`, redefined for dark.
