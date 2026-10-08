# Changelog

## 1.0.1 — citation drift fix

- Removed `cit-constraint-mailto-terms` / `cit-constraint-mailto-privacy` and every claim resting on them. The two
  `mailto:` hrefs they cited (`TermsContent.jsx:168`, `PrivacyContent.jsx:273`) no longer exist in `src/`
  (`grep -rn mailto src public` returns zero), so `verify_all.py` check [i] failed. Corrected in
  `extraction/measured-values.json`, `compatibility/graph.json` (`NO_EXTERNAL_LINKS` rule prose; the rule itself and
  the validator are unchanged and still reject every scheme), `registry.manifest.json`, `README.md`.
  Item 10 below is the historical record of the original finding.

## 1.0.0 — initial build (from scratch; no design-repo existed before)

Built bottom-up: tokens -> primitives -> components -> sections -> templates -> compatibility graph ->
schema -> example instance -> semantic validator -> adversarial tests -> manifest / allowlist / docs.

### What was produced

- **270 tokens** across four tiers (foundation 173, semantic 61, component 26, layout 10), plus **two theme
  resolutions** that each resolve all 61 semantic roles.
- **11 primitives, 11 components, 14 sections** — one section contract per distinct section type actually
  observed in `src/` (the 14 real `<section>` classes, with `page` excluded as a wrapper and the four
  `section.tech` routes modelled as one section with three variants, and the body-level `#awwwards` badge
  added as the sixth chrome section).
- **5 templates covering 6 routes 1:1**, with **20 graph rules** (19 `error`, 1 `warn`), **10 motion patterns**,
  **14 asset roles** (12 pinned), and **336 ledger citations**.
- **16 automated checks** in `extraction/verify_all.py`, **70 adversarial mutations**, and **32 drift injections**
  in `extraction/prove_drift.py`.

### Tooling written to make the build auditable rather than asserted

- `extraction/classify_routes.py` — a real first-party classifier that derives each route's node list from the
  source project's own JSX. The 5 page shapes were **derived by running it**, not by inspecting a grouping
  (MASTER-GUIDE 3.22). `--check` re-asserts that every route's real node list still matches its template.
- `extraction/build_pagespec_schema.py` — generates `schema/pagespec.schema.json` from the contracts, so the
  schema can never silently drift from them. Check `[c]` runs it in `--check` mode.
- `extraction/prove_drift.py` — injects one real drift per scratch copy and requires a `FAIL` line from the
  intended check, so no check in `verify_all.py` is merely asserted to work.
- The compatibility graph is written by a build script that **verifies every rule against
  `templates.json`'s real node sequences before writing the file and refuses to write on any mismatch**
  (MASTER-GUIDE 3.18). The sequences it checked against are stored in `graph.json` under `verifiedAgainst`,
  and check `[h]` fails if they ever go stale.

### Corrections to `CLONE_SPEC.md`

Each was verified directly against the current source before being recorded.

1. **`CLONE_SPEC.md:71` — "Accent used by the flash-word reveals: `rgb(249, 74, 0)`" is wrong.**
   `rgb(249,74,0)` appears **zero** times anywhere in `src/`. The flash-word colours are set at **runtime** by
   the motion scripts and there are **four** of them: `#F94A00`, `#FD7B03`, `#FFFFFF` and `var(--fonts-100)`,
   in `public/motion/m23.js`, `m24.js` and `m25.js`. `m24` ends on the white literal; `m23` and `m25` end on
   `var(--fonts-100)`. **`m22.js` carries no colour at all** — it is the `splitToWords()` helper that creates the
   `.flash-word` spans the other three animate, so attributing the colours to `m22` is also incorrect.
2. **`CLONE_SPEC.md:107` — "732 dots" is wrong; it is 728.** Verified three independent ways:
   `grep -c 'className="dot"' src/components/Footer.jsx` = 728; `data-row` spans 0–13 and `data-col` 0–51, so
   14 × 52 = 728; the highest `data-index` is 727. `m07.js`'s own `COLS * ROWS` arithmetic (`ROWS = 14`,
   `COLS = 52`) agrees. `m07.js` also rebuilds the field responsively at **its own JS thresholds** — 52 / 24 / 22
   columns at ≥992 / ≥768 / below — giving 728 / 336 / 308 dots, which the spec does not record at all.
