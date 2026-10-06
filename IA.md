# fourmula-clone — pixel-verified clone of fourmula.ai (React 18 + Vite, react-router-dom)

Source: fourmula-clone — pixel-verified clone of fourmula.ai (React 18 + Vite, react-router-dom) · Homepage/404 transcribed from a saved copy of the original; legal pages from live fetch. See CLONE_SPEC.md.
Status: **measured-from-codebase** · production approved: **false**
6 routes · 5 templates · 16 unique sections

> Generated from `ia.json` by `build.mjs`. Edit the JSON, not this file.

## Shape of the site

The largest 3 templates (Legal document, Homepage, App entry) account for 4 of 6 routes (67%). The remaining 2 routes span 2 templates.

| template | routes | share |
|---|---:|---:|
| Legal document | 2 | 33% |
| Homepage | 1 | 17% |
| App entry | 1 | 17% |
| Auth entry | 1 | 17% |
| Not found | 1 | 17% |

## Page chrome

**5 routes carry chrome = `full`** — Homepage, Legal document, App entry, Auth entry.

**1 routes carry chrome = `reduced`** — Not found.

## Sections by reuse

How widely a section is shared determines whether it belongs in a shared
component library or stays local to its page.

| section | category | templates | routes | implementation | scope |
|---|---|---:|---:|---|---|
| `shell.cookie-consent` | SHELL | 5 | 6 | `src/components/Cookies.jsx` | Present on all 6 routes. |
| `shell.header` | SHELL | 5 | 6 | `src/components/Header.jsx` | Present on all 6 routes; marks the brand link as current only on the homepage. |
| `shell.awards-badge` | SHELL | 5 | 6 | `src/components/AwwwardsBadge.jsx` | Present on all 6 routes. |
| `shell.menu-overlay` | SHELL | 4 | 5 | `src/components/Menu.jsx` | Present on 5 routes; the not-found template drops it entirely. |
| `shell.footer` | SHELL | 4 | 5 | `src/components/Footer.jsx` | Present on 5 routes; the not-found template drops it entirely, which is also why that route has no dot field. |
| `shell.preloader` | SHELL | 2 | 2 | `src/components/Preloader.jsx` | Present on 2 routes — the homepage and the not-found page. Every other template omits it. |
| `content.legal-document` | CONTENT | 1 | 2 | `src/pages/PrivacyContent.jsx, src/pages/TermsContent.jsx` | Carried by the legal template across 2 routes, as two separately authored page-local components rather than one shared body component. |
| `hero.catalog` | HERO | 1 | 1 | `src/components/Hero.jsx` | Homepage only — 1 route. |
| `hero.not-found` | HERO | 1 | 1 | `src/pages/NotFoundContent.jsx` | Not-found route only — 1 route. |
| `value.capability-statement` | VALUE | 1 | 1 | `src/components/What.jsx` | Homepage only — 1 route. |
| `value.photoshoot-showcase` | VALUE | 1 | 1 | `src/components/AiSection.jsx` | Homepage only — 1 route. |
| `value.how-it-works` | VALUE | 1 | 1 | `src/components/How.jsx` | Homepage only — 1 route. |
| `process.four-steps` | PROCESS | 1 | 1 | `src/components/ListSection.jsx` | Homepage only — 1 route. |
| `support.faq` | SUPPORT | 1 | 1 | `src/components/Faq.jsx` | Homepage only — 1 route. |
| `content.start-panel` | CONTENT | 1 | 1 | `src/pages/Start.jsx` | Start route only — 1 route. |
| `content.auth-panel` | CONTENT | 1 | 1 | `src/pages/Auth.jsx` | Auth route only — 1 route. |

**6 shared sections** appear in more than one template and belong in a component library.

**10 single-use sections** appear in exactly one template. Building these
as "reusable" components up front would be speculative — keep them page-local
until a second caller actually appears.

## Templates

### Homepage — `template.home`

