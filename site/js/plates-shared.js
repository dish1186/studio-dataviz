// Moved from index.html (snapshot d689e08), line 1035; comments on calculations and sources added 2026-10-07; code unchanged.
/* WHERE THE NUMBERS COME FROM (data/pm25.js, built by viz/pm25-scrolly/build.py; the method is fixed in docs/experiment-design-pm25.md)
   pm          worst-week PM2.5: mean of the daily reference-monitor values in the city's worst week, µg/m³
               (scripts/openaq/07_city_screening.py -> step08_pm_normals/pm_normals.csv, event_week_pm25)
   pm_normal   the city's "normal": median of the weekly PM2.5 averages for the same calendar month, 2019-2025, leaving out the
               worst week and any week with fewer than 5 of 7 days of data (scripts/openaq/08_pm_normals_and_pairs.py, pm25_normal)
   ratio       "× normal" = pm / pm_normal, rounded to 2 decimals (08_pm_normals_and_pairs.py, ratio_to_normal)
   bad_days    median number of days a year with daily PM2.5 >= 35.5 µg/m³, 2019-2025 (see js/map-dots.js)
   share_normal, share_event   air-talk share = % of the week's kept posts + comments that match the air lexicon.
               share_event = the worst week's share; share_normal = median share of the city's usable normal weeks
               (same month, 2019-2025; a week is dropped for PM2.5 > 35.5 or no data, fireworks, < 100 kept items, or comments on
               < 5 of 7 days). scripts/reddit/analysis_01_event_rise.py -> data/processed/reddit/analysis_01/cities.csv
   rise        "× more air talk" = share_event / share_normal (analysis_01/cities.csv, rise_ratio)
   beat        "k of N": the worst week's share is higher than k of the city's N usable normal weeks (percentile_higher_than)
   rho         Spearman rank correlation across the 9 cities, computed in build.py spearman():
               rho.ratio = rho(rise, ratio), rho.abs = rho(rise, pm), rho.measures = rho(ratio, pm), rho.bad_days = rho(rise, bad_days)
   verdict     "Pos" if rho.ratio is higher than rho.abs by 0.2 or more, "Neg" if rho.abs is higher by 0.2 or more, else mixed
   pairs[]     from analysis_01/pairs.csv (scripts/reddit/analysis_01_event_rise.py): outcome "as Pos predicts" = the city with the higher
               ratio has the higher rise; "as Neg predicts" = in a crossed pair, the city with the higher PM2.5 has the higher rise;
               otherwise "against Pos" (or "tie") */
const D = window.PM25;
const C = Object.fromEntries(D.cities.map(c => [c.slug, c]));
const READY = D.cities.filter(c => c.ready);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const f = (v, d = 1) => v == null ? "–" : Number(v).toFixed(d);
const NUMW = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];

/* ---------- text bindings ---------- */
function bindText() {
  const stampTxt = D.run === "interim" ? `Early results · ${D.n_ready} of ${D.n_total} cities` : `All ${D.n_total} cities`;
  document.querySelectorAll("[data-stamp]").forEach(e => { e.textContent = stampTxt; e.classList.toggle("full", D.run !== "interim"); });
  const short = document.querySelector("[data-stamp-short]"); if (short) short.textContent = D.run === "interim" ? `Early results · ${D.n_ready} of ${D.n_total} cities` : "Full results";
  // CALCULATION · normal weeks with MORE air talk than the worst week = N - k, from beat "k of N"
  const higher = c => { const [a, b] = (c.beat || "0 of 0").split(" of ").map(Number); return b - a; };
  document.querySelectorAll("[data-v]").forEach(e => {
    const [path, dig] = e.dataset.v.split("|"); const [k, field] = path.split(".");
    let v;
    if (k === "rho") v = D.rho[field];
    else if (field === "higher") v = NUMW[higher(C[k])] ?? higher(C[k]);
    else v = C[k][field];
    e.textContent = dig != null && typeof v === "number" ? f(v, +dig) : (typeof v === "number" ? v.toLocaleString("en-US") : v);
  });
  if (D.cities.every(c => c.ready)) document.querySelector("[data-pending-key]")?.remove();   // nothing pending: drop that key entry
  const nWord = NUMW[D.n_ready] ?? D.n_ready;
  if (D.verdict !== "Pos") document.querySelector("[data-verdict]").textContent = `Across ${nWord} cities the main test came out ${D.verdict === "Neg" ? "the other way: reaction followed harm" : "mixed"}.`;
  else document.querySelector("[data-verdict]").innerHTML = `Across ${D.run === "interim" ? "these " + nWord : "all " + nWord} cities, reaction followed how <span class="c-unus">unusual</span> the air was, not how <span class="c-harm">harmful</span>.`;
  document.querySelector("[data-note-run]").textContent = D.run === "interim"
    ? `Early results from ${D.n_ready} of ${D.n_total} cities (${D.cities.filter(c => !c.ready).map(c => c.name).join(", ")} still being collected). The final result uses all ${D.n_total} cities and the same method, fixed before any worst-week posts were read.`
    : `All ${D.n_total} cities, same method as the early results, fixed before any worst-week posts were read.`;
}

