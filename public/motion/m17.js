document.addEventListener("DOMContentLoaded", () => {
  const el = document.querySelector(".hero__carousel__in");
  if (!el) return;

  gsap.to(el, {
    rotate: 360,
    duration: 32,
    ease: "none",
    repeat: -1
  });
});