// Moved from index.html (snapshot d689e08), line 1193; comments on calculations and sources added 2026-10-07; code unchanged.
// No data calculations in this file: layout and motion only.
// Plate I hero: Dish's pot (img/side/) and Claude's frog. Bubbles, water and blinking are decoration only;
// nothing here reads data.js.
(() => {
const NS = "http://www.w3.org/2000/svg";
const hero = document.getElementById("side-hero"), svg = document.getElementById("scene");
const steamG = document.getElementById("steam"), water = document.getElementById("water"), surface = document.getElementById("surface");
const frog = document.getElementById("frog"), pupils = [document.getElementById("pupils")], lids = [...frog.querySelectorAll(".lid")];
water.setAttribute("d", "M0,0");
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p && p.appendChild(e); return e; };
const OFF = 40;
const fit = () => svg.setAttribute("preserveAspectRatio", hero.clientWidth < hero.clientHeight * .9 ? "xMidYMid meet" : "xMidYMax meet");
fit(); new ResizeObserver(fit).observe(hero);                                   // pot translate
const lipY = u => 742 - u * 32 - Math.sin(u * Math.PI) * 55;   // top edge of Dish's water, x 315–1182
function waterPath(t, h) {                                    // wavy top edge; the mask keeps it inside the pot
  const pts = [];
  for (let i = 0; i <= 30; i++) {
    const u = i / 30, x = 300 + u * 890, amp = 5 + 11 * h;
    pts.push([x, lipY(Math.min(1, Math.max(0, (x - 315) / 867))) + 6 + Math.sin(u * 11 + t * (1.5 + 3 * h)) * amp + Math.sin(u * 23 - t * 2.2) * amp * .35]);
  }
  return "M" + pts.map(p => p.map(v => v.toFixed(1)).join(",")).join(" L") + " L1190,900 L300,900 Z";
}

// bubble clouds: puffs of 3–6 circles that rise in a curl, grow, and fade
const PALE = ["#ffffff", "#f1ecfa", "#e3daf3", "#d6cbee"];
let puffs = [], pops = [];
function addPuff(h) {
  const u = .12 + Math.random() * .76, x = 315 + u * 867, y = lipY(u) + OFF - 10;
  const g = el("g", {}, steamG), n = 3 + Math.floor(Math.random() * 4), R = 18 + Math.random() * 22;
  for (let i = 0; i < n; i++) el("circle", { cx: (Math.random() - .5) * R * 2.2, cy: (Math.random() - .5) * R * 1.4, r: R * (.55 + Math.random() * .6), fill: PALE[Math.floor(Math.random() * PALE.length)] }, g);
  puffs.push({ g, x0: x, y, age: 0, life: 5 + Math.random() * 4, vy: 70 + 110 * h, curl: (Math.random() < .5 ? -1 : 1) * (60 + Math.random() * 90), ph: Math.random() * 6 });
}
function addPop(h) {
  const u = .1 + Math.random() * .8, x = 315 + u * 867, y = lipY(u) + 8 + Math.random() * 30;
  const c = el("circle", { cx: x, cy: y, r: 0, fill: "none", stroke: "#fff", "stroke-width": 3, opacity: .9 }, surface);
  pops.push({ c, R: 6 + Math.random() * (10 + 12 * h), age: 0, life: .5 + Math.random() * .6 });
}

// eyes follow the cursor (pupils move within the eye)
let look = [0, 0], lookT = [0, 0];
addEventListener("pointermove", e => {
  const r = svg.getBoundingClientRect(), s = Math.min(r.width / 1390, r.height / 1250);   // "meet" scale
  const top = r.top + (svg.getAttribute("preserveAspectRatio").includes("YMid") ? (r.height - 1250 * s) / 2 : r.height - 1250 * s);
  const ex = r.left + (r.width - 1390 * s) / 2 + 718 * s, ey = top + (588 + OFF) * s;
  const dx = e.clientX - ex, dy = e.clientY - ey, d = Math.hypot(dx, dy) || 1, m = Math.min(1, d / 300);
  lookT = [dx / d * 6 * m, dy / d * 5 * m];
});

let H_ = 0, t0 = performance.now(), last = t0, nextBlink = 2;
function frame(now) {
  const dt = Math.max(0, Math.min(.05, (now - last) / 1000)), t = (now - t0) / 1000; last = now;
  const r = hero.getBoundingClientRect();
  if (r.height > 1 && r.bottom > 0) {
    const target = Math.max(0, Math.min(1, -r.top / (r.height * .7)), Math.min(.3, t / 45));
    H_ += (target - H_) * Math.min(1, dt * 2.5); const h = H_;
    water.setAttribute("d", waterPath(t, h));
    // frog: calm bob, sinks a little as it heats (the point: it doesn't notice)
    frog.setAttribute("transform", `translate(0,${(-21 + Math.sin(t * 1.3) * 5 + 26 * h).toFixed(2)})`);   // never rises above where Dish drew it
    look = [look[0] + (lookT[0] - look[0]) * Math.min(1, dt * 8), look[1] + (lookT[1] - look[1]) * Math.min(1, dt * 8)];
    pupils.forEach(p => p.setAttribute("transform", `translate(${look[0].toFixed(2)},${look[1].toFixed(2)})`));
    nextBlink -= dt;
    const b = nextBlink < 0 ? Math.max(0, 1 - Math.abs(nextBlink + .09) / .09) : 0;   // ~0.18 s blink
    lids.forEach(l => l.setAttribute("height", (b * 58).toFixed(1)));
    if (nextBlink < -.18) nextBlink = 2.5 + Math.random() * 3;

    if (Math.random() < dt * (.8 + 7 * h)) addPuff(h);
    puffs = puffs.filter(p => {
      p.age += dt; const f = p.age / p.life;
      p.y -= p.vy * dt;
      const x = p.x0 + Math.sin(p.ph + p.age * .9) * p.curl * Math.min(1, f * 2);
      const s = .35 + 1.3 * f;
      p.g.setAttribute("transform", `translate(${x.toFixed(1)},${p.y.toFixed(1)}) scale(${s.toFixed(3)})`);
      p.g.setAttribute("opacity", (Math.min(1, f * 6) * (1 - f) * (.55 + .4 * h)).toFixed(3));
      if (f >= 1 || p.y < -200) { p.g.remove(); return false; } return true;
    });
    if (Math.random() < dt * (1 + 14 * h)) addPop(h);
    pops = pops.filter(p => {
      p.age += dt; const f = p.age / p.life;
      p.c.setAttribute("r", (p.R * Math.sqrt(f)).toFixed(1)); p.c.setAttribute("opacity", (.9 * (1 - f * f)).toFixed(3));
      if (f >= 1) { p.c.remove(); return false; } return true;
    });
  }
  requestAnimationFrame(frame);
}
if (reduce) { for (let i = 0; i < 6; i++) { addPuff(.3); } puffs.forEach((p, i) => { p.y -= 120 + i * 90; p.g.setAttribute("transform", `translate(${p.x0},${p.y}) scale(.9)`); p.g.setAttribute("opacity", .7); }); }
else requestAnimationFrame(frame);
})();