1 route · `/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.preloader` | shared ×2 |
| 2 | SHELL | `shell.cookie-consent` | shared ×5 |
| 3 | SHELL | `shell.header` | shared ×5 |
| 4 | SHELL | `shell.menu-overlay` | shared ×4 |
| 5 | HERO | `hero.catalog` | page-local |
| 6 | VALUE | `value.capability-statement` | page-local |
| 7 | VALUE | `value.photoshoot-showcase` | page-local |
| 8 | VALUE | `value.how-it-works` | page-local |
| 9 | PROCESS | `process.four-steps` | page-local |
| 10 | SUPPORT | `support.faq` | page-local |
| 11 | SHELL | `shell.footer` | shared ×4 |
| 12 | SHELL | `shell.awards-badge` | shared ×5 |

### Legal document — `template.legal`

2 routes · `/privacy-policy`, `/terms-of-service` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.cookie-consent` | shared ×5 |
| 2 | SHELL | `shell.header` | shared ×5 |
| 3 | SHELL | `shell.menu-overlay` | shared ×4 |
| 4 | CONTENT | `content.legal-document` | page-local |
| 5 | SHELL | `shell.footer` | shared ×4 |
| 6 | SHELL | `shell.awards-badge` | shared ×5 |

### App entry — `template.app-entry`

1 route · `/start` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.cookie-consent` | shared ×5 |
| 2 | SHELL | `shell.header` | shared ×5 |
| 3 | SHELL | `shell.menu-overlay` | shared ×4 |
| 4 | CONTENT | `content.start-panel` | page-local |
| 5 | SHELL | `shell.footer` | shared ×4 |
| 6 | SHELL | `shell.awards-badge` | shared ×5 |

### Auth entry — `template.auth`