/* ---------- tooltip ---------- */
const tip = document.getElementById("tip");
function cityTip(c) {
  return `<b>${c.name}, ${c.state}</b><br>${c.dates} · ${c.cause}<br>PM2.5 ${f(c.pm, 0)} µg/m³ · ${f(c.ratio, 1)}× its normal (${f(c.pm_normal, 0)})<br>` +
    (c.ready ? `Air talk ${f(c.share_normal, 2)}% → ${f(c.share_event, 1)}% (${f(c.rise, 1)}×)<br>Higher than ${c.beat} normal weeks` : `Reddit data still being collected`);
}
function attachTip(sel, html) {
  sel.attr("tabindex", 0)
    .on("mousemove focus", function (ev, d) {
      tip.innerHTML = html(d); tip.hidden = false;
      const r = this.getBoundingClientRect();
      const x = ev.pageX ?? (r.left + scrollX + r.width / 2), y = ev.pageY ?? (r.top + scrollY + r.height / 2);
      const tw = tip.offsetWidth; tip.style.left = Math.max(8, Math.min(document.documentElement.clientWidth - tw - 8, x + 14)) + "px"; tip.style.top = (y + 14) + "px";
    })
    .on("mouseleave blur", () => { tip.hidden = true; });
}
const W = el => Math.max(280, el.parentElement.clientWidth - 32);

/* ---------- Fig 2: safe ruler ---------- */
function drawSafe() {
  if (!document.getElementById("fig-safe")) return;   // Fig. 3 was taken out with the "So what?" plate
  const svg = d3.select("#fig-safe"); svg.selectAll("*").remove();
  const w = W(svg.node()), narrow = w < 480, L = narrow ? 92 : 120, R = 20, h = 170;
  svg.attr("viewBox", `0 0 ${w} ${h}`);
  const x = d3.scaleLinear([0, 60], [L, w - R]), col = "var(--on-q)";
  [0, 15, 30, 45, 60].forEach(t => svg.append("text").attr("class", "num").attr("x", x(t)).attr("y", h - 6).attr("text-anchor", "middle").attr("font-size", 11).attr("fill", col).text(t));
  [[15, "WHO 15"], [35, "EPA 35"]].forEach(([v, t]) => {
    svg.append("line").attr("x1", x(v)).attr("x2", x(v)).attr("y1", 22).attr("y2", h - 22).attr("stroke", col).attr("stroke-width", 1.5).attr("stroke-dasharray", v === 15 ? "0" : "4 3");
    svg.append("text").attr("x", x(v)).attr("y", 14).attr("text-anchor", "middle").attr("font-size", 12).attr("font-weight", 700).attr("fill", col).text(t);
  });
  ["bakersfield", "indianapolis"].forEach((k, i) => {
    const c = C[k], y = 62 + i * 48;
    svg.append("text").attr("x", 0).attr("y", y + 5).attr("font-size", 14).attr("font-weight", 600).attr("fill", col).text(c.name);
    svg.append("line").attr("x1", x(c.pm_normal)).attr("x2", x(c.pm)).attr("y1", y).attr("y2", y).attr("stroke", "var(--event)").attr("stroke-width", 2);
    svg.append("circle").attr("cx", x(c.pm_normal)).attr("cy", y).attr("r", 6).attr("fill", "var(--q-ground)").attr("stroke", col).attr("stroke-width", 2);
    svg.append("circle").attr("cx", x(c.pm)).attr("cy", y).attr("r", 6.5).attr("fill", "var(--event)");
    svg.append("text").attr("class", "num").attr("x", x(c.pm_normal)).attr("y", y - 11).attr("text-anchor", "middle").attr("font-size", 11).attr("fill", col).text(f(c.pm_normal, 0));
  });
}

