// Moved from index.html (snapshot d689e08), line 1001; comments on calculations and sources added 2026-10-07; code unchanged.
// No data calculations in this file: layout and motion only.
// Skip-to buttons. "case study" lands on the story frame "let's take a look at two cities" (both states are in by
// about 7.6 on the story timeline, so the scroll position is computed from the live ScrollTrigger, on phones too).
(() => {
  const smooth = matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
  const go = {
    intro: () => document.querySelector(".door-plate"),
    scope: () => document.querySelector(".say-plate"),   // "We followed nine U.S. cities…"
    viz: () => document.querySelector(".imap-plate"),
    details: () => document.querySelector(".sa-close"),                        // "we hope to explore how environments…"
    results: () => document.querySelector('section[aria-label="Conclusion"]'),  // "Across all nine cities…"
    case: () => { const st = window.ScrollTrigger && ScrollTrigger.getAll().find(s => s.trigger && s.trigger.id === "sa-story");
      if (!st) return document.getElementById("sa-story");
      scrollTo({ top: st.start + (7.6 / st.animation.duration()) * (st.end - st.start), behavior: smooth }); return null; }
  };
  const bar = document.querySelector("nav.skip");
  const setH = () => { if (bar) document.documentElement.style.setProperty("--skip-h", bar.offsetHeight + "px"); };
  setH(); addEventListener("resize", setH); document.fonts && document.fonts.ready.then(setH);
  document.querySelector("nav.skip")?.addEventListener("click", e => { const b = e.target.closest("button[data-go]"); if (!b || b.disabled) return;
    const el = go[b.dataset.go] && go[b.dataset.go](); if (el) el.scrollIntoView({ behavior: smooth, block: "start" }); });
})();
