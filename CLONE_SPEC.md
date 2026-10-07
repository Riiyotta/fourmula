# CLONE_SPEC — fourmula.ai

All values below were measured from the original's own stylesheets, head `<style>`
blocks, and inline scripts, or computed and verified numerically. Nothing here is
estimated by eye.

> The recon subagent assigned to produce this file terminated on an API timeout
> before writing anything. This spec was written from first-hand measurement
> during the build instead.

## 1. Stack

React 18 + Vite 5, styled by vendored Webflow CSS + inline head styles (no Tailwind). GSAP
3.12.5 + ScrollTrigger + SplitText + SplitType load as classic scripts from `public/vendor/`.

Fidelity approach: the original is a Webflow site whose design system lives in one
102KB stylesheet plus 11 inline head `<style>` blocks, and whose motion lives in 26
inline scripts. Rather than re-derive those by eye, all three are ported verbatim
and the markup is transcribed from the saved document. The original's CSS custom
properties are the source of truth for tokens; any new work should reference them.

## 2. Root font-size — FLUID (read this first)

Almost every length on the page is a `rem`, and the root font-size scales with
viewport width. Any uniform ratio seen across many measured values is this rule,
not a layout bug.

```css
:root { --user-zoom: 1; }
html { font-size: calc(1.484375rem * var(--user-zoom)); }
@media (max-width:2560px){ html{ font-size: calc((-0.006009615384615419rem + 0.9314903846153846vw) * var(--user-zoom)) } }
@media (max-width:1728px){ html{ font-size: calc((-0.009345794392523143rem + 0.9345794392523362vw) * var(--user-zoom)) } }
@media (max-width: 991px){ html{ font-size: calc(( 0.021640258215962493rem + 1.8779342723004695vw) * var(--user-zoom)) } }
@media (max-width: 767px){ html{ font-size: calc((-0.0025905678851174934rem + 4.14490861618799vw) * var(--user-zoom)) } }
```

Worked example: at 1920px wide → `0.93149038462 × 19.20 − 0.00600961538 × 16 =`
**17.7885px**, i.e. 1.11178× the default 16px. A clone pinned at 16px reports every
rem-based value low by exactly that factor.

`--user-zoom` is driven by `m06.js` (localStorage key `site-user-zoom`, step 0.1).

## 3. Breakpoints

Webflow standard, as max-width queries: **991px**, **767px**, **479px**.
Root font-size adds **2560px** and **1728px** stops. One `min-width: 992px` query
flips the hero slider marquee axis; `min-width: 768px` affects only lightbox CSS.

## 4. Color tokens

Defined as custom properties. **The naming is inverted** — `.body` is the dark
palette and `.body.dark` is the light one. The site ships `<body class="body dark">`,
so **the default rendered state is the LIGHT theme** (white background). Verified on
both the original and the clone as `rgb(255,255,255)` on first paint.

| Token | `.body` (dark) | `.body.dark` (light — default) |
|---|---|---|
| `--mainbg` | `#020108` | `white` |
| `--mainbg-gradient` | `#02010800` | `#fff0` |
| `--secondbg` | `#111` | `#f7f7f7` |
| `--menu` | `#272727` | `#020108` |
| `--menu-colors` | `#fff3` | `#fff3` |
| `--lines` | `#2a2a30` | `#d7d7d6` |
| `--dots-pattern` | `#1a1a1a` | `#d9d9d9` |
| `--fonts-100` | `white` | `#020108` |
| `--fonts-64` | `#ffffffa3` | `#020108a3` |
| `--fonts-50` | `#ffffff80` | `#02010880` |
| `--fonts-30` | `#ffffff4d` | `#0201084d` |
| `--fonts-20` | `#fff3` | `#02010833` |

Flash-word reveal colours are set at runtime by `m23.js`/`m24.js`/`m25.js`, not in CSS: `#F94A00` → `#FD7B03` → (`#FFFFFF` | `var(--fonts-100)`). The string `rgb(249,74,0)` does not appear anywhere in `src/`. (Corrected from an earlier draft of this section.)

## 5. Typography

Family: `"Sf Pro Display", Arial, sans-serif`, weights 400 and 500, served as two
`.otf` files from `/assets/fonts/`. These were absent from the saved folder and were
downloaded; without them the page silently falls back to Arial.

Type scale in rem (scales with the fluid root above). Three tiers — base, ≤991px, ≤767px:

| Token | base | ≤991px | ≤767px |
|---|---|---|---|
| `h1` | 5.5 | 4.5 | 2.5 |
| `h2` | 7.5 | 5.5 | 2.25 |
| `h2-5` | 4 | 4 | 2.25 |
| `h3` | 3.25 | 3.25 | 1.5 |
| `h4` | 2.25 | 2.25 | 2 |
| `title-1` / `title-2` / `title-3` | 1 / .875 / 1.5 | same | same |
| `body-1` / `body-2` / `body-3` | 1.125 / 1 / 1.25 | same | 1 / .875 / 1 |
| `tag` / `tag-small` | 1.125 / 1.125 | same | 1 / 1.125 |
| `btn` | 1.0625 | same | same |
| `small-text-1` / `small-text-2` | .75 / .625 | same | same |

