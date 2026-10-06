document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".how__right");
  const titles = container.querySelectorAll(".how__right-title");

  const containerRect = container.getBoundingClientRect();
  const containerHeight = containerRect.height;

  const fadeFinish = 0.15;

  function animateOpacity() {
    const containerRect = container.getBoundingClientRect();

    titles.forEach(title => {
      const rect = title.getBoundingClientRect();
      const top = rect.top - containerRect.top;
      const bottom = top + rect.height;

      let opacity = 0.2;

      if (bottom > 0 && top < containerHeight) {
        let norm = 1 - (bottom / containerHeight);
        norm = Math.min(Math.max(norm, 0), 1);

        let progress = norm / (1 - fadeFinish);
        progress = Math.min(Math.max(progress, 0), 1);

        opacity = 0.2 + progress * 0.8;
      }

      title.style.opacity = opacity;
    });

    requestAnimationFrame(animateOpacity);
  }

  animateOpacity();
});