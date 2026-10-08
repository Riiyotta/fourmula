import { JSDOM } from 'jsdom';
import fetch from 'node-fetch';

const routes = [
  { path: '/', preloader: true, menu: true, footer: true, badge: true },
  { path: '/privacy-policy', preloader: false, menu: true, footer: true, badge: true },
  { path: '/terms-of-service', preloader: false, menu: true, footer: true, badge: true },
  { path: '/some-missing-page', preloader: true, menu: false, footer: false, badge: true },
];

async function testRoute(route) {
  try {
    console.log(`\n=== Testing ${route.path} ===`);
    const response = await fetch(`http://localhost:5190${route.path}`);
    const html = await response.text();
    
    const dom = new JSDOM(html);
    const document = dom.window.document;
    
    console.log(`Status: ${response.status}`);
    
    // Check for chrome elements
    const hasPreloader = !!document.querySelector('.preloader');
    const hasMenu = !!document.querySelector('.menu');
    const hasFooter = !!document.querySelector('.footer');
    const hasBadge = !!document.querySelector('#awwwards');
    const hasHeader = !!document.querySelector('.header');
    
    console.log(`Chrome elements:`);
    console.log(`  Preloader (expected: ${route.preloader}): ${hasPreloader}`);
    console.log(`  Menu (expected: ${route.menu}): ${hasMenu}`);
    console.log(`  Footer (expected: ${route.footer}): ${hasFooter}`);
    console.log(`  Badge #awwwards (expected: ${route.badge}): ${hasBadge}`);
    console.log(`  Header: ${hasHeader}`);
    
    // Check body scroll height
    const body = document.body;
    console.log(`Body scroll height: ${body.scrollHeight || 'N/A'}`);
    
    // Check for content
    const mainContent = document.querySelector('.page');
    console.log(`Main content (.page) found: ${!!mainContent}`);
    
  } catch (err) {
    console.error(`Error testing ${route.path}:`, err.message);
  }
}

async function runTests() {
  for (const route of routes) {
    await testRoute(route);
  }
}

runTests();
