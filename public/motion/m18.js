document.addEventListener("DOMContentLoaded", () => {
  const eli = document.querySelectorAll(".hero__carousel__img");
  if (!eli) return;

  gsap.to(eli, {
    rotate: -360,
    duration: 32,
    ease: "none",
    repeat: -1
  });
});