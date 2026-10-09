// Moved from card/index.html (snapshot d689e08), line 221; comments on calculations and sources added 2026-10-07; code unchanged.
/* WHERE THE NUMBERS COME FROM: data/cards.js (built by Gina + Claude on 2026-10-05; see the header of that file).
   pm, normal, ratio, rise, share_normal, share_event: the same values as data/pm25.js (see js/plates-shared.js for how each is made).
   daily:  daily PM2.5 from OpenAQ reference monitors, data/processed/openaq/step05_averages, from 2019-01-01.
   tone:   corrected counts A, J, E, N (spectrum_07_corrected/city_shares.csv, as CORR in js/how-they-talked.js).
   living_lo, living_hi: the 95% range of the corrected "living with it" share (city_shares.csv two_living_lo, two_living_hi).
   CALCULATIONS in this file:
     × over EPA / WHO  = pm / 35.5 or pm / 15
     response level    = Low under 5× rise, Medium 5× to under 15×, High 15× and up (level())
     reacting %        = round(100 × (A + J) / (A + J + E + N)); living with it % = 100 - reacting %
     biggest group     = the group with the largest corrected count
     air spiral        = one dot per week, at that week's mean of its daily PM2.5 values (the worst week shows pm);
                         colour by the line crossed (WHO 15, EPA 35.5); radius = 1.4 + 5 × √(min(PM2.5, 60) / 60) */
const K = window.CARDS, QU = window.QUOTES || {};
const ORDER = ["bakersfield", "indianapolis", "fresno", "pittsburgh", "eugene", "detroit", "fairbanks", "sanjose", "seattle"];
const SUB = { bakersfield: "r/bakersfield", indianapolis: "r/indianapolis", fresno: "r/fresno", pittsburgh: "r/pittsburgh", eugene: "r/Eugene",
  detroit: "r/Detroit", fairbanks: "r/fairbanks", sanjose: "r/SanJose", seattle: "r/Seattle" };
const EVENT = { bakersfield: "Winter inversion", indianapolis: "Canadian wildfire smoke", fresno: "Lightning Siege fires", pittsburgh: "Canadian wildfire smoke",
  eugene: "Labor Day fires", detroit: "Canadian wildfire smoke", fairbanks: "Interior Alaska wildfires", sanjose: "SCU Lightning Complex", seattle: "Labor Day fires (OR/WA)" };
const ABOUT = {
  bakersfield: ["Oil and agriculture", "San Joaquin Valley basin traps winter air", "Leans Republican (Kern County)"],
  indianapolis: ["Logistics, life sciences, government", "Flat Midwest; summer ozone, distant smoke", "Leans Democratic (Marion County)"],
  fresno: ["Agriculture and health care", "San Joaquin Valley; smoke and farm dust", "Swing county (Fresno County)"],
  pittsburgh: ["Health care, universities, tech", "River valleys; legacy industry, inversions", "Leans Democratic (Allegheny County)"],
  eugene: ["University, health care, wood products", "Willamette Valley; forests, fire smoke", "Leans Democratic (Lane County)"],
  detroit: ["Autos and health care", "Great Lakes; industry, Canadian smoke", "Strongly Democratic (Wayne County)"],
  fairbanks: ["Military bases, university, government", "Interior Alaska; winter inversions, summer fires", "Leans Republican (borough)"],
  sanjose: ["Tech (Silicon Valley)", "Bay Area; usually clean, fire smoke", "Strongly Democratic (Santa Clara County)"],
  seattle: ["Tech, aerospace, port", "Puget Sound; usually clean, late-summer smoke", "Strongly Democratic (King County)"] };
const ST = { CA: "California", IN: "Indiana", PA: "Pennsylvania", OR: "Oregon", MI: "Michigan", AK: "Alaska", WA: "Washington" };
const LL = { bakersfield: [35.37, -119.02], fairbanks: [64.84, -147.72], fresno: [36.74, -119.79], eugene: [44.05, -123.09], sanjose: [37.34, -121.89],
  indianapolis: [39.77, -86.16], seattle: [47.61, -122.33], detroit: [42.33, -83.05], pittsburgh: [40.44, -79.99] };
