import puppeteer from 'puppeteer';
import fs from 'fs';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const routes = [
  { path: '/', preloader: true, menu: true, footer: true, badge: true, name: 'Home' },
  { path: '/privacy-policy', preloader: false, menu: true, footer: true, badge: true, name: 'Privacy' },
  { path: '/terms-of-service', preloader: false, menu: true, footer: true, badge: true, name: 'Terms' },
  { path: '/some-missing-page', preloader: true, menu: false, footer: false, badge: true, name: '404' },
];

async function waitForPreloaderHidden(page) {
  try {
    await page.waitForFunction(() => {
      const preloader = document.querySelector('.preloader');
      const html = document.documentElement;
      return !preloader && !html.classList.contains('is-loading');
    }, { timeout: 8000 });
  } catch (e) {
    // Timeout is ok, preloader might not exist on this page
  }
}

async function captureScreenshot(page, route, viewportWidth) {
  const filename = `/tmp/test-${route.path.replace(/\//g, '-')}-${viewportWidth}px.png`;
  try {
    await page.screenshot({ path: filename, fullPage: true });
    return filename;
  } catch (e) {
    return null;
  }
}

async function testRoute(browser, route) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`TESTING: ${route.name} (${route.path})`);
  console.log(`${'='.repeat(60)}`);
  
  try {
    const page = await browser.newPage();
    
    // Collect console messages
    const consoleLogs = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });
    
    // Collect network errors
    const networkErrors = [];
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push({
          status: response.status(),
          url: response.url()
        });
      }
    });
    
    // Test at 1440px (desktop)
    console.log('\n[1440px Desktop]');
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto(`http://localhost:5190${route.path}`, { waitUntil: 'networkidle2', timeout: 30000 });
    await waitForPreloaderHidden(page);
    await sleep(500); // Wait for animations
    
    // Screenshot at 1440px
    await captureScreenshot(page, route, 1440);
    
    // Check chrome elements
    const chromeElements = await page.evaluate(() => {
      return {
        preloader: !!document.querySelector('.preloader'),
        menu: !!document.querySelector('.menu'),
        footer: !!document.querySelector('.footer'),
        badge: !!document.querySelector('#awwwards'),
        header: !!document.querySelector('.header'),
        bodyHeight: document.body.scrollHeight,
        bodyClass: document.body.className
      };
    });
    
    console.log(`Chrome elements found:`);
    console.log(`  .preloader (expected: ${route.preloader}): ${chromeElements.preloader} ${chromeElements.preloader !== route.preloader ? '❌ MISMATCH' : '✓'}`);
    console.log(`  .menu (expected: ${route.menu}): ${chromeElements.menu} ${chromeElements.menu !== route.menu ? '❌ MISMATCH' : '✓'}`);
    console.log(`  .footer (expected: ${route.footer}): ${chromeElements.footer} ${chromeElements.footer !== route.footer ? '❌ MISMATCH' : '✓'}`);
    console.log(`  #awwwards (expected: ${route.badge}): ${chromeElements.badge} ${chromeElements.badge !== route.badge ? '❌ MISMATCH' : '✓'}`);
    console.log(`  .header: ${chromeElements.header}`);
    console.log(`Body scroll height: ${chromeElements.bodyHeight}`);
    console.log(`Body class: ${chromeElements.bodyClass}`);
    
    // Check for visible content
    const hasContent = await page.evaluate(() => {
      const page = document.querySelector('.page');
      const children = page ? page.children.length : 0;
      const text = document.body.innerText.length;
      return { page: !!page, children, text };
    });
    console.log(`Content check: .page=${hasContent.page}, children=${hasContent.children}, text length=${hasContent.text}`);
    
    // Test GSAP and menu interaction
    if (route.menu) {
      console.log(`\nMenu interaction test:`);
      const gsapExists = await page.evaluate(() => !!window.gsap);
      console.log(`  window.gsap exists: ${gsapExists}`);
      
      const headerMenuElement = await page.$('.header__menu');
      if (headerMenuElement) {
        const beforeClick = await page.evaluate(() => {
          const menuWrap = document.querySelector('.menu__wrap');
          const headerMenu = document.querySelector('.header__menu');
          return {
            menuWrapWidth: menuWrap ? getComputedStyle(menuWrap).width : 'N/A',
            menuWrapHeight: menuWrap ? getComputedStyle(menuWrap).height : 'N/A',
            headerMenuOpen: headerMenu ? headerMenu.classList.contains('is-open') : false
          };
        });
        
        await headerMenuElement.click();
        await sleep(700);
        
        const afterClick = await page.evaluate(() => {
          const menuWrap = document.querySelector('.menu__wrap');
          const headerMenu = document.querySelector('.header__menu');
          return {
            menuWrapWidth: menuWrap ? getComputedStyle(menuWrap).width : 'N/A',
            menuWrapHeight: menuWrap ? getComputedStyle(menuWrap).height : 'N/A',
            headerMenuOpen: headerMenu ? headerMenu.classList.contains('is-open') : false
          };
        });
        
        console.log(`  Before click: is-open=${beforeClick.headerMenuOpen}, width=${beforeClick.menuWrapWidth}, height=${beforeClick.menuWrapHeight}`);
        console.log(`  After click: is-open=${afterClick.headerMenuOpen}, width=${afterClick.menuWrapWidth}, height=${afterClick.menuWrapHeight}`);
        
        const menuChanged = beforeClick.menuWrapWidth !== afterClick.menuWrapWidth || 
                           beforeClick.menuWrapHeight !== afterClick.menuWrapHeight ||
                           beforeClick.headerMenuOpen !== afterClick.headerMenuOpen;
        console.log(`  Menu changed on click: ${menuChanged ? '✓' : '❌'}`);
      }
    }
    
    // Check for legal content (privacy/terms)
    if (route.path === '/privacy-policy' || route.path === '/terms-of-service') {
      console.log(`\nLegal content check:`);
      const legalContent = await page.evaluate(() => {
        const tech = document.querySelector('.tech');
        const heading = tech ? tech.querySelector('h1, h2, h3') : null;
        const table = document.querySelector('.tech__rich-table');
        const h2s = tech ? tech.querySelectorAll('h2').length : 0;
        const ps = tech ? tech.querySelectorAll('p').length : 0;
        const tocLinks = document.querySelectorAll('a[href^="#"]');
        return {
          tech: !!tech,
          heading: !!heading,
          headingText: heading ? heading.textContent.substring(0, 50) : 'N/A',
          table: !!table,
          h2Count: h2s,
          pCount: ps,
          tocLinksCount: tocLinks.length
        };
      });
      console.log(`  .tech section: ${legalContent.tech} ${legalContent.tech ? '✓' : '❌'}`);
      if (legalContent.tech) {
        console.log(`    Heading found: ${legalContent.heading} - "${legalContent.headingText}..."`);
        console.log(`    Table (.tech__rich-table): ${legalContent.table}`);
        console.log(`    h2 count: ${legalContent.h2Count}`);
        console.log(`    p count: ${legalContent.pCount}`);
        console.log(`    TOC anchor links: ${legalContent.tocLinksCount}`);
      }
    }
    
    // Check for 404 content
    if (route.path === '/some-missing-page') {
      console.log(`\n404 content check:`);
      const notFoundContent = await page.evaluate(() => {
        const wrap = document.querySelector('.hero__404__wrap');
        const images = document.querySelectorAll('.hero__404__loop-img');
        return {
          wrap: !!wrap,
          imageCount: images.length
        };
      });
      console.log(`  .hero__404__wrap: ${notFoundContent.wrap}`);
      console.log(`  .hero__404__loop-img images: ${notFoundContent.imageCount}`);
    }
    
    // Test active nav state
    if (route.path !== '/' && route.path !== '/some-missing-page') {
      console.log(`\nActive nav state check:`);
      const navState = await page.evaluate((currentPath) => {
        const links = document.querySelectorAll('a[href]');
        const currentLink = Array.from(links).find(a => a.getAttribute('href') === currentPath);
        const logoLink = document.querySelector('a.logo, a.header__logo, [class*="logo"]');
        return {
          currentLinkHasAriaCurrent: currentLink ? currentLink.getAttribute('aria-current') === 'page' : 'N/A',
          currentLinkHasCurrent: currentLink ? currentLink.classList.contains('w--current') : 'N/A',
          logoHasAriaCurrent: logoLink ? logoLink.getAttribute('aria-current') : 'N/A',
          logoHasCurrent: logoLink ? logoLink.classList.contains('w--current') : 'N/A'
        };
      }, route.path);
      console.log(`  Current route link: aria-current="page"=${navState.currentLinkHasAriaCurrent}, w--current=${navState.currentLinkHasCurrent}`);
      console.log(`  Logo link: aria-current=${navState.logoHasAriaCurrent}, w--current=${navState.logoHasCurrent}`);
    }
    
    // Test at 390px (mobile)
    console.log(`\n[390px Mobile]`);
    await page.setViewport({ width: 390, height: 844 });
    
    // Check for horizontal overflow
    const horizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth;
    });
    console.log(`Horizontal overflow at 390px: ${horizontalOverflow ? '❌ YES - OVERFLOW DETECTED' : '✓ No'}`);
    
    // Log console errors/warnings
    if (consoleLogs.length > 0) {
      const errors = consoleLogs.filter(l => l.type === 'error' || l.type === 'warning');
      if (errors.length > 0) {
        console.log(`\nConsole errors/warnings:`);
        errors.forEach(e => {
          console.log(`  [${e.type.toUpperCase()}] ${e.text}`);
        });
      }
    }
    
    // Log network errors
    if (networkErrors.length > 0) {
      console.log(`\nNetwork errors (status >= 400):`);
      networkErrors.forEach(e => {
        console.log(`  [${e.status}] ${e.url}`);
      });
    }
    
    await page.close();
    
  } catch (err) {
    console.error(`ERROR TESTING ${route.path}:`, err.message);
  }
}

