"""Step 2 of the site plan: split the snapshot page into readable files, without changing what it does.

Reads index.html and card/index.html exactly as they were in the snapshot commit (d689e08), and writes:
  css/NN-*.css        each <style> block, unchanged, linked at the same place in the page
  js/*.js             each inline <script>, unchanged, loaded at the same place in the page
  card/card.css, card/card.js, card/embed.js   the same for the city card
  index.html, card/index.html                  the pages, with each block swapped for its <link> or <script src>

Only three kinds of edit are made, all needed because code moved into files:
  1. url("img/...") inside CSS now points at "../img/..." (CSS paths resolve from the CSS file, not the page).
  2. The three libraries load from js/lib/ (pinned copies of the same cdnjs versions) instead of cdnjs.
  3. The data files load from data/ (moved there, contents unchanged).
The 337 hand-coded comments stay inline in index.html (<script id="qdata" type="application/json">) until step 3.

Run from the repo root:  python3 site/tools/split_page.py
"""
import re
import subprocess
from pathlib import Path

SNAPSHOT = "d689e08"
SITE = Path("site")

# one name per inline block, in page order (checked against the block count below)
MAIN_STYLES = ["00-host-reset", "01-layout", "02-type-roles", "03-pairs-dots", "04-how-they-talked", "05-how-they-talked-brand"]
MAIN_SCRIPTS = ["skip-to", "map-dots", "plates-shared", "hero", "door-walk", "map-plate", "pairs-map", "scope",
                "story-same-air", "see-numbers-rule", "pairs-dots", "study-details", "city-cards", "outro", "air-layer",
                "reddit-posts", "how-they-talked"]
CARD_STYLES = ["card"]
CARD_SCRIPTS = ["card", "embed"]

SRC_MOVES = {
    "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js": "js/lib/d3-7.9.0.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js": "js/lib/gsap-3.12.5.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js": "js/lib/ScrollTrigger-3.12.5.min.js",
    "data.js": "data/pm25.js",
    "states.js": "data/states.js",
}
CARD_SRC_MOVES = {
    "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js": "../js/lib/d3-7.9.0.min.js",
    "cards-data.js": "../data/cards.js",
    "quotes-data.js": "../data/quotes.js",
    "../states.js": "../data/states.js",
}
DATA_MOVES = {"data.js": "data/pm25.js", "states.js": "data/states.js",
              "card/cards-data.js": "data/cards.js", "card/quotes-data.js": "data/quotes.js"}
UNUSED = ["city-panel.js", "city-panel-data.js"]   # published with the artifact but loaded by neither page

BLOCK = re.compile(r"<(style|script)([^>]*)>(.*?)</\1>", re.S)


def from_snapshot(path):
    return subprocess.run(["git", "show", f"{SNAPSHOT}:site/{path}"], check=True, capture_output=True, text=True).stdout


def split(page, styles, scripts, src_moves, css_dir, js_dir, link_prefix, css_url_fix):
    text = from_snapshot(page)
    styles, scripts = list(styles), list(scripts)
    n_style = n_script = 0

    def swap(m):
        nonlocal n_style, n_script
        tag, attrs, body = m.group(1), m.group(2), m.group(3)
        line = text.count("\n", 0, m.start()) + 1
        where = f"Moved unchanged from {page} (snapshot {SNAPSHOT}), line {line}."
        if tag == "style":
            name = styles[n_style]; n_style += 1
            css = body.replace('url("img/', 'url("../img/') if css_url_fix else body
            (css_dir / f"{name}.css").write_text(f"/* {where} */\n{css.strip()}\n")
            return f'<link rel="stylesheet" href="{link_prefix}css/{name}.css">' if css_dir.name == "css" else f'<link rel="stylesheet" href="{name}.css">'
        src = re.search(r'src="([^"]+)"', attrs)
        if src:
            return f'<script src="{src_moves.get(src.group(1), src.group(1))}"></script>'
        if "application/json" in attrs:
            return m.group(0)   # data, not code: stays until step 3
        name = scripts[n_script]; n_script += 1
        (js_dir / f"{name}.js").write_text(f"// {where}\n{body.strip()}\n")
        return f'<script src="{link_prefix}js/{name}.js"></script>' if js_dir.name == "js" else f'<script src="{name}.js"></script>'

    out = BLOCK.sub(swap, text)
    assert n_style == len(styles) and n_script == len(scripts), (page, n_style, len(styles), n_script, len(scripts))
    (SITE / page).write_text(out)
    print(f"{page}: {n_style} style blocks, {n_script} scripts moved out; {len(text):,} -> {len(out):,} characters")


def main():
    (SITE / "css").mkdir(exist_ok=True); (SITE / "js").mkdir(exist_ok=True); (SITE / "data").mkdir(exist_ok=True)
    for old, new in DATA_MOVES.items():
        if (SITE / old).exists():
            (SITE / old).rename(SITE / new)
    (SITE / "_unused").mkdir(exist_ok=True)
    for f in UNUSED:
        if (SITE / f).exists():
            (SITE / f).rename(SITE / "_unused" / f)
    split("index.html", MAIN_STYLES, MAIN_SCRIPTS, SRC_MOVES, SITE / "css", SITE / "js", "", True)
    split("card/index.html", CARD_STYLES, CARD_SCRIPTS, CARD_SRC_MOVES, SITE / "card", SITE / "card", "", False)


if __name__ == "__main__":
    main()
