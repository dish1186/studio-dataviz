// Moved unchanged from index.html (snapshot d689e08), line 1837.
// "see the numbers" sits in the full-bleed story section, so its rule is matched to the width of the plates' rules.
(() => { const set = () => { const p = document.querySelector(".map-plate"); if (p) document.documentElement.style.setProperty("--plate-w", p.getBoundingClientRect().width + "px"); };
  set(); addEventListener("resize", set); })();
