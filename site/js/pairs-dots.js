// Moved unchanged from index.html (snapshot d689e08), line 1852.
// Pairs dots (Dish's mockup, Oct 6). Slide 1: the nine cities in a row (indigo = used to bad air, green = not). Slide 2: the
// heading changes and the dots slide into the three matched and six crossed pairs; a city in several pairs splits into copies,
// Eugene (in no pair) fades out, and the city names fade in. Pinned and scrubbed by scroll. Pairs as in data.js.
(() => {
  const box = document.getElementById("sd-pairs"), svg = document.getElementById("sdp-svg"); if (!box || !svg) return;
  const NS = "http://www.w3.org/2000/svg", el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p.appendChild(e); return e; };
  const NAME = { fairbanks: "Fairbanks", bakersfield: "Bakersfield", fresno: "Fresno", detroit: "Detroit", indianapolis: "Indianapolis",
    pittsburgh: "Pittsburgh", sanjose: "San Jose", seattle: "Seattle", eugene: "Eugene" };
  const USED = new Set(["fairbanks", "bakersfield", "fresno"]);
  const ROW = ["fairbanks", "bakersfield", "fresno", "detroit", "indianapolis", "pittsburgh", "sanjose", "seattle", "eugene"];
  const PAIRS = [["fairbanks", "detroit"], ["bakersfield", "indianapolis"], ["fresno", "pittsburgh"],   // matched
    ["bakersfield", "sanjose"], ["indianapolis", "sanjose"], ["fresno", "seattle"], ["pittsburgh", "seattle"], ["bakersfield", "seattle"], ["indianapolis", "seattle"]];   // crossed
  const R = 25, RX = k => 300 + (ROW.indexOf(k) - 4) * 62, RY = 300, LX = 264, PX = 336;
  const PY = i => (i < 3 ? 46 + i * 64 : 282 + (i - 3) * 64);   // a gap between the matched and the crossed pairs
  const fill = k => USED.has(k) ? "var(--sdp-used)" : "var(--sdp-new)";
  // one dot per pair slot, all starting on their city's spot in the row (so copies sit under the original until they move)
  const dots = [], names = [];
  PAIRS.forEach(([a, b], i) => [[a, LX], [b, PX]].forEach(([k, x], side) => {
    dots.push({ k, c: el("circle", { cx: RX(k), cy: RY, r: R, fill: fill(k) }, svg), x, y: PY(i) });
    const t = el("text", { x: side ? x + 40 : x - 40, y: PY(i) + 7, "text-anchor": side ? "start" : "end", opacity: 0 }, svg); t.textContent = NAME[k]; names.push(t);
  }));
  const eug = el("circle", { cx: RX("eugene"), cy: RY, r: R, fill: fill("eugene") }, svg);
  const h1 = document.getElementById("sdp-h1"), h2 = document.getElementById("sdp-h2");
  [h1, h2].forEach(p => [...p.childNodes].forEach(function wrap(n) {   // words become spans so they can rise one by one
    if (n.nodeType === 3) { const f = document.createDocumentFragment();
      n.textContent.split(/(\s+)/).forEach(w => { if (!w) return; if (/^\s+$/.test(w)) f.appendChild(document.createTextNode(w)); else { const s = document.createElement("span"); s.className = "w"; s.textContent = w; f.appendChild(s); } });
      n.replaceWith(f); }
    else if (n.nodeType === 1 && n.tagName === "B") [...n.childNodes].forEach(wrap);
  }));
  const final = () => { dots.forEach(d => { d.c.setAttribute("cx", d.x); d.c.setAttribute("cy", d.y); }); names.forEach(t => t.setAttribute("opacity", 1)); eug.setAttribute("opacity", 0); h1.style.opacity = 0; };
  if (!window.gsap || !window.ScrollTrigger || matchMedia("(prefers-reduced-motion: reduce)").matches) { final(); return; }
  gsap.registerPlugin(ScrollTrigger);
  const all = [...dots.map(d => d.c), eug], w1 = h1.querySelectorAll(".w"), w2 = h2.querySelectorAll(".w");
  gsap.set(w2, { opacity: 0 });
  // slide 1 comes in as the frame rises into view: the heading word by word, scrubbed by scroll
  gsap.timeline({ scrollTrigger: { trigger: box, start: "top 85%", end: "top 15%", scrub: .6 } })
    .fromTo(w1, { opacity: 0, y: 24, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", stagger: .045, duration: .6, ease: "power3.out" }, 0);
  // the dots play on a clock, not the scroll (Dish, Oct 6): first the story's two cities, Bakersfield (indigo) and Indianapolis
  // (green), side by side in the middle; a second later they step to their places in the row and the seven new cities pop in.
  const START = ["bakersfield", "indianapolis"], cityDots = k => k === "eugene" ? [eug] : dots.filter(d => d.k === k).map(d => d.c);
  const twoIn = START.flatMap(cityDots), newIn = ROW.filter(k => !START.includes(k)).map(cityDots);
  const off = k => 300 + (START.indexOf(k) - .5) * 62 - RX(k);   // from its row spot to the middle pair
  gsap.set(all, { scale: 0, transformOrigin: "50% 50%" });
  START.forEach(k => gsap.set(cityDots(k), { x: off(k) }));
  const intro = gsap.timeline({ paused: true })
    .to(twoIn, { scale: 1, duration: .5, ease: "back.out(1.8)" }, 0)
    .to(twoIn, { x: 0, duration: .7, ease: "power3.inOut" }, 1.5)
    .to(newIn, { scale: 1, duration: .5, stagger: .09, ease: "back.out(1.6)" }, 2.05);   // after the two have settled, so nothing pops in under a moving dot
  // starts once the row of dots is on screen (the frame is near the top); scrolling back above it resets it to play again
  ScrollTrigger.create({ trigger: box, start: "top 20%", onEnter: () => intro.timeScale(1).play(), onLeaveBack: () => intro.pause(0) });
  // pinned: slide 1 holds long enough for the dots to play; then its heading leaves, slide 2's heading rises, the dots move
  // into their pairs, then the names. If the reader scrolls on before the dots have finished, they speed up (never jump).
  const HOLD = 1.2;
  const tl = gsap.timeline({ scrollTrigger: { trigger: box, start: () => "top " + (document.querySelector("nav.skip")?.offsetHeight || 0) + "px", end: () => "+=" + Math.round(innerHeight * 3.2), pin: true, scrub: 1,   // no anticipatePin: it pinned early and made the frame jump
    onUpdate: s => { if (intro.progress() < 1 && s.progress * tl.duration() > HOLD * .5) intro.timeScale(3.5).play(); } } });
  tl.to({}, { duration: HOLD })
    .to(w1, { opacity: 0, y: -18, filter: "blur(6px)", stagger: .02, duration: .4, ease: "power2.in" }, HOLD)
    .fromTo(w2, { opacity: 0, y: 24, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", stagger: .03, duration: .6, ease: "power3.out" }, HOLD + .4);
  dots.forEach((d, i) => tl.to(d.c, { attr: { cx: d.x, cy: d.y }, duration: 1.1, ease: "power3.inOut" }, HOLD + .6 + (i >> 1) * .07));
  tl.to(eug, { opacity: 0, duration: .5, ease: "power2.in" }, HOLD + .6)   // opacity only: the intro owns the dots' scale
    .to(names, { opacity: 1, duration: .4, stagger: .03, ease: "power1.out" }, HOLD + 1.6)
    .to({}, { duration: .5 });
})();
