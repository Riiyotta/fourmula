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
    
    console.log('\n===== CAROUSEL ROTATION MEASUREMENTS =====\n');
    
    // Helper to extract rotation angle from matrix
    const getAngle = (matrixStr) => {
      if (!matrixStr || matrixStr === 'none') return 0;
      const match = matrixStr.match(/matrix\(([^,]+),\s*([^,]+)/);
      if (!match) return null;
      const a = parseFloat(match[1]);
      const b = parseFloat(match[2]);
      const angle = Math.atan2(b, a) * 180 / Math.PI;
      return Math.round(angle * 100) / 100;
    };
    
    // Test Original site
    console.log('--- ORIGINAL SITE ---');
    const origPage = await browser.newPage();
    await origPage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await origPage.goto('https://fourmula.ai/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      
      // Measure at different times
      const times = [1000, 2000, 3000, 4000, 5000];
      
      for (const time of times) {
        await sleep(time);
        const data = await origPage.evaluate(() => {
          const carousel = document.querySelector('.hero__carousel__in');
          return carousel ? getComputedStyle(carousel).transform : null;
        });
        const angle = getAngle(data);
        console.log(`At ${time}ms: rotation = ${angle} degrees, matrix: ${data}`);
      }
      
    } catch (e) {
      console.error('Error with original:', e.message);
    }
    
    await origPage.close();
    
    // Test Clone site
    console.log('\n--- CLONE SITE ---');
    const clonePage = await browser.newPage();
    await clonePage.setViewport({ width: 1920, height: 1080 });
    
    try {
      await clonePage.goto('http://localhost:5190/', { waitUntil: 'networkidle2', timeout: 30000 });
      
      // Measure at different times
      const times = [1000, 2000, 3000, 4000, 5000];
      
      for (const time of times) {
        await sleep(time);
        const data = await clonePage.evaluate(() => {
          const carousel = document.querySelector('.hero__carousel__in');
          return carousel ? getComputedStyle(carousel).transform : null;
        });
        const angle = getAngle(data);
        console.log(`At ${time}ms: rotation = ${angle} degrees, matrix: ${data}`);
      }
      
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
