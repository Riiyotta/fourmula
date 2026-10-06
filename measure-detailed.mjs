import puppeteer from 'puppeteer';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    
    console.log('\n===== PRIORITY 1: MENU TESTING =====\n');
    
    // Test Original
    console.log('--- ORIGINAL SITE ---');
    const origPage = await browser.newPage();
    await origPage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await origPage.goto('https://fourmula.ai/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      await sleep(2000);
      
      console.log('\nBefore clicking menu:');
      const before = await origPage.evaluate(() => {
        const headerMenu = document.querySelector('.header__menu');
        const menuWrap = document.querySelector('.menu__wrap');
        const topLine = document.querySelector('.header__menu-line.is-top');
        const bottomLine = document.querySelector('.header__menu-line.is-bottom');
        const menuTxt = document.querySelector('.header__menu-txt');
        const menuItems = document.querySelectorAll('.menu__item');
        
        const getLineRotation = (el) => {
          if (!el) return null;
          const transform = getComputedStyle(el).transform;
          if (!transform || transform === 'none') return 0;
          const match = transform.match(/rotate\(([^)]+)deg/);
          return match ? parseFloat(match[1]) : null;
        };
        
        return {
          headerMenuHasOpen: headerMenu.classList.contains('is-open'),
          menuWrapWidth: getComputedStyle(menuWrap).width,
          menuWrapHeight: getComputedStyle(menuWrap).height,
          menuWrapOverflow: getComputedStyle(menuWrap).overflow,
          menuWrapTransform: getComputedStyle(menuWrap).transform,
          menuItemOpacity: Array.from(menuItems).map(el => parseFloat(getComputedStyle(el).opacity))[0],
          topLineRotate: getLineRotation(topLine),
          bottomLineRotate: getLineRotation(bottomLine),
          topLineTransform: topLine ? getComputedStyle(topLine).transform : null,
          bottomLineTransform: bottomLine ? getComputedStyle(bottomLine).transform : null,
          menuTxt: menuTxt ? menuTxt.textContent.trim() : null
        };
      });
      console.log(JSON.stringify(before, null, 2));
      
      // Click menu
      const headerMenuOrig = await origPage.$('.header__menu');
      if (headerMenuOrig) {
        await headerMenuOrig.click();
        await sleep(800);
        
        console.log('\nAfter clicking menu:');
        const after = await origPage.evaluate(() => {
          const headerMenu = document.querySelector('.header__menu');
          const menuWrap = document.querySelector('.menu__wrap');
          const topLine = document.querySelector('.header__menu-line.is-top');
          const bottomLine = document.querySelector('.header__menu-line.is-bottom');
          const menuTxt = document.querySelector('.header__menu-txt');
          const menuItems = document.querySelectorAll('.menu__item');
          
          const getLineRotation = (el) => {
            if (!el) return null;
            const transform = getComputedStyle(el).transform;
            if (!transform || transform === 'none') return 0;
            const match = transform.match(/rotate\(([^)]+)deg/);
            return match ? parseFloat(match[1]) : null;
          };
          
          return {
            headerMenuHasOpen: headerMenu.classList.contains('is-open'),
            menuWrapHeight: getComputedStyle(menuWrap).height,
            menuItemOpacity: Array.from(menuItems).map(el => parseFloat(getComputedStyle(el).opacity))[0],
            topLineRotate: getLineRotation(topLine),
            bottomLineRotate: getLineRotation(bottomLine),
            topLineTransform: topLine ? getComputedStyle(topLine).transform : null,
            bottomLineTransform: bottomLine ? getComputedStyle(bottomLine).transform : null,
            menuTxt: menuTxt ? menuTxt.textContent.trim() : null
          };
        });
        console.log(JSON.stringify(after, null, 2));
      }
    } catch (e) {
      console.error('Error with original:', e.message);
    }
    
    await origPage.close();
    
    // Test Clone
    console.log('\n--- CLONE SITE ---');
    const clonePage = await browser.newPage();
    await clonePage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await clonePage.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      await sleep(2000);
      
      console.log('\nBefore clicking menu:');
      const before = await clonePage.evaluate(() => {
        const headerMenu = document.querySelector('.header__menu');
        const menuWrap = document.querySelector('.menu__wrap');
        const topLine = document.querySelector('.header__menu-line.is-top');
        const bottomLine = document.querySelector('.header__menu-line.is-bottom');
        const menuTxt = document.querySelector('.header__menu-txt');
        const menuItems = document.querySelectorAll('.menu__item');
        
        const getLineRotation = (el) => {
          if (!el) return null;
          const transform = getComputedStyle(el).transform;
          if (!transform || transform === 'none') return 0;
          const match = transform.match(/rotate\(([^)]+)deg/);
          return match ? parseFloat(match[1]) : null;
        };
        
        return {
          headerMenuHasOpen: headerMenu.classList.contains('is-open'),
          menuWrapWidth: getComputedStyle(menuWrap).width,
          menuWrapHeight: getComputedStyle(menuWrap).height,
          menuWrapOverflow: getComputedStyle(menuWrap).overflow,
          menuWrapTransform: getComputedStyle(menuWrap).transform,
          menuItemOpacity: Array.from(menuItems).map(el => parseFloat(getComputedStyle(el).opacity))[0],
          topLineRotate: getLineRotation(topLine),
          bottomLineRotate: getLineRotation(bottomLine),
          topLineTransform: topLine ? getComputedStyle(topLine).transform : null,
          bottomLineTransform: bottomLine ? getComputedStyle(bottomLine).transform : null,
          menuTxt: menuTxt ? menuTxt.textContent.trim() : null
        };
      });
      console.log(JSON.stringify(before, null, 2));
      
      // Click menu
      const headerMenuClone = await clonePage.$('.header__menu');
      if (headerMenuClone) {
        await headerMenuClone.click();
        await sleep(800);
        
        console.log('\nAfter clicking menu:');
        const after = await clonePage.evaluate(() => {
          const headerMenu = document.querySelector('.header__menu');
          const menuWrap = document.querySelector('.menu__wrap');
          const topLine = document.querySelector('.header__menu-line.is-top');
          const bottomLine = document.querySelector('.header__menu-line.is-bottom');
          const menuTxt = document.querySelector('.header__menu-txt');
          const menuItems = document.querySelectorAll('.menu__item');
          
          const getLineRotation = (el) => {
            if (!el) return null;
            const transform = getComputedStyle(el).transform;
            if (!transform || transform === 'none') return 0;
            const match = transform.match(/rotate\(([^)]+)deg/);
            return match ? parseFloat(match[1]) : null;
          };
          
          return {
            headerMenuHasOpen: headerMenu.classList.contains('is-open'),
            menuWrapHeight: getComputedStyle(menuWrap).height,
            menuItemOpacity: Array.from(menuItems).map(el => parseFloat(getComputedStyle(el).opacity))[0],
            topLineRotate: getLineRotation(topLine),
            bottomLineRotate: getLineRotation(bottomLine),
            topLineTransform: topLine ? getComputedStyle(topLine).transform : null,
            bottomLineTransform: bottomLine ? getComputedStyle(bottomLine).transform : null,
            menuTxt: menuTxt ? menuTxt.textContent.trim() : null
          };
        });
        console.log(JSON.stringify(after, null, 2));
      }
    } catch (e) {
      console.error('Error with clone:', e.message);
    }
    
    await clonePage.close();
    
    console.log('\n===== PRIORITY 3: THEME & CAROUSEL =====\n');
    
    // Test Original carousel and theme
    console.log('--- ORIGINAL SITE ---');
    const origPage2 = await browser.newPage();
    await origPage2.setViewport({ width: 1920, height: 1080 });
    
    try {
      await origPage2.goto('https://fourmula.ai/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      await sleep(1000);
      
      const data = await origPage2.evaluate(() => {
        const body = document.body;
        const carousel = document.querySelector('.hero__carousel__in');
        const bgColor = getComputedStyle(body).backgroundColor;
        
        return {
          bodyClass: body.className,
          backgroundColor: bgColor,
          carouselTransform: carousel ? getComputedStyle(carousel).transform : null
        };
      });
      console.log(JSON.stringify(data, null, 2));
    } catch (e) {
      console.error('Error:', e.message);
    }
    
    await origPage2.close();
    
    // Test Clone carousel and theme
    console.log('\n--- CLONE SITE ---');
    const clonePage2 = await browser.newPage();
    await clonePage2.setViewport({ width: 1920, height: 1080 });
    
    try {
      await clonePage2.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      await sleep(1000);
      
      const data = await clonePage2.evaluate(() => {
        const body = document.body;
        const carousel = document.querySelector('.hero__carousel__in');
        const bgColor = getComputedStyle(body).backgroundColor;
        
        return {
          bodyClass: body.className,
          backgroundColor: bgColor,
          carouselTransform: carousel ? getComputedStyle(carousel).transform : null
        };
      });
      console.log(JSON.stringify(data, null, 2));
    } catch (e) {
      console.error('Error:', e.message);
    }
    
    await clonePage2.close();
    
  } catch (e) {
    console.error('Fatal error:', e);
  } finally {
    if (browser) await browser.close();
  }
})();