async function testNavigation(browser) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`NAVIGATION TEST: Privacy -> Terms`);
  console.log(`${'='.repeat(60)}`);
  
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });
    
    // Go to privacy
    await page.goto('http://localhost:5190/privacy-policy', { waitUntil: 'networkidle2', timeout: 30000 });
    await waitForPreloaderHidden(page);
    
    console.log('Navigated to /privacy-policy');
    
    // Find and click link to terms
    const termsLink = await page.$('a[href="/terms-of-service"]');
    if (termsLink) {
      console.log('Found link to /terms-of-service, navigating...');
      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }),
        termsLink.click()
      ]);
      
      await waitForPreloaderHidden(page);
      
      const currentUrl = page.url();
      const termsContent = await page.evaluate(() => {
        return !!document.querySelector('.tech');
      });
      
      console.log(`Current URL: ${currentUrl}`);
      console.log(`Terms content rendered: ${termsContent}`);
    } else {
      console.log('Terms link not found');
    }
    
    await page.close();
  } catch (err) {
    console.error('Navigation test error:', err.message);
  }
}

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    
    for (const route of routes) {
      await testRoute(browser, route);
    }
    
    // Test navigation between pages
    await testNavigation(browser);
    
  } catch (e) {
    console.error('Fatal error:', e);
  } finally {
    if (browser) await browser.close();
  }
})();