## 6. Section order (DOM order)

`preloader` → `cookies` → `section.page` wrapping: `header`, `menu`, `hero`,
`what` (`#what-is-fourmula`), `ai`, `how`, `list`, `faq`, `footer`.

## 7. Motion inventory

CSS-driven (from head `<style>` blocks — all 24s linear infinite):

| Keyframe | Target | Notes |
|---|---|---|
| `hero-row` | `.hero__slider__row` | vertical ≥992px; switches to horizontal ≤991px via `--tx/--ty` vars |
| `marquee` | `.how__bottom-row` | translateX 0 → −100% |
| `columnanima` | `.how__column` | translateY 0 → −100% |
| `spinStep` | `.preloader__loader` | `steps(8)`, 1s |

GSAP-driven, one file per original inline script:

| Script | Target | Key values |
|---|---|---|
| `m03` | `[data-current-year]` | injects current year |
| `m06` | `:root` | user zoom, step 0.1 |
| `m07`–`m09` | `#dotsField`, `.dot` | 728 dots; `steps(2)`; cursor proximity 0.2s `power2.out` |
| `m10`/`m11` | theme toggle | localStorage `isDarkMode`; swaps `.theme-light`/`.theme-dark` |
| `m12` | `#progress` | scroll progress width |
| `m13` | `.faq__item` | accordion, toggles `active` |
| `m14` | `.how__right-title` | title switching |
| `m15` | `.header`/`.footer`/`.menu` | 0.2s `power2.out` |
| `m16` | `#dropZone` | drag-and-drop upload |
| `m17` | `.hero__carousel__in` | `rotate:360`, 32s, `none`, `repeat:-1` |
| `m18` | `.hero__carousel__img` | counter-rotation, 32s, `none`, `repeat:-1` |
| `m19` | `.menu__wrap` | open 0.4s `power2.out`; items stagger 0.05 / 0.3s; closed 15rem × 2.7rem, y 1.25rem (15.5rem / y 0.5rem ≤767px); open 18rem × 39rem (16.2rem ≤991px) |
| `m20` | `.header__menu-line` | ±45°, 0.25s `power2.out` |
| `m21` | `.preloader` | counter 1s, images stagger 0.05 |
| `m22`–`m24` | `[data-flash]`, `[data-flash-stb]` | word split + 0.05/0.1s reveals |
| `m25` | `[data-hero-text]`, `.hero-flash-word` | stagger 0.2; honours `data-final-opacity` (some words end at **0.5**, not 1) |
| `m26` | `[hover-stagger]` | stagger 0.02, 0.2s `power1.inOut` |
| `m27` | `.w-background-video` | respects `prefers-reduced-motion` and Save-Data |
| `m28` | `.is-img-anima-1…5` | 0.8–1.5s, `repeat:-1` |
| `m29` | `.list__main__slide` | 3D slides, `power1.in` |
| `m30` | `.cookies` | 0.8s `power2.out` |

Motion is run by `src/loadSite.js`, which loads vendor then `public/motion/m*.js` in
original document order, then re-dispatches `DOMContentLoaded` and `load` (both had
already fired before React mounted). The scripts are byte-identical to the original's
— **do not edit `public/motion/`.**

## 8. Assets

Images (incl. 4 Webflow `-p-500` srcset variants), 3 mp4 background videos, 2
font files. All local under `public/assets/`; 51/51 references resolve (75 files on disk, 24 unreferenced). Downloaded
because they were missing from the saved folder: both `.otf` fonts, the 3 videos
(were still pointing at S3), the 4 `-p-500` variants, `paperclip.avif`, the radio and
checkbox SVGs, favicon.

## 9. Known quirks in the ORIGINAL, deliberately preserved

1. **Malformed CSS.** The list section ships `transform-style: preserve-3d` with no
   semicolon before `transform-origin: 50% 10%;`. Browsers discard the whole
   malformed declaration, so neither property applies on the live site. Kept
   commented out in `fourmula-head.css`; "fixing" it would create a difference.
2. **Dead plugin.** The original loads `ScrambleTextPlugin.min.js` from a cdnjs path
   that returns **404**, and never uses it — `m19.js` implements its own
   `scrambleText()`. Not reproduced, no behavioural difference.
3. **Inverted theme class names**, see §4.

## 10. Licensing before any public deploy

SF Pro Display is Apple-licensed and GSAP SplitText is a paid Club GreenSock plugin.
Both are fine for local work; neither may be served publicly as-is. The copy,
branding and imagery are fourmula.ai's.

## 11. Routes and shared layout

The original is a real multi-page Webflow site, so there is **no sitemap.xml**; the
route set was established by crawling the homepage's links and probing paths. Only
three real pages exist — unknown paths are served the 404 page.

| Route | Source | Unique section |
|---|---|---|
| `/` | homepage | `hero`, `what`, `ai`, `how`, `list`, `faq` |
| `/privacy-policy` | live fetch | `section.tech` |
| `/terms-of-service` | live fetch | `section.tech` |
| `*` (catch-all) | `/404` | `section.hero__404__wrap` |

