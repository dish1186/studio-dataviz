// Moved unchanged from index.html (snapshot d689e08), line 1917.
// Study details: every block rises word by word out of a blur as it scrolls in (same motion as the story headings);
// the three result boxes come in one after another.
(() => {
  const blocks = [...document.querySelectorAll(".sa-close .sd-b")]; if (!blocks.length) return;
  blocks.forEach(bl => bl.querySelectorAll(".h, .sd-k, .sd-t").forEach(p => [...p.childNodes].forEach(function wrap(n) {
    if (n.nodeType === 3) { const f = document.createDocumentFragment();
      n.textContent.split(/(\s+)/).forEach(w => { if (!w) return; if (/^\s+$/.test(w)) f.appendChild(document.createTextNode(w)); else { const e = document.createElement("span"); e.className = "w"; e.textContent = w; f.appendChild(e); } });
      n.replaceWith(f); }
    else if (n.nodeType === 1 && n.tagName === "B") [...n.childNodes].forEach(wrap);
  })));
  if (!window.gsap || !window.ScrollTrigger || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  blocks.forEach(bl => {
    const box = bl.classList.contains("sd-box"), words = bl.querySelectorAll(".w");
    const tl = gsap.timeline({ scrollTrigger: { trigger: box ? bl.parentElement : bl, start: "top 85%", end: "top 40%", scrub: .6 } });
    const at = box ? [...bl.parentElement.children].indexOf(bl) * .35 : 0;   // boxes follow one another
    if (box) tl.fromTo(bl, { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: .5, ease: "power3.out" }, at);
    tl.fromTo(words, { opacity: 0, y: 24, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", stagger: .045, duration: .6, ease: "power3.out" }, at + (box ? .15 : 0));
  });
})();
