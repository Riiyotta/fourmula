# Fourmula.ai clone design repository

An AI-ready design repository extracted from a Vite + React clone of **fourmula.ai** (6 routes, 5 page shapes):
design tokens, primitive / component / section contracts, page templates, a compatibility graph, a PageSpec JSON
Schema with a semantic validator, and the scripts that keep all of it honest. Status: **design-review-pending**
(`productionApproved: false`). Repository 1.1.0, PageSpec 2.0.0 (adds the required `mode`), allowlist 1.1.0.
Bound to the N0 common policy `n0-saas-design-constraints-common` 0.1.0 as a **SaaS** site (see "Policy binding"). It is a specification for generating pages in this site's style, not a component
library.

## Counts (recomputed from disk by `extraction/verify_all.py`; that script fails if this block or the manifest drifts)

<!-- counts:begin -->
- Tokens: 270 total (foundation 173, semantic 61, component 26, layout 10); catalog entries 270
- Primitives 11, components 11, sections 16
- Templates 5, routes 6 (1:1), graph rules 37, motion patterns 10, asset roles 23, ledger citations 344
- Example PageSpecs 6, retrieval-ineligible sections 4
<!-- counts:end -->

Routes to templates, each route served by exactly one template: `/` -> home; `/privacy-policy` and
`/terms-of-service` -> legal; `/start` -> app-onboarding; `/auth` -> app-auth; `/404` -> not-found. The
machine-readable map is `routeTemplateMap` in `registry.manifest.json`.

---

## Read these four facts before using anything here

### 1. The root font-size is FLUID. Every rem scales with the viewport.

```css
html { font-size: calc(1.484375rem * var(--user-zoom)); }
@media (max-width:2560px){ calc((-0.006009615384615419rem + 0.9314903846153846vw) * var(--user-zoom)) }
@media (max-width:1728px){ calc((-0.009345794392523143rem + 0.9345794392523362vw) * var(--user-zoom)) }
@media (max-width: 991px){ calc(( 0.021640258215962493rem + 1.8779342723004695vw) * var(--user-zoom)) }
@media (max-width: 767px){ calc((-0.0025905678851174934rem + 4.14490861618799vw) * var(--user-zoom)) }
```

Measured real values: **13.3084px at a 1440px viewport, 16.1237px at 390px**. At 1920px it is 17.7885px, i.e.
1.11178x the 16px default. **Multiplying any rem token in this repository by 16 is wrong at every viewport.**
Full detail in `tokens/00-foundation/typography.json` -> `ROOT_FONT_SIZE_IS_FLUID`.

### 2. The theme class names are INVERTED, and the default is LIGHT.

| CSS selector | palette it carries |
| --- | --- |
| `.body` | the **DARK** values |
| `.body.dark` | the **LIGHT** values |

The app ships `<body class="body dark">`, so the class literally named `dark` selects the **light** palette and the
**default rendered theme is LIGHT** (white canvas). `public/motion/m10.js` reinforces it: it toggles the class
`dark`, defaults to true, persists `localStorage['isDarkMode']` and sets `data-theme-state="dark"` — all while the
page renders light. The inversion repeats at two more layers: `.theme-dark` images ship *visible*, and the asset
shown in the default light rendering is the one whose filename ends `-dark.avif`. **A generator that reads
`.body.dark` as "the dark theme" inverts the entire palette.** Do not normalise it.

### 3. This is NOT a Tailwind project.

`tailwindcss ^3.4.13` is installed but **deliberately unused**: `src/index.css` removed the `@tailwind` directives
because Preflight, loaded after the site's own stylesheets, overrode the ported cascade. `tailwind.config.js` and
`postcss.config.js` remain on disk, inert. Styling is a vendored Webflow stylesheet plus 11 ported inline head
`<style>` blocks. (An earlier `CLONE_SPEC.md` described it as a Tailwind project; that was wrong and has been corrected — see the CHANGELOG.)

### 4. Zero external links is an enforced build constraint.

