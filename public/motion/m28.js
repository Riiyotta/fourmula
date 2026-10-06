(function () {

  const IMAGES = [
    '.is-img-anima-1',
    '.is-img-anima-2',
    '.is-img-anima-3',
    '.is-img-anima-4',
    '.is-img-anima-5'
  ];

  gsap.set(IMAGES, {
    opacity: 0,
    scale: 0.96,
    filter: 'blur(6px)'
  });

  const tl = gsap.timeline({
    repeat: -1,
    defaults: {
      ease: 'power2.out'
    }
  });

  IMAGES.forEach(selector => {
    tl.to(selector, {
      opacity: 1,
      scale: 1,
      filter: 'blur(0px)',
      duration: 0.9
    });
  });

  tl.to({}, { duration: 1.5 });

  IMAGES.forEach(selector => {
    tl.to(selector, {
      opacity: 0,
      scale: 0.98,
      filter: 'blur(6px)',
      duration: 0.8
    });
  });

})();