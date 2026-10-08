const puppeteer = require('puppeteer');

const measurementScript = `
function getMenuState() {
  const headerMenu = document.querySelector('.header__menu');
  const menuWrap = document.querySelector('.menu__wrap');
  const menuItems = document.querySelectorAll('.menu__item');
  const topLine = document.querySelector('.header__menu-line.is-top');
  const bottomLine = document.querySelector('.header__menu-line.is-bottom');
  const menuTxt = document.querySelector('.header__menu-txt');
  
  const getTransformRotation = (transform) => {
    if (!transform || transform === 'none') return 0;
    const match = transform.match(/rotate\\(([^)]+)deg/);
    return match ? parseFloat(match[1]) : null;
  };
  
  return {
    headerMenuHasOpen: headerMenu ? headerMenu.classList.contains('is-open') : null,
    menuWrapWidth: menuWrap ? getComputedStyle(menuWrap).width : null,
    menuWrapHeight: menuWrap ? getComputedStyle(menuWrap).height : null,
    menuWrapOverflow: menuWrap ? getComputedStyle(menuWrap).overflow : null,
    menuWrapTransform: menuWrap ? getComputedStyle(menuWrap).transform : null,
    menuItemOpacity: menuItems.length > 0 ? parseFloat(getComputedStyle(menuItems[0]).opacity) : null,
    topLineRotate: topLine ? getTransformRotation(getComputedStyle(topLine).transform) : null,
    bottomLineRotate: bottomLine ? getTransformRotation(getComputedStyle(bottomLine).transform) : null,
    menuTxt: menuTxt ? menuTxt.textContent.trim() : null
  };
}

function getHeroState() {
  const carousel = document.querySelector('.hero__carousel__in');
  const carouselImg = document.querySelector('.hero__carousel__img');
  
  return {
    carouselTransform: carousel ? getComputedStyle(carousel).transform : null,
    carouselImgTransform: carouselImg ? getComputedStyle(carouselImg).transform : null
  };
}

function getThemeState() {
  const body = document.body;
  const bgColor = getComputedStyle(body).backgroundColor;
  
  return {
    bodyClass: body.className,
    backgroundColor: bgColor
  };
}

return {
  menuState: getMenuState(),
  heroState: getHeroState(),
  theme: getThemeState()
};
`;

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    
    console.log('\\n=== ORIGINAL SITE (fourmula.ai) ===');
    const origPage = await browser.newPage();
    await origPage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await origPage.goto('https://fourmula.ai/', { waitUntil: 'networkidle2', timeout: 30000 });
      await origPage.waitForTimeout(2000);
      
      const origMeasurements = await origPage.evaluate(measurementScript);
      console.log(JSON.stringify(origMeasurements, null, 2));
    } catch (e) {
      console.error('Error measuring original:', e.message);
    }
    
    try {
      const headerMenuOrig = await origPage.$('.header__menu');
      if (headerMenuOrig) {
        console.log('\\n=== MENU CLICK TEST - ORIGINAL ===');
        await headerMenuOrig.click();
        await origPage.waitForTimeout(600);
        const menuAfter = await origPage.evaluate(() => {
          const headerMenu = document.querySelector('.header__menu');
          const menuWrap = document.querySelector('.menu__wrap');
          return {
            headerMenuHasOpen: headerMenu.classList.contains('is-open'),
            menuWrapDisplay: getComputedStyle(menuWrap).display,
            menuWrapHeight: getComputedStyle(menuWrap).height
          };
        });
        console.log(JSON.stringify(menuAfter, null, 2));
      }
    } catch (e) {
      console.error('Error testing menu:', e.message);
    }
    
    await origPage.close();
    
    console.log('\\n=== CLONE SITE (localhost:5190) ===');
    const clonePage = await browser.newPage();
    await clonePage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await clonePage.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      await clonePage.waitForTimeout(2000);
      
      const cloneMeasurements = await clonePage.evaluate(measurementScript);
      console.log(JSON.stringify(cloneMeasurements, null, 2));
    } catch (e) {
      console.error('Error measuring clone:', e.message);
    }
    
    try {
      const headerMenuClone = await clonePage.$('.header__menu');
      if (headerMenuClone) {
        console.log('\\n=== MENU CLICK TEST - CLONE ===');
        await headerMenuClone.click();
        await clonePage.waitForTimeout(600);
        const menuAfter = await clonePage.evaluate(() => {
          const headerMenu = document.querySelector('.header__menu');
          const menuWrap = document.querySelector('.menu__wrap');
          return {
            headerMenuHasOpen: headerMenu.classList.contains('is-open'),
            menuWrapDisplay: getComputedStyle(menuWrap).display,
            menuWrapHeight: getComputedStyle(menuWrap).height
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
