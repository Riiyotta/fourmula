#!/usr/bin/env node
// measure_sections.mjs - OPTIONAL re-measure tool for extraction/measured-values.json -> sectionHeights.
//
// Measures every section of every route of the BUILT clone in a headless browser at a 1440px viewport
// and prints JSON on stdout (or writes it to OUT_FILE). It never edits the repository by itself; the
// recorded numbers are pasted into extraction/measured-values.json and gated by extraction/wrapper_gate.py.
//
//   npx vite build --outDir <scratch> && npx vite preview --outDir <scratch> --port 5737
//   NODE_PATH="$(npm root -g)" BASE_URL=http://localhost:5737 node design-repo/extraction/measure_sections.mjs
//
// Playwright is resolved from the normal module path, then from NODE_PATH, then from the env var
// PLAYWRIGHT_MODULE (a path to playwright/index.mjs). No absolute browser or module path is stored here.
import { createRequire } from 'node:module'
import { writeFileSync } from 'node:fs'

async function loadPlaywright() {
  try { return await import('playwright') } catch (e) { /* fall through */ }
  try { return createRequire(import.meta.url)('playwright') } catch (e) { /* fall through */ }
  if (process.env.PLAYWRIGHT_MODULE) return await import(process.env.PLAYWRIGHT_MODULE)
  throw new Error('playwright not found: set NODE_PATH="$(npm root -g)" or PLAYWRIGHT_MODULE')
}

const BASE = process.env.BASE_URL || 'http://localhost:5737'
const VIEWPORT = { width: 1440, height: 900 }
// route -> the URL actually loaded ('/404' is App.jsx's path="*" catch-all, so any unknown path)
const ROUTES = { '/': '/', '/privacy-policy': '/privacy-policy', '/terms-of-service': '/terms-of-service',
  '/start': '/start', '/auth': '/auth', '/404': '/this-route-does-not-exist' }
// design-repo section id -> the real root element (the <section> each component renders)
const SELECTORS = {
  'chrome.preloader': 'section.preloader', 'chrome.cookie-consent': 'section.cookies',
  'chrome.header': 'section.header', 'chrome.menu': 'section.menu', 'hero.home': 'section.hero',
  'content.what-intro': 'section.what', 'showcase.ai-capabilities': 'section.ai',
  'marquee.how-trusted': 'section.how', 'steps.pinned-list': 'section.list', 'faq.accordion': 'section.faq',
  'content.tech': 'section.tech', 'hero.not-found': 'section.hero__404__wrap',
  'chrome.footer': 'section.footer', 'chrome.awards-badge': '#awwwards',
}

const pw = await loadPlaywright()
const browser = await pw.chromium.launch()
const page = await browser.newPage({ viewport: VIEWPORT })
const out = { viewport: VIEWPORT, measuredWith: 'extraction/measure_sections.mjs (headless Chromium via Playwright)', routes: {} }
for (const [route, path] of Object.entries(ROUTES)) {
  await page.goto(BASE + path, { waitUntil: 'load' })
  await page.waitForTimeout(4500) // the preloader and the motion scripts settle
  // scroll the whole page once so scroll-driven pin spacers exist, then return to the top
  await page.evaluate(async () => {
    for (let y = 0; y < document.documentElement.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)) }
    window.scrollTo(0, 0)
  })
  await page.waitForTimeout(800)
  const r = await page.evaluate((sel) => {
    const doc = document.documentElement.scrollHeight
    const sections = {}
    for (const [id, s] of Object.entries(sel)) {
      const el = document.querySelector(s)
      if (!el) continue
      const cs = getComputedStyle(el)
      // a GSAP-pinned section takes its page height through its .pin-spacer wrapper
      const flowEl = el.parentElement && el.parentElement.classList.contains('pin-spacer') ? el.parentElement : el
      const pos = getComputedStyle(flowEl).position
      const rect = flowEl.getBoundingClientRect()
      sections[id] = {
        heightPx: Math.round(rect.height),
        topPx: Math.round(rect.top + window.scrollY),
        position: pos,
        display: cs.display,
        inFlow: !(pos === 'fixed' || pos === 'absolute' || pos === 'sticky') && cs.display !== 'none' && rect.height > 0,
        pinSpacer: flowEl !== el,
      }
    }
    // R6: a long-form legal body is ONE <section class="tech"> in the DOM but two semantic units: the header
    // (h1, intro, anchor index) and one chapter per h2, each starting at its <div class="w-embed"> anchor.
    const tech = document.querySelector('section.tech')
    const embeds = tech ? [...tech.querySelectorAll('.tech__rich > .w-embed')] : []
    if (tech && embeds.length >= 5) {
      const t = tech.getBoundingClientRect()
      const tops = embeds.map(e => e.getBoundingClientRect().top)
      sections['content.legal-header'] = { heightPx: Math.round(tops[0] - t.top), topPx: Math.round(t.top + window.scrollY), position: 'static', display: 'block', inFlow: true, pinSpacer: false }
      sections['content.legal-chapter'] = { instances: tops.map((top, i) => ({ heightPx: Math.round((i + 1 < tops.length ? tops[i + 1] : t.bottom) - top), topPx: Math.round(top + window.scrollY) })), position: 'static', display: 'block', inFlow: true, pinSpacer: false }
      sections['content.legal-chapter'].heightPx = Math.max(...sections['content.legal-chapter'].instances.map(x => x.heightPx))
      delete sections['content.tech']
    }
    return { pageHeightPx: doc, sections }
  }, SELECTORS)
  out.routes[route] = r
}
await browser.close()
const json = JSON.stringify(out, null, 1)
if (process.env.OUT_FILE) writeFileSync(process.env.OUT_FILE, json + '\n')
else console.log(json)