3. **`CLONE_SPEC.md:13` — "React 18 + Vite 5 + Tailwind v3" misdescribes the project.** Tailwind is installed
   but **deliberately unused**: `src/index.css:6-11` removed the `@tailwind` directives with a comment explaining
   that Preflight broke the ported cascade. `tailwind.config.js` and `postcss.config.js` remain on disk, inert.
   The spec's "Tailwind tokens mirror the original's custom properties for any new work" describes a config
   nothing consumes.
4. **`CLONE_SPEC.md:142-144` — "41 images … 49/49 references resolve" undercounts.** The real figure is **51**
   local references, all resolving: 41 `.avif` + 2 `.webp` images, 3 videos, 2 fonts, 2 SVGs and 1 favicon.
   **75 files sit on disk**, 24 of them referenced by nothing.
5. **`CLONE_SPEC.md:107` — "`m22`–`m24` | `[data-flash]`, `[data-flash-stb]`"** attributes selectors to `m22`,
   which queries nothing. `m23` handles `[data-flash]`, `m24` handles `[data-flash-stb]`, `m22` is the splitter.

### Corrections to the build groundwork this repository was briefed with

6. **`/start` and `/auth` have NO preloader.** Both pass only `current` to `Layout`
   (`src/pages/Start.jsx:15`, `src/pages/Auth.jsx:17`), so both inherit `Layout`'s own
   `preloader = false` default. The groundwork listed them as "yes". The reason the brief was uncertain is
   itself worth recording: **`Layout.jsx`'s docstring table (lines 14-18) documents only 4 of the 6 real
   routes** — it omits `/start` and `/auth` entirely — so their chrome composition had to be read from the real
   call sites. Encoded as the `PRELOADER_ABSENT_ON_INNER_ROUTES` graph rule and proven in both directions.
7. **`#progress` does not live in the footer, so it is NOT absent from the 404.**
   `grep -rn 'id="progress"' src` returns exactly one hit, `src/components/Header.jsx:23`, and `Layout` renders
   `Header` unconditionally on every route. Only `#dotsField` (`src/components/Footer.jsx:85`) is genuinely
   missing from the 404.
8. **There are FOUR step-slide gradients, not three.** `.list__main__content.is-fourth` is
   `linear-gradient(#9a0101, #fd7b03)` at `src/styles/fourmula-base.css:4037-4039`, and the markup carries it at
   `src/components/ListSection.jsx:114`. A **fifth** gradient was also unrecorded: the shared 10rem
   `.list__main__bottom-gradient` scrim, `linear-gradient(#fc730300, #fc7303)`.
9. **`public/assets/` holds 23 `.svg` files, not 2.** Two sit at the assets root and are the only two anything
   references (both from CSS `url()`); the other **21 live under `public/assets/svg/`** and are referenced by
   nothing — every glyph, logo and wordmark is inlined as `<svg>` in the JSX instead. They still carry the same
   brand and third-party marks, so they inherit the same `generationPolicy` and are **not** free-to-use icon
   files. Three more unreferenced files exist: two spare favicon PNGs and `banner.avif`, for which `index.html`
   declares no `og:image` meta tag.
10. **"Zero external links" is true for `http:`/`https:` but not for every scheme.** Two `mailto:` hrefs survive
    inside the legal pages' placeholder filler prose, both with nonsense link text:
    `mailto:support@fourmula.ai` (`src/pages/TermsContent.jsx:168`, link text "Typography.") and
    `mailto:infot@fourmeta.com` (`src/pages/PrivacyContent.jsx:273`, link text "Body.") — the second at an
    **unrelated domain** with a malformed local part. Both are filler artifacts, not real contact links. Neither
    reaches any PageSpec field, so `NO_EXTERNAL_LINKS` rejects **every** scheme without rejecting real structure.
    Separately, the "only remaining `http://` strings are SVG `xmlns` namespaces" claim needs one addition:
    `src/loadSite.js:5` also holds a commented-out cdnjs URL documenting the original's 404ing
    `ScrambleTextPlugin`.
11. **Breakpoint use counts: `767px` is 5 and `min-width:768px` is 2, not 4 and 1.** The inline `<style>` block
    inside `src/components/Footer.jsx` adds one of each for the dots field, and the groundwork counted only the
    two stylesheet files. `991px` = 5, `479px` = 4 and `min-width:992px` = 1 are confirmed unchanged.