/* ---------- pairs ---------- */
function drawPairs() {
  const done = D.pairs.filter(p => p.rise_worse != null && p.rise_other != null);
  // CALCULATION · the tally: number of finished pairs whose outcome is "as Pos predicts", out of all finished pairs
  const wonU = done.filter(p => p.outcome === "as Pos predicts").length;
  document.querySelector("[data-tally]").textContent = `${wonU} of ${done.length}`;
  const waiting = D.pairs.length - done.length;
  const wWord = String(NUMW[waiting] ?? waiting);
  document.querySelector("[data-tally-text]").textContent = `finished pairs went the way "unusual" predicts.` + (waiting ? ` ${wWord[0].toUpperCase() + wWord.slice(1)} more are waiting on Reddit data.` : "");
  const bar = (label, a, b, va, vb, unit, dig) => {
    // CALCULATION · bar length = value / larger value of the two cities × 100%; the larger one is marked "lead"
    const max = Math.max(va, vb);
    const row = (c, v) => `<div class="br"><span>${C[c].name}</span><span class="tr"><span class="b${v === max && va !== vb ? " lead" : ""}" style="width:${(v / max * 100).toFixed(1)}%"></span></span><span class="v">${f(v, dig)}${unit}</span></div>`;
    return `<div class="m"><span class="mh">${label}</span>${row(a, va)}${row(b, vb)}</div>`;
  };
  const sorted = [...done, ...D.pairs.filter(p => !done.includes(p))];
  document.getElementById("pairs").innerHTML = sorted.map(p => {
    const ok = done.includes(p), A = C[p.worse], B = C[p.other];
    // plain-language result; "barely" when the two reactions are within 5% (display only)
    const close = ok && Math.abs(p.rise_worse - p.rise_other) / Math.max(p.rise_worse, p.rise_other) < .05;
    const res = ok ? (p.outcome === "as Pos predicts" ? `${close ? "barely " : ""}went the "unusual" way` : p.outcome.includes("Neg") ? `went the "harmful" way` : `went against "unusual"`) : "waiting";
    const miss = [A, B].filter(c => !c.ready).map(c => c.name).join(" and ");
    return `<article class="pair${ok ? "" : " wait"}"><div class="top"><span>${p.type} pair</span><span class="res">${res}</span></div>
      <div class="vs">${A.name} vs. ${B.name}</div>
      ${bar("How harmful · <i>µg/m³</i>", p.worse, p.other, p.pm_worse, p.pm_other, "", 0)}
      ${bar("How unusual · <i>× normal</i>", p.worse, p.other, p.ratio_worse, p.ratio_other, "×", 1)}
      ${ok ? bar("Reaction · <i>× more air talk</i>", p.worse, p.other, p.rise_worse, p.rise_other, "×", 1) : `<div class="pend">Waiting for ${miss}'s Reddit data</div>`}
      <div class="talk m" data-talk="${p.worse},${p.other}"></div></article>`;
  }).join("");
}

/* ---------- table ---------- */
function drawTable() {
  document.getElementById("tbl").innerHTML = `<thead><tr><th>City</th><th>Worst week</th><th>PM2.5</th><th>Normal</th><th>× normal</th><th>Unhealthy days/yr</th><th>Air talk, normal</th><th>Air talk, worst week</th><th>Reaction</th><th>Higher than</th></tr></thead><tbody>` +
    D.cities.map(c => `<tr><td>${c.name}, ${c.state}</td><td class="l">${c.dates}</td><td class="mono">${f(c.pm, 1)}</td><td class="mono">${f(c.pm_normal, 1)}</td><td class="mono">${f(c.ratio, 2)}</td><td class="mono">${c.bad_days}</td>` +
      (c.ready ? `<td class="mono">${f(c.share_normal, 2)}%</td><td class="mono">${f(c.share_event, 2)}%</td><td class="mono">${f(c.rise, 1)}×</td><td>${c.beat}</td>` : `<td colspan="4" class="l">Reddit data still being collected</td>`) + `</tr>`).join("") + `</tbody>`;
}

function drawAll() { drawSafe(); }
/* ---------- air-talk groupings under each pair (added by Gina + Claude) ---------- */
// Comment counts per tone group (A Alarm, J Adjusting, E Enduring, N Normalizing; not-about-the-air left out).
// Source: data/processed/reddit/spectrum_03_outputs (Claude draft labels) + spectrum_02_labels weights; big = the city's biggest thread.
// CALCULATION / DATA · SPEC, typed in from these files (checked 2026-10-07):
//   read = number of air items with each Claude draft label, A Alarm, J Adjusting, E Enduring, N Normalizing (X, not about
//          the air, left out): data/processed/reddit/spectrum_03_outputs/spectrum_labels_<city>_<week>_claude_draft.csv, column band
//   est  = the same counts weighted back to the full week for the three sampled weeks (Eugene, Seattle, Pittsburgh), using the
//          weights in spectrum_02_labels/<city>_<week>_to_label.csv = spectrum_07_corrected/city_shares.csv, method claude_draft, count_A..N
//   big  = the part of each count that comes from the city's single biggest thread
const SPEC = {
  eugene: { read: { A: 144, J: 160, E: 5, N: 13 }, est: { A: 423.3, J: 470.4, E: 13.8, N: 38.7 }, big: { A: 17.6, J: 29.4, E: 0, N: 0 } },
  fairbanks: { read: { A: 13, J: 17, E: 0, N: 5 }, est: { A: 13, J: 17, E: 0, N: 5 }, big: { A: 4, J: 7, E: 0, N: 2 } },
  detroit: { read: { A: 138, J: 87, E: 5, N: 14 }, est: { A: 138, J: 87, E: 5, N: 14 }, big: { A: 38, J: 40, E: 2, N: 4 } },
  seattle: { read: { A: 104, J: 139, E: 13, N: 20 }, est: { A: 316.8, J: 422.9, E: 40.3, N: 60.3 }, big: { A: 0, J: 0, E: 0, N: 0 } },
  fresno: { read: { A: 22, J: 7, E: 5, N: 2 }, est: { A: 22, J: 7, E: 5, N: 2 }, big: { A: 0, J: 0, E: 0, N: 0 } },
  pittsburgh: { read: { A: 143, J: 113, E: 10, N: 33 }, est: { A: 408.8, J: 320.8, E: 28.3, N: 94.5 }, big: { A: 14.4, J: 25.9, E: 0, N: 2.9 } },
  sanjose: { read: { A: 128, J: 138, E: 6, N: 14 }, est: { A: 128, J: 138, E: 6, N: 14 }, big: { A: 6, J: 13, E: 0, N: 0 } },
  indianapolis: { read: { A: 61, J: 22, E: 1, N: 9 }, est: { A: 61, J: 22, E: 1, N: 9 }, big: { A: 19, J: 3, E: 0, N: 2 } },
  bakersfield: { read: { A: 15, J: 5, E: 22, N: 9 }, est: { A: 15, J: 5, E: 22, N: 9 }, big: { A: 0, J: 0, E: 18, N: 8 } },
};
const TG = {
  two: [["Reacting", "AJ", "--t-alarm", "Alarm + Adjusting"], ["Living with it", "EN", "--t-endure", "Enduring + Normalizing"]],
  three: [["Alarm", "A", "--t-alarm"], ["Adjusting", "J", "--t-adjust"], ["Living with it", "EN", "--t-endure", "Enduring + Normalizing"]],
  four: [["Alarm", "A", "--t-alarm"], ["Adjusting", "J", "--t-adjust"], ["Enduring", "E", "--t-endure"], ["Normalizing", "N", "--t-norm"]],
  jliving: [["Reacting", "A", "--t-alarm", "Alarm"], ["Living with it", "JEN", "--t-endure", "Adjusting + Enduring + Normalizing"]],
};
const talkSt = { g: "two", c: "read", big: false };
// CALCULATION · a group's count = read (or est); with "leave out the big thread" on, Bakersfield's big-thread counts are subtracted
function talkCount(slug, b) { const s = SPEC[slug]; let v = s[talkSt.c][b]; if (talkSt.big && slug === "bakersfield") v -= s.big[b]; return Math.max(0, v); }
function drawTalk() {
  const G = TG[talkSt.g];
  document.getElementById("talk-key").innerHTML = G.map(g => `<span><i style="background:var(${g[2]})"></i>${g[0]}${g[3] ? ` <span class="v">(${g[3]})</span>` : ""}</span>`).join("");
  document.querySelectorAll("[data-talk]").forEach(box => {
    const rows = box.dataset.talk.split(",").map(slug => {
      // CALCULATION · each group's share = its count / all four groups' count × 100 (rounded); "lead" = the largest group
      const v = G.map(g => [...g[1]].reduce((s, b) => s + talkCount(slug, b), 0)), t = v.reduce((a, b) => a + b, 0);
      const segs = v.map((x, i) => x > 0 ? `<span title="${G[i][0]}: ${Math.round(100 * x / t)}% (${Math.round(x)} comments)" style="width:${(100 * x / t).toFixed(1)}%;background:var(${G[i][2]})"></span>` : "").join("");
      const lead = v.map((x, i) => [x, i]).sort((a, b) => b[0] - a[0])[0];
      const note = talkSt.big && slug === "bakersfield" ? "*" : "";
      return `<div class="br"><span>${C[slug].name}${note}</span><span class="tb" role="img" aria-label="${C[slug].name}: ${G.map((g, i) => `${g[0]} ${Math.round(100 * v[i] / t)}%`).join(", ")}">${segs}</span><span class="v">${Math.round(t)}</span></div>
        <div class="br" style="margin-top:-2px"><span></span><span style="font-size:11.5px;color:var(--ink-2)">${Math.round(100 * lead[0] / t)}% ${G[lead[1]][0].toLowerCase()}</span><span></span></div>`;
    }).join("");
    box.innerHTML = `<span class="mh">How they talked · <i>share of air comments, draft labels</i></span>${rows}` +
      (talkSt.big && box.dataset.talk.includes("bakersfield") ? `<span style="font-family:var(--label);font-size:11.5px;color:var(--ink-2)">* without its biggest thread</span>` : "");
  });
  document.querySelectorAll("[data-tg]").forEach(b => b.setAttribute("aria-pressed", b.dataset.tg === talkSt.g));
  document.querySelectorAll("[data-tc]").forEach(b => b.setAttribute("aria-pressed", b.dataset.tc === talkSt.c));
  document.getElementById("tbig").setAttribute("aria-pressed", talkSt.big);
}
document.querySelectorAll("[data-tg]").forEach(b => b.addEventListener("click", () => { talkSt.g = b.dataset.tg; drawTalk(); }));
document.querySelectorAll("[data-tc]").forEach(b => b.addEventListener("click", () => { talkSt.c = b.dataset.tc; drawTalk(); }));
document.getElementById("tbig")?.addEventListener("click", () => { talkSt.big = !talkSt.big; drawTalk(); });

bindText(); if (document.getElementById("pairs")) { drawPairs(); drawTalk(); } drawTable(); drawAll();
let lastW = document.querySelector(".book").clientWidth, rt;
new ResizeObserver(() => { const w = document.querySelector(".book").clientWidth; if (w === lastW) return; lastW = w; clearTimeout(rt); rt = setTimeout(drawAll, 90); }).observe(document.querySelector(".book"));
