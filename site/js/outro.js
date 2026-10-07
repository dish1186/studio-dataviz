// Moved unchanged from index.html (snapshot d689e08), line 1977.
// Outro: fourteen frogs in Dish's pot, placed after her sketch. Each bobs on its own rhythm, blinks now and then,
// and turns its eyes toward the cursor. Same vector frog as Plate I. Decoration only; nothing here reads data.js.
(() => {
const NS = "http://www.w3.org/2000/svg", svg = document.getElementById("outro"), sec = svg.closest(".outro");
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p && p.appendChild(e); return e; };
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const S = .41;                                                 // frog scale (eye spacing in the sketch ≈ 84 px)
// [centre between the eyes x, eyes y], back rows first so front frogs overlap them
const SPOTS = [[828, 588], [1018, 598], [578, 620], [708, 628], [905, 630], [452, 652], [630, 653], [1050, 652], [808, 665],
               [695, 697], [488, 707], [918, 707], [770, 718], [585, 742]];
const BODY = `<path fill="var(--frog)" d="M576,600 C566,548 632,524 662,560 C705,566 760,566 792,556 C820,526 868,544 860,600 L868,668 C898,718 930,762 946,808 L950,880 L480,880 L484,830 C508,762 546,702 576,660 Z"/>
  <path fill="#fbeac7" d="M572,880 L572,800 C576,712 646,640 718,638 C806,640 852,706 852,800 L852,880 Z"/>
  <path fill="none" stroke="var(--frog)" stroke-width="6" stroke-linecap="round" d="M590,724 C626,676 676,656 718,656 C762,656 812,676 846,722"/>
  <circle cx="615" cy="588" r="27" fill="#fbeac7"/><circle cx="822" cy="588" r="27" fill="#fbeac7"/>`;
const host = document.getElementById("o-frogs"), defs = svg.querySelector("defs");
const frogs = SPOTS.map(([cx, ey], i) => {
  const cp = el("clipPath", { id: "ofc" + i }, defs);
  el("rect", { x: 0, y: 0, width: 1390, height: ey + 110 }, cp);   // the frog sits in the water: a flat cut, as in the sketch
  const outer = el("g", { "clip-path": `url(#ofc${i})` }, host);
  const bob = el("g", {}, outer);
  const g = el("g", { transform: `translate(${(cx - 718.5 * S).toFixed(1)},${(ey - 588 * S).toFixed(1)}) scale(${S})` }, bob);
  g.innerHTML = BODY;
  const pup = el("g", {}, g);
  el("ellipse", { cx: 615, cy: 588, rx: 17, ry: 21, fill: "#000" }, pup); el("ellipse", { cx: 822, cy: 588, rx: 17, ry: 21, fill: "#000" }, pup);
  const lids = [el("rect", { x: 586, y: 560, width: 60, height: 0, fill: "var(--frog)" }, g), el("rect", { x: 793, y: 560, width: 60, height: 0, fill: "var(--frog)" }, g)];
  return { cx, ey, bob, pup, lids, ph: Math.random() * 6.3, sp: 1.1 + Math.random() * .9, amp: 4 + Math.random() * 4,
           look: [0, 0], lookT: [0, 0], blink: 1 + Math.random() * 5 };
});

// eyes: each frog looks from its own position toward the cursor
let cursor = null;
addEventListener("pointermove", e => { cursor = [e.clientX, e.clientY]; if (reduce) aim(true); });
function aim(snap) {
  if (!cursor) return;
  const m = svg.getScreenCTM(); if (!m) return;
  const p = new DOMPoint(cursor[0], cursor[1]).matrixTransform(m.inverse());
  frogs.forEach(f => {
    const dx = p.x - f.cx, dy = p.y - f.ey, d = Math.hypot(dx, dy) || 1, k = Math.min(1, d / 260);
    f.lookT = [dx / d * 8 * k, dy / d * 7 * k];
    if (snap) { f.look = f.lookT.slice(); f.pup.setAttribute("transform", `translate(${f.look[0].toFixed(2)},${f.look[1].toFixed(2)})`); }
  });
}

// calm water, a few soft puffs, like the opening
const water = document.getElementById("o-water"), steam = document.getElementById("o-steam");
const lipY = u => 742 - u * 32 - Math.sin(u * Math.PI) * 55;
function waterPath(t) {
  const pts = [];
  for (let i = 0; i <= 30; i++) { const u = i / 30, x = 300 + u * 890;
    pts.push([x, lipY(Math.min(1, Math.max(0, (x - 315) / 867))) + 6 + Math.sin(u * 11 + t * 1.6) * 6 + Math.sin(u * 23 - t * 2.2) * 2]); }
  return "M" + pts.map(q => q.map(v => v.toFixed(1)).join(",")).join(" L") + " L1190,900 L300,900 Z";
}
const PALE = ["#ffffff", "#f1ecfa", "#e3daf3", "#d6cbee"];
let puffs = [];
function addPuff() {
  const u = .12 + Math.random() * .76, x = 315 + u * 867, y = lipY(u) - 30, R = 14 + Math.random() * 16;
  const g = el("g", {}, steam), n = 3 + Math.floor(Math.random() * 3);
  for (let i = 0; i < n; i++) el("circle", { cx: (Math.random() - .5) * R * 2.2, cy: (Math.random() - .5) * R * 1.4, r: R * (.55 + Math.random() * .6), fill: PALE[i % 4] }, g);
  puffs.push({ g, x0: x, y, age: 0, life: 5 + Math.random() * 3, vy: 60 + Math.random() * 30, curl: (Math.random() < .5 ? -1 : 1) * (40 + Math.random() * 60), ph: Math.random() * 6 });
}

water.setAttribute("d", waterPath(0));
if (reduce) return;
let t0 = performance.now(), last = t0;
(function frame(now) {
  const dt = Math.max(0, Math.min(.05, (now - last) / 1000)), t = (now - t0) / 1000; last = now;
  const r = sec.getBoundingClientRect();
  if (r.height > 1 && r.bottom > 0 && r.top < innerHeight) {
    water.setAttribute("d", waterPath(t));
    aim(false);
    frogs.forEach(f => {
      f.bob.setAttribute("transform", `translate(0,${(Math.sin(t * f.sp + f.ph) * f.amp).toFixed(2)})`);
      f.look = [f.look[0] + (f.lookT[0] - f.look[0]) * Math.min(1, dt * 8), f.look[1] + (f.lookT[1] - f.look[1]) * Math.min(1, dt * 8)];
      f.pup.setAttribute("transform", `translate(${f.look[0].toFixed(2)},${f.look[1].toFixed(2)})`);
      f.blink -= dt;
      const b = f.blink < 0 ? Math.max(0, 1 - Math.abs(f.blink + .09) / .09) : 0;
      f.lids.forEach(l => l.setAttribute("height", (b * 58).toFixed(1)));
      if (f.blink < -.18) f.blink = 2 + Math.random() * 5;
    });
    if (Math.random() < dt * .9) addPuff();
    puffs = puffs.filter(p => {
      p.age += dt; const f = p.age / p.life; p.y -= p.vy * dt;
      p.g.setAttribute("transform", `translate(${(p.x0 + Math.sin(p.ph + p.age * .9) * p.curl * Math.min(1, f * 2)).toFixed(1)},${p.y.toFixed(1)}) scale(${(.35 + 1.1 * f).toFixed(3)})`);
      p.g.setAttribute("opacity", (Math.min(1, f * 6) * (1 - f) * .6).toFixed(3));
      if (f >= 1) { p.g.remove(); return false; } return true;
    });
  }
  requestAnimationFrame(frame);
})(t0);
})();
