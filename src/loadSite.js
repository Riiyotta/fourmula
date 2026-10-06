import motionScripts from './motionManifest.json'

// Load order mirrors the original document exactly.
// ScrambleTextPlugin is intentionally absent: the original references
// https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrambleTextPlugin.min.js
// which returns 404, so the scramble effect does not run on the live site either.
const VENDOR = [
  '/vendor/gsap.min.js',
  '/vendor/ScrollTrigger.min.js',
  '/vendor/SplitText.min.js',
  '/vendor/split-type.min.js',
]

const TRAILING = ['/vendor/jquery.min.js', '/vendor/webflow.js']

function loadScript(src) {
  return new Promise((resolve) => {
    const s = document.createElement('script')
    s.src = src
    s.async = false
    s.onload = resolve
    s.onerror = () => {
      console.warn('[clone] failed to load', src)
      resolve()
    }
    document.body.appendChild(s)
  })
}

let booted = false

export default async function loadSite() {
  if (booted) return
  booted = true

  // Webflow's own feature-detect classes (original inline script #1)
  const root = document.documentElement
  root.className += ' w-mod-js'
  if ('ontouchstart' in window) root.className += ' w-mod-touch'

  root.classList.add('is-loading')

  for (const src of VENDOR) await loadScript(src)
  for (const src of motionScripts) await loadScript(src)

  // The site's scripts bind to DOMContentLoaded / load, which already fired
  // before React mounted. Re-dispatch so they run, unmodified.
  document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true }))
  window.dispatchEvent(new Event('load'))

  for (const src of TRAILING) await loadScript(src)
}
