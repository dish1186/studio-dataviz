// Moved from index.html (snapshot d689e08), line 1023; comments on calculations and sources added 2026-10-07; code unchanged.
// Map dots (Gina, Oct 6): fill = used to it (frog green) or not (ink), from unhealthy days a year (>= 8 days at
// PM2.5 >= 35.5, median 2019-2025; data.js bad_days); a magenta ring because each dot is the city's worst week.
// CALCULATION · "used to it": bad_days >= 8.
//   bad_days = data/pm25.js cities[].bad_days, built by viz/pm25-scrolly/build.py from
//   data/processed/openaq/step08_pm_normals/pm_normals.csv, column median_days_ge_35_5_2019_2025: for each year 2019-2025,
//   count the days with daily reference PM2.5 >= 35.5 µg/m³, then take the median of the 7 yearly counts.
//   Cut-off 8 = the default of the slider on Dish's Boiling Frog Pots page. Result: Bakersfield 12, Fairbanks 8, Fresno 8 are used to it.
window.BF_USED = slug => { const c = (window.PM25 && PM25.cities || []).find(q => q.slug === slug); return !!c && c.bad_days >= 8; };
window.BF_DOTFILL = slug => BF_USED(slug) ? "var(--used)" : "var(--ink)";
window.BF_LEGEND = (ring) => `<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="var(--used)"/></svg>used to it (8+ unhealthy days a year)</span>`
  + `<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="var(--ink)"/></svg>not used to it</span>`
  + `<span>worst week, PM2.5 ${ring(35)}35 ${ring(100)}100 ${ring(280)}280 µg/m³</span>`;
