(function () {

  gsap.set('[data-hero-text]', { opacity: 0 });

  gsap.set(
    '.header__left-link, .header__main, .menu__wrap-main, .is-header-btn',
    { opacity: 0, y: 24, scale: 0.9 }
  );

  gsap.set('.hero__upload, .hero__carousel__item', {
    opacity: 0,
    scale: 0.5
  });

  gsap.set('.hero__slider__item', {
    opacity: 0,
    x: 40,
    scale: 0.9
  });

  function splitHeroWords(element) {
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );

    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      const words = node.textContent.split(/(\s+)/);
      const frag = document.createDocumentFragment();

      words.forEach(word => {
        if (!word.trim()) {
          frag.appendChild(document.createTextNode(word));
        } else {
          const span = document.createElement('span');
          span.className = 'hero-flash-word';
          span.textContent = word;

          const parent50 =
            node.parentElement.closest('.u-fonts-50') ||
            node.parentElement.classList.contains('u-fonts-50');

          span.dataset.finalOpacity = parent50 ? 0.5 : 1;

          frag.appendChild(span);
        }
      });

      node.parentNode.replaceChild(frag, node);
    });
  }

  function playHeroIntro() {

    const tl = gsap.timeline();

    document.querySelectorAll('[data-hero-text]').forEach(el => {
      splitHeroWords(el);

      const words = el.querySelectorAll('.hero-flash-word');

      gsap.set(words, { opacity: 0, color: '#F94A00' });
      gsap.set(el, { opacity: 1 });

      tl.to(words, {
        stagger: 0.2,
        ease: 'power2.out',
        keyframes: [
          { opacity: 1, color: '#F94A00', duration: 0.05 },
          { color: '#FD7B03', duration: 0.05 },
          {
            opacity: i => words[i].dataset.finalOpacity,
            color: 'var(--fonts-100)',
            duration: 0.05
          }
        ]
      }, 0);
    });

    tl.to('.header__left-link', {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.5,
      ease: 'power2.out'
    }, 0.1);

    tl.to(['.header__main', '.menu__wrap-main'], {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.6,
      ease: 'power2.out'
    }, 0.2);

    tl.to('.is-header-btn', {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.5,
      ease: 'power2.out'
    }, 0.35);

    tl.to('.hero__upload', {
      opacity: 1,
      scale: 1,
      duration: 0.6,
      ease: 'power2.out'
    }, 0.25);

    tl.to('.hero__carousel__item', {
      opacity: 1,
      scale: 1,
      duration: 0.5,
      stagger: 0.12,
      ease: 'power2.out'
    }, 0.3);

    tl.to('.hero__slider__item', {
      opacity: 1,
      x: 0,
      scale: 1,
      duration: 0.5,
      stagger: 0.12,
      ease: 'power2.out'
    }, 0.35);
  }

  document.addEventListener('preloader:done', () => {
    playHeroIntro();
  });

})();