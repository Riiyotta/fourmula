(function () {

  const DEFAULTS = {
    direction: 'up',
    stagger: 0.02,
    duration: 0.2,
    delay: 0,
    ease: 'power1.inOut',
    reverse: true,
    custom: { opacity: 1 }
  };

  function splitToChars(element) {
    return new SplitType(element, { types: 'chars' });
  }

  function zeroState(element, props) {
    const computed = getComputedStyle(element);
    const out = {};

    for (const key in props) {
      if (key === 'opacity') {
        out[key] = 1;
      } else {
        out[key] = props[key].replace(/-?\d+(\.\d+)?/g, '0');
        if (!/\d/.test(props[key])) out[key] = computed[key];
      }
    }
    return out;
  }

  document.querySelectorAll('[hover-stagger]').forEach(el => {
    const hoverTarget = el.closest('[hover-stagger-wrap]') || el;

    el.style.position ||= 'relative';
    el.style.display ||= 'inline-block';
    el.style.overflow = 'hidden';

    el.style.webkitMaskImage = 'linear-gradient(#000 0 0)';
    el.style.maskImage = 'linear-gradient(#000 0 0)';
    el.style.webkitMaskSize = '100% 70%';
    el.style.maskSize = '100% 70%';
    el.style.webkitMaskPosition = 'center';
    el.style.maskPosition = 'center';
    el.style.webkitMaskRepeat = 'no-repeat';
    el.style.maskRepeat = 'no-repeat';

    const original = document.createElement('span');
    original.textContent = el.textContent;
    el.textContent = '';
    el.appendChild(original);

    const clone = original.cloneNode(true);
    clone.style.position = 'absolute';
    clone.style.left = 0;
    clone.style.top = DEFAULTS.direction === 'up' ? '100%' : '-100%';
    el.appendChild(clone);

    const splitMain = splitToChars(original);
    const splitClone = splitToChars(clone);

    const toState = zeroState(original, DEFAULTS.custom);
    const move = DEFAULTS.direction === 'up' ? -100 : 100;

    const tl = gsap.timeline({
      paused: true,
      defaults: {
        ease: DEFAULTS.ease,
        duration: DEFAULTS.duration,
        stagger: DEFAULTS.stagger,
        delay: DEFAULTS.delay
      }
    });

    tl.fromTo(
      splitMain.chars,
      { yPercent: 0, ...DEFAULTS.custom },
      { yPercent: move, ...toState }
    ).fromTo(
      splitClone.chars,
      { yPercent: 0, ...DEFAULTS.custom },
      { yPercent: move, ...toState },
      '<'
    );

    hoverTarget.addEventListener('mouseenter', () => tl.restart());
    hoverTarget.addEventListener('mouseleave', () => DEFAULTS.reverse && tl.reverse());
  });

})();