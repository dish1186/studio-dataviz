// Moved unchanged from index.html (snapshot d689e08), line 2135.
// Reddit posts under "or they come from ourselves.": one at a time, swapping every 4.5 s while the section is on screen.
(() => {
const box = document.getElementById("posts"), posts = [...box.querySelectorAll(".post")];
if (matchMedia("(prefers-reduced-motion: reduce)").matches) { box.classList.add("still"); posts.forEach(p => p.classList.add("on")); return; }
const fit = () => { box.style.height = Math.max(...posts.map(p => p.offsetHeight)) + "px"; };   // the window fits the longest post
fit(); addEventListener("resize", fit); document.fonts?.ready.then(fit);
let i = 0, timer = null, seen = false, paused = false;
function next() {
  const cur = posts[i], nx = posts[(i + 1) % posts.length];
  nx.style.transition = "none"; nx.classList.remove("out", "on"); void nx.offsetHeight; nx.style.transition = "";   // park it just below the window
  cur.classList.remove("on"); cur.classList.add("out"); nx.classList.add("on");
  i = (i + 1) % posts.length;
}
const run = () => { clearInterval(timer); timer = seen && !paused ? setInterval(next, 4500) : null; };
new IntersectionObserver(es => { seen = es[0].isIntersecting; run(); }, { threshold: .6 }).observe(box);
["mouseenter", "focusin"].forEach(e => box.addEventListener(e, () => { paused = true; run(); }));
["mouseleave", "focusout"].forEach(e => box.addEventListener(e, () => { paused = false; run(); }));
})();
