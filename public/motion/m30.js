(function () {

  const cookies = document.querySelector('.cookies');
  if (!cookies) return;

  gsap.set(cookies, {
    opacity: 0,
    y: 10
  });

  document.addEventListener('preloader:done', () => {

    gsap.delayedCall(2, () => {
      gsap.to(cookies, {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: 'power2.out'
      });
    });

  });

})();