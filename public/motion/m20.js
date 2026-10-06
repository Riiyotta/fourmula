document.addEventListener("DOMContentLoaded", () => {
  const btn = document.querySelector(".header__menu");
  const topLine = document.querySelector(".header__menu-line.is-top");
  const bottomLine = document.querySelector(".header__menu-line.is-bottom");

  if (!btn || !topLine || !bottomLine || typeof gsap === "undefined") return;

  // Настройки закрытого состояния
  const closedTopY = "-0.2rem";
  const closedBottomY = "0.2rem";

  // Настройки открытого состояния
  // Меняйте эти значения, чтобы поймать идеальный крестик.
  // Если надо выше: отрицательное значение, например "-0.02rem".
  // Если надо ниже: положительное значение, например "0.02rem".
  const openTopY = "0.025rem";
  const openBottomY = "-0.025rem";

  gsap.set(topLine, {
    x: 0,
    y: closedTopY,
    rotate: 0,
    transformOrigin: "50% 50%"
  });

  gsap.set(bottomLine, {
    x: 0,
    y: closedBottomY,
    rotate: 0,
    transformOrigin: "50% 50%"
  });

  const tl = gsap.timeline({
    paused: true,
    defaults: {
      duration: 0.25,
      ease: "power2.out"
    }
  });

  tl.to(topLine, {
    y: openTopY,
    rotate: 45
  }, 0)
  .to(bottomLine, {
    y: openBottomY,
    rotate: -45
  }, 0);

  function syncIcon() {
    if (btn.classList.contains("is-open")) {
      tl.play();
    } else {
      tl.reverse();
    }
  }

  syncIcon();

  const observer = new MutationObserver(syncIcon);

  observer.observe(btn, {
    attributes: true,
    attributeFilter: ["class"]
  });
});