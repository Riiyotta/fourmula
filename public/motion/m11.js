document.addEventListener("DOMContentLoaded", () => {
  const darkImages = document.querySelectorAll(".theme-light");

  function toggleImages(isDark) {
    darkImages.forEach(darkImg => {
      const parent = darkImg.parentElement;
      const lightImg = parent.querySelector(".theme-dark");
      if (!lightImg) return;

      if (isDark) {
        darkImg.style.display = "flex";
        lightImg.style.display = "none";
      } else {
        darkImg.style.display = "none";
        lightImg.style.display = "flex";
      }
    });
  }

  toggleImages(document.body.classList.contains("light"));

  window.addEventListener("theme:changed", e => {
    toggleImages(e.detail);
  });
});