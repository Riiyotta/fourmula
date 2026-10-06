window.addEventListener('load', () => {
  const preloader = document.querySelector('.preloader');
  const numberEl = document.querySelector('.preloader__number');
  const images = document.querySelectorAll('.preloader__images-in');

  const VISIT_KEY = 'preloader_visited_v2';
  const isReturningUser = localStorage.getItem(VISIT_KEY) === '1';

  const speed = isReturningUser ? 1 / 5 : 1;

  localStorage.setItem(VISIT_KEY, '1');

  window.scrollTo(0, 0);

  const lockScroll = () => {
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
  };

  const unlockScroll = () => {
    document.documentElement.style.overflow = '';
    document.body.style.overflow = '';
  };

  lockScroll();

  let imageInterval;
  if (images.length) {
    let index = 0;
    imageInterval = setInterval(() => {
      images.forEach((img, i) => {
        img.style.zIndex = i === index ? 9 : 1;
      });
      index = (index + 1) % images.length;
    }, 500 * speed);
  }

  if (numberEl) {
    if (isReturningUser) {
      numberEl.textContent = 'Synced';
      gsap.fromTo(
        numberEl,
        { opacity: 0, y: 8, filter: 'blur(6px)' },
        { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.2, delay: 0.1, ease: 'power2.out' }
      );
    } else {
      const steps = [0, 17, 35, 58, 76, 89, 100];
      const totalDuration = 2.5;
      const tlNumber = gsap.timeline({ delay: 0.5 });

      steps.forEach((val, i) => {
        const prev = i === 0 ? 0 : steps[i - 1];
        tlNumber.to({ n: prev }, {
          n: val,
          duration: totalDuration / (steps.length - 1),
          ease: 'power2.out',
          onUpdate() {
            numberEl.textContent = Math.round(this.targets()[0].n);
          }
        });
      });
    }
  }

  const tl = gsap.timeline({
    onComplete: () => {
      document.documentElement.classList.remove('is-loading');
      document.dispatchEvent(new CustomEvent('preloader:done'));
      if (imageInterval) clearInterval(imageInterval);
      gsap.delayedCall(1 * speed, unlockScroll);
    }
  });

  tl.set('.preloader > *', { visibility: 'visible' });

  tl.fromTo(
    '.preloader > *',
    { opacity: 0, filter: 'blur(20px)' },
    { opacity: 1, filter: 'blur(0px)', duration: 1 * speed, stagger: 0.05 * speed, ease: 'power2.out' }
  );

  tl.to('.preloader > *', {
    opacity: 0,
    filter: 'blur(20px)',
    duration: 1 * speed,
    delay: 2.5 * speed,
    stagger: 0.05 * speed,
    ease: 'power2.in'
  });

  tl.to(preloader, { opacity: 0, duration: 0.6 * speed, ease: 'power2.in' });
});