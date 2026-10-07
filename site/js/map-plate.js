// Moved from index.html (snapshot d689e08), line 1327; comments on calculations and sources added 2026-10-07; code unchanged.
// Plate V: the nine cities on a map, fixed view (dots sized by worst-week PM2.5; no pairs, no controls).
// Adapted from the map plate artifact; numbers come from data.js (lat/lon are the only additions: city-centre coordinates).
(() => {
const D = window.PM25, LL = { bakersfield: [35.37, -119.02], fairbanks: [64.84, -147.72], fresno: [36.74, -119.79], eugene: [44.05, -123.09],
  sanjose: [37.34, -121.89], indianapolis: [39.77, -86.16], seattle: [47.61, -122.33], detroit: [42.33, -83.05], pittsburgh: [40.44, -79.99] };
const CITIES = D.cities.map(c => ({ ...c, lat: LL[c.slug][0], lon: LL[c.slug][1] }));

const W = 975, H = 610, svg = d3.select("#map").attr("viewBox", `0 0 ${W} ${H}`);
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
const LBL = { seattle: [10, -8, "start"], eugene: [-10, 4, "end"], sanjose: [-10, 4, "end"], fresno: [10, -4, "start"], bakersfield: [10, 12, "start"],
  fairbanks: [10, 4, "start"], indianapolis: [-10, 14, "end"], detroit: [8, -8, "start"], pittsburgh: [10, 12, "start"] };
// CALCULATION · dot radius = 3 + 17 × √(PM2.5 / 300) px: the area grows with worst-week PM2.5 (pm, data/pm25.js), plus a 3 px minimum
const rPM = v => 3 + 17 * Math.sqrt(v / 300);        // dot area ∝ PM2.5 (µg/m³)
const bad = c => `about ${c.days_over_15} "bad" days a year`;

const tip = document.getElementById("mtip");
function showTip(ev, html) { tip.innerHTML = html; tip.hidden = false; const tw = tip.offsetWidth, vw = document.documentElement.clientWidth;
  let left = ev.pageX + 16; if (left + tw > vw - 8) left = ev.pageX - tw - 16; tip.style.left = Math.max(8, left) + "px"; tip.style.top = (ev.pageY + 14) + "px"; }
const hideTip = () => { tip.hidden = true; };
const cityTip = c => `<div class="tn">${c.name}, ${c.state}</div><div>${bad(c)[0].toUpperCase() + bad(c).slice(1)}</div><div style="font-size:12px;opacity:.85">days above 15 µg/m³, 2019–2025</div>`;

const gCities = svg.append("g");
CITIES.forEach(c => {
  const g = gCities.append("g").attr("class", "mcity").attr("data-slug", c.slug).attr("tabindex", 0).attr("role", "img")
    .attr("aria-label", `${c.name}, ${c.state}: ${bad(c)} above 15 µg/m³`);
  g.append("circle").attr("cx", c.x).attr("cy", c.y).attr("r", 14).attr("fill", "transparent");
  g.append("circle").attr("cx", c.x).attr("cy", c.y).attr("r", rPM(c.pm)).attr("fill", BF_DOTFILL(c.slug)).attr("fill-opacity", .9).attr("stroke", "var(--event)").attr("stroke-width", 2.2);
  const [dx, dy, an] = LBL[c.slug], push = Math.max(0, rPM(c.pm) - 6) * Math.sign(dx);
  const t = g.append("text").attr("x", c.x + dx + push).attr("y", c.y + dy).attr("text-anchor", an).attr("font-size", 14.5).attr("font-weight", 700).attr("fill", "var(--ink)").text(c.name);
  t.clone(true).lower().attr("stroke", "var(--ground-2)").attr("stroke-width", 4).attr("stroke-linejoin", "round").attr("fill", "none");
  g.on("pointermove", ev => showTip(ev, cityTip(c))).on("pointerleave", hideTip)
   .on("focus", function () { const r = this.getBoundingClientRect(); showTip({ pageX: r.right + scrollX, pageY: r.top + scrollY }, cityTip(c)); }).on("blur", hideTip);
});
const ring = v => `<svg width="${2 * rPM(v) + 6}" height="${2 * rPM(v) + 6}" aria-hidden="true"><circle cx="${rPM(v) + 3}" cy="${rPM(v) + 3}" r="${rPM(v)}" fill="none" stroke="var(--event)" stroke-width="2"/></svg>`;
document.getElementById("legend").innerHTML = BF_LEGEND(ring);
addEventListener("scroll", hideTip, { passive: true });
})();