// unhealthy days a year = median count of days with PM2.5 >= 35.5, 2019–2025 (data/processed/openaq/step08_pm_normals/pm_normals.csv,
// median_days_ge_35_5_2019_2025); "used to it" cut-off = 8 days, the default on Dish's Boiling Frog Pots page
const BAD = { bakersfield: 12, fairbanks: 8, fresno: 8, detroit: 2, indianapolis: 1, seattle: 1, eugene: 0, sanjose: 0, pittsburgh: 0 }, USED_CUT = 8;
const THR = { epa: { v: 35.5, name: "EPA", lab: "EPA 35.5" }, who: { v: 15, name: "WHO", lab: "WHO 15" } };
const S = { k: "eugene", thr: "epa", tab: "air", u: 0, g: null };
try { const s = JSON.parse(localStorage.getItem("bf-cards3") || "{}"); Object.assign(S, s, { g: null }); } catch (e) {}
const save = () => { try { const { g, ...keep } = S; localStorage.setItem("bf-cards3", JSON.stringify(keep)); } catch (e) {} };
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const NS = "http://www.w3.org/2000/svg", E = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p && p.appendChild(e); return e; },
  T = (p, a, s) => { const e = E("text", a, p); e.textContent = s; return e; };
const fx = v => (v >= 10 ? v.toFixed(0) : v.toFixed(1)) + "×";
const D0 = Date.UTC(2019, 0, 1), dayIdx = iso => Math.round((Date.parse(iso + "T00:00:00Z") - D0) / 864e5);
// CALCULATION · response level from rise (× more air talk): High at 15× and up, Medium at 5×, else Low
const level = r => r >= 15 ? "High" : r >= 5 ? "Medium" : "Low";
const esc = s => s.replace(/[&<>"]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
const FINE = "Cormorant Garamond,Didot,Georgia,serif", LAB = "Jost,Futura,sans-serif", MONO = "IBM Plex Mono,monospace";
// SVG text keeps a readable size when a drawing is shown small: n is the size in viewBox units, min is the smallest on-screen px
const sz = (svg, vbW) => { const w = svg.getBoundingClientRect().width || vbW; return (n, min = 10.5) => Math.max(n, min * vbW / w).toFixed(1); };
// type roles (brand.md): text 16, comments 14, header 2 28 — in screen px, whatever size the drawing is shown at
const px = (svg, vbW) => { const w = svg.getBoundingClientRect().width || vbW; return n => (n * vbW / w).toFixed(1); };

/* ---------- top strip: one red line per day above the chosen line ---------- */
function strip(c) {
  const svg = document.getElementById("tl"), W = Math.max(300, svg.parentElement.clientWidth), H = 42, L = 4, R = 4, n = c.daily.length, x = i => L + (W - L - R) * i / (n - 1);
  const t = THR[S.thr], ev = dayIdx(c.week_start), MAG = css("--event"), HARM = css("--harm-3"), INK = css("--ink");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
  E("rect", { x: x(ev) - 3, y: 6, width: Math.max(6, x(ev + 7) - x(ev)) + 6, height: 16, fill: MAG, "fill-opacity": .15 }, svg);
  let cnt = 0;
  c.daily.forEach((v, i) => { if (v != null && v > t.v && !(i >= ev && i < ev + 7)) { cnt++; E("line", { x1: x(i), x2: x(i), y1: 12, y2: 22, stroke: HARM, "stroke-width": 1, "stroke-opacity": .8 }, svg); } });
  for (let i = ev; i < ev + 7; i++) E("line", { x1: x(i), x2: x(i), y1: 6, y2: 22, stroke: MAG, "stroke-width": 2 }, svg);
  E("line", { x1: L, x2: W - R, y1: 22, y2: 22, stroke: INK, "stroke-width": .8 }, svg);
  for (let y = 2019; y <= 2026; y++) { const i = Math.round((Date.UTC(y, 0, 1) - D0) / 864e5); E("line", { x1: x(i), x2: x(i), y1: 22, y2: 26, stroke: INK, "stroke-width": .8 }, svg);
    if (W > 420 || y % 2 === 1) T(svg, { x: x(i) + 2, y: 38, "font-size": 12, fill: css("--ink-2"), "font-family": LAB }, String(y)); }
  svg.setAttribute("aria-label", `${cnt} days above ${t.lab} µg/m³ from 2019 to 2026, outside the worst week (shaded)`);
}

/* ---------- state outline ---------- */
function outline(c) {
  const svg = document.getElementById("st"), f = (window.US_STATES ? US_STATES.features : []).find(q => q.properties.n === c.state);
  svg.setAttribute("viewBox", "0 0 120 120"); svg.innerHTML = ""; if (!f || !window.d3) return;
  const pj = d3.geoMercator().fitExtent([[10, 10], [110, 104]], f), [x, y] = pj([LL[S.k][1], LL[S.k][0]]);
  E("path", { d: d3.geoPath(pj)(f), fill: "none", stroke: css("--ink"), "stroke-width": 1, "stroke-linejoin": "round" }, svg);
  E("circle", { cx: x, cy: y, r: 5.5, fill: css(BAD[S.k] >= USED_CUT ? "--used" : "--ink"), stroke: css("--event"), "stroke-width": 2 }, svg);   // map dot: used to it (green) or not (ink), magenta ring = the worst week
  T(svg, { x: 60, y: 117, "text-anchor": "middle", "font-size": 9, fill: css("--ink-2"), "letter-spacing": ".08em", "font-family": LAB }, (ST[c.state] || c.state).toUpperCase());
}

/* ---------- air: every week 2019–2025 (plus the worst week); the slider unwinds the stacked years into a spiral ----------
   Position shows only time: angle = time of year (Jan at the top, clockwise; axes at Jan, Apr, Jul, Oct). PM2.5 is shown by
   colour (against the chosen line) and dot size, never by distance from the centre.
   Stacked: the seven years sit in a narrow band, 2019 innermost. Spiral: one loop per year, 2019 inside. */
const Z = 520, CC = Z / 2, CLIP = 60;
let AIR = null;
const dotCol = v => v > THR[S.thr].v ? css("--harm-3") : S.thr === "epa" && v > 15 ? css("--harm-2") : css("--harm-1");   // harmful = flame orange (brand.md)
const dotR = v => 1.4 + 5 * Math.sqrt(Math.min(v, CLIP) / CLIP);
function airBuild(c) {
  const svg = document.getElementById("air"); svg.setAttribute("viewBox", `0 0 ${Z} ${Z}`); svg.innerHTML = ""; const f = sz(svg, Z), P = px(svg, Z);
  const n = c.daily.length, ev = dayIdx(c.week_start);
  const doyOf = i => { const d = new Date(D0 + i * 864e5); return (d - Date.UTC(d.getUTCFullYear(), 0, 1)) / 864e5; }, yOf = i => new Date(D0 + i * 864e5).getUTCFullYear() - 2019;
  const nY = Math.max(7, yOf(ev) + 1), B0 = 70, BW = 12, sp0 = 15, SP1 = 196, gap = (SP1 - sp0) / nY;
  const stR = i => B0 + BW * Math.min(yOf(i), 6), spR = i => sp0 + gap * (yOf(i) + doyOf(i) / 365), ang = i => -Math.PI / 2 + doyOf(i) / 365 * 2 * Math.PI;
  const INK = css("--ink"), INK2 = css("--ink-2"), RX = 222;
  // time axes: Jan / Jul vertical, Apr / Oct horizontal
  [["JAN", -Math.PI / 2], ["APR", 0], ["JUL", Math.PI / 2], ["OCT", Math.PI]].forEach(([m, a]) => {
    E("line", { x1: CC, y1: CC, x2: (CC + RX * Math.cos(a)).toFixed(1), y2: (CC + RX * Math.sin(a)).toFixed(1), stroke: INK, "stroke-width": .7, "stroke-opacity": .4 }, svg);
    const lx = CC + (RX + 14) * Math.cos(a), ly = CC + (RX + 14) * Math.sin(a) + 4, anc = Math.abs(Math.cos(a)) < .5 ? "middle" : Math.cos(a) > 0 ? "start" : "end";
    T(svg, { x: (anc === "start" ? lx - 10 : anc === "end" ? lx + 10 : lx).toFixed(1), y: (Math.sin(a) < -.5 ? ly - 4 : Math.sin(a) > .5 ? ly + 6 : ly).toFixed(1), "text-anchor": anc, "font-size": P(14), "letter-spacing": ".3em", fill: INK, "font-family": LAB }, m); });
  const years = E("g", { opacity: 0 }, svg);
  [0, nY - 1].forEach(y => { const i = Math.min(n - 1, Math.round((Date.UTC(2019 + y, 0, 1) - D0) / 864e5)), r = spR(i);
    T(years, { x: CC + 6, y: CC - r + 4, "font-size": P(14), fill: INK2, "font-family": LAB, stroke: css("--ground"), "stroke-width": 3, "paint-order": "stroke" }, String(2019 + y)); });
  const pts = [], dots = E("g", {}, svg);
  for (let w = 0; w * 7 < n; w++) {
    const i = Math.min(n - 1, w * 7 + 3), isEv = Math.abs(i - (ev + 3)) <= 3;
    if (yOf(i) > 6 && !isEv) continue;   // stacked years are 2019–2025; the worst week is kept even when it falls in 2026
    const a = c.daily.slice(w * 7, w * 7 + 7).filter(v => v != null); if (a.length < 3 && !isEv) continue;
    const v = isEv ? c.pm : a.reduce((s, q) => s + q, 0) / a.length;
    pts.push({ v, ang: ang(i), rv: stR(i), rs: spR(i), isEv,
      el: E("circle", { r: isEv ? 9 : dotR(v).toFixed(2), fill: isEv ? css("--event") : dotCol(v), stroke: isEv ? css("--ground") : "none", "stroke-width": 2, "fill-opacity": isEv ? 1 : .8 }, dots) });
  }
  pts.sort((p, q) => p.isEv - q.isEv || p.v - q.v).forEach(p => dots.appendChild(p.el));   // bigger dots on top, worst week last
  // the worst week's label sits outside the dots, joined by a hairline
  const evp = pts.find(p => p.isEv), lab = E("g", {}, svg), lead = E("line", { stroke: css("--event"), "stroke-width": .8 }, lab), halo = { stroke: css("--ground"), "stroke-width": 4, "paint-order": "stroke" };
  const l1 = T(lab, { "font-size": P(14), fill: css("--event-ink"), "font-family": LAB, ...halo }, Math.round(c.pm) + " avg");
  const l2 = T(lab, { "font-size": P(16), fill: INK, "font-family": LAB, ...halo }, c.dates.replace(/,\s*\d{4}$/, "") + ", " + c.week_start.slice(0, 4));
  AIR = { pts, years, evp, lead, l1, l2, outS: B0 + BW * 6, outP: SP1 };
  airPlace();
}
function airPlace() {
  if (!AIR) return; const u = S.u, e = u * u * (3 - 2 * u);
  AIR.pts.forEach(p => { const r = p.rv + (p.rs - p.rv) * e; p.el.setAttribute("cx", (CC + r * Math.cos(p.ang)).toFixed(1)); p.el.setAttribute("cy", (CC + r * Math.sin(p.ang)).toFixed(1)); });
  AIR.years.setAttribute("opacity", Math.max(0, e * 1.6 - .6).toFixed(2));
  const p = AIR.evp; if (!p) return;
  const r = p.rv + (p.rs - p.rv) * e, ca = Math.cos(p.ang), sa = Math.sin(p.ang), out = AIR.outS + (AIR.outP - AIR.outS) * e + 26;
  const lr = Math.max(out, r + 26), lx = CC + lr * ca, ly = CC + lr * sa, anc = ca >= 0 ? "start" : "end", dx = ca >= 0 ? 4 : -4;
  AIR.lead.setAttribute("x1", (CC + (r + 10) * ca).toFixed(1)); AIR.lead.setAttribute("y1", (CC + (r + 10) * sa).toFixed(1));
  AIR.lead.setAttribute("x2", lx.toFixed(1)); AIR.lead.setAttribute("y2", ly.toFixed(1));
  const X = Math.max(6, Math.min(Z - 6, lx + dx)), Y = Math.max(16, Math.min(Z - 22, ly));
  [AIR.l1, AIR.l2].forEach((t, k) => { t.setAttribute("text-anchor", anc); t.setAttribute("x", X.toFixed(1)); t.setAttribute("y", (Y + (k ? 14 : -4)).toFixed(1)); });
}

/* ---------- response: one stem and circle at the city's jump; the three levels named on the right ---------- */
function barometer(c) {
  const svg = document.getElementById("baro"), H = 440; svg.setAttribute("viewBox", `0 0 ${Z} ${H}`); svg.innerHTML = ""; const f = sz(svg, Z), P = px(svg, Z);
  const top = 40, bot = H - 30, ax = 230, y = v => bot - (Math.log(Math.min(40, Math.max(3.5, v))) - Math.log(3.5)) / (Math.log(40) - Math.log(3.5)) * (bot - top);
  const INK = css("--ink"), INK2 = css("--ink-2"), lv = level(c.rise), my = y(c.rise);
  E("line", { x1: ax, x2: ax, y1: top, y2: bot, stroke: INK, "stroke-width": 1, "stroke-opacity": .25 }, svg);
  [5, 15].forEach(v => E("line", { x1: ax - 10, x2: Z - 40, y1: y(v), y2: y(v), stroke: INK, "stroke-width": .7, "stroke-opacity": .4, "stroke-dasharray": "1 4" }, svg));
  [[3.5, 5, "LOW", "under 5×"], [5, 15, "MEDIUM", "5–15×"], [15, 40, "HIGH", "15× and up"]].forEach(([a, b, l, rng]) => { const on = l === lv.toUpperCase(), cy = (y(a) + y(b)) / 2, o = on ? 1 : .45;
    T(svg, { x: ax + 70, y: cy - 2, "font-size": P(14), "letter-spacing": ".3em", fill: INK, "fill-opacity": o, "font-family": LAB, "font-weight": on ? 600 : 400 }, l);
    T(svg, { x: ax + 70, y: cy + 20, "font-size": P(16), fill: INK2, "fill-opacity": o, "font-family": LAB }, rng); });
  const col = css("--react"), rb = { Low: 14, Medium: 20, High: 27 }[lv];   // reaction = pot indigo; the ball grows from low to high (brand.md)
  E("line", { x1: ax, x2: ax, y1: bot, y2: my, stroke: col, "stroke-width": 1.6 }, svg);
  E("circle", { cx: ax, cy: my, r: rb, fill: col }, svg);
  T(svg, { x: ax - rb - 14, y: my + 10, "text-anchor": "end", "font-size": P(28), "font-weight": 700, fill: col, "font-family": LAB }, fx(c.rise));
  svg.setAttribute("aria-label", `${c.name}: ${fx(c.rise)} more air talk, ${lv.toLowerCase()} response`);
}

/* ---------- sentiment: the talk disk, drawn as in Dish's Air Talk Disks plate (riso palette, grain, dot screen, split) ---------- */
const GR = [{ k: "A", n: "Alarm" }, { k: "J", n: "Adjusting" }, { k: "E", n: "Enduring" }, { k: "N", n: "Normalizing" }];
const SPOKES = [-135, 135, 45, -45].map(d => d * Math.PI / 180);
const RISO = [["#f2643c", "#ec4f9a", "#8a4fe0", "#2a9d9a"], ["#ff7a52", "#ff6fb0", "#a77bff", "#3fc4c0"]];
function hexMix(a, b, t) { const h = x => [1, 3, 5].map(i => parseInt(x.slice(i, i + 2), 16)), A = h(a), B = h(b); return "#" + A.map((x, i) => Math.round(x + (B[i] - x) * t).toString(16).padStart(2, "0")).join(""); }
function hueAt(u) { const P = RISO[css("--ground").toLowerCase() === "#160d4c" ? 1 : 0], t = Math.min(1, Math.max(0, u / 4)) * (P.length - 1), k = Math.min(P.length - 2, Math.floor(t)); return hexMix(P[k], P[k + 1], t - k); }
const GCOL = () => GR.map((g, i) => hueAt(i + .5));
const pt = (c, r, a) => [c + r * Math.cos(a), c + r * Math.sin(a)];
function blob(c, rs, an, pinch) { const P = [], n = rs.length; for (let i = 0; i < n; i++) { const j = (i + 1) % n, am = an[i] + ((an[j] - an[i] + 4 * Math.PI) % (2 * Math.PI)) / 2; P.push(pt(c, rs[i], an[i])); P.push(pt(c, Math.min(rs[i], rs[j]) * pinch + 5, am)); }
  const m = P.length; let d = `M${P[0][0].toFixed(1)},${P[0][1].toFixed(1)}`; for (let i = 0; i < m; i++) { const p0 = P[(i - 1 + m) % m], p1 = P[i], p2 = P[(i + 1) % m], p3 = P[(i + 2) % m];
    d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)},${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)},${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`; } return d + "Z"; }
function grain(defs, id) {   // Dish's grain: keep each pixel only where the shape is denser than a noise field
  const f = E("filter", { id, filterUnits: "userSpaceOnUse", x: -40, y: -40, width: 380, height: 380, "color-interpolation-filters": "sRGB" }, defs);
  E("feTurbulence", { type: "fractalNoise", baseFrequency: "0.95", numOctaves: 2, seed: 7, result: "nz" }, f);
  E("feColorMatrix", { in: "nz", type: "matrix", values: "0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.6 0 0 0 -0.3", result: "na" }, f);
  E("feColorMatrix", { in: "SourceGraphic", type: "matrix", values: "0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0", result: "sa" }, f);
  E("feComposite", { in: "sa", in2: "na", operator: "arithmetic", k1: 0, k2: 2.4, k3: -1.4, k4: .15, result: "mask" }, f);
  E("feComposite", { in: "SourceGraphic", in2: "mask", operator: "in" }, f);
}
function talkDisk(c) {
  const svg = document.getElementById("talk"), VB = 400; svg.setAttribute("viewBox", `-50 -50 ${VB} ${VB}`); svg.innerHTML = ""; const f = sz(svg, VB), P = px(svg, VB);
  const cx = 150, R = 96, RR = R + 34, tn = c.tone, cnt = GR.map(g => tn[g.k]), tot = cnt.reduce((a, b) => a + b, 0), sh = cnt.map(x => x / tot), mx = Math.max(...sh);
  const INK = css("--ink"), GC = GCOL(), step = Math.PI / 2, ord = [0, 1, 2, 3].sort((i, j) => SPOKES[i] - SPOKES[j]), pick = a => ord.map(i => a[i]);
  const defs = E("defs", {}, svg);
  // dot screen, fading toward the rim
  const pat = E("pattern", { id: "ht", width: 9, height: 9, patternUnits: "userSpaceOnUse", x: cx, y: cx }, defs); E("circle", { cx: 4.5, cy: 4.5, r: .75, fill: INK }, pat);
  const rg = E("radialGradient", { id: "rf", cx, cy: cx, r: RR, gradientUnits: "userSpaceOnUse" }, defs); [[0, 1], [.65, .9], [1, 0]].forEach(([o, a]) => E("stop", { offset: o, "stop-color": "#fff", "stop-opacity": a }, rg));
  const m = E("mask", { id: "hm", maskUnits: "userSpaceOnUse", x: -40, y: -40, width: 380, height: 380 }, defs); E("circle", { cx, cy: cx, r: RR, fill: "url(#rf)" }, m);
  E("circle", { cx, cy: cx, r: RR, fill: "url(#ht)", opacity: .34, mask: "url(#hm)" }, svg);
  // the reacting | living-with-it split
  E("line", { x1: cx, x2: cx, y1: cx - RR - 8, y2: cx + RR + 8, stroke: css("--split"), "stroke-width": .8, "stroke-opacity": .7 }, svg);
  // the two sides, named at the top of the split
  const rx = Math.round(100 * (sh[0] + sh[1])), yT = cx - RR - 14, gap = +P(18);   // label gaps in screen px, so bigger type never collides
  [["REACTING", rx, "end", -8], ["LIVING WITH IT", 100 - rx, "start", 8]].forEach(([l, v, anc, dx]) => {
    T(svg, { x: cx + dx, y: (yT - gap).toFixed(1), "text-anchor": anc, "font-size": P(14), "letter-spacing": ".16em", fill: INK, "font-family": LAB }, l);
    T(svg, { x: cx + dx, y: yT, "text-anchor": anc, "font-size": P(16), fill: INK, "font-family": LAB }, v + "%"); });
  // spokes
  SPOKES.forEach(a => { const [xa, ya] = pt(cx, R * .22, a), [x, y] = pt(cx, R + 38, a); E("line", { x1: xa.toFixed(1), y1: ya.toFixed(1), x2: x.toFixed(1), y2: y.toFixed(1), stroke: INK, "stroke-width": .75, "stroke-opacity": .45 }, svg); });
  // the shape: coloured wedges, blurred so the hues blend, clipped to the outline and grained
  const tgt = sh.map(x => R * Math.min(1.08, .18 + 1.9 * x)),   // Dish's outline, stretched a little more (1.9 instead of 1.3) so it fills the bigger disk
   cp = E("clipPath", { id: "dc" }, defs); E("path", { d: blob(cx, pick(tgt), pick(SPOKES), .42) }, cp);
  grain(defs, "gr"); const fb = E("filter", { id: "wb", filterUnits: "userSpaceOnUse", x: -40, y: -40, width: 380, height: 380 }, defs); E("feGaussianBlur", { stdDeviation: 9 }, fb);
  const gi = E("g", { "clip-path": "url(#dc)" }, E("g", { filter: "url(#gr)" }, svg)), gb = E("g", { filter: "url(#wb)" }, gi);
  SPOKES.forEach((a, i) => { const r = R + 40, [x0, y0] = pt(cx, r, a - step / 2), [x1, y1] = pt(cx, r, a + step / 2), dim = S.g && S.g !== GR[i].k;
    E("path", { d: `M${cx},${cx}L${x0.toFixed(1)},${y0.toFixed(1)}A${r},${r} 0 0 1 ${x1.toFixed(1)},${y1.toFixed(1)}Z`, fill: GC[i], "fill-opacity": ((.4 + .6 * sh[i] / mx) * (dim ? .6 : 1)).toFixed(3) }, gb); });
  E("circle", { cx, cy: cx, r: 2.6, fill: INK }, svg);
  // group names and shares: clickable, open the quotes
  SPOKES.forEach((a, i) => { const [x, y] = pt(cx, R + 50, a), ca = Math.cos(a), anc = ca > 0 ? "start" : "end", up = Math.sin(a) < 0, g = GR[i], on = S.g === g.k;
    const gp = +P(18), y1 = up ? y - 2 - gp : y + +P(12), grp = E("g", { class: "grp", tabindex: 0, role: "button", "aria-pressed": String(on), "aria-label": `${g.n} ${Math.round(100 * sh[i])}%: show quotes` }, svg);
    const box = E("rect", { class: "hit", fill: "transparent", stroke: on ? GC[i] : "none", "stroke-width": 1 }, grp);
    const t1 = T(grp, { x: x.toFixed(1), y: y1.toFixed(1), "text-anchor": anc, "font-size": P(14), "letter-spacing": ".16em", fill: INK, "font-family": LAB }, g.n.toUpperCase());
    T(grp, { x: x.toFixed(1), y: (y1 + gp).toFixed(1), "text-anchor": anc, "font-size": P(16), fill: INK, "font-family": LAB }, Math.round(sh[i] * 100) + "%");
    // the box is fitted to the drawn text (name + share), so it always wraps both, at any size; letter-spacing trails the last letter, so trim it
    const fitBox = () => { grp.removeAttribute("transform"); box.setAttribute("width", 0); box.setAttribute("height", 0);
      const b0 = grp.getBBox(), over = Math.max(0, b0.x + b0.width + 8 - 350) - Math.max(0, -50 + 8 - b0.x);   // keep the label (and its box) inside the drawing
      if (over) grp.setAttribute("transform", `translate(${(-over).toFixed(1)},0)`);
      const b = grp.getBBox(), ls = .26 * parseFloat(t1.getAttribute("font-size")), pad = 6;
      const x0 = anc === "start" ? b.x : b.x + ls, w = b.width - ls;
      box.setAttribute("x", (x0 - pad).toFixed(1)); box.setAttribute("y", (b.y - pad).toFixed(1)); box.setAttribute("width", (w + 2 * pad).toFixed(1)); box.setAttribute("height", (b.height + 2 * pad).toFixed(1)); };
    fitBox(); if (document.fonts) document.fonts.ready.then(fitBox);
    const go = () => { S.g = S.g === g.k ? null : g.k; drawSent(); };
    grp.addEventListener("click", go); grp.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } }); });
  const dom = sh.indexOf(mx);
  document.getElementById("dlead").innerHTML = `<span class="disc">${Math.round(tot)}</span><span>air posts and comments</span>`;
}
function drawSent() {
  const c = K[S.k], tn = c.tone, tot = tn.A + tn.J + tn.E + tn.N, react = Math.round(100 * (tn.A + tn.J) / tot), GC = GCOL();
  document.getElementById("s-share").innerHTML = `<b>${react}%</b> reacting<br><b>${100 - react}%</b> living with it`;
  const top = [...GR].sort((a, b) => tn[b.k] - tn[a.k])[0];
  document.getElementById("s-sub").textContent = `${top.n} was the biggest group in ${c.name}'s air talk (${Math.round(100 * tn[top.k] / tot)}%).`;
  document.getElementById("legend").innerHTML = GR.map((g, i) => `<button data-g="${g.k}" style="--c:${GC[i]}" aria-pressed="${S.g === g.k}"><i></i>${g.n}</button>`).join("");
  const box = document.getElementById("quotes"), gi = GR.findIndex(q => q.k === S.g);
  document.getElementById("sgrid").classList.toggle("open", gi >= 0); box.hidden = gi < 0;
  if (gi >= 0) { const g = GR[gi], qs = (QU[S.k] || {})[g.k] || []; box.style.setProperty("--c", GC[gi]);
    box.innerHTML = `<header><h3><i></i>${g.n} · ${SUB[S.k]}</h3><button class="x" aria-label="Close quotes">×</button></header>` +
      (qs.length ? qs.map(q => `<blockquote>${esc(q.t)}</blockquote>`).join("") : `<p class="foot">No short quote in this group for ${c.name}.</p>`);
    box.querySelector(".x").addEventListener("click", () => { S.g = null; drawSent(); }); }
  talkDisk(c);   // drawn after the panel opens, so its text sizes fit the narrower column
}
document.getElementById("legend").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; S.g = S.g === b.dataset.g ? null : b.dataset.g; drawSent(); });

