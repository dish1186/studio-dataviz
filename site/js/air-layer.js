// Moved unchanged from index.html (snapshot d689e08), line 2069.
// The boiling-frog air layer. Specks start sparse and thicken with scroll progress, too slowly to notice from one
// screen to the next; at the "So what?" plate everything snaps to clean air, then returns after it. Decoration only.
(() => {
const cv = document.getElementById("air"), ctx = cv.getContext("2d"), warm = document.getElementById("air-warm"), haze = document.getElementById("air-haze");
const sowhat = document.querySelector(".sowhat") || document.querySelector(".outro"), reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const st = { particles: true, warm: true, haze: false };
try { Object.assign(st, JSON.parse(localStorage.getItem("bf-air") || "{}")); } catch (e) {}
st.particles = false;   // dust specks off for now (Gina, Oct 5); the presenter control can still switch them on for a session
const COLS = ["#d4502a", "#e0592a", "#c8401f", "#ea6b3b", "#b93a1c"];
const START = 8, END = 950;           // specks per million screen pixels, top of the page → just before "So what?"
const MAX_WARM = .2, MAX_HAZE = .16;
let W = 0, H = 0, dpr = 1, pool = [];
function resize() {
  const oW = W, oH = H;
  dpr = Math.min(2, devicePixelRatio || 1); W = innerWidth; H = innerHeight;
  if (oW && oH) pool.forEach(q => { q.x *= W / oW; q.y *= H / oH; });   // a wider window spreads the specks, never leaves a bare strip
  cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const need = Math.ceil(END * W * H / 1e6);
  while (pool.length < need) pool.push({ x: Math.random() * W, y: Math.random() * H, vx: 0, vy: 0,
    s: Math.random() < .8 ? 1.5 + Math.random() * 1.5 : 3 + Math.random() * 1.5, c: COLS[Math.floor(Math.random() * COLS.length)],
    a: .35 + Math.random() * .45, f: 0 });
}
resize(); addEventListener("resize", resize);
// progress: 0 at the top, 1 just before "So what?" arrives; mostly a fourth power, so most of the page adds very little
function progress() {
  const end = Math.max(1, sowhat.getBoundingClientRect().top + scrollY - H * .6);
  const p = Math.min(1, Math.max(0, scrollY / end)); return .06 * p + .94 * p * p * p * p;
}
function clean() { if (!document.querySelector(".sowhat")) return false; const r = sowhat.getBoundingClientRect(); return r.top < H * .55 && r.bottom > H * .45; }   // "So what?" fills the screen
let k = 1, last = performance.now();
function frame(now) {
  const dt = Math.min(.05, (now - last) / 1000); last = now;
  const p = progress(), target = clean() ? 0 : 1;
  k += (target - k) * Math.min(1, dt * (target ? 1.2 : 14));       // snap off fast, come back slowly
  warm.style.opacity = st.warm ? (p * MAX_WARM * k).toFixed(3) : 0;
  haze.style.opacity = st.haze ? (p * MAX_HAZE * k).toFixed(3) : 0;
  haze.style.backdropFilter = st.haze && p > .6 && k > .5 ? `blur(${((p - .6) * 1.5).toFixed(2)}px)` : "none";
  ctx.clearRect(0, 0, W, H);
  if (st.particles && k > .01) {
    const n = Math.min(pool.length, Math.round((START + (END - START) * p) * W * H / 1e6));
    for (let i = 0; i < pool.length; i++) {
      const q = pool[i]; q.f += ((i < n ? 1 : 0) - q.f) * Math.min(1, dt * 1.5);   // new specks fade in, extra ones fade out
      if (q.f < .01) continue;
      if (!reduce) {                                                  // slow random drift, a slight lift like warm air
        q.vx += (Math.random() - .5) * 14 * dt; q.vy += ((Math.random() - .5) * 14 - 1.2) * dt;
        q.vx *= .985; q.vy *= .985; q.x += q.vx * dt * 6; q.y += q.vy * dt * 6;
        if (q.x < -5) q.x = W + 5; else if (q.x > W + 5) q.x = -5;
        if (q.y < -5) q.y = H + 5; else if (q.y > H + 5) q.y = -5;
      }
      ctx.globalAlpha = q.a * q.f * k; ctx.fillStyle = q.c; ctx.fillRect(q.x, q.y, q.s, q.s);
    }
    ctx.globalAlpha = 1;
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
// presenter control: a faint dot in the corner; open it to switch each effect on or off
const pane = document.getElementById("air-pane"), open = document.getElementById("air-open"), box = document.getElementById("air-ctl");
const sync = () => { document.querySelectorAll("[data-air]").forEach(b => b.setAttribute("aria-pressed", String(!!st[b.dataset.air])));
  try { localStorage.setItem("bf-air", JSON.stringify(st)); } catch (e) {} };
open.addEventListener("click", () => { pane.hidden = !pane.hidden; open.setAttribute("aria-expanded", String(!pane.hidden)); box.classList.toggle("open", !pane.hidden); });
document.querySelectorAll("[data-air]").forEach(b => b.addEventListener("click", () => { st[b.dataset.air] = !st[b.dataset.air]; sync(); }));
sync();
})();
