// Moved from index.html (snapshot d689e08), line 1837; comments on calculations and sources added 2026-10-07; code unchanged.
// No data calculations in this file: layout and motion only.
// "see the numbers" sits in the full-bleed story section, so its rule is matched to the width of the plates' rules.
(() => { const set = () => { const p = document.querySelector(".map-plate"); if (p) document.documentElement.style.setProperty("--plate-w", p.getBoundingClientRect().width + "px"); };
  set(); addEventListener("resize", set); })();
