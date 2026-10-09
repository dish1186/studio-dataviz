// Moved from index.html (snapshot d689e08), line 1938; comments on calculations and sources added 2026-10-07; code unchanged.
// No data calculations in this file: layout and motion only.
// City cards (Gina + Claude, Oct 6). Replaces the four-city panel: any of the nine cities on the pairs map opens its card
// (card/index.html, the "Boiling Frog City Cards" mockup) in a panel to the right of the map. The card page reports its
// height and follows this page's theme; the selected city gets a magenta ring on the map. Does not change the map code.
(() => {
const stage = document.querySelector(".imap-plate .stage"), pan = document.getElementById("cc-panel"), fr = document.getElementById("cc-frame"),
  map = document.getElementById("imap"), nm = document.getElementById("cc-name");
if (!stage || !pan || !fr || !map) return;
let cur = null;
const send = msg => { try { fr.contentWindow && fr.contentWindow.postMessage(msg, "*"); } catch (e) {} };
const theme = () => document.documentElement.getAttribute("data-theme") || "";
function ring() {
  map.querySelectorAll(".cc-ring").forEach(n => n.remove()); if (!cur) return;
  const g = map.querySelector(`.mcity[data-slug="${cur}"]`); if (!g) return;
  const cs = [...g.querySelectorAll("circle")], vis = cs.filter(c => c.getAttribute("fill") !== "transparent"), c0 = cs[0];
  const r = Math.max(5.5, ...vis.map(c => +c.getAttribute("r") || 0)) + 5;
  const el = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  Object.entries({ class: "cc-ring", cx: c0.getAttribute("cx"), cy: c0.getAttribute("cy"), r, fill: "none", stroke: "var(--select)", "stroke-width": 2.5, "pointer-events": "none" }).forEach(([k, v]) => el.setAttribute(k, v));
  g.appendChild(el);
}
function open(k) {
  const g = map.querySelector(`.mcity[data-slug="${k}"]`); cur = k;
  nm.textContent = (g && (g.getAttribute("aria-label") || "").split(":")[0]) || "city card";
  if (!fr.getAttribute("src")) fr.setAttribute("src", `card/index.html#${k}`); else send({ bfCity: k, bfTheme: theme() });
  pan.hidden = false; stage.classList.add("cc-open"); ring();
  requestAnimationFrame(() => pan.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest" }));
}
function close() { cur = null; pan.hidden = true; stage.classList.remove("cc-open"); ring(); }
fr.addEventListener("load", () => send({ bfCity: cur, bfTheme: theme() }));
addEventListener("message", e => { if (e.source !== fr.contentWindow) return; const h = e.data && e.data.bfCardH; if (h > 0) fr.style.height = Math.ceil(h) + "px"; });
document.getElementById("cc-x").addEventListener("click", close);
map.addEventListener("click", e => { const g = e.target.closest(".mcity"); if (g) open(g.dataset.slug); });
map.addEventListener("keydown", e => { if (e.key !== "Enter" && e.key !== " ") return; const g = e.target.closest(".mcity"); if (g) { e.preventDefault(); open(g.dataset.slug); } });
// the map redraws its cities when its settings change: put the ring back
new MutationObserver(() => { if (cur && !map.querySelector(".cc-ring")) ring(); }).observe(map, { childList: true, subtree: true });
new MutationObserver(() => send({ bfTheme: theme() })).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
})();