1 route · `/auth` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.cookie-consent` | shared ×5 |
| 2 | SHELL | `shell.header` | shared ×5 |
| 3 | SHELL | `shell.menu-overlay` | shared ×4 |
| 4 | CONTENT | `content.auth-panel` | page-local |
| 5 | SHELL | `shell.footer` | shared ×4 |
| 6 | SHELL | `shell.awards-badge` | shared ×5 |

### Not found — `template.not-found`

1 route · `*` · chrome: **reduced**

| # | category | section | |
|---:|---|---|---|
| 1 | SHELL | `shell.preloader` | shared ×2 |
| 2 | SHELL | `shell.cookie-consent` | shared ×5 |
| 3 | SHELL | `shell.header` | shared ×5 |
| 4 | HERO | `hero.not-found` | page-local |
| 5 | SHELL | `shell.awards-badge` | shared ×5 |

## Section reference

### SHELL

_Chrome composed by src/layout/Layout.jsx and toggled per route: preloader, consent banner, header, menu overlay, footer, fixed badge._

**`shell.preloader`** — Full-viewport entry overlay: a stepped spinner, a counting percentage readout and a stack of preloading images, gated by an `is-loading` class on documentElement and torn down by the site's own GSAP script.

· Present on 2 routes — the homepage and the not-found page. Every other template omits it. · appears on 2 routes · implemented by `src/components/Preloader.jsx`

**`shell.cookie-consent`** — Finsweet-driven consent banner plus a settings modal with per-category toggles. Carries its own accent color, distinct from the brand palette.

· Present on all 6 routes. · appears on 6 routes · implemented by `src/components/Cookies.jsx`

**`shell.header`** — Fixed top bar: brand mark, a burger that drives the menu overlay, a scroll-progress readout, a theme toggle, and sign-in plus get-started actions.

· Present on all 6 routes; marks the brand link as current only on the homepage. · appears on 6 routes · implemented by `src/components/Header.jsx`

**`shell.menu-overlay`** — Collapsed pill that expands into a full navigation panel on burger click, with staggered link reveals and a hand-rolled text scramble on the trigger label. Closed state has zero height, so its links are not hit-testable until opened.

· Present on 5 routes; the not-found template drops it entirely. · appears on 5 routes · implemented by `src/components/Menu.jsx`

**`shell.footer`** — Closing chrome: brand mark, grouped navigation, legal links, social link and registration detail, plus the interactive dot field that the homepage motion scripts animate.

· Present on 5 routes; the not-found template drops it entirely, which is also why that route has no dot field. · appears on 5 routes · implemented by `src/components/Footer.jsx`

**`shell.awards-badge`** — Fixed vertical badge pinned to the right edge, mounted at body level outside the page wrapper so it is unaffected by page transforms. Its outbound link is deliberately inert.

· Present on all 6 routes. · appears on 6 routes · implemented by `src/components/AwwwardsBadge.jsx`

### HERO

_The page-opening block that sets a route's premise._

**`hero.catalog`** — Homepage opener: the catalog headline with a per-word opacity reveal, a continuously rotating image carousel with counter-rotated frames, a vertical marquee of output types, and a drag-and-drop upload affordance.

· Homepage only — 1 route. · appears on 1 routes · implemented by `src/components/Hero.jsx`

**`hero.not-found`** — Not-found opener: a two-line broken-formula headline, a get-started action, and a looping theme-paired image that swaps with the active theme.

· Not-found route only — 1 route. · appears on 1 routes · implemented by `src/pages/NotFoundContent.jsx`

### VALUE

_Product explanation — what the tool makes and how it behaves._

**`value.capability-statement`** — Short two-part statement block: a small eyebrow label beside a large headline whose words flash in on scroll. Carries no imagery or actions.

· Homepage only — 1 route. · appears on 1 routes · implemented by `src/components/What.jsx`

**`value.photoshoot-showcase`** — The heaviest media block: a studio-quality pitch over a grid of product stills and autoplaying background videos with poster fallbacks, honouring reduced-motion and Save-Data, plus its own call to action.

· Homepage only — 1 route. · appears on 1 routes · implemented by `src/components/AiSection.jsx`

**`value.how-it-works`** — How-it-works block built from CSS marquees — a horizontally scrolling bottom row and vertically scrolling columns — with a rotating set of claim titles and a single get-started action.

· Homepage only — 1 route. · appears on 1 routes · implemented by `src/components/How.jsx`

### PROCESS

_Step-through of the product flow from input to finished assets._

**`process.four-steps`** — Scroll-driven sequence taking the reader from product input to finished assets, as stacked slides over gradient backdrops with a pinned, perspective-based transition.

· Homepage only — 1 route. · appears on 1 routes · implemented by `src/components/ListSection.jsx`

### SUPPORT

_Objection handling and reference answers._

**`support.faq`** — Accordion of product questions, one open at a time, each toggling an `active` class and rotating its indicator.

· Homepage only — 1 route. · appears on 1 routes · implemented by `src/components/Faq.jsx`

### CONTENT

_The substantive body of an inner route._

**`content.legal-document`** — Legal document body in the inner-page `.tech` shell: an oversized title above a rich-text block of numbered sections, a table-of-contents anchor list, and nested lists. The privacy instance additionally carries a multi-row cookie data table that the terms instance has no equivalent of.

· Carried by the legal template across 2 routes, as two separately authored page-local components rather than one shared body component. · appears on 2 routes · implemented by `src/pages/PrivacyContent.jsx, src/pages/TermsContent.jsx`

**`content.start-panel`** — Onboarding entry panel in the `.tech` shell: title, a short explanatory paragraph, and a pair of actions leading to sign-in and back to the site. Composed from this project's own design system — the real target renders client-side only, so nothing was measured for it.

· Start route only — 1 route. · appears on 1 routes · implemented by `src/pages/Start.jsx`

**`content.auth-panel`** — Sign-in stand-in in the `.tech` shell: title, explanatory paragraph, a single-field form and a return action. The form is deliberately inert — no action, no handler beyond preventDefault, no state and no network — and must not be wired up. Composed, not measured.

· Auth route only — 1 route. · appears on 1 routes · implemented by `src/pages/Auth.jsx`