`grep -rhoE '(href|src)="https?://' src --include='*.jsx'` returns **zero** matches. Formerly-external links became
local routes (`/start`, `/auth`) or inert hashes on purpose. A generated PageSpec may never introduce a remote URL,
a protocol-relative `//` URL, any URL scheme, or a `..` traversal — the schema pattern, the semantic validator and
the `NO_EXTERNAL_LINKS` graph rule all reject them, and the adversarial suite proves it in both directions. No `mailto:` or other
non-http scheme remains in `src/` either (the two filler-prose `mailto:` hrefs recorded at the initial build have since been removed).

---

## Folder map

| Path | What it holds |
| --- | --- |
| `registry.manifest.json` | status, versions (and which are machine-checked), recomputed counts, route map, scope, constraints, entry points |
| `tokens/00-foundation/`, `10-semantic/`, `20-component/`, `30-layout/`, `themes/` | the four token tiers and both theme resolutions; ids are dotted (`color.mainbg-light`, `text.primary`, `component.button.primary.fill`) |
| `tokens/llm/` | `token-catalog.json`, `token-policy.json` (its category keys are exactly the catalog's; it names every enforced TOKEN_* rule), `component-allowlist.json` (versioned, closed id list, plus `retrievalIneligible`) — all registered in the manifest (`tokenRegistration`, check [w]) |
| `tokens/00-foundation/motion-patterns.json` | the closed motion-pattern vocabulary, generated from the contracts and checked against them and the schema |
| `assets/asset-roles.json` | the closed 23-role `assetRole` enum with a closed `availability` (clone-only / generation-safe / blocked-for-generation) pinned in code, `generationSafeSubstitutes`, `generatedModeGuidance`, the closed 6-value `generationPolicy` enum, and a pinned policy for each of the 13 compliance-critical roles |
| `policy/design-policy.json` | the binding record for the N0 common SaaS policy: classification evidence, local application, `enforcedBy` files, approval state |
| `primitives/`, `components/`, `sections/` | one contract per id (`hero.home` -> `sections/hero-home.json`) |
| `templates/templates.json` | the 5 page shapes, as structured node sequences with per-template evidence levels |
| `compatibility/graph.json` | 37 rules (rhythm, position, retrieval pin, availability pin, 9 GENERATION_MODE_* and 6 TOKEN_* rules), each with a severity and named exceptions, plus the exact node sequences every rule was verified against |
| `schema/` | `pagespec.schema.json` (Draft-07, generated), `section-contract.schema.json` (closed contract shape), `example.pagespec.json` (mode=clone), `examples/generated-*.pagespec.json` (one mode=generation example per template), `generation-leakage.json` (generated leakage registry), `semantic_validate.py`, `schema/tests/adversarial_test.py` |
| `extraction/` | `measured-values.json` (the citation ledger and the measured `sectionHeights`), `verify_all.py`, `prove_drift.py`, `wrapper_gate.py`, `measure_sections.mjs`, `build_pagespec_schema.py`, `build_leakage_patterns.py`, `build_provenance.py`, `classify_routes.py` |

## How to run (Python 3 with the `jsonschema` package, from the repository root)

```
python3 extraction/verify_all.py                                   # 23 checks, PASS/FAIL/WARN each, non-zero exit on any failure
python3 schema/tests/adversarial_test.py                           # controls + mutations + CLI + drift-injection layers
python3 extraction/prove_drift.py [--scratch DIR]                  # injects drift into scratch copies; verify_all.py must fail on each
python3 extraction/wrapper_gate.py                                 # the whole-page-wrapper gate over the measured heights
python3 extraction/build_leakage_patterns.py [--check]             # rebuild the generation-mode leakage registry from the real source
python3 extraction/build_provenance.py [--check]                   # rebuild each contract's source/semantic objects from the real files
python3 extraction/verify_all.py --emit-policy-hash                # print the designPolicy contentHash
python3 schema/semantic_validate.py schema/example.pagespec.json   # validate one PageSpec (0 valid, 1 errors, 2 unreadable)
python3 schema/semantic_validate.py --parity                       # graph rule ids <-> validator RULES, both directions
python3 extraction/build_pagespec_schema.py [--check]              # regenerate / drift-check the shipped schema
python3 extraction/classify_routes.py [--check]                    # re-derive each route's node list from the real JSX
```

Every script derives its root from its own location, so they all run on a copy of this folder with **no sibling
directories**. Citations (`path:line-line` plus a stored `quote`) resolve against the source project only while it
sits beside this folder; otherwise `verify_all.py` prints a WARN and skips them — a warning, not a failure.
Citations that point into this package itself are always checked. `classify_routes.py` likewise prints a notice and
exits 0 with no source tree.

## Licensing and generation guidance — read before generating anything

- **The source is a real, live company.** Real, identifiable people appear in 8 hero photographs and 4 preloader
  images. **11 real third-party company logos** appear in a "Trusted By" marquee — the highest-risk assets here. 20
  real product images and 3 real produced videos appear in the showcase. A generator must **never** reproduce,
  redraw, recolour, approximate or AI-regenerate fourmula.ai's real logo or wordmark, its real brand marks, its real
  product imagery, any real person's likeness, any third-party mark, or its real copy. `assets/asset-roles.json`
  gives every role a `generationPolicy` and **pins** it for the 12 compliance-critical roles; check `[j]` enforces
  the pinned **value**, not merely membership in the enum.
- **SF Pro Display is Apple-licensed** (`public/assets/fonts/*.otf`) and may not be redistributed or served
  publicly. **GSAP SplitText is a paid Club GreenSock plugin** (`public/vendor/SplitText.min.js`) under the same
  restriction. Both are role `brand-typeface-file`, pinned `must-not-redistribute`.
- **The legal pages' prose is placeholder filler on purpose** — shipping another company's policy text is a
  liability. Their DOM scaffolding is measured; their words are not the original's.
- **The `/auth` form is deliberately inert** and must stay inert: no action, no handler, no state, no storage, no
  network call, no analytics event. Role `auth-inert-form` is pinned `must-not-wire-up`.
- Nothing here grants any right to fourmula.ai's copy, marks or assets. **Do not publish or make this repository
  public without the owner's licence review.**
- Packaging: at extraction time the source project was not yet a git repository (it is now maintained and published through GitHub); `design-repo.zip`
  is nonetheless listed by name in the project's `.gitignore`, and is regenerated fresh and last, with the CLI
  `zip` tool, after every check passes.

## Evidence levels — three of them, recorded per route and never flattened

| Level | Routes | What it means |
| --- | --- | --- |
| `measured` | `/`, `/404` | Structure, layout, motion and copy measured against the live original. The homepage pixel audit verified **1382/1382 elements at 1440px and 962/962 at 390px with zero deltas**. |
| `measured-scaffolding-placeholder-prose` | `/privacy-policy`, `/terms-of-service` | DOM scaffolding measured against the live original and independently re-counted from the real JSX (privacy `h1:1 h2:12 h3:2 p:39 li:31 a:15 table:2 tr:25 td:105`; terms `h1:1 h2:16 h3:1 p:63 li:30 a:21` — both match exactly). **The body prose is deliberate placeholder filler.** No word budget is derived from it. |
| `composed-not-measured` | `/start`, `/auth` | **No source existed to measure.** app.fourmula.ai emits `BAILOUT_TO_CLIENT_SIDE_RENDERING` with an empty shell (11–18 characters of body text, zero forms, zero inputs). These two pages are **original compositions** from this design system and are **not evidence about fourmula.ai**. |

Check `[o]` fails the run if the ledger and `templates.json` ever disagree about a route's level, or if a composed
route is described as measured. The `COMPOSED_EVIDENCE_DISCLOSED` graph rule emits a non-fatal **warning** on any
PageSpec built on a composed template, so a generator can never cite those pages as measured fact.

## How the 5 page shapes were decided

By running a real first-party classifier, `extraction/classify_routes.py`, against the source project's own JSX —
not by inspecting a grouping or trusting a description. Grouping on the **node list alone** collapses 6 routes into
3 shapes, because `/privacy-policy`, `/terms-of-service`, `/start` and `/auth` all produce the identical list
`[chrome.cookie-consent, chrome.header, chrome.menu, content.tech, chrome.footer, chrome.awards-badge]`. That
grouping would be wrong. (Revision 1.1: the legal pages now decompose into `content.legal-header` + 12-16
`content.legal-chapter` nodes at their real h2 boundaries, so their node list differs from /start and /auth
even before slots are compared; the slot comparison below still separates /start from /auth.) The classifier therefore also compares **structural slots**, which is what actually
decides shape:

| Route(s) | Structural slots | Template |
| --- | --- | --- |
| `/` | — (12 nodes) | `home` |
| `/privacy-policy`, `/terms-of-service` | `longFormProse`, `anchorIndex` | `legal` — the one genuinely shared shape |
| `/start` | `ctaRow` | `app-onboarding` |
| `/auth` | `ctaRow`, **`inertForm`** | `app-auth` — **not merged** with `/start`: it has a real `<form>` node |
| `/404` | `ctaRow` (5 nodes, no menu, no footer) | `not-found` |

`proseTable` is deliberately excluded from the shape key: privacy has two tables and terms none, but both fill the
same long-form legal rich-text slot, so a table is instance content rather than a different page shape. Even had the
slots matched, privacy/terms are *measured scaffolding* while `/start` and `/auth` are *composed*, so merging them
would launder one evidence level into the other.

## Known limitations and things not to "fix"

- **Two of the original's own bugs are deliberately preserved.** (1) `src/styles/fourmula-head.css:150-159` keeps
  `transform-style: preserve-3d` and `transform-origin: 50% 10%` **commented out**, because the original ships the
  first with no semicolon so browsers discard both; uncommenting them creates a visible divergence. (2) The original
  loads a `ScrambleTextPlugin` from a cdnjs path that **404s** and never uses it — `public/motion/m19.js` has its own
  hand-rolled `scrambleText()`. A third, smaller asymmetry is recorded rather than fixed: `public/motion/m11.js:20`
  initialises from a class (`light`) that `m10.js` never sets, so which member of a theme image pair is visible
  differs between first paint and a toggle round trip.
- **The 26 scripts in `public/motion/` are READ-ONLY** — byte-identical copies of the original site's inline
  scripts, injected by `src/loadSite.js`, which re-dispatches `DOMContentLoaded` and `load` after React mounts.
- **Reduced-motion handling is partial, not absent.** `public/motion/m27.js` is the only script that reads
  `prefers-reduced-motion` (it gates background-video autoplay, and also honours `navigator.connection.saveData`),
  and no stylesheet contains a `prefers-reduced-motion` rule. So the background-video slot's
  `reducedMotionFallback` **mirrors** real behaviour and every other section's is a **design rule** this repository
  prescribes. Each contract says which, and the validator rejects a dishonest `mirrored` claim.
- **No shadows.** The site-authored stylesheet has zero `box-shadow` declarations. Elevation is z-index layers plus
  two inline blur filters.
- **No focus states.** `*:focus { outline: none }` is declared with no replacement focus ring anywhere, and the
  Finsweet checkbox explicitly sets `box-shadow: none` on its focus state. This is an accessibility gap in the
  source; it is recorded, not silently inherited, and the primitives say so.
- **No text alternative on the 11 trusted logos.** They are bare inline SVG with no `.u-hidden-copy` sibling and no
  `aria-label`. The contract exposes an `accessibleLabel` field so generated output can do better.
- **Styling in a PageSpec is token references only.** A free-form `tokens` key is still rejected. Revision 1.1 adds
  the optional closed `styleTokens` node field (semantic role ids only) so the token policy is machine-enforceable:
  unknown ids, raw colours, raw lengths, unsupported fonts, other-palette ids and wrong-family ids are rejected by
  the TOKEN_* rules. Token-file drift is still also tested at the catalog/policy layer.
- **No motion budget rule.** The home page genuinely runs many concurrent animations (three 24s CSS marquees, a 32s
  carousel ring plus counter-rotation, a 728-dot wave with cursor proximity, five image cross-fades, three
  background videos, four pinned 3D slides), so there is no evidence of a cap to encode. See `notEvidenced` in
  `compatibility/graph.json`.
- **The source's own inconsistencies are preserved, not reconciled.** The menu's hidden social list says `Linkedin`
  where the footer's says `Facebook`; the menu CTA ships the typo `Ge tstarted` where every other instance says
  `Get started`; `/privacy-policy` duplicates each anchor slug onto both a `<div id>` and its `<h2>` while
  `/terms-of-service` uses only the `<div id>` pattern. All four are documented in the relevant contracts.
- `repositoryVersion` and `pageSpecVersion` are **documentation-only**. Only `allowlistVersion` is machine-checked —
  and the `counts` block is too. See `versionFieldNote` in the manifest.

## Revision 1.1 — modes, generation safety, retrieval, height gate, policy binding

- **`mode` is required** (`clone` | `generation`). Clone mode may reuse real copy and clone-only assets for fidelity
  (`schema/example.pagespec.json` is the clone control). Generation mode is for a new page for someone else; one
  generation example per template lives in `schema/examples/` (fictional brand "Kestrelwave", placeholder assets,
  `.example` host only).
- **Generation-mode rules** `GENERATION_MODE_BRAND / _ASSET / _PERSON / _CUSTOMER / _SCREENSHOT / _COPY / _CLAIM /
  _URL / _EMBED` read `schema/generation-leakage.json`, which `extraction/build_leakage_patterns.py` derives from
  `src/`, `index.html`, `CLONE_SPEC.md` and `public/assets/` with file:line evidence. Copy is stored only as hashed
  5-word shingles; text is normalised (NFKC, zero-width removal, curly quotes, dashes) before matching. **Detection is
  string-based and can be evaded by paraphrase. No human has reviewed these patterns.**
- **Asset availability** is closed and pinned in code in both validators; every clone-only / blocked role names
  generation-safe substitutes, and eight generation-safe roles were added. The Awwwards badge was misfiled as a
  generic `ui-icon-glyph` (may-generate-new); it is now `third-party-award-badge` (clone-only, must-not-fabricate).
- **Legal pages decomposed (R6).** Measured at 1440px, the single `content.tech` node held 86% (/privacy-policy) and
  88% (/terms-of-service) of the page. The legal template now composes `content.legal-header` + 12-16
  `content.legal-chapter` nodes, split at the documents' own h2 boundaries; `content.tech` keeps only the two
  composed stand-ins. Same DOM, different purpose.
- **Provenance vs taxonomy (R7)**: every section contract carries closed `source` {id, tag, file, lines} and
  `semantic` {id, category}, generated by `build_provenance.py` and re-read against the real files by check [s].
- **Retrieval eligibility (R8)**: the consent UI, preloader, menu drawer and floating badge are pinned
  `retrievalEligible: false` in both validators, the contracts and the allowlist.
- **Wrapper gate (R9)**: `extraction/wrapper_gate.py` gates heights MEASURED from the built clone (headless
  Chromium, 1440px, every route). No section trips it; the whitelist is empty. Any future agent whitelist entry must
  say "agent attestation, not a human sign-off". **No clone-vs-live visual parity was measured in this revision.**

## Policy binding

`registry.manifest.json` carries `category: "saas"` and `designPolicy` bound to `n0-saas-design-constraints-common`
0.1.0 (commonIrVersion 0.5, enforcementMode hard-and-soft). The classification is recorded with cited evidence in
`policy/design-policy.json` (self-serve sign-up, a hosted app behind sign-in, a fees/subscriptions/credits terms
chapter, a B2B trusted-by row, copy addressed to a store and a creative team). The clone has no pricing page and no
dashboard. The decision is an **agent attestation, not a human sign-off**; approval stays
`defined-pending-architecture-review`. `contentHash` is the sha256 over the policy's `enforcedBy` files and is
recomputed by check [r].

## Snapshot warning

This repository is a snapshot of the source project (React `^18.3.1`, Vite `^5.4.8`, react-router-dom `^7.18.4`,
GSAP `^3.12.5` per its `package.json` when this was finalised). If the project changes — a dependency bump, a new
route, a copy or layout edit — re-diff the counts, framework versions, citations and per-route node sequences before
trusting it. `verify_all.py` re-checks citations, and `classify_routes.py --check` re-derives the route/template
mapping, only while the source tree sits beside this folder.