/* ---------- card ---------- */
function draw() {
  const c = K[S.k], t = THR[S.thr];
  document.querySelectorAll("#pick button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.k === S.k)));
  document.querySelectorAll("#thr button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === S.thr)));
  document.querySelectorAll(".tabs button").forEach(b => { const on = b.dataset.t === S.tab; b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1;
    document.getElementById(b.getAttribute("aria-controls")).hidden = !on; });
  document.getElementById("nm").innerHTML = `${c.name}<small>${c.state}</small>`;
  document.getElementById("c-wk").textContent = `worst week · ${c.dates}`;
  document.getElementById("c-pm").textContent = `${Math.round(c.pm)} µg/m³ worst week (normal ${Math.round(c.normal)})`;
  document.getElementById("c-ev").textContent = EVENT[S.k];
  document.getElementById("ab-h").textContent = `about ${c.name}`;
  const ab = ABOUT[S.k]; document.getElementById("ab").innerHTML = `<dt>Economy</dt><dd>${ab[0]}</dd><dt>Environment</dt><dd>${ab[1]}</dd><dt>Politics</dt><dd>${ab[2]}</dd>`;
  strip(c); outline(c);
  // air
  document.getElementById("a-pm").textContent = Math.round(c.pm);
  const bad = BAD[S.k], used = bad >= USED_CUT, ue = document.getElementById("a-used");
  ue.textContent = used ? "used to it" : "not used to it"; ue.classList.toggle("used", used);
  ue.title = `${bad} unhealthy day${bad === 1 ? "" : "s"} a year (median, 2019–2025); used to it = ${USED_CUT} or more`;
  document.getElementById("a-norm").textContent = `${fx(c.ratio)} normal`;
  document.getElementById("a-thr").textContent = `${(c.pm / t.v).toFixed(1)}× over ${t.name}`;
  document.getElementById("a-key").innerHTML = (S.thr === "epa"
    ? `<span><i style="background:var(--harm-1)"></i>up to WHO 15</span><span><i style="background:var(--harm-2)"></i>WHO 15 to EPA 35.5</span><span><i style="background:var(--harm-3)"></i>above EPA 35.5</span><span><i style="background:var(--event)"></i>worst week</span>`
    : `<span><i style="background:var(--harm-1)"></i>up to WHO 15</span><span><i style="background:var(--harm-3)"></i>above WHO 15</span><span><i style="background:var(--event)"></i>worst week</span>`) + `<span class="v">each dot is a week; bigger = worse air</span>`;
  document.getElementById("a-how").innerHTML = `
    <li>PM2.5 is the daily average from OpenAQ reference monitors in ${c.name}.</li>
    <li>Each dot is one week: the average of its 7 daily values (weeks with fewer than 3 days of data are left out). Weeks are 7-day blocks counted from Jan 1, 2019.</li>
    <li>The big number (${Math.round(c.pm)} µg/m³) is the average of the 7 days of the worst week, ${c.dates}${+c.week_start.slice(0, 4) > 2025 ? "; it is shown even though it falls after 2025" : ""}.</li>
    <li>Normal (${Math.round(c.normal)} µg/m³) is the median weekly average for the same calendar month, 2019–2025. ${fx(c.ratio)} normal = ${Math.round(c.pm)} ÷ ${Math.round(c.normal)}.</li>
    <li>${used ? "Used to it" : "Not used to it"}: ${c.name} has ${bad} unhealthy day${bad === 1 ? "" : "s"} a year (daily PM2.5 of 35.5 µg/m³ or more; median of 2019–2025). Cities with ${USED_CUT} or more a year count as used to it, the cut-off from Dish's Pots page.</li>
    <li>× over ${t.name} = ${Math.round(c.pm)} ÷ ${t.v}. Position shows only the time of year (Jan at the top, clockwise). Colour shows the line crossed; dot size grows with PM2.5 up to 60 µg/m³.</li>`;
  document.getElementById("unw").value = S.u;
  // response
  document.getElementById("r-lvl").textContent = `${level(c.rise)} response`;
  document.getElementById("r-big").innerHTML = `<b>${fx(c.rise)}</b> more air talk`;
  document.getElementById("r-t").textContent = `During its worst air week, air-related posts and comments in ${SUB[S.k]} went up ${fx(c.rise)}: from ${c.share_normal.toFixed(2)}% to ${c.share_event.toFixed(1)}% of everything posted.`;
  // the graphics are drawn once their pane is visible, so text sizes follow the drawn width
  if (S.tab === "air") airBuild(c); if (S.tab === "resp") barometer(c); if (S.tab === "sent") drawSent();
  save();
}
document.getElementById("pick").innerHTML = ORDER.map(k => `<button data-k="${k}">${K[k].name}</button>`).join("");
document.getElementById("pick").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { S.k = b.dataset.k; S.g = null; draw(); } });
document.getElementById("thr").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { S.thr = b.dataset.v; draw(); } });
const tabs = [...document.querySelectorAll(".tabs button")];
tabs.forEach((b, i) => { b.addEventListener("click", () => { S.tab = b.dataset.t; draw(); });
  b.addEventListener("keydown", e => { const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!d) return; const n = tabs[(i + d + tabs.length) % tabs.length]; S.tab = n.dataset.t; draw(); n.focus(); }); });
document.getElementById("unw").addEventListener("input", e => { S.u = +e.target.value; airPlace(); });
document.getElementById("unw").addEventListener("change", save);
let lastW = 0, rz; new ResizeObserver(() => { const w = document.getElementById("card").clientWidth; if (w === lastW) return; lastW = w; clearTimeout(rz); rz = setTimeout(draw, 80); }).observe(document.getElementById("card"));
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
new MutationObserver(draw).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
draw();