12. **`#146ef5` is not hover-only.** It is correctly identified as a vendored Finsweet colour rather than a brand
    colour, but it is also the **checked-state fill** of `.fs-cc_checkbox-button`
    (`fourmula-base.css:4406-4409`, `4419-4422`). Three further vendored Finsweet colours were unrecorded:
    `#468df7`, `#f8f8f8` and `#0000001a`. All four are namespaced `vendor.cookie-*` so a generator cannot mistake
    them for brand values.
13. **Reduced-motion handling is PARTIAL, not absent.** `public/motion/m27.js:2` reads
    `prefers-reduced-motion` to gate background-video autoplay (and also honours
    `navigator.connection.saveData`). No stylesheet contains a `prefers-reduced-motion` rule and nothing else in
    the project reads it. So the background-video slot's `reducedMotionFallback` genuinely **mirrors** real
    behaviour while every other section's is a **design rule** this repository prescribes. Each contract states
    which, and the validator rejects a dishonest `mirrored` claim.
14. **The spacing histogram yields 47 distinct rem values, not 50**, under the measurement this repository
    actually states (margin / padding / gap / grid-\*-gap / column-gap / row-gap / top / bottom / left / right /
    inset, site-authored rules only). 35 positive, 12 negative. A narrower property set gives a different count,
    which is why the method is written down rather than just the number. The 0.25rem-based structure holds either
    way. Likewise the Webflow-vs-site-authored rule split is **380 / 554** of 934 under the partition this
    repository states (framework = lines 1-2077, plus every post-2077 `.w-*` / `w--*` / `wf-*` / `webflow-icons`
    selector, plus the bare-element resets); the groundwork's 302 / 632 used a narrower framework definition. The
    conclusion is unchanged and is the point: `#3898ec`, `#ddd`, `#ccc`, `#222`, `#333`, `#fafafa`, `#c8c8c8`,
    `#999`, `#5d6c7b` and the 38/32/24/18/14/12px heading sizes occur **only** in the framework partition and are
    not tokens.
15. **Three source inconsistencies found and preserved rather than reconciled**, each documented in the relevant
    contract: the menu's hidden social list says `Linkedin` where the footer's says `Facebook`; the menu CTA ships
    the typo `Ge tstarted` (`Menu.jsx:41`) where every other instance says `Get started`; and `/privacy-policy`
    duplicates each anchor slug onto both a `<div id>` and its `<h2>` while `/terms-of-service` uses only the
    `<div id>` pattern (16 `<div id>`, zero `<h2 id>`).
16. **A fourth preserved-bug class, beyond the two the groundwork named.** `public/motion/m11.js:20` initialises
    from `document.body.classList.contains("light")`, but `m10.js` only ever toggles the class `dark` and never
    `light`, so that expression is always false. Its `theme:changed` listener uses the real boolean instead, so
    which member of a theme image pair is visible differs between first paint and a toggle round trip. The motion
    scripts are byte-identical copies and are read-only, so this is recorded, not fixed.

### Measurements independently re-derived and CONFIRMED

- The 12 themed custom properties and the inverted `.body` / `.body.dark` palettes, at
  `fourmula-base.css:2094-2127`, `2248-2265` and `2273-2286`; `<body class="body dark">` at `index.html:16`.
- All 16 type steps across all three tiers (`:root`, `≤991px`, `≤767px`) — every value in the groundwork's table
  matched exactly.
- The fluid root font-size, all four media branches, and `--user-zoom`.
- The radius histogram: the groundwork's list is exactly correct, plus two values it omitted (`1rem`, `1.25rem`).
- The legal pages' DOM counts: `/privacy-policy` `h1:1 h2:12 h3:2 p:39 li:31 a:15 table:2 tr:25 td:105` and
  `/terms-of-service` `h1:1 h2:16 h3:1 p:63 li:30 a:21` — **both matched to the digit.**
- The 14 real `<section>` classes, the 26 motion scripts (`m03`, then `m06`–`m30`), the ~47 MB of video, and
  zero `(href|src)="https?://` in any `.jsx`.
