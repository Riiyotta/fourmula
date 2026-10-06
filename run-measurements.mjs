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
    
    console.log('\n=== ORIGINAL SITE (fourmula.ai) ===');
    const origPage = await browser.newPage();
    await origPage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await origPage.goto('https://fourmula.ai/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      await sleep(3000);
      
      const origMeasurements = await origPage.evaluate(() => {
        const headerMenu = document.querySelector('.header__menu');
        const menuWrap = document.querySelector('.menu__wrap');
        const menuItems = document.querySelectorAll('.menu__item');
        const topLine = document.querySelector('.header__menu-line.is-top');
        const bottomLine = document.querySelector('.header__menu-line.is-bottom');
        const menuTxt = document.querySelector('.header__menu-txt');
        const body = document.body;
        const carousel = document.querySelector('.hero__carousel__in');
        
        return {
          headerMenuHasOpen: headerMenu ? headerMenu.classList.contains('is-open') : null,
          menuWrapWidth: menuWrap ? getComputedStyle(menuWrap).width : null,
          menuWrapHeight: menuWrap ? getComputedStyle(menuWrap).height : null,
          menuWrapOverflow: menuWrap ? getComputedStyle(menuWrap).overflow : null,
          menuItemOpacity: menuItems.length > 0 ? parseFloat(getComputedStyle(menuItems[0]).opacity) : null,
          menuTxt: menuTxt ? menuTxt.textContent.trim() : null,
          bodyClass: body.className,
          backgroundColor: getComputedStyle(body).backgroundColor,
          carouselTransform: carousel ? getComputedStyle(carousel).transform : null
        };
      });
      console.log(JSON.stringify(origMeasurements, null, 2));
    } catch (e) {
      console.error('Error measuring original:', e.message);
    }
    
    try {
      const headerMenuOrig = await origPage.$('.header__menu');
      if (headerMenuOrig) {
        console.log('\n=== MENU CLICK TEST - ORIGINAL ===');
        await headerMenuOrig.click();
        await sleep(700);
        const menuAfter = await origPage.evaluate(() => {
          const headerMenu = document.querySelector('.header__menu');
          const menuWrap = document.querySelector('.menu__wrap');
          const menuItems = document.querySelectorAll('.menu__item');
          return {
            headerMenuHasOpen: headerMenu.classList.contains('is-open'),
            menuWrapHeight: getComputedStyle(menuWrap).height,
            menuItemOpacity: menuItems.length > 0 ? parseFloat(getComputedStyle(menuItems[0]).opacity) : null
          };
        });
        console.log(JSON.stringify(menuAfter, null, 2));
      }
    } catch (e) {
      console.error('Error testing menu:', e.message);
    }
    
    await origPage.close();
    
    console.log('\n=== CLONE SITE (localhost:5190) ===');
    const clonePage = await browser.newPage();
    await clonePage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await clonePage.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      await sleep(2000);
      
      const cloneMeasurements = await clonePage.evaluate(() => {
        const headerMenu = document.querySelector('.header__menu');
        const menuWrap = document.querySelector('.menu__wrap');
        const menuItems = document.querySelectorAll('.menu__item');
        const topLine = document.querySelector('.header__menu-line.is-top');
        const bottomLine = document.querySelector('.header__menu-line.is-bottom');
        const menuTxt = document.querySelector('.header__menu-txt');
        const body = document.body;
        const carousel = document.querySelector('.hero__carousel__in');
        
        return {
          headerMenuHasOpen: headerMenu ? headerMenu.classList.contains('is-open') : null,
          menuWrapWidth: menuWrap ? getComputedStyle(menuWrap).width : null,
          menuWrapHeight: menuWrap ? getComputedStyle(menuWrap).height : null,
          menuWrapOverflow: menuWrap ? getComputedStyle(menuWrap).overflow : null,
          menuItemOpacity: menuItems.length > 0 ? parseFloat(getComputedStyle(menuItems[0]).opacity) : null,
          menuTxt: menuTxt ? menuTxt.textContent.trim() : null,
          bodyClass: body.className,
          backgroundColor: getComputedStyle(body).backgroundColor,
          carouselTransform: carousel ? getComputedStyle(carousel).transform : null
        };
      });
      console.log(JSON.stringify(cloneMeasurements, null, 2));
    } catch (e) {
      console.error('Error measuring clone:', e.message);
    }
    
    try {
      const headerMenuClone = await clonePage.$('.header__menu');
      if (headerMenuClone) {
        console.log('\n=== MENU CLICK TEST - CLONE ===');
        await headerMenuClone.click();
        await sleep(700);
        const menuAfter = await clonePage.evaluate(() => {
          const headerMenu = document.querySelector('.header__menu');
          const menuWrap = document.querySelector('.menu__wrap');
          const menuItems = document.querySelectorAll('.menu__item');
          return {
            headerMenuHasOpen: headerMenu.classList.contains('is-open'),
            menuWrapHeight: getComputedStyle(menuWrap).height,
            menuItemOpacity: menuItems.length > 0 ? parseFloat(getComputedStyle(menuItems[0]).opacity) : null
          };
        });
        console.log(JSON.stringify(menuAfter, null, 2));
      }
    } catch (e) {
      console.error('Error testing menu clone:', e.message);
    }
    
    await clonePage.close();
    
  } catch (e) {
    console.error('Fatal error:', e);
  } finally {
    if (browser) await browser.close();
  }
})();
