// Moved unchanged from index.html (snapshot d689e08), line 1023.
// Map dots (Gina, Oct 6): fill = used to it (frog green) or not (ink), from unhealthy days a year (>= 8 days at
// PM2.5 >= 35.5, median 2019-2025; data.js bad_days); a magenta ring because each dot is the city's worst week.
window.BF_USED = slug => { const c = (window.PM25 && PM25.cities || []).find(q => q.slug === slug); return !!c && c.bad_days >= 8; };
window.BF_DOTFILL = slug => BF_USED(slug) ? "var(--used)" : "var(--ink)";
window.BF_LEGEND = (ring) => `<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="var(--used)"/></svg>used to it (8+ unhealthy days a year)</span>`
  + `<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="var(--ink)"/></svg>not used to it</span>`
  + `<span>worst week, PM2.5 ${ring(35)}35 ${ring(100)}100 ${ring(280)}280 µg/m³</span>`;
