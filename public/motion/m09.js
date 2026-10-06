document.addEventListener("DOMContentLoaded", () => {
  const dots = Array.from(document.querySelectorAll(".dot"));
  if (!dots.length) return;

  const MAX_DISTANCE = 200;
  const MIN_SCALE = 0.25;

  document.addEventListener("mousemove", (e) => {
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    dots.forEach(dot => {
      const rect = dot.getBoundingClientRect();
      const dotX = rect.left + rect.width / 2;
      const dotY = rect.top + rect.height / 2;

      const dx = dotX - mouseX;
      const dy = dotY - mouseY;
      const dist = Math.sqrt(dx*dx + dy*dy);

      let scale = 1 - (1 - MIN_SCALE) * Math.max(0, (MAX_DISTANCE - dist) / MAX_DISTANCE);
      scale = Math.max(MIN_SCALE, Math.min(1, scale));

      gsap.to(dot, { scale, duration: 0.2, ease: "power2.out" });
    });
  });
});