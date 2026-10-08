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
    
    console.log('\n===== PRIORITY 2: PRELOADER & HERO TEXT =====\n');
    
    // Test Original
    console.log('--- ORIGINAL SITE - Preloader & Hero ---');
    const origPage = await browser.newPage();
    await origPage.setViewport({ width: 1920, height: 1080 });
    
    try {
      // Navigate with page start timing
      const startTime = Date.now();
      await origPage.goto('https://fourmula.ai/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      const preloadStart = Date.now() - startTime;
      
      // Check preloader immediately
      let preloaderVisible = true;
      const checkInterval = 100;
      let preloaderHideTime = null;
      
      // Check for preloader status over time
      for (let t = 0; t < 5000; t += checkInterval) {
        const status = await origPage.evaluate(() => {
          const preloader = document.querySelector('.preloader');
          const docElem = document.documentElement;
          const heroText = document.querySelector('[data-hero-text]');
          
          return {
            preloaderDisplay: preloader ? getComputedStyle(preloader).display : null,
            preloaderOpacity: preloader ? getComputedStyle(preloader).opacity : null,
            isLoadingClass: docElem.classList.contains('is-loading'),
            heroTextOpacity: heroText ? getComputedStyle(heroText).opacity : null
          };
        });
        
        if (status.preloaderDisplay === 'none' || status.preloaderOpacity === '0') {
          if (!preloaderHideTime) preloaderHideTime = t + preloadStart;
        }
        
        if (t === 0) {
          console.log('At page load (DOMContentLoaded):');
          console.log(JSON.stringify(status, null, 2));
        }
        
        await sleep(checkInterval);
      }
      
      if (preloaderHideTime) {
        console.log(`\nPreloader hidden at: ${preloaderHideTime}ms from page start`);
      }
      
      // Check hero text opacity
      console.log('\nHero text opacity at 3s:');
      const heroText = await origPage.evaluate(() => {
        const texts = document.querySelectorAll('[data-hero-text]');
        const result = [];
        texts.forEach((el, idx) => {
          if (idx < 3) {
            result.push({
              text: el.textContent.substring(0, 20),
              opacity: parseFloat(getComputedStyle(el).opacity),
              dataFinalOpacity: el.getAttribute('data-final-opacity')
            });
          }
        });
        return result;
      });
      console.log(JSON.stringify(heroText, null, 2));
      
    } catch (e) {
      console.error('Error with original:', e.message);
    }
    
    await origPage.close();
    
    // Test Clone
    console.log('\n--- CLONE SITE - Preloader & Hero ---');
    const clonePage = await browser.newPage();
    await clonePage.setViewport({ width: 1920, height: 1080 });
    
    try {
      const startTime = Date.now();
      await clonePage.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      const preloadStart = Date.now() - startTime;
      
      // Check preloader immediately
      const checkInterval = 100;
      let preloaderHideTime = null;
      
      for (let t = 0; t < 5000; t += checkInterval) {
        const status = await clonePage.evaluate(() => {
          const preloader = document.querySelector('.preloader');
          const docElem = document.documentElement;
          const heroText = document.querySelector('[data-hero-text]');
          
          return {
            preloaderDisplay: preloader ? getComputedStyle(preloader).display : null,
            preloaderOpacity: preloader ? getComputedStyle(preloader).opacity : null,
            isLoadingClass: docElem.classList.contains('is-loading'),
            heroTextOpacity: heroText ? getComputedStyle(heroText).opacity : null
          };
        });
        
        if (status.preloaderDisplay === 'none' || status.preloaderOpacity === '0') {
          if (!preloaderHideTime) preloaderHideTime = t + preloadStart;
        }
        
        if (t === 0) {
          console.log('At page load (networkidle2):');
          console.log(JSON.stringify(status, null, 2));
        }
        
        await sleep(checkInterval);
      }
      
      if (preloaderHideTime) {
        console.log(`\nPreloader hidden at: ${preloaderHideTime}ms from page start`);
      }
      
      // Check hero text opacity
      console.log('\nHero text opacity at 3s:');
      const heroText = await clonePage.evaluate(() => {
        const texts = document.querySelectorAll('[data-hero-text]');
        const result = [];
        texts.forEach((el, idx) => {
          if (idx < 3) {
            result.push({
              text: el.textContent.substring(0, 20),
              opacity: parseFloat(getComputedStyle(el).opacity),
              dataFinalOpacity: el.getAttribute('data-final-opacity')
            });
          }
        });
        return result;
      });
      console.log(JSON.stringify(heroText, null, 2));
      
    } catch (e) {
      console.error('Error with clone:', e.message);
    }
    
    await clonePage.close();
    
  } catch (e) {
    console.error('Fatal error:', e);
  } finally {
    if (browser) await browser.close();
  }
})();