- `git rev-parse --git-dir` **fails**: the source project is not a git repository, so no build artifact can
  currently be tracked and the "zip committed to git" trap cannot apply here. `design-repo.zip` is nonetheless
  listed **by name** in the project's `.gitignore` so it stays untracked if the project is ever put under git.

### Defects found in this repository's own work, by its own checks, and fixed

Recorded because they are the reason the checks exist.

- The schema generator stripped `title` and `description` even when they were **property names** rather than
  schema keywords, silently dropping two real content fields. Fixed by never filtering keys inside a
  `properties` map, and the controls caught it immediately.
- `alt` text was being counted toward `contentMaxWordsTotal`, blowing two section budgets, and the four
  decorative preloader images legitimately ship `alt=""` which a `minLength: 1` rejected. Fixed with
  `countsTowardTotal: false` and `allowEmpty: true`, on the principle that accessibility text is not visible page
  copy.
- **Nine of the fourteen `contentMaxWordsTotal` caps were VACUOUS** — set above the maximum their own per-field
  budgets could ever reach, so they could never reject anything. Seven were retightened to sit between the
  measured total and that maximum; two (`chrome.preloader`, `chrome.awards-badge`) were removed with a note,
  because a total is meaningless for a section with one short field or none. A new check `[p]` now fails the run
  if any declared cap becomes unreachable, and it was run **unscoped across every section**, which is how all
  nine were found rather than just the one the adversarial test surfaced.
- `NO_EXTERNAL_LINKS` only matched an **anchored** scheme, so `"See https://fourmula.ai for details."` smuggled
  into a body-copy field was accepted. Hardened with an embedded-URL rule. The first version of that rule then
  over-fired on the company's own name, `fourmula.ai`, and on the section id `showcase.ai-capabilities`; the bare
  host-shaped alternative was therefore dropped (a bare host with no scheme is not a working link) and structural
  node keys are skipped.
- Three prose sentences sat under `assetRole` keys in primitive and component contracts (`"one of
  hero-carousel-photo, …"`). Check `[j]` reported them as unlisted roles, which was correct: they were replaced
  with real, machine-checkable `allowedAssetRoles` arrays.
- Four citations carried HTML-entity-escaped or mislocated quotes (`&amp;` where the source has `&`, a
  `tech__rich-anchor` line off by three). All four were corrected against the real files, and the ledger
  generator was changed to **look every line number up in the real source** so they are accurate by construction.
- An absence claim (`cit-motion-no-reduced-css`) carried a `quote` naming the string that is **absent**, which the
  quote check rightly rejected. Absence claims now use an `absenceOf` field, and check `[i]` asserts the named
  string is **not** present — turning a comment into a real check.
- Colour provenance was gated on `src/` plus `package.json` existing, so it ran against an empty haystack in a
  standalone copy sitting beside an unrelated `src/`. Now gated on the real stylesheet.
- Two adversarial mutations were wrong rather than the validator: one set a route the declared template really
  serves, and one stayed under the total cap it meant to exceed. Both were rewritten; the second now fills every
  field to its own per-field maximum, which is exactly the case a per-field-only validator misses.

### Deliberate decisions worth challenging later

- **`/start` and `/auth` are separate templates.** The real classifier reports identical node lists for them and
  for the two legal routes; they are split on **structural slots**, because `/auth` carries a real `<form>` node
  `/start` does not, and because merging them would launder a `composed-not-measured` evidence level into a
  `measured-scaffolding` one.
- **`proseTable` is excluded from the page-shape key**, which is what keeps `/privacy-policy` and
  `/terms-of-service` on one template despite privacy having two tables and terms none.
- **No `MOTION_BUDGET` rule.** The home page genuinely runs many concurrent animations, so there is no evidence
  of a cap to encode. Recorded in `notEvidenced` rather than invented.
- **No per-instance token override field exists, and none was invented** so as to have something to validate.
  Token safety is tested at the catalog/policy layer by drift injection instead.
- The source has **no focus states at all** (`*:focus { outline: none }` with no replacement, and an explicit
  `box-shadow: none` on the Finsweet checkbox focus state) and **no text alternative on the 11 trusted logos**.
  Both are accessibility gaps in the source. They are recorded in the primitives and the section contract, with
  an `accessibleLabel` field exposed so generated output can do better, rather than silently inherited.
