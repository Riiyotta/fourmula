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
    
    console.log('\n===== FINAL MEASUREMENTS: DOT FIELD & PROGRESS BAR =====\n');
    
    // Test Original
    console.log('--- ORIGINAL SITE ---');
    const origPage = await browser.newPage();
    await origPage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await origPage.goto('https://fourmula.ai/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      await sleep(2000);
      
      const data = await origPage.evaluate(() => {
        const dots = document.querySelectorAll('[class*="dot"]');
        const dotField = document.querySelector('[class*="dot-field"]');
        const dotRing = document.querySelector('.dot-ring');
        const progressBar = document.querySelector('#progress');
        
        return {
          dotsCount: dots.length,
          dotFieldExists: dotField ? true : false,
          dotRingExists: dotRing ? true : false,
          progressBarExists: progressBar ? true : false,
          progressBarWidth: progressBar ? getComputedStyle(progressBar).width : null,
          progressBarDisplay: progressBar ? getComputedStyle(progressBar).display : null
        };
      });
      console.log(JSON.stringify(data, null, 2));
      
    } catch (e) {
      console.error('Error:', e.message);
    }
    
    await origPage.close();
    
    // Test Clone
    console.log('\n--- CLONE SITE ---');
    const clonePage = await browser.newPage();
    await clonePage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await clonePage.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      await sleep(2000);
      
      const data = await clonePage.evaluate(() => {
        const dots = document.querySelectorAll('[class*="dot"]');
        const dotField = document.querySelector('[class*="dot-field"]');
        const dotRing = document.querySelector('.dot-ring');
        const progressBar = document.querySelector('#progress');
        
        return {
          dotsCount: dots.length,
          dotFieldExists: dotField ? true : false,
          dotRingExists: dotRing ? true : false,
          progressBarExists: progressBar ? true : false,
          progressBarWidth: progressBar ? getComputedStyle(progressBar).width : null,
          progressBarDisplay: progressBar ? getComputedStyle(progressBar).display : null
        };
      });
      console.log(JSON.stringify(data, null, 2));
      
    } catch (e) {
      console.error('Error:', e.message);
    }
    
    await clonePage.close();
    
  } catch (e) {
    console.error('Fatal error:', e);
  } finally {
    if (browser) await browser.close();
  }
})();
