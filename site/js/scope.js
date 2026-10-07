// Moved unchanged from index.html (snapshot d689e08), line 1545.
// Scope plate (Gina, Oct 6): the plate pins while you scroll. First the header ("We followed nine U.S. cities…") rises and
// fills line by line, then "we looked at:", each item and each note in turn; only then does the page move on to the map.
(() => {
  const plate = document.querySelector(".say-plate"), lines = [...document.querySelectorAll(".say-plate .rise")];
  if (!plate || !lines.length || !window.gsap || !window.ScrollTrigger) return;
  lines.forEach(line => [...line.childNodes].forEach(function wrap(n) {   // words become <em class="fw"> so they can fill one by one
    if (n.nodeType === 3) { const f = document.createDocumentFragment();
      n.textContent.split(/(\s+)/).forEach(w => { if (!w) return; if (/^\s+$/.test(w)) f.appendChild(document.createTextNode(w)); else { const e = document.createElement("em"); e.className = "fw"; e.textContent = w; f.appendChild(e); } });
      n.replaceWith(f); }
    else if (n.nodeType === 1 && n.tagName === "B") [...n.childNodes].forEach(wrap);
  }));
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  gsap.registerPlugin(ScrollTrigger);
  const head = lines.filter(l => l.closest(".say")), rest = lines.filter(l => !l.closest(".say"));
  const parts = l => l.querySelectorAll("em.fw, .rd-inline, sup");
  // same word motion as the story headings below: each word rises 24px out of an 8px blur (stagger .045, power3.out)
  lines.forEach(l => gsap.set(parts(l), { opacity: 0, y: 24, filter: "blur(8px)" }));
  gsap.set(".say-plate .fw", { display: "inline-block" });   // so words can move on their own
  const tl = gsap.timeline({ scrollTrigger: { trigger: plate, start: () => "top " + (document.querySelector("nav.skip")?.offsetHeight || 0) + "px", end: () => "+=" + Math.round(innerHeight * 2.4), pin: true, scrub: .5, anticipatePin: 1 } });
  let t = 0;
  const reveal = l => tl.to(parts(l), { opacity: 1, y: 0, filter: "blur(0px)", stagger: .045, duration: .6, ease: "power3.out" }, t);
  head.forEach(l => { reveal(l); t += .55; });   // the header first, line after line
  t += .6;                                          // a beat before the list
  rest.forEach(l => { reveal(l); t += .8; });   // then each line on its own
  tl.to({}, { duration: .6 });                      // hold the finished plate a moment before the map comes up
})();
