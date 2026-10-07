// Moved unchanged from card/index.html (snapshot d689e08), line 490.
// Embedded mode: the parent page picks the city (hash or message), passes its theme, and sizes the frame to this page's height.
(() => {
  if (window.parent === window) return;
  document.documentElement.classList.add("embed");
  const pick = k => { if (k && K[k] && k !== S.k) { S.k = k; S.g = null; draw(); } };
  pick(location.hash.slice(1));
  addEventListener("hashchange", () => pick(location.hash.slice(1)));
  addEventListener("message", e => { if (e.source !== window.parent) return; const d = e.data || {};
    if ("bfTheme" in d) { const r = document.documentElement, was = r.getAttribute("data-theme") || ""; if (d.bfTheme) r.setAttribute("data-theme", d.bfTheme); else r.removeAttribute("data-theme"); if (was !== (d.bfTheme || "")) draw(); }
    if (d.bfCity) pick(d.bfCity); });
  const post = () => window.parent.postMessage({ bfCardH: document.documentElement.scrollHeight }, "*");
  new ResizeObserver(post).observe(document.body); post();
})();
