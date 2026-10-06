document.addEventListener("DOMContentLoaded", () => {
  const header = document.querySelector(".header");
  const footer = document.querySelector(".footer");
  const menu = document.querySelector(".menu"); 
  if (!header || !footer || !menu) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        const visible = entry.intersectionRatio;

        const tl = gsap.timeline({ defaults: { duration: 0.2, ease: "power2.out" } });

        if (visible >= 0.5) {
          tl.to(header, { y: "-10rem" }, 0)
            .to(menu, { y: "-10rem" }, 0);
        } else {
          tl.to(header, { y: "0rem" }, 0)
            .to(menu, { y: "0rem" }, 0);
        }
      });
    },
    { threshold: Array.from({ length: 101 }, (_, i) => i / 100) }
  );

  observer.observe(footer);
});