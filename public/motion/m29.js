gsap.registerPlugin(ScrollTrigger);

window.addEventListener("DOMContentLoaded", () => {

  const slides = document.querySelectorAll('.list__main__wrap .list__main__slide');

  slides.forEach((slide, index) => {

    if (index === slides.length - 1) return;

    const contentWrapper = slide.querySelector('.list__main__content__wrap');
    const content = slide.querySelector('.list__main__content');

    gsap.to(content, {
      rotationZ: (Math.random() - 0.5) * 10,
      scale: 0.7,
      rotationX: 40,
      ease: 'power1.in',
      scrollTrigger: {
        pin: contentWrapper,
        trigger: slide,
        start: 'top 0%',
        end: '+=' + window.innerHeight,
        scrub: true
      }
    });

    gsap.to(content, {
      autoAlpha: 0,
      ease: 'power1.in',
      scrollTrigger: {
        trigger: content,
        start: 'top -80%',
        end: '+=' + 0.5 * window.innerHeight,
        scrub: true
      }
    });
  });

});