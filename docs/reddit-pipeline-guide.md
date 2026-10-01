# Reddit pipeline: how to run it

A guide for running the Reddit analysis on your own downloaded data (for example r/boston, 2020–2026). No background in sentiment analysis needed. If something in a printout looks wrong, copy the printout and send it to Dish or Claude.

---

## What the pipeline does, in plain words

We want to know whether people react to weather that is **harmful** or weather that is **unusual for them**. Reddit shows us what people *say*. The pipeline turns a pile of posts and comments into a few numbers per week:

1. **How much people talked about the topic** (heat, or air quality). Every post and comment is checked against a **word list**: if it contains a word like *heat wave*, *so hot* or *humid*, it counts as heat talk. This is called a **bag-of-words** method: the computer does not understand sentences, it only looks for listed words. The result is the **share** of the week's conversation that was about heat, for example 3% of all comments.
2. **The mood of everything else people wrote.** A free tool called **VADER** gives every comment a score from negative to positive, based on a dictionary of words rated by people (*awful* is negative, *love* is positive). We score only the comments that are *not* about the weather, to see whether a bad week makes people grumpier about everything, even when they don't mention it. This idea comes from the study we follow: Moore et al. (2019), *PNAS*, who did the same with tweets.
3. **What kind of talk it was.** The heat or air comments are sorted into **registers** with a second word list: **comfort** (coping: fans, sleep, staying in), **safety** (the body: breathing, asthma, kids, AQI), **meaning** (what this is: climate, every year, never like this), plus **normalizing** ("grew up here, it doesn't bother me").

Nothing here is magic. Every number traces back to a word list you can open and read in a spreadsheet.

---

## Before you start (once)

**1. Get the latest scripts.** In Terminal:
```
cd ~/studio-dataviz
git pull
```
You should now have `scripts/reddit/`, `studies/` and `data/lexicons/`.

**2. Install the two tools the scripts use:**
```
pip3 install pandas vaderSentiment
```
If your downloads end in `.zst`, also run `pip3 install zstandard`.

**3. Always run commands from the repo folder** (`~/studio-dataviz`), in **Terminal**, not in IDLE or the Python shell. If you see `SyntaxError` after typing a `python3 ...` line, you are in the Python shell: open Terminal instead.

---

## Step 1: tell the scripts where your data is

The scripts never contain city names or dates. Those live in a **study file**: a small text file in `studies/`. Open `studies/boston_weekly_2020_2026.json` in any text editor (TextEdit in plain-text mode, VS Code). It looks like this:

```json
{
  "study": "boston_weekly_2020_2026",
  "topic_name": "heat",
  "lexicon_topic": "data/lexicons/lexicon_heat_v0.csv",
  "lexicon_registers": "data/lexicons/lexicon_registers_v0.csv",
  "cities": {
    "Boston": {"subreddit": "boston", "timezone": "America/New_York",
               "raw": ["data/raw/reddit/arctic-shift/boston_*.jsonl"]}
  },
  "periods": [{"city": "Boston", "start": "2020-01-05", "end": "2026-09-26", "bin_days": 7}]
}
```

Change only two things:

- **`"raw"`: where your files are.** Put the folder and file names of your downloads. A `*` means "anything here", so `"/Users/gina/Downloads/reddit/boston*"` picks up every file in that folder starting with `boston`. Posts and comments can be in one file or separate files; if downloads overlap, duplicates are removed automatically. Accepted formats: `.jsonl`, `.ndjson`, `.json`, `.zst`.
- **`"start"` and `"end"`:** the dates your data covers. Keep **start on a Sunday** and end on a Saturday: the weeks then run Sunday to Saturday and line up with our weekly heat data (`heat_map_weekly.csv`).

Save the file. Keep the quote marks and commas exactly as they are; a missing comma is the most common error.

---

## Step 2: clean the data

```
python3 scripts/reddit/02_clean.py --study studies/boston_weekly_2020_2026.json
```

