// Mobile navigation drawer. The shared stylesheet hides `.nav-links` off-canvas below 1180px
// and reveals it on `.active`; when the pages were templated the toggle script was dropped with
// them, so phones showed a dead hamburger button and the menu could not be opened at all.
(() => {
  const btn = document.getElementById("menuToggle");
  const links = document.getElementById("navLinks");
  if (!btn || !links) return;
  const setOpen = (open) => {
    links.classList.toggle("active", open);
    document.body.classList.toggle("nav-open", open);
    btn.setAttribute("aria-expanded", String(open));
  };
  btn.setAttribute("aria-expanded", "false");
  btn.addEventListener("click", () => setOpen(!links.classList.contains("active")));
  links.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => setOpen(false)));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
})();