### Global chrome is single-sourced

`src/layout/Layout.jsx` owns every reused component. Each of `Header`, `Menu`,
`Footer`, `Cookies`, `Preloader`, `AwwwardsBadge` is defined once and imported
once. Pages contain only their unique sections. Per-page composition, verified
against each live page rather than assumed:

| Route | preloader | menu | footer | badge |
|---|---|---|---|---|
| `/` | yes | yes | yes | yes |
| `/privacy-policy` | no | yes | yes | yes |
| `/terms-of-service` | no | yes | yes | yes |
| 404 | yes | **no** | **no** | yes |

The progress bar (`#progress`) lives in `Header`, so it IS present on the 404. The dot field (`#dotsField`) lives in `Footer`, so
they are correctly absent from the 404 — matching the original.

### Navigation model

Navigation is plain `<a>` full page loads, as on the original. `react-router-dom`
only maps URL → page component; no `<Link>` components are used. This keeps the
markup byte-identical to the original and lets the preloader re-run per navigation
exactly as it does live. Absolute `https://fourmula.ai/...` hrefs were rewritten to
relative paths so the clone navigates internally instead of leaving for the real site.

### Active nav state

The shared chrome was diffed across all four live pages. Differences were purely
mechanical: `aria-current="page"` / `w--current` markers, and inert Webflow
`data-wf-page-id` hashes. `Header`, `Menu` and `Footer` therefore take a `current`
prop that reproduces those markers per route.

### Deliberate deviations from the original (2)

1. **Legal body prose is placeheld.** The `.tech` DOM scaffolding is exact — verified
   by element count against the live pages (privacy `h1:1 h2:12 h3:2 p:39 li:31 a:15
   table:2 tr:25 td:105`; terms `h1:1 h2:16 h3:1 p:63 li:30 a:21`) — with headings,
   lists, table and TOC anchors intact and filler matched to the original word count
   per element, so layout, measure and scroll length hold. The ~6,300 words of
   fourmula.ai's actual policy text are not reproduced; substitute your own wording.
2. **Legal-page nav links are functional.** The original ships `href="#"` dead links
   for the section-anchor nav on its legal pages (an authoring oversight); the clone
   points them at `/#pdp`, `/#products`, `/#video`, `/#list` so they work. Revert to
   `#` if byte-exactness matters more than usability.

## 12. External domains removed — clone is self-contained

The original linked out to 4 external domains across 20 links. All are now local or
inert; the project contains **zero external `href`/`src` values** (the only remaining
`http://` strings are SVG `xmlns` namespace identifiers, which are not links).

### app.fourmula.ai (16 links) → local routes

The product app could **not** be cloned from markup. It is a Next.js app that emits
`<template data-dgst="BAILOUT_TO_CLIENT_SIDE_RENDERING">` and ships an empty shell:
`/` and `/auth` return 11 characters of body text, `/start` returns 18, with **zero
forms and zero inputs**. The UI exists only after JS executes, and `/auth` is behind
sign-in. There was nothing to transcribe.

| Original | Count | Now | Element classes |
|---|---|---|---|
| `app.fourmula.ai/start` | 11 | `/start` | `btn-primary`, `btn-primary-stb`, `ai__btn`, `is-menu`, `is-how`, `is-header-btn`, `btn-outline` |
| `app.fourmula.ai/auth` | 2 | `/auth` | `header_signin` |
| `app.fourmula.ai` (bare) | 3 | `/start` | inline links inside the legal rich text |

`src/pages/Start.jsx` and `src/pages/Auth.jsx` are therefore **not replicas** — no
source existed. They are composed from this project's own design system (the `.tech`
inner-page layout shared with the legal pages, the `u-*` type scale, `btn-primary` /
`btn-outline`, `w-input`) so the CTAs resolve somewhere that belongs to the site.

**`Auth.jsx` is deliberately inert:** no `action`, no submit handler beyond
`preventDefault`, no state, no network call, and nothing read from or stored for the
fields. It is layout only. Do not wire it up.

### Genuine third-party sites (4 links) → inert

Not cloned — these belong to other parties, not fourmula.ai. Rewritten to `href="#"`
with `target="_blank"` dropped, leaving markup and layout unchanged.

| Original | Count | What it is |
|---|---|---|
| `instagram.com/fourmula.ai` | 2 | social profile |
| `awwwards.com/sites/fourmula-ai` | 1 | awards directory (the fixed badge) |
| `ico.org.uk` | 1 | UK Information Commissioner's Office, cited in the privacy policy |

Also fixed: one leftover absolute `https://fourmula.ai/` self-link → `/`, and
`target="_blank"` removed from the two internal `/#` cookie-consent buttons.

### Route set

| Route | Source |
|---|---|
| `/` | cloned from original |
| `/privacy-policy` | cloned (prose placeheld, §11) |
| `/terms-of-service` | cloned (prose placeheld, §11) |
| `/start` | local, design-system composition (no source) |
| `/auth` | local, design-system composition, inert form (no source) |
| `*` | cloned from original `/404` |
