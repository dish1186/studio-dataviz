"""Step 4 of the site plan: check the site's data. Reads files only; writes nothing.

Two checks, run from the repo root:  python3 site/tools/check.py

1. Inputs unchanged. Each file in site/data/ lists the inputs it was built from with their SHA-256. If an input has
   changed since, the data file is out of date: re-run its script (scripts/site/).
2. Same numbers as the published page. Every value is compared with the snapshot of the published artifact
   (commit d689e08, version 94), including the numbers that used to be typed into the code (CORR, SPEC, C, the
   story's DATA, the pairs-dots USED list) and the 337 comments that used to sit inline in index.html.
   Known, explained differences are listed as NOTE, not as failures.

Exit code 0 = everything passes; 1 = something failed.
"""
import hashlib
import json
import re
import subprocess
import sys

SNAPSHOT = "d689e08"
fails, notes = [], []


def ok(cond, what):
    print(("PASS  " if cond else "FAIL  ") + what)
    if not cond:
        fails.append(what)


def snap(path):
    return subprocess.run(["git", "show", f"{SNAPSHOT}:site/{path}"], check=True, capture_output=True, text=True).stdout


def var(text, name):
    i = text.index("window." + name)
    return json.loads(text[i:].split("=", 1)[1].strip().rstrip(";"))


def jsobj(s):   # a JavaScript object literal with bare keys -> Python
    s = re.sub(r"([{,])\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', s)
    return json.loads(re.sub(r",\s*([}\]])", r"\1", s))


def data(name, v):
    return var(open(f"site/data/{name}", encoding="utf-8").read(), v)


# ---------------------------------------------------------------- 1. inputs unchanged
print("1. Inputs unchanged since each data file was built")
for name in ["pm25.js", "hand-coded-comments.js", "tone-counts.js", "cards.js", "quotes.js"]:
    head = open(f"site/data/{name}", encoding="utf-8").read().split("window.", 1)[0]
    pairs = re.findall(r"^//   (\S+)  ([0-9a-f]{64})$", head, re.M)
    changed = [p for p, h in pairs if hashlib.sha256(open(p, "rb").read()).hexdigest() != h]
    ok(pairs and not changed, f"{name}: {len(pairs)} inputs" + (f", changed: {', '.join(changed)}" if changed else ""))
    for line in re.findall(r"^// (.*COPIED.*)$", head, re.M):
        notes.append(f"{name}: {line}")

# ---------------------------------------------------------------- 2. same numbers as the published page
print("\n2. Same values as the published page (snapshot " + SNAPSHOT + ")")
page = snap("index.html")

a, b = data("pm25.js", "PM25"), var(snap("data.js"), "PM25")
notes.append(f"pm25.js: built date {a['built']} (published {b['built']}); the date is when build.py ran, not data")
a.pop("built"); b.pop("built")
ok(a == b, "pm25.js = published data.js (all cities, pairs, rho, verdict, weekly, Fairbanks months)")
ok(data("cards.js", "CARDS") == var(snap("card/cards-data.js"), "CARDS"), "cards.js = published card/cards-data.js")
ok(data("quotes.js", "QUOTES") == var(snap("card/quotes-data.js"), "QUOTES"), "quotes.js = published card/quotes-data.js")
q = json.loads(re.search(r'<script id="qdata" type="application/json">(.*?)</script>', page, re.S).group(1))
ok(data("hand-coded-comments.js", "HAND_CODED") == q, "hand-coded-comments.js = the 337 comments inline in the published page (same order)")

T = data("tone-counts.js", "TONE")
CORR = jsobj(re.search(r"const CORR=(\{.*?\});", page).group(1))
ok(T["corrected"] == CORR, "tone-counts.js corrected = CORR typed into the published page")
SPEC = jsobj(re.search(r"const SPEC = (\{.*?\n\});", page, re.S).group(1).replace("\n", ""))
ok(all(T["draft_read"][k] == SPEC[k]["read"] and T["draft_est"][k] == SPEC[k]["est"] and T["big_thread"][k] == SPEC[k]["big"] for k in SPEC),
   "tone-counts.js draft_read, draft_est, big_thread = SPEC typed into the published page")
body = re.search(r"const C=\{(.*?)\n\};", page, re.S).group(1)
C = {m.group(1): m.group(2) for m in re.finditer(r"\n (\w+):\{(.*?)\},?(?=\n|$)", body)}
pm = {c["slug"]: c for c in var(snap("data.js"), "PM25")["cities"]}
good = True
for k, s in C.items():
    good &= int(re.search(r"air:(\d+)", s).group(1)) == T["air_items"][k]
    good &= jsobj(re.search(r"read:(\{[^}]*\})", s).group(1)) == T["draft_read"][k]
    for f, src in [("pm", "pm"), ("rise", "rise"), ("bad", "bad_days"), ("ratio", "ratio")]:
        good &= float(re.search(rf"\b{f}:([\d.]+)", s).group(1)) == pm[k][src]
    if "big:" in s:
        good &= jsobj(re.search(r"big:(\{[^}]*\})", s).group(1)) == T["big_thread"][k]
ok(good and len(C) == 9, "C (how-they-talked) = values now read from pm25.js and tone-counts.js, all 9 cities")
d = re.search(r"const DATA=\{bakersfield:\{[^}]*ratio:([\d.]+),cnt:(\[[^\]]*\])\},indianapolis:\{[^}]*ratio:([\d.]+),cnt:(\[[^\]]*\])", page)
P = {c["slug"]: c for c in data("pm25.js", "PM25")["cities"]}
ok(float(d.group(1)) == round(P["bakersfield"]["rise"], 1) and float(d.group(3)) == round(P["indianapolis"]["rise"], 1)
   and json.loads(d.group(2)) == T["corrected"]["bakersfield"] and json.loads(d.group(4)) == T["corrected"]["indianapolis"],
   "story disks (DATA) = rise rounded to 1 decimal and corrected counts")
used = set(re.search(r'const USED = new Set\((\[[^\]]*\])\)', page).group(1).strip("[]").replace('"', "").replace(" ", "").split(","))
ok(used == {k for k, c in P.items() if c["bad_days"] >= 8}, "pairs-dots USED = cities with bad_days >= 8")

print("\nNOTE")
for n in notes:
    print("  " + n)
print(f"\n{'All checks passed.' if not fails else str(len(fails)) + ' check(s) FAILED.'}")
sys.exit(1 if fails else 0)
