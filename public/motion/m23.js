gsap.registerPlugin(ScrollTrigger);

document.querySelectorAll('.flash-text, [data-flash]').forEach(el => {
  splitToWords(el);

  const words = el.querySelectorAll('.flash-word');

  gsap.set(words, {
    opacity: 0,
    color: '#F94A00'
  });

  gsap.to(words, {
    scrollTrigger: {
      trigger: el,
      start: 'top 90%',
      once: true
    },
    keyframes: [
      { opacity: 1, color: '#F94A00', duration: 0.2, ease: 'power2.out' },
      { color: '#FD7B03', duration: 0.05 },
      { color: 'var(--fonts-100)', duration: 0.1 }
    ],
    stagger: { each: 0.1 }
  });
});