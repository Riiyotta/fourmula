document.addEventListener("DOMContentLoaded", () => {
  const field = document.getElementById("dotsField");
  let lastMode = null;

  function getMode() {
    const w = window.innerWidth;

    if (w >= 992) return "desktop";
    if (w >= 768) return "tablet";
    return "mobile";
  }

  function buildDots() {
    const mode = getMode();
    if (mode === lastMode) return;
    lastMode = mode;

    field.innerHTML = "";

    let COLS;
    const ROWS = 14;

    switch (mode) {
      case "desktop":
        COLS = 52;
        break;
      case "tablet":
        COLS = 24;
        break;
      case "mobile":
        COLS = 22;
        break;
    }

    field.style.gridTemplateColumns = `repeat(${COLS}, var(--dot-size))`;

    const total = COLS * ROWS;

    for (let i = 0; i < total; i++) {
      const dot = document.createElement("div");
      dot.className = "dot";

      dot.dataset.index = i;
      dot.dataset.col = i % COLS;
      dot.dataset.row = Math.floor(i / COLS);

      dot.style.setProperty("--i", i);

      field.appendChild(dot);
    }
  }

  buildDots();
  window.addEventListener("resize", buildDots);
});