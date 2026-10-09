"""Static 16:9 slide of the PM2.5 thresholds (WHO, EU, US EPA, China MEE) in the Boiling Frog deck style.
Writes thresholds-slide.html; render to PNG with headless Chrome (see bottom of file)."""
import math, pathlib

W, H = 1920, 1080
L, R = 330, 1840                  # plot x-range
LO, HI = 2, 400
INK, INK2, RULE, GROUND = "#1a0f6b", "#463d88", "#cdb88a", "#f8ebcb"
TIER = [0, .13, .30, .55]          # ink density for each step past a daily line
ROWS = [
    ("WHO", "World Health Organization", [(15, "above guideline", 0)], [(5, "annual", 0)]),
    ("EU", "European Commission", [(25, "exceedance day (2030 rule: max 18 a year)", 0)], [(10, "annual, from 2030", 0), (25, "annual, current limit", 1)]),
    ("US EPA", "Air Quality Index", [(35.5, "unhealthy for sensitive groups", 0), (55.5, "unhealthy", 1), (225.5, "hazardous", 0)], []),
    ("CHINA MEE", "Individual Air Quality Index", [(60, "light pollution", 0), (115, "moderate", 1), (250, "severe", 0)], []),
]
TICKS = [2, 5, 10, 15, 25, 50, 100, 250, 400]
x = lambda v: L + (math.log(v) - math.log(LO)) / (math.log(HI) - math.log(LO)) * (R - L)
fmt = lambda v: f"{v:g}"

TOP, ROW_H = 330, 152
s = []
a = s.append
bottom = TOP + len(ROWS) * ROW_H
for t in TICKS:
    a(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{TOP-20}" y2="{bottom}" stroke="{RULE}" stroke-width="1.5"/>')
    a(f'<text class="num" x="{x(t):.1f}" y="{bottom+34}" text-anchor="middle" font-size="20" fill="{INK2}">{t}</text>')
a(f'<text x="{L-24}" y="{bottom+34}" text-anchor="end" font-size="18" font-weight="500" fill="{INK2}">PM2.5, µg/m³ (log scale)</text>')

for i, (name, sub, daily, annual) in enumerate(ROWS):
    y = TOP + i * ROW_H + 52
    a(f'<text x="80" y="{y+8}" font-size="26" font-weight="700" letter-spacing="2.6" fill="{INK}">{name}</text>')
    a(f'<text x="80" y="{y+36}" font-size="18" fill="{INK2}">{sub}</text>')
    for j, (v, _, _) in enumerate(daily):
        end = daily[j+1][0] if j + 1 < len(daily) else HI
        op = TIER[min(3, j + 1 + (1 if len(daily) == 1 else 0))]
        a(f'<rect x="{x(v):.1f}" y="{y-11}" width="{x(end)-x(v):.1f}" height="22" fill="{INK}" opacity="{op}"/>')
    a(f'<line x1="{L}" x2="{R}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="2.5"/>')
    note = lambda v, txt, lvl, start: a(
        f'<text x="{x(v)+(8 if start else 0):.1f}" y="{y+40+lvl*24}" text-anchor="{"start" if start else "middle"}" font-size="19" fill="{INK2}">{txt}</text>')
    dv = {d[0] for d in daily}
    for v, txt, lvl in annual:
        big = v in dv
        a(f'<circle cx="{x(v):.1f}" cy="{y}" r="{14 if big else 10}" fill="{"none" if big else GROUND}" stroke="{INK}" stroke-width="3"/>')
        if not big:
            a(f'<text class="num" x="{x(v):.1f}" y="{y-22}" text-anchor="middle" font-size="24" font-weight="500" fill="{INK}">{fmt(v)}<tspan font-family="Jost" font-size="18" fill="{INK2}">/yr</tspan></text>')
        note(v, txt, lvl, big)
    for v, txt, lvl in daily:
        a(f'<circle cx="{x(v):.1f}" cy="{y}" r="8" fill="{INK}" stroke="{GROUND}" stroke-width="2"/>')
        a(f'<text class="num" x="{x(v):.1f}" y="{y-22}" text-anchor="middle" font-size="24" font-weight="500" fill="{INK}">{fmt(v)}</text>')
        note(v, txt, lvl, True)

# the WHO daily line, carried through every row
a(f'<line x1="{x(15):.1f}" x2="{x(15):.1f}" y1="{TOP+64}" y2="{bottom}" stroke="{INK}" stroke-width="2" stroke-dasharray="6 6"/>')

legend = f'''
<g transform="translate(1250 252)" font-size="19" fill="{INK}">
  <circle cx="8" cy="-6" r="8" fill="{INK}"/><text x="26" y="0">24-hour limit</text>
  <circle cx="186" cy="-6" r="9" fill="{GROUND}" stroke="{INK}" stroke-width="3"/><text x="206" y="0">Annual-average limit</text>
  <rect x="420" y="-15" width="26" height="18" fill="{INK}" opacity="{TIER[1]}"/><rect x="448" y="-15" width="26" height="18" fill="{INK}" opacity="{TIER[2]}"/><rect x="476" y="-15" width="26" height="18" fill="{INK}" opacity="{TIER[3]}"/>
</g>
<text x="1772" y="282" text-anchor="end" font-size="16" fill="{INK2}">darker = further past a daily limit</text>'''

html = f'''<!doctype html><meta charset="utf-8"><title>PM2.5 thresholds slide</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&family=Jost:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
html, body {{ margin: 0; background: {GROUND}; }}
svg {{ display: block; }}
svg text {{ font-family: "Jost", "Futura", sans-serif; }}
svg .num {{ font-family: "IBM Plex Mono", Menlo, monospace; }}
svg .serif {{ font-family: "Libre Caslon Text", Georgia, serif; }}
</style>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="{W}" height="{H}" fill="{GROUND}"/>
<text x="80" y="92" font-size="20" font-weight="700" letter-spacing="2.8" fill="{INK}">WHO DRAWS THE LINE · PM2.5</text>
<line x1="80" x2="{W-80}" y1="110" y2="110" stroke="{INK}" stroke-width="2"/>
<text class="serif" x="80" y="190" font-size="62" font-weight="700" fill="{INK}">The same air gets four different verdicts</text>
<text class="serif" x="80" y="240" font-size="27" fill="{INK2}">The WHO flags a day at 15 µg/m³. China doesn’t call a day polluted until 60.</text>
{legend}
{''.join(s)}
<text x="80" y="{H-48}" font-size="16" fill="{INK2}">Rings are yearly averages; dots apply to a single day. EPA and China values are where the air quality index changes category (lower steps not shown).</text>
<text x="80" y="{H-24}" font-size="16" fill="{INK2}">Sources: WHO Global Air Quality Guidelines (2021); U.S. EPA AQI for PM2.5 (2024); China MEE HJ 633-2012; EU Directive 2024/2881.</text>
</svg>'''
out = pathlib.Path(__file__).with_name("thresholds-slide.html")
out.write_text(html)
print(out)
# Render: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
#   --window-size=1920,1080 --force-device-scale-factor=2 --virtual-time-budget=8000 \
#   --screenshot=thresholds-slide.png file://$PWD/thresholds-slide.html
