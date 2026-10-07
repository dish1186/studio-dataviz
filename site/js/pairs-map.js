// Moved from index.html (snapshot d689e08), line 1374; comments on calculations and sources added 2026-10-07; code unchanged.
// Interactive pairs map (after the pairs plate). Adapted from the map plate artifact; cities, numbers and pair
// results now come from data.js (lat/lon are the only additions: city-centre coordinates).
(() => {
const D = window.PM25, LL = { bakersfield: [35.37, -119.02], fairbanks: [64.84, -147.72], fresno: [36.74, -119.79], eugene: [44.05, -123.09],
  sanjose: [37.34, -121.89], indianapolis: [39.77, -86.16], seattle: [47.61, -122.33], detroit: [42.33, -83.05], pittsburgh: [40.44, -79.99] };
const CITIES = D.cities.map(c => ({ ...c, lat: LL[c.slug][0], lon: LL[c.slug][1] }));
const C = Object.fromEntries(CITIES.map(c => [c.slug, c]));
const PAIRS = D.pairs.filter(p => p.rise_worse != null && p.rise_other != null).map((p, i) => ({ type: p.type, a: p.worse, b: p.other, ok: p.outcome === "as Pos predicts", i }));
// CALCULATION · per pair: "more unusual" = the city with the higher ratio; "reacted more" = the city with the higher rise; ok = outcome "as Pos predicts"
PAIRS.forEach(p => { p.unusual = C[p.a].ratio > C[p.b].ratio ? p.a : p.b; p.more = C[p.a].rise > C[p.b].rise ? p.a : p.b; });
const COL = { matched: "var(--ink)", crossed: "var(--ink)" };   // pair type is told by solid vs dashed, not colour (brand.md)
const st = { dots: "size", pairs: "all", arrow: "off",   // arrowheads off (Gina, Oct 6); still in map settings
 labels: "on", lift: 45, hl: null };
try { Object.assign(st, JSON.parse(localStorage.getItem("bf-imap") || "{}"), { hl: null }); } catch (e) {}
st.arrow = "off"; st.pairs = "off";   // pair lines and arrowheads taken out (Gina, Oct 6), even for viewers who had them on
const f = (v, d = 1) => v == null ? "–" : Number(v).toFixed(d), fx = v => f(v, v >= 10 ? 0 : 1) + "×";

const W = 975, H = 610, svg = d3.select("#imap").attr("viewBox", `0 0 ${W} ${H}`);
US_STATES.features.forEach(ft => { const g = ft.geometry, polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
  polys.forEach(p => { if (d3.geoArea({ type: "Polygon", coordinates: p }) > 2 * Math.PI) p.forEach(r => r.reverse()); }); });
const proj = d3.geoAlbersUsa().fitExtent([[20, 20], [W - 20, H - 20]], US_STATES), path = d3.geoPath(proj);
svg.append("g").selectAll("path").data(US_STATES.features).join("path").attr("d", path)
  .attr("fill", "var(--ground)").attr("stroke", "var(--ink)").attr("stroke-width", .55).attr("stroke-linejoin", "round");
{ const ak = US_STATES.features.find(d => d.properties.n === "AK"), b = path.bounds(ak);
  svg.append("rect").attr("x", b[0][0] - 8).attr("y", b[0][1] - 8).attr("width", b[1][0] - b[0][0] + 16).attr("height", b[1][1] - b[0][1] + 16)
    .attr("fill", "none").attr("stroke", "var(--ink)").attr("stroke-dasharray", "3 3").attr("stroke-width", .8);
  svg.append("text").attr("x", b[0][0] - 6).attr("y", b[1][1] + 22).attr("font-size", 11).attr("fill", "var(--ink-2)").text("Alaska, shown smaller"); }
CITIES.forEach(c => { [c.x, c.y] = proj([c.lon, c.lat]); });
const defs = svg.append("defs");
["matched", "crossed"].forEach(t => defs.append("marker").attr("id", "marr-" + t).attr("viewBox", "0 0 10 10").attr("refX", 9).attr("refY", 5)
  .attr("markerWidth", 7).attr("markerHeight", 7).attr("orient", "auto-start-reverse").append("path").attr("d", "M0,0L10,5L0,10Z").attr("fill", COL[t]));
const gPairs = svg.append("g"), gCities = svg.append("g");
const LBL = { seattle: [10, -8, "start"], eugene: [-10, 4, "end"], sanjose: [-10, 4, "end"], fresno: [10, -4, "start"], bakersfield: [10, 12, "start"],
  fairbanks: [10, 4, "start"], indianapolis: [-10, 14, "end"], detroit: [8, -8, "start"], pittsburgh: [10, 12, "start"] };
// CALCULATION · dot radius = 3 + 17 × √(PM2.5 / 300) px: the area grows with worst-week PM2.5 (pm, data/pm25.js), plus a 3 px minimum
const rPM = v => 3 + 17 * Math.sqrt(v / 300);        // dot area ∝ PM2.5 (µg/m³)
const BEND = [1, .9, 1.1, 1.25, .8, 1, .75, 1.2, .95];
function arc(p) {
  const s = C[p.more === p.a ? p.b : p.a], t = C[p.more];
  const dx = t.x - s.x, dy = t.y - s.y, len = Math.hypot(dx, dy), k = BEND[p.i % BEND.length] * st.lift / 100;
  let nx = -dy / len, ny = dx / len; if (ny > 0) { nx = -nx; ny = -ny; }
  const mx = (s.x + t.x) / 2 + nx * len * k, my = (s.y + t.y) / 2 + ny * len * k, gap = 9 + (st.dots === "plain" ? 0 : rPM(t.pm) - 5);
  const dd = Math.hypot(t.x - mx, t.y - my), ex = t.x - (t.x - mx) / dd * gap, ey = t.y - (t.y - my) / dd * gap;
  return `M${s.x},${s.y}Q${mx},${my} ${ex},${ey}`;
}
const visible = p => st.pairs === "all" || st.pairs === p.type;
function pairTip(p) {
  const A = C[p.a], B = C[p.b], row = (lab, va, vb, fm) => `<tr><td>${lab}</td><td>${fm(va)}</td><td>${fm(vb)}</td></tr>`;
  return `<span class="k">${p.type} pair</span><div class="tn">${A.name} vs. ${B.name}</div>
    <table><tr><th></th><th>${A.name}</th><th>${B.name}</th></tr>${row("PM2.5", A.pm, B.pm, v => f(v, 0))}${row("× normal", A.ratio, B.ratio, fx)}${row("Air talk", A.rise, B.rise, fx)}</table>
    <div>${C[p.unusual].name} had the more unusual week; ${C[p.more].name} reacted more. <b>${p.ok ? "As predicted." : "Against the prediction."}</b></div>`;
}
function cityTip(c) {
  const n = PAIRS.filter(p => p.a === c.slug || p.b === c.slug).length;
  return `<div class="tn">${c.name}, ${c.state}</div><div style="font-size:12px;opacity:.85">${c.dates} · ${c.cause}</div>
    <div>PM2.5 ${f(c.pm, 0)} µg/m³ (normal ${f(c.pm_normal, 0)}) · ${fx(c.ratio)} its normal · air talk ${fx(c.rise)}</div><div class="k">In ${n} pair${n === 1 ? "" : "s"}</div>`;
}
const tip = document.getElementById("mtip");
function showTip(ev, html) { tip.innerHTML = html; tip.hidden = false; const tw = tip.offsetWidth, vw = document.documentElement.clientWidth;
  let left = ev.pageX + 16; if (left + tw > vw - 8) left = ev.pageX - tw - 16; tip.style.left = Math.max(8, left) + "px"; tip.style.top = (ev.pageY + 14) + "px"; }
const hideTip = () => { tip.hidden = true; };
function draw() {
  gPairs.selectAll("*").remove(); gCities.selectAll("*").remove();
  if (st.pairs !== "off") PAIRS.filter(visible).forEach(p => {
    const g = gPairs.append("g").attr("class", "mpair").attr("data-i", p.i).attr("tabindex", 0).attr("role", "img")
      .attr("aria-label", `${p.type} pair: ${C[p.a].name} and ${C[p.b].name}. ${C[p.more].name} reacted more, ${p.ok ? "as predicted" : "against the prediction"}.`);
    const d = arc(p);
    g.append("path").attr("d", d).attr("fill", "none").attr("stroke", "transparent").attr("stroke-width", 14);
    const ln = g.append("path").attr("d", d).attr("fill", "none").attr("stroke", COL[p.type]).attr("stroke-width", 2.6).attr("stroke-linecap", "round")
      .attr("stroke-dasharray", p.type === "crossed" ? "7 5" : null).attr("marker-end", st.arrow === "on" ? `url(#marr-${p.type})` : null);
    if (!p.ok) { const node = ln.node(), mid = node.getPointAtLength(node.getTotalLength() / 2);
      g.append("circle").attr("cx", mid.x).attr("cy", mid.y).attr("r", 8).attr("fill", "var(--ground-2)").attr("stroke", COL[p.type]).attr("stroke-width", 1.6);
      g.append("text").attr("x", mid.x).attr("y", mid.y + 4).attr("text-anchor", "middle").attr("font-size", 11).attr("font-weight", 700).attr("fill", COL[p.type]).text("✕"); }
    g.on("pointermove", ev => { setHl(p.i); showTip(ev, pairTip(p)); }).on("pointerleave", () => { setHl(null); hideTip(); })
     .on("focus", () => setHl(p.i)).on("blur", () => setHl(null));
  });
  CITIES.forEach(c => {
    const g = gCities.append("g").attr("class", "mcity").attr("data-slug", c.slug).attr("tabindex", 0).attr("role", "img")
      .attr("aria-label", `${c.name}, ${c.state}: worst week ${f(c.pm, 0)} µg/m³, ${fx(c.ratio)} its normal`);
    g.append("circle").attr("cx", c.x).attr("cy", c.y).attr("r", 14).attr("fill", "transparent");
    if (st.dots === "plain") g.append("circle").attr("cx", c.x).attr("cy", c.y).attr("r", 6.5).attr("fill", BF_DOTFILL(c.slug)).attr("stroke", "var(--event)").attr("stroke-width", 2);
    else {
      g.append("circle").attr("cx", c.x).attr("cy", c.y).attr("r", rPM(c.pm)).attr("fill", BF_DOTFILL(c.slug)).attr("fill-opacity", .9).attr("stroke", "var(--event)").attr("stroke-width", 2.2);
      if (st.dots === "both") g.append("circle").attr("cx", c.x).attr("cy", c.y).attr("r", rPM(c.pm_normal)).attr("fill", "var(--ground)").attr("stroke", "var(--ink)").attr("stroke-width", 1.8);
    }
    if (st.labels === "on") { const [dx, dy, an] = LBL[c.slug], push = st.dots === "plain" ? 0 : Math.max(0, rPM(c.pm) - 6) * Math.sign(dx);
      const t = g.append("text").attr("x", c.x + dx + push).attr("y", c.y + dy).attr("text-anchor", an).attr("font-size", 14.5).attr("font-weight", 700).attr("fill", "var(--ink)").text(c.name);
      t.clone(true).lower().attr("stroke", "var(--ground-2)").attr("stroke-width", 4).attr("stroke-linejoin", "round").attr("fill", "none"); }
    g.on("pointermove", ev => showTip(ev, cityTip(c))).on("pointerleave", hideTip);
  });
  drawLegend(); drawList(); sync();
  try { const { hl, ...keep } = st; localStorage.setItem("bf-imap", JSON.stringify(keep)); } catch (e) {}
}
function setHl(i) {
  st.hl = i; gPairs.selectAll(".mpair").classed("dim", function () { return i != null && +this.dataset.i !== i; });
  const p = i != null ? PAIRS.find(q => q.i === i) : null;
  gCities.selectAll(".mcity").classed("dim", function () { return p && this.dataset.slug !== p.a && this.dataset.slug !== p.b; });
  document.querySelectorAll(".pi").forEach(e => e.classList.toggle("on", +e.dataset.i === i));
}
function drawLegend() {
  const sw = (t, dash) => `<svg width="34" height="10" aria-hidden="true"><line x1="1" y1="5" x2="33" y2="5" stroke="${COL[t]}" stroke-width="2.6" ${dash ? 'stroke-dasharray="7 5"' : ""}/></svg>`;
  const ring = v => `<svg width="${2 * rPM(v) + 6}" height="${2 * rPM(v) + 6}" aria-hidden="true"><circle cx="${rPM(v) + 3}" cy="${rPM(v) + 3}" r="${rPM(v)}" fill="none" stroke="var(--event)" stroke-width="2"/></svg>`;
  let h = st.dots === "plain" ? BF_LEGEND(ring).replace(/<span>worst week[\s\S]*$/, "")
    : BF_LEGEND(ring) + (st.dots === "both" ? `<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="var(--ground)" stroke="var(--ink)" stroke-width="1.8"/></svg>Inner ring: the city's normal</span>` : "");
  if (st.pairs !== "off") h += `<span>${sw("matched")}Matched pair</span><span>${sw("crossed", true)}Crossed pair</span>` + (st.arrow === "on" ? `<span>▶ points at the city that reacted more</span>` : "") + `<span>✕ went against the prediction</span>`;
  document.getElementById("ilegend").innerHTML = h;
}
function drawList() {
  const box = document.getElementById("iplist");
  // the results list always shows every pair, even though the map no longer draws pair lines (Gina, Oct 6)
  const mode = st.pairs === "off" ? "all" : st.pairs;
  const sw = t => `<svg width="30" height="10" aria-hidden="true"><line x1="1" y1="5" x2="29" y2="5" stroke="${COL[t]}" stroke-width="2.6" ${t === "crossed" ? 'stroke-dasharray="6 4"' : ""}/></svg>`;
  const vis = PAIRS.filter(p => mode === "all" || p.type === mode), ok = vis.filter(p => p.ok).length;
  let h = `<div class="ptally"><b>${ok} of ${vis.length}</b> ${mode === "all" ? "" : mode + " "}pairs went the way the study predicted</div>`;
  ["matched", "crossed"].filter(t => mode === "all" || mode === t).forEach(t => {
    h += `<div class="pgrp"><h3>${t === "matched" ? "Matched · about equally harmful air" : "Crossed · one worse, one more unusual"}</h3>`;
    PAIRS.filter(p => p.type === t).forEach(p => {
      h += `<details class="pi" data-i="${p.i}"><summary>${sw(t)}<span class="nm">${C[p.a].name} vs. ${C[p.b].name}</span>
        <span class="res ${p.ok ? "" : "no"}">${p.ok ? "As predicted" : "Against"}</span></summary>
        <div class="why">More unusual: ${C[p.unusual].name} (${fx(C[p.unusual].ratio)}). Reacted more: ${C[p.more].name} (${fx(C[p.more].rise)}).</div>
        <svg class="pchart" role="img" aria-label="${C[p.a].name} vs ${C[p.b].name}: ${[C[p.a], C[p.b]].map(c => `${c.name} ${fx(c.ratio)} unusual, ${fx(c.rise)} air talk`).join("; ")}. ${p.ok ? "As predicted" : "Against prediction"}."></svg></details>`;
    });
    h += `</div>`;
  });
  box.innerHTML = h;
  box.querySelectorAll(".pi").forEach(e => e.addEventListener("toggle", () => { if (e.open) pairChart(e.querySelector(".pchart"), PAIRS.find(q => q.i === +e.dataset.i)); }));
  box.querySelectorAll(".pi").forEach(e => { e.addEventListener("mouseenter", () => setHl(+e.dataset.i)); e.addEventListener("mouseleave", () => setHl(null));
    e.addEventListener("focusin", () => setHl(+e.dataset.i)); e.addEventListener("focusout", () => setHl(null)); });
}
// "Distance from normal" for one pair, as in the Boiling Frog Pairs artifact: the line is each city's normal week;
// the indigo dot sits above it by the air-talk jump, the magenta dot below it by how unusual the air was (log scale, 1× to 50×).
function pairChart(el, p) {
  const svg = d3.select(el); svg.selectAll("*").remove();
  // CALCULATION · pair chart: rise drawn upward and ratio downward from the middle line, both on a log scale from 1× to 50×
  const W = 320, half = 78, sp = 26 + 78, H = 26 + 78 * 2 + 64, d = d3.scaleLog([1, 50], [0, half]), r = 7.5, cs = [C[p.a], C[p.b]];
  svg.attr("viewBox", `0 0 ${W} ${H}`);
  svg.append("text").attr("x", 10).attr("y", 16).attr("font-size", 10.5).attr("font-weight", 700).attr("letter-spacing", ".08em").attr("fill", "var(--ink)").text("↑ TALK");
  svg.append("text").attr("x", 10).attr("y", sp + half + 14).attr("font-size", 10.5).attr("font-weight", 700).attr("letter-spacing", ".08em").attr("fill", "var(--event-ink)").text("↓ UNUSUAL");
  const xs = [W / 2 - 34, W / 2 + 34];
  const nA = svg.append("text").attr("x", 10).attr("y", sp + 5).attr("font-family", "var(--display)").attr("font-weight", 700).attr("font-size", 16).attr("fill", "var(--ink)").text(cs[0].name);
  const nB = svg.append("text").attr("x", W - 10).attr("y", sp + 5).attr("text-anchor", "end").attr("font-family", "var(--display)").attr("font-weight", 700).attr("font-size", 16).attr("fill", "var(--ink)").text(cs[1].name);
  const ba = nA.node().getBBox(), bb = nB.node().getBBox();
  svg.insert("line", "text").attr("x1", ba.x + ba.width + 6).attr("x2", bb.x - 6).attr("y1", sp).attr("y2", sp).attr("stroke", "var(--ink)").attr("stroke-width", 1.5);
  cs.forEach((c, i) => svg.append("text").attr("class", "num").attr("x", i ? W - 10 : 10).attr("y", sp - 13).attr("text-anchor", i ? "end" : "start").attr("font-size", 11).attr("fill", "var(--ink-2)").text(`PM2.5 ${f(c.pm, 0)} µg/m³`));
  svg.append("line").attr("x1", xs[0]).attr("y1", sp - d(cs[0].rise)).attr("x2", xs[1]).attr("y2", sp - d(cs[1].rise)).attr("stroke", "var(--react)").attr("stroke-width", 1.4).attr("stroke-dasharray", "4 4");
  svg.append("line").attr("x1", xs[0]).attr("y1", sp + d(cs[0].ratio)).attr("x2", xs[1]).attr("y2", sp + d(cs[1].ratio)).attr("stroke", "var(--unusual-2)").attr("stroke-width", 1.4).attr("stroke-dasharray", "4 4");
  cs.forEach((c, i) => {
    const x = xs[i], uy = sp - d(c.rise), dy = sp + d(c.ratio), side = i ? 1 : -1, tx = x + side * (r + 5), an = i ? "start" : "end";
    svg.append("line").attr("x1", x).attr("x2", x).attr("y1", sp).attr("y2", uy).attr("stroke", "var(--react)").attr("stroke-width", 2);
    svg.append("line").attr("x1", x).attr("x2", x).attr("y1", sp).attr("y2", dy).attr("stroke", "var(--unusual-2)").attr("stroke-width", 2);
    svg.append("circle").attr("cx", x).attr("cy", uy).attr("r", r).attr("fill", "var(--react)").attr("stroke", "var(--ground)").attr("stroke-width", 1.5);
    svg.append("circle").attr("cx", x).attr("cy", dy).attr("r", r).attr("fill", "var(--unusual-2)").attr("stroke", "var(--ground)").attr("stroke-width", 1.5);
    svg.append("text").attr("class", "num").attr("x", tx).attr("y", uy + 4).attr("text-anchor", an).attr("font-size", 11).attr("fill", "var(--react)").text(fx(c.rise));
    svg.append("text").attr("class", "num").attr("x", tx).attr("y", dy + 4).attr("text-anchor", an).attr("font-size", 11).attr("fill", "var(--unusual-ink)").text(fx(c.ratio));
  });
  svg.append("text").attr("x", W / 2).attr("y", H - 24).attr("text-anchor", "middle").attr("font-size", 13).attr("font-weight", 700)
    .attr("fill", p.ok ? "var(--ink)" : "var(--event-ink)").text(p.ok ? "✓ As predicted" : "✗ Against prediction");
  svg.append("text").attr("x", W / 2).attr("y", H - 7).attr("text-anchor", "middle").attr("font-size", 11.5).attr("fill", "var(--ink-2)")
    .text(p.ok ? "More unusual city talked more" : "Less unusual city talked more");
}
function sync() {
  document.getElementById("ilift").value = st.lift; document.getElementById("ilift-o").textContent = st.lift ? st.lift + "%" : "flat";
  document.querySelectorAll(".imap-plate [data-ch]").forEach(row => row.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(st[row.dataset.ch] === b.dataset.o))));
}
document.getElementById("ilift").addEventListener("input", e => { st.lift = +e.target.value; draw(); });
document.querySelectorAll(".imap-plate [data-ch]").forEach(row => row.addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; st[row.dataset.ch] = b.dataset.o; draw(); }));
document.addEventListener("pointermove", e => { if (!e.target.closest("#imap .mpair, #imap .mcity, #map .mcity")) hideTip(); });   // the Plate V map shares this tooltip
addEventListener("scroll", hideTip, { passive: true });
draw();
})();