**What it does:** sorts every post and comment into its week (in Boston time), throws out removed and deleted posts, bots and moderator notices, deletes usernames, and strips links and formatting.

**What to check in the printout:**
- Each of your files is listed with a number of rows. **0 rows** means the `"raw"` path is wrong.
- **"WARNING: raw data covers ... but the windows run ..."** means your data starts later or ends earlier than your study dates. Either change `"start"`/`"end"` to match, or accept that the first or last weeks are incomplete.
- **"unreadable"** should be 0 or close to it.

Results go to `data/processed/reddit/boston_weekly_2020_2026/step02_clean/`. You only run this step once.

---

## Step 3: count the topic talk

Run it once for heat and once for air quality:
```
python3 scripts/reddit/03_remarkability.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv
python3 scripts/reddit/03_remarkability.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_air_v1.csv
```
This can take a while on six years of r/boston. If it seems stuck, give it time before stopping it.

**What it gives you** (in `step03_remarkability/lexicon_heat_v0/` and `.../lexicon_air_v1/`):

| File | What it is |
|---|---|
| `share_by_window.csv` | **The main result.** One row per week: how many items, how many about the topic, and the **share** (`topic_share`), with a 95% range (`topic_lo`, `topic_hi`). |
| `term_counts.csv` | Which words did the matching, per week. **Look at this first.** |
| `daily_share.csv` | The same share per day. |
| `items_flagged.csv` | Every post and comment with a yes/no for topic talk (no text). |

**Three versions of the share:**
- `topic_share`: the **main measure**. Only clear words (*heat wave*, *so hot*, *AQI*).
- `topic_wide_share`: also counts **uncertain words** (*hot*, *heat*, *fan*). If the main and wide versions tell the same story, uncertain words aren't driving it.
- `topic_thread_share`: also counts every comment under a post that is about the topic, because replies like "same here, it's brutal" don't contain the words.

**The 95% range** says how sure we are. A week with 2.0% [1.1–3.2] means the true share is very likely between 1.1% and 3.2%. Wide ranges mean few comments that week; don't read much into small differences between weeks whose ranges overlap.

**Check `term_counts.csv` for nonsense.** If one word suddenly dominates a week (for example *heat* during the NBA playoffs), the word list is picking up something else. The heat list already excludes the Miami Heat, hot food and hot takes, and winter heating, but it has **not been checked by hand yet** (next step).

---

## Step 4: check the word list by hand (important for heat)

A word list makes mistakes. Before trusting the heat results, check a sample yourself. It takes about an hour.

```
python3 scripts/reddit/03b_validation_sample.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv --n 25
```

This makes `coding_sheet_gina.csv` (in `step03b_validation/lexicon_heat_v0/`): a shuffled list of posts and comments, some the word list counted as heat talk and some it didn't. **You don't see which is which**, so your judgment stays independent. Read `CODING_GUIDE.txt` in the same folder first.

Open the sheet in Excel or Numbers. In the `code` column, type one letter per row:
- **A** = about the heat (any mention of hot weather, how it feels, what people do about it)
- **F** = about the separate measure only (for the air list this is fire news; the heat list has none, so use A or N)
- **N** = neither (sports, food, slang, anything else)

Don't sort the rows. Save as CSV with the same name. Then:
```
python3 scripts/reddit/03c_validation_results.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv --coder gina
```

**How to read it:**
- **"flagged" groups:** the share you coded A is the word list's **accuracy** when it says "heat". Above about 75% is decent.
- **"not flagged" groups:** the share you coded A is what the list **missed**. A few percent is normal.
- **WORDS BEHIND FALSE ALARMS:** words that fooled the list. Send these to Dish or Claude, and they can be added as exclusions.
- **MISSED:** heat talk the list didn't catch: vocabulary to add.

After fixing the list once, freeze it (rename to `lexicon_heat_v1.csv`) and don't change it again before reporting results.

---

## Step 5: measure mood

