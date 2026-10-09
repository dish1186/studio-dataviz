// Moved from index.html (snapshot d689e08), line 1283; comments on calculations and sources added 2026-10-07; code unchanged.
// No data calculations in this file: layout and motion only.
// Plate II: the figure walks past the doors as you scroll and stops in the light of the last one.
// Door geometry is traced from Dish's image (2000 px wide). Decoration only; nothing here reads data.js.
(() => {
const NS = "http://www.w3.org/2000/svg", plate = document.querySelector(".door-plate");
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p && p.appendChild(e); return e; };
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
// each door: left edge x, top and bottom y; right edge x, top and bottom y (a slightly tilted quad)
const D = [[62, 140, 385, 184, 117, 355], [486, 128, 368, 608, 100, 338], [910, 122, 368, 1032, 100, 338], [1255, 113, 330, 1358, 95, 310]]
  .map(([x, yt, yb, xr, ytr, ybr]) => ({ x, yt, yb, xr, ytr, ybr }));
const set = document.getElementById("door-set"), beams = document.getElementById("beams"), shadowG = document.getElementById("shadow"), walker = document.getElementById("walker");
const beamEls = D.map(d => {
  el("polygon", { points: `${d.x},${d.yt} ${d.xr},${d.ytr} ${d.xr},${d.ybr} ${d.x},${d.yb}`, fill: "var(--event)" }, set);
  el("polygon", { points: `${d.x},${d.yb - 62} ${d.xr},${d.ybr - 2} ${d.xr},${d.ybr} ${d.x},${d.yb}`, fill: "#ef9581" }, set);   // light on the doorway floor
  return el("polygon", { fill: "#eab198", opacity: 0 }, beams);
});
const shadow = el("polygon", { fill: "#3e484e", opacity: 0 }, shadowG);
const ss = t => t * t * (3 - 2 * t);
let pos = 0, t0 = performance.now();
function draw(p, t) {
  // walk door to door, pausing at each (first and last quarter of every leg)
  const f = Math.min(3, p * 3), k = Math.min(2, Math.floor(f)), u = f - k, e = ss(Math.min(1, Math.max(0, (u - .25) / .5)));
  const a = D[k], b = D[Math.min(3, k + 1)], moving = e > 0 && e < 1;
  const fx = a.x - 4 + (b.x - a.x) * e, fy = a.yb - 2 + (b.yb - a.yb) * e;
  pos = k + e;
  walker.setAttribute("transform", `translate(${fx.toFixed(1)},${(fy + (moving ? -Math.abs(Math.sin(t * 9)) * 3 : 0)).toFixed(1)})`);
  D.forEach((d, i) => {                          // the door the figure stands at throws its light out across the floor
    const w = Math.max(0, 1 - Math.abs(pos - i) * 1.6), L = (i === 3 ? 760 : 520) * ss(w);
    beamEls[i].setAttribute("points", `${d.x},${d.yb} ${d.xr},${d.ybr} ${d.xr + L * 1.08},${d.ybr + L * 1.08 * .32} ${d.x + L},${d.yb + L * .4}`);
    beamEls[i].setAttribute("opacity", (w > 0 ? .95 : 0).toFixed(2));
  });
  const near = Math.round(pos), wn = Math.max(0, 1 - Math.abs(pos - near) * 1.6), L = (near === 3 ? 760 : 520) * ss(wn) * .86;
  shadow.setAttribute("points", `${fx + 5},${fy} ${fx + 22},${fy - 3} ${fx + 22 + L},${fy - 3 + L * .3} ${fx + 4 + L},${fy + L * .345 + 8}`);   // falls inside the light, as in Dish's image
  shadow.setAttribute("opacity", (wn * .85).toFixed(2));
}
function progress() {
  const r = plate.getBoundingClientRect(), vh = innerHeight;
  return Math.min(1, Math.max(0, (vh * .8 - r.top) / (vh * .7)));   // starts as the plate rises into view, done by the time it reaches the top
}
if (reduce) draw(1, 0);
else (function loop(now) { if (plate.getBoundingClientRect().height > 1) draw(progress(), (now - t0) / 1000); requestAnimationFrame(loop); })(t0);
})();
