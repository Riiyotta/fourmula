(() => {
  const STEP = 0.1;
  const KEY = "site-user-zoom";
  const root = document.documentElement;

  let zoom = parseFloat(localStorage.getItem(KEY) || "1");
  if (!Number.isFinite(zoom) || zoom <= 0) zoom = 1;

  function applyZoom() {
    root.style.setProperty("--user-zoom", String(zoom));
    localStorage.setItem(KEY, String(zoom));
  }

  function zoomIn() {
    zoom += STEP;
    applyZoom();
  }

  function zoomOut() {
    zoom = Math.max(0.1, zoom - STEP);
    applyZoom();
  }

  function zoomReset() {
    zoom = 1;
    applyZoom();
  }

  applyZoom();

  window.addEventListener("keydown", (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (!mod) return;

    if (e.key === "+" || e.key === "=") {
      e.preventDefault();
      zoomIn();
    } else if (e.key === "-") {
      e.preventDefault();
      zoomOut();
    } else if (e.key === "0") {
      e.preventDefault();
      zoomReset();
    }
  }, { passive: false });

  window.addEventListener("wheel", (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    if (e.deltaY < 0) zoomIn();
    else zoomOut();
  }, { passive: false });

  window.siteZoom = { in: zoomIn, out: zoomOut, reset: zoomReset };
})();