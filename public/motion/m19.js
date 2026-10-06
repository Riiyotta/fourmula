document.addEventListener('DOMContentLoaded', () => {
    const btn = document.querySelector('.header__menu');
    const txt = document.querySelector('.header__menu-txt');
    const menu = document.querySelector('.menu__wrap');
    const items = menu.querySelectorAll('.menu__item');
    const footer = document.querySelector('.footer');
    const letters = '•';

    if (!btn || !txt || !menu || !footer) return;

    let isOpen = false;

    function getInitialMenuProps() {
      if (window.innerWidth <= 767) {
        return { width: '15.5rem', height: '2.7rem', y: '0.5rem', padding: '0rem', overflow: 'hidden' };
      }

      return { width: '15rem', height: '2.7rem', y: '1.25rem', padding: '0rem', overflow: 'hidden' };
    }

    gsap.set(menu, getInitialMenuProps());
    gsap.set(items, { opacity: 0 });

    function getMenuProps() {
      if (window.innerWidth <= 991) {
        return { width: '16.2rem', height: '39rem', padding: '5rem 1rem 1rem 1rem' };
      }

      return { width: '18rem', height: '39rem', padding: '6.25rem 1.25rem 2.5rem 1.25rem' };
    }

    function scrambleText(newText) {
      const oldText = txt.textContent;
      const length = Math.max(oldText.length, newText.length);
      let frame = 0;
      const totalFrames = 20;

      const interval = setInterval(() => {
        let display = '';

        for (let i = 0; i < length; i++) {
          if (i < newText.length && frame / totalFrames > i / length) {
            display += newText[i];
          } else {
            display += letters[Math.floor(Math.random() * letters.length)];
          }
        }

        txt.textContent = display;
        frame++;

        if (frame > totalFrames) {
          txt.textContent = newText;
          clearInterval(interval);
        }
      }, 20);
    }

    const menuTL = gsap.timeline({ paused: true });
    const props = getMenuProps();

    menuTL
      .to(menu, {
        y: 0,
        width: props.width,
        height: props.height,
        padding: props.padding,
        duration: 0.4,
        ease: 'power2.out',
      })
      .to(
        items,
        {
          opacity: 1,
          stagger: 0.05,
          duration: 0.3,
        },
        '-=0.2',
      );

    function closeMenu(delay = 0) {
      if (!isOpen) return;

      isOpen = false;
      btn.classList.remove('is-open');
      scrambleText('Menu');

      gsap.to([...items].reverse(), {
        opacity: 0,
        stagger: 0.05,
        duration: 0.2,
      });

      menuTL.reverse(delay);
    }

    function openMenu() {
      if (isOpen) return;

      isOpen = true;
      btn.classList.add('is-open');
      scrambleText('Close');
      menuTL.play();
    }

    btn.addEventListener('click', () => {
      if (isOpen) {
        closeMenu(0.3);
      } else {
        openMenu();
      }
    });

    document.addEventListener('click', (e) => {
      if (isOpen && !menu.contains(e.target) && !btn.contains(e.target)) {
        closeMenu(0.3);
      }
    });

    items.forEach((item) => {
      item.addEventListener('click', () => {
        if (isOpen) closeMenu(0.3);
      });
    });

    window.addEventListener('resize', () => {
      if (isOpen) {
        const props = getMenuProps();

        gsap.to(menu, {
          width: props.width,
          height: props.height,
          padding: props.padding,
          duration: 0.2,
        });
      } else {
        gsap.set(menu, getInitialMenuProps());
      }
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.intersectionRatio >= 0.5) {
            closeMenu(0.3);
          }
        });
      },
      {
        threshold: Array.from({ length: 101 }, (_, i) => i / 100),
      },
    );

    observer.observe(footer);
  });