```
python3 scripts/reddit/04_mood.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv
```

**What it does:** gives every comment that is *not* about heat, air, fire or the weather a VADER score, then averages them per week.

**How to read `mood_by_window.csv`:**
- `composite` is the main mood score (positive minus negative). Around +0.05 to +0.10 is typical for a city subreddit. **Only the differences between weeks matter**, not the number itself.
- `topic_composite` is the tone of the heat talk itself, just for description.
- `audit_extremes.csv` lists the most negative and most positive comments per week. **Skim it** to check VADER is reading Reddit sensibly; it is bad at sarcasm. It contains people's words: keep it on your computer.

**Be cautious:** in our Eugene and Bakersfield test, mood did not change detectably. Mood effects in the Moore study were tiny and needed billions of tweets. A flat result means "no large change", not "no effect".

---

## Step 6: what kind of talk was it

```
python3 scripts/reddit/05_language.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv --set wide
```

**How to read `register_summary.csv`:** for each week, the share of heat talk in each register (comfort, safety, meaning, normalizing, alarm, institution), next to the same share in **everything else** people wrote ("other"). A register only means something if it is clearly higher in heat talk than in other talk.

**Read `fragments.csv` before trusting any register.** It shows the actual sentences each register picked up, with the matched word. In Eugene, the "institution" register turned out to be mostly mistakes (*EPA* used as a data source, *mother-in-law* matching *law*), so we dropped it. The pronoun and "too ___" results in the same folder also didn't work in our test; ignore them unless they look clearly meaningful.

`fragments.csv` and `concordance.csv` contain people's words. Keep them local, and on slides quote only short pieces without usernames.

---

## What the weekly series can and can't tell you

The series tells you **when** r/boston talked about heat or air, and how much. On its own it **doesn't answer** "harmful or unusual?". For that, each week has to be compared with that week's heat: the actual temperature or felt heat (harm) and the difference from normal (unusual). That joining step is not written yet; ask Dish or Claude for "step 06".

Things you can say from the series alone: which weeks stood out, what words people used, whether heat talk is concentrated in a few weeks or spread across summers.

---

## If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `SyntaxError: invalid decimal literal` | You typed the command in the Python shell | Use Terminal |
| `No such file or directory: scripts/...` | You are not in the repo folder | `cd ~/studio-dataviz` first |
| `ModuleNotFoundError: pandas` (or `vaderSentiment`) | A tool isn't installed | `pip3 install pandas vaderSentiment` |
| `MISSING: no raw files matched` | The `"raw"` path in the study file is wrong | Check the folder and file names; try the full path |
| `json.decoder.JSONDecodeError` when starting | A comma or quote is missing in the study file | Compare with the example above |
| `items.csv exists; use --force` | You already ran step 02 | Add `--force` to run it again |
| A step runs for a very long time | Six years of r/boston is a lot of text | Wait, or shorten `"start"`/`"end"` to one year and run years separately |

---

## Keep a record

Add a short entry to `logs/data-log-gina.md` for each step you run: the date, the command, the study file, the word list, and anything you changed. The scripts list their own rules at the top of each file (codes like C1, R3, V6); mention those if you change any of them.

---

## Words used in this guide

- **Bag of words:** counting whether listed words appear, without understanding the sentence.
- **Word list / lexicon:** the CSV in `data/lexicons/` that decides what counts. `include` words count, `candidate` words count only in the "wide" measure, `exclude` phrases are removed first (e.g. *Miami Heat*, *hot take*).
- **Share:** topic posts and comments divided by all posts and comments in that week.
- **95% range:** the span the true value very likely falls in. Overlapping ranges mean you can't tell two weeks apart.
- **VADER:** a free sentiment tool built for social media. Scores each text from negative to positive using a dictionary of human-rated words.
- **Register:** the kind of talk: coping (comfort), the body (safety), what it means (meaning).
- **Study file:** the settings file in `studies/` that tells the scripts which city, dates, data and word list to use.
