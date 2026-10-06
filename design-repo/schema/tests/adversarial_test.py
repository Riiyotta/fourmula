#!/usr/bin/env python3
"""Adversarial tests for the PageSpec schema, the semantic validator and the drift checks.

Runs from the design-repo alone - the root is derived from this file's location and no sibling folders
are needed:

    python3 schema/tests/adversarial_test.py     exit 0 only if EVERY control passed and EVERY mutation was rejected

Layers
  1. CONTROLS - the shipped example, plus synthesize_control(t) for EVERY template in templates.json
     (auto-iterated, so a template added later is covered with no new code), plus hand-built controls for
     each content.tech variant, must all produce ZERO errors. A validator that rejects everything is as
     broken as one that rejects nothing.
  2. MUTATIONS - each mutated PageSpec must be REJECTED, and rejected BY THE RULE THE MUTATION TARGETS.
     A mutation that is rejected by the wrong rule is reported as WRONGRULE, not as a pass.
  3. BOTH DIRECTIONS - for each corrected rule this repository carries, the suite proves the old wrong
     structure is rejected AND the real, correct structure is accepted (see the CORRECTIONS block).
  4. CLI - unparseable and missing input give one clean error line and exit code 2, never a traceback.
  5. CATALOG / POLICY DRIFT INJECTION - a PageSpec has NO per-instance token or style override field (the
     schema rejects a `tokens` key; mutation "per-instance tokens field at page level" proves it), so
     there is nothing at the PageSpec layer to mutate for token misuse. Token safety is therefore tested
     one layer down, by injecting drift into a scratch copy and asserting verify_all.py fails.
  6. PINNED ASSET POLICY - a compliance-critical role's generationPolicy is changed to a
     DIFFERENT-BUT-STILL-VALID enum value in a scratch copy, and verify_all.py must fail. Membership in
     the 5-value enum alone would not catch this (MASTER-GUIDE 3.23).
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "schema"))
import semantic_validate as sv  # noqa: E402

FAILED = []


def load_example():
    with open(os.path.join(ROOT, "schema", "example.pagespec.json"), encoding="utf-8") as f:
        return json.load(f)


EX = load_example()
REPO = sv.load_repo(ROOT)
TEMPLATES = sorted(REPO["templates"])


def first(spec, t, n=0):
    return [i for i, x in enumerate(spec["nodes"]) if x["type"] == t][n]


def node_of(template, section):
    spec = sv.synthesize_control(template, ROOT)
    return copy.deepcopy(spec["nodes"][first(spec, section)])


def words(n):
    return " ".join("word%d" % i for i in range(n))


# ---------------------------------------------------------------------------------- mutations
MUTS = []


def mut(name, expect):
    def deco(fn):
        MUTS.append((name, expect, fn))
        return fn
    return deco


# --- schema layer: bad enum, invented alias, missing required, invented field ------------------
@mut("wrong template enum value", ["SCHEMA"])
def _(s):
    s["template"] = "landing-bogus"


@mut("wrong route enum value", ["SCHEMA"])
def _(s):
    s["route"] = "/pricing"


@mut("wrong pageSpecVersion", ["SCHEMA"])
def _(s):
    s["pageSpecVersion"] = "2.0.0"


@mut("route not served by the declared template (home template, legal route)", ["TEMPLATE_SERVES_ROUTE"])
def _(s):
    s["route"] = "/privacy-policy"   # template stays `home`, which serves only "/"


@mut("invented node type (hero.banner)", ["SCHEMA"])
def _(s):
    s["nodes"][4]["type"] = "hero.banner"


@mut("invented section alias (hero-home instead of hero.home)", ["SCHEMA"])
def _(s):
    s["nodes"][4]["type"] = "hero-home"


@mut("missing required node field (content)", ["SCHEMA"])
def _(s):
    del s["nodes"][5]["content"]


@mut("missing required content field (hero heading)", ["SCHEMA"])
def _(s):
    del s["nodes"][4]["content"]["heading"]


@mut("extra content field not in the contract", ["SCHEMA"])
def _(s):
    s["nodes"][4]["content"]["subtitle"] = "not in the contract"


@mut("extra top-level field", ["SCHEMA"])
def _(s):
    s["seoTitle"] = "not in the schema"


# --- motion layer -----------------------------------------------------------------------------
@mut("missing reducedMotionFallback", ["SCHEMA", "SEM-MOTION"])
def _(s):
    del s["nodes"][5]["motion"]["reducedMotionFallback"]


@mut("empty reducedMotionFallback", ["SCHEMA", "SEM-MOTION"])
def _(s):
    s["nodes"][5]["motion"]["reducedMotionFallback"] = "   "


@mut("missing motion object entirely", ["SCHEMA", "SEM-MOTION"])
def _(s):
    del s["nodes"][7]["motion"]


@mut("invented motion field (duration) - proves motion is closed", ["SCHEMA"])
def _(s):
    s["nodes"][7]["motion"]["duration"] = 900


@mut("wrong motion pattern for the section", ["SCHEMA", "SEM-MOTION"])
def _(s):
    s["nodes"][9]["motion"]["pattern"] = "marquee-scroll"


@mut("dishonest reducedMotionFallbackKind 'mirrored' on a design-rule section", ["SEM-MOTION"])
def _(s):
    s["nodes"][9]["motion"]["reducedMotionFallbackKind"] = "mirrored"


@mut("reducedMotionFallback word overflow", ["SEM-WORDS"])
def _(s):
    s["nodes"][5]["motion"]["reducedMotionFallback"] = words(80)


# --- per-instance token override: the field does not exist, and must not ----------------------
@mut("per-instance `tokens` field at page level", ["SCHEMA"])
def _(s):
    s["tokens"] = {"text.primary": "color.mainbg-light"}


@mut("per-instance `tokens` field on a node", ["SCHEMA"])
def _(s):
    s["nodes"][4]["tokens"] = {"color.mainbg-light": "#ff0000"}


# --- structural: duplicate one-per-page, removed mandatory, reordered fixed position ----------
@mut("duplicate one-per-page section (a second hero)", ["ONE_HERO_PER_PAGE", "SECTION_CONTRACT_CONSTRAINTS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].insert(5, copy.deepcopy(s["nodes"][4]))


@mut("duplicate chrome.header", ["HEADER_ONCE_AFTER_COOKIES", "SECTION_CONTRACT_CONSTRAINTS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].insert(3, copy.deepcopy(s["nodes"][2]))


@mut("duplicate chrome.awards-badge", ["BADGE_LAST", "SECTION_CONTRACT_CONSTRAINTS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].append(copy.deepcopy(s["nodes"][-1]))


for _sec in ("chrome.cookie-consent", "chrome.header", "chrome.menu", "hero.home", "content.what-intro",
             "showcase.ai-capabilities", "marquee.how-trusted", "steps.pinned-list", "faq.accordion",
             "chrome.footer", "chrome.awards-badge", "chrome.preloader"):
    def _mk(sec):
        @mut("removed mandatory section %s" % sec, ["TEMPLATE_NODE_MATCH"])
        def _(s):
            del s["nodes"][first(s, sec)]
    _mk(_sec)


@mut("reordered fixed position: preloader and cookie banner swapped", ["PRELOADER_FIRST_WHEN_PRESENT", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][0], s["nodes"][1] = s["nodes"][1], s["nodes"][0]


@mut("reordered fixed position: header and menu swapped", ["MENU_FOLLOWS_HEADER", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][2], s["nodes"][3] = s["nodes"][3], s["nodes"][2]


@mut("reordered fixed position: footer and badge swapped", ["BADGE_LAST", "FOOTER_PRESENT_AND_PRECEDES_BADGE", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][-1], s["nodes"][-2] = s["nodes"][-2], s["nodes"][-1]


@mut("reordered fixed position: hero moved to the end of the body", ["TEMPLATE_NODE_MATCH"])
def _(s):
    n = s["nodes"].pop(first(s, "hero.home"))
    s["nodes"].insert(first(s, "faq.accordion") + 1, n)


@mut("adjacent identical sections", ["NO_ADJACENT_SAME_SECTION", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][6] = copy.deepcopy(s["nodes"][5])


# --- template / node-sequence mismatch -------------------------------------------------------
@mut("template/node mismatch: legal nodes under the home template", ["TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"] = sv.synthesize_control("legal", ROOT)["nodes"]


@mut("template/node mismatch: home nodes relabelled as not-found", ["TEMPLATE_NODE_MATCH"])
def _(s):
    s["template"], s["route"] = "not-found", "/404"


@mut("template/node mismatch: a 404 body on the home template", ["TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"][4] = node_of("not-found", "hero.not-found")


# --- route restriction -----------------------------------------------------------------------
@mut("home-only section on a legal page (faq.accordion)", ["HOME_ONLY_SECTIONS", "ROUTE_RESTRICTED_SECTIONS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["template"], s["route"] = "legal", "/privacy-policy"
    s["nodes"] = sv.synthesize_control("legal", ROOT)["nodes"]
    s["nodes"].insert(4, node_of("home", "faq.accordion"))


@mut("not-found-only section on the home page", ["NOT_FOUND_ONLY_SECTIONS", "ROUTE_RESTRICTED_SECTIONS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].insert(5, node_of("not-found", "hero.not-found"))


@mut("content.tech on the home route", ["ROUTE_RESTRICTED_SECTIONS", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["nodes"].insert(5, node_of("legal", "content.tech"))


# --- the preloader correction, in the rejecting direction -------------------------------------
@mut("preloader on /start (it passes no preloader prop, so it has none)", ["PRELOADER_ABSENT_ON_INNER_ROUTES", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["template"], s["route"] = "app-onboarding", "/start"
    s["nodes"] = sv.synthesize_control("app-onboarding", ROOT)["nodes"]
    s["nodes"].insert(0, node_of("home", "chrome.preloader"))


@mut("preloader on /privacy-policy", ["PRELOADER_ABSENT_ON_INNER_ROUTES", "TEMPLATE_NODE_MATCH"])
def _(s):
    s["template"], s["route"] = "legal", "/privacy-policy"
    s["nodes"] = sv.synthesize_control("legal", ROOT)["nodes"]
    s["nodes"].insert(0, node_of("home", "chrome.preloader"))


# --- runtime: maxWords overflow on real fields -----------------------------------------------
@mut("maxWords overflow on the hero heading", ["SEM-WORDS"])
def _(s):
    s["nodes"][4]["content"]["heading"] = words(12)


@mut("maxWords overflow on a FAQ answer", ["SEM-WORDS"])
def _(s):
    s["nodes"][9]["content"]["items"][0]["answer"] = words(60)


@mut("maxWords overflow on a showcase body", ["SEM-WORDS"])
def _(s):
    s["nodes"][6]["content"]["blocks"][0]["body"] = words(90)


@mut("contentMaxWordsTotal overflow: every FAQ field at its own per-field maximum", ["SEM-WORDS"])
def _(s):
    # Each field stays within its OWN maxWords, so only the section-wide total can catch this.
    # It is the case a per-field-only validator misses, and it is why no total cap may be vacuous.
    n = s["nodes"][9]["content"]
    n["eyebrow"] = words(2)
    n["headingLines"] = [words(4), words(4)]
    for it in n["items"]:
        it["question"] = words(9)
        it["answer"] = words(18)


# --- assets --------------------------------------------------------------------------------
@mut("invented assetRole", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][4]["content"]["carouselImages"][0]["assetRole"] = "stock-photo"


@mut("assetRole valid globally but not allowed in this slot", ["SCHEMA", "SEM-ASSET"])
def _(s):
    s["nodes"][4]["content"]["carouselImages"][0]["assetRole"] = "brand-typeface-file"


@mut("role/path mismatch: a non-video role under /assets/video/", ["SEM-ASSET"])
def _(s):
    s["nodes"][4]["content"]["carouselImages"][0]["assetRef"] = "/assets/video/wrong.mp4"


# --- the zero-external-links constraint ------------------------------------------------------
@mut("EXTERNAL LINK: remote https URL in an asset path", ["SCHEMA", "SEM-ASSET", "NO_EXTERNAL_LINKS"])
def _(s):
    s["nodes"][4]["content"]["carouselImages"][0]["assetRef"] = "https://cdn.example.com/x.avif"


@mut("EXTERNAL LINK: remote https URL in a link href", ["SCHEMA", "SEM-ASSET", "NO_EXTERNAL_LINKS"])
def _(s):
    s["nodes"][2]["content"]["cta"]["href"] = "https://app.fourmula.ai/start"


@mut("EXTERNAL LINK: protocol-relative // URL", ["SCHEMA", "SEM-ASSET", "NO_EXTERNAL_LINKS"])
def _(s):
    s["nodes"][4]["content"]["carouselImages"][0]["assetRef"] = "//cdn.example.com/x.avif"


@mut("EXTERNAL LINK: mailto: scheme in a link href", ["SCHEMA", "SEM-ASSET", "NO_EXTERNAL_LINKS"])
def _(s):
    s["nodes"][2]["content"]["cta"]["href"] = "mailto:support@fourmula.ai"


@mut("EXTERNAL LINK: path traversal in an asset path", ["SCHEMA", "SEM-ASSET", "NO_EXTERNAL_LINKS"])
def _(s):
    s["nodes"][4]["content"]["carouselImages"][0]["assetRef"] = "/assets/../../etc/passwd"


@mut("EXTERNAL LINK: smuggled into a plain text field", ["NO_EXTERNAL_LINKS"])
def _(s):
    s["nodes"][9]["content"]["items"][0]["answer"] = "See https://fourmula.ai for details."


# --- variants ------------------------------------------------------------------------------
@mut("variant on a section that declares none", ["SCHEMA", "VARIANT_MATCHES_ROUTE"])
def _(s):
    s["nodes"][4]["variant"] = "legal-prose"


# ---------------------------------------------------------------------------- extra bases
MUT_EXTRA = []


def extra(name, expect, base, fn):
    MUT_EXTRA.append((name, expect, base, fn))


def _legal(route="/privacy-policy"):
    s = sv.synthesize_control("legal", ROOT)
    s["route"] = route
    return s


def _auth():
    return sv.synthesize_control("app-auth", ROOT)


def _start():
    return sv.synthesize_control("app-onboarding", ROOT)


def _nf():
    return sv.synthesize_control("not-found", ROOT)


# --- content.tech variant pinning ------------------------------------------------------------
def _wrong_variant(s):
    s["nodes"][first(s, "content.tech")]["variant"] = "auth-form"


extra("content.tech variant auth-form on /privacy-policy", ["TECH_VARIANT_MATCHES_ROUTE", "INERT_FORM_ONLY_ON_AUTH", "TEMPLATE_NODE_MATCH"], _legal, _wrong_variant)


def _onboarding_variant_on_legal(s):
    s["nodes"][first(s, "content.tech")]["variant"] = "onboarding-cta"


extra("content.tech variant onboarding-cta on /privacy-policy", ["TECH_VARIANT_MATCHES_ROUTE", "TEMPLATE_NODE_MATCH", "VARIANT_MATCHES_ROUTE"], _legal, _onboarding_variant_on_legal)


# --- THE PINNED INERT FORM: a different-but-structurally-valid wiring ------------------------
def _form_not_inert(s):
    s["nodes"][first(s, "content.tech")]["content"]["form"]["inert"] = False


extra("PINNED: the /auth form marked inert=false", ["SCHEMA", "INERT_FORM_ONLY_ON_AUTH"], _auth, _form_not_inert)


def _form_wrong_role(s):
    s["nodes"][first(s, "content.tech")]["content"]["form"]["assetRole"] = "ui-icon-glyph"


extra("PINNED: the /auth form's assetRole changed to a DIFFERENT-BUT-VALID enum member", ["SCHEMA", "SEM-ASSET", "INERT_FORM_ONLY_ON_AUTH"], _auth, _form_wrong_role)


def _form_on_start(s):
    auth = _auth()
    i = first(s, "content.tech")
    s["nodes"][i]["content"]["form"] = copy.deepcopy(auth["nodes"][first(auth, "content.tech")]["content"]["form"])


extra("a form slot added to /start", ["SCHEMA", "INERT_FORM_ONLY_ON_AUTH"], _start, _form_on_start)


# --- the 404 exceptions, in the rejecting direction ------------------------------------------
def _menu_on_404(s):
    s["nodes"].insert(3, node_of("home", "chrome.menu"))


extra("chrome.menu added to the 404 (it has none)", ["TEMPLATE_NODE_MATCH", "ROUTE_RESTRICTED_SECTIONS"], _nf, _menu_on_404)


def _footer_on_404(s):
    s["nodes"].insert(len(s["nodes"]) - 1, node_of("home", "chrome.footer"))


extra("chrome.footer added to the 404 (it has none)", ["TEMPLATE_NODE_MATCH", "ROUTE_RESTRICTED_SECTIONS"], _nf, _footer_on_404)


def _hero_removed_from_404(s):
    del s["nodes"][first(s, "hero.not-found")]


extra("the 404's only hero removed", ["ONE_HERO_PER_PAGE", "TEMPLATE_NODE_MATCH"], _nf, _hero_removed_from_404)


def _hero_on_legal(s):
    s["nodes"].insert(3, node_of("home", "hero.home"))


extra("a hero added to a hero-less legal page", ["HOME_ONLY_SECTIONS", "TEMPLATE_NODE_MATCH"], _legal, _hero_on_legal)


# ------------------------------------------------------------------- BOTH-DIRECTION controls
# Every corrected fact this repository carries is proven in BOTH directions: the mutations above
# reject the wrong structure, and these controls prove the real, correct structure is ACCEPTED.
CORRECTIONS = [
    ("CORRECTION /start has NO preloader: the real 5-node-after-cookies shape is accepted",
     lambda: _start()),
    ("CORRECTION /auth has NO preloader and DOES have an inert form: the real shape is accepted",
     lambda: _auth()),
    ("CORRECTION the 404 has no menu and no footer: the real 5-node shape is accepted",
     lambda: _nf()),
    ("CORRECTION /terms-of-service shares the legal template: the real shape is accepted",
     lambda: _legal("/terms-of-service")),
    ("CORRECTION the four-slide step list (is-fourth included) is accepted",
     lambda: copy.deepcopy(EX)),
]


def _four_slides_ok():
    """The example really carries FOUR step slides, including the is-fourth variant the
    groundwork said did not exist. Assert it rather than assuming it."""
    slides = EX["nodes"][first(EX, "steps.pinned-list")]["content"]["slides"]
    return len(slides) == 4 and [s["variant"] for s in slides] == ["is-first", "is-second", "is-third", "is-fourth"]


def _progress_in_header_ok():
    """The example's #progress readout really lives on the header node, so it survives on the 404."""
    hdr = EX["nodes"][first(EX, "chrome.header")]["content"]
    nf = sv.synthesize_control("not-found", ROOT)
    return "progressInitial" in hdr and "chrome.header" in [n["type"] for n in nf["nodes"]]


ASSERTIONS = [
    ("the example carries FOUR step slides, is-first..is-fourth", _four_slides_ok),
    ("#progress lives on chrome.header, so it is present on the 404 template", _progress_in_header_ok),
]


# ---------------------------------------------------------------------------------- runner
def rejected_by(spec):
    errors, _ = sv.validate(spec, ROOT)
    return errors


def report(ok, tag, name, detail=""):
    print("%-9s %s%s" % (tag, name, (" <- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def run_controls():
    print("== controls (each must produce 0 errors) ==")
    errs = rejected_by(copy.deepcopy(EX))
    report(not errs, "PASS" if not errs else "FAIL", "the shipped example", "; ".join(e[:110] for e in errs[:2]))
    for t in TEMPLATES:
        errs = rejected_by(sv.synthesize_control(t, ROOT))
        report(not errs, "PASS" if not errs else "FAIL", "synthesize_control(%s)" % t,
               "; ".join(e[:110] for e in errs[:2]))
    for branch, route in (("legal-prose", "/terms-of-service"),):
        s = sv.synthesize_control("legal", ROOT, branch=branch)
        s["route"] = route
        errs = rejected_by(s)
        report(not errs, "PASS" if not errs else "FAIL", "content.tech branch %s on %s" % (branch, route),
               "; ".join(e[:110] for e in errs[:2]))
    for name, fn in CORRECTIONS:
        errs = rejected_by(fn())
        report(not errs, "PASS" if not errs else "FAIL", name, "; ".join(e[:110] for e in errs[:2]))
    print("== direct assertions about the shipped data ==")
    for name, fn in ASSERTIONS:
        ok = bool(fn())
        report(ok, "PASS" if ok else "FAIL", name)


def run_mutations():
    print("== mutations (each must be REJECTED by the rule it targets) ==")
    cases = ([(n, e, copy.deepcopy(EX), fn) for n, e, fn in MUTS]
             + [(n, e, b(), fn) for n, e, b, fn in MUT_EXTRA])
    for name, expect, base, fn in cases:
        fn(base)
        errs = rejected_by(base)
        hit = [e for e in errs if any(x in e for x in expect)]
        if not errs:
            report(False, "ACCEPTED", name, "the validator ACCEPTED a mutated PageSpec")
        elif not hit:
            report(False, "WRONGRULE", name, "rejected, but not by %s: %s" % (expect, errs[0][:130]))
        else:
            report(True, "REJECTED", name, hit[0][:140])


def run_cli():
    print("== validator CLI robustness ==")
    tmp = tempfile.mkdtemp()
    try:
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w") as f:
            f.write("{ not json")
        for label, path in (("unparseable JSON", bad), ("missing file", os.path.join(tmp, "nope.json"))):
            r = subprocess.run([sys.executable, os.path.join(ROOT, "schema", "semantic_validate.py"), path],
                               capture_output=True, text=True)
            clean = r.returncode == 2 and "Traceback" not in r.stderr + r.stdout and r.stdout.startswith("ERROR")
            report(clean, "PASS" if clean else "FAIL", "CLI " + label,
                   "exit %d, %s" % (r.returncode, (r.stdout.strip() or r.stderr.strip())[:80]))
        r = subprocess.run([sys.executable, os.path.join(ROOT, "schema", "semantic_validate.py"), "--parity"],
                           capture_output=True, text=True)
        report(r.returncode == 0, "PASS" if r.returncode == 0 else "FAIL", "CLI --parity",
               r.stdout.strip().splitlines()[-1][:90])
        spec = copy.deepcopy(EX)
        del spec["nodes"][first(spec, "faq.accordion")]
        errs = rejected_by(spec)
        readable = 1 <= len(errs) <= 3 and len(errs) == len(set(errs))
        report(readable, "PASS" if readable else "FAIL",
               "a missing node gives a short de-duplicated message set",
               "%d message(s): %s" % (len(errs), errs[0][:80]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def scratch_copy():
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "design-repo")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    return tmp, dst


def verify_fails(dst, expect_check):
    r = subprocess.run([sys.executable, os.path.join(dst, "extraction", "verify_all.py")],
                       capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith("FAIL") and expect_check in l]
    return (r.returncode != 0 and bool(lines),
            lines[0][:165] if lines else "verify_all did NOT fail on %s (exit %d)" % (expect_check, r.returncode))


def edit_json(path, fn):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def run_drift_layer():
    print("== catalog / policy / pinned-asset drift injection (scratch copies; a PageSpec has no token field) ==")

    def policy_category(d):
        d["rawValueRestrictions"]["shadow"] = d["rawValueRestrictions"].pop("elevation")

    def dangling_ref(d):
        d["tokens"]["text.primary"] = {"$type": "color", "themed": True,
                                       "$refDark": "color.does-not-exist", "$refLight": "color.mainbg-light",
                                       "rationale": "x", "usage": 1, "evidence": []}

    def drop_catalog_entry(d):
        d["categories"]["color"]["tokens"].pop()

    def unpin_role(d):
        r = next(x for x in d["roles"] if x["complianceCritical"])
        assert r["generationPolicy"] != "may-generate-new"
        r["generationPolicy"] = "may-generate-new"   # a VALID enum member, wrong for a pinned role

    def unpin_auth_form(d):
        r = next(x for x in d["roles"] if x["id"] == "auth-inert-form")
        assert r["generationPolicy"] == "must-not-wire-up"
        r["generationPolicy"] = "must-reuse-exact"   # DIFFERENT-BUT-STILL-VALID: the exact case an enum check misses
        r["pinnedPolicy"] = "must-reuse-exact"

    def unpin_typeface(d):
        r = next(x for x in d["roles"] if x["id"] == "brand-typeface-file")
        r["generationPolicy"] = "must-reuse-exact"
        r["pinnedPolicy"] = "must-reuse-exact"

    def unpin_trusted_logo(d):
        r = next(x for x in d["roles"] if x["id"] == "trusted-partner-logo")
        r["generationPolicy"] = "must-reuse-exact"
        r["pinnedPolicy"] = "must-reuse-exact"

    def break_theme(d):
        d["resolutions"].pop(sorted(d["resolutions"])[0])

    def flatten_evidence(d):
        for t in d["templates"]:
            t["evidenceLevel"] = "measured"

    cases = [
        ("a policy category renamed to a label that is no catalog key (elevation -> shadow)",
         "tokens/llm/token-policy.json", policy_category, "[k]"),
        ("a dangling $refDark in a semantic token", "tokens/10-semantic/color.json", dangling_ref, "[k]"),
        ("a catalog entry removed (count and id drift)", "tokens/llm/token-catalog.json", drop_catalog_entry, "[f]"),
        ("a theme stops resolving one semantic role", "tokens/themes/light.json", break_theme, "[k]"),
        ("PINNED: a compliance-critical role switched to may-generate-new (a VALID enum value)",
         "assets/asset-roles.json", unpin_role, "[j]"),
        ("PINNED: auth-inert-form switched to must-reuse-exact (DIFFERENT-BUT-VALID, with pinnedPolicy moved too)",
         "assets/asset-roles.json", unpin_auth_form, "[j]"),
        ("PINNED: brand-typeface-file switched off must-not-redistribute (Apple-licensed font)",
         "assets/asset-roles.json", unpin_typeface, "[j]"),
        ("PINNED: trusted-partner-logo switched off must-not-fabricate (real third-party marks)",
         "assets/asset-roles.json", unpin_trusted_logo, "[j]"),
        ("EVIDENCE: every template flattened to 'measured' (laundering the composed pages)",
         "templates/templates.json", flatten_evidence, "[o]"),
    ]
    for name, relp, fn, tag in cases:
        tmp, dst = scratch_copy()
        try:
            edit_json(os.path.join(dst, *relp.split("/")), fn)
            ok, line = verify_fails(dst, tag)
            report(ok, "CAUGHT" if ok else "MISSED", name, line)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    tmp, dst = scratch_copy()  # sanity: an UNMODIFIED scratch copy must pass, so the failures above are the injections
    try:
        r = subprocess.run([sys.executable, os.path.join(dst, "extraction", "verify_all.py")],
                           capture_output=True, text=True)
        report(r.returncode == 0, "PASS" if r.returncode == 0 else "FAIL",
               "an unmodified scratch copy passes verify_all",
               (r.stdout.strip().splitlines() or ["no output"])[-1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    run_controls()
    run_mutations()
    run_cli()
    run_drift_layer()
    print("== summary ==")
    n_mut = len(MUTS) + len(MUT_EXTRA)
    print("controls: %d templates + the example + %d correction controls + %d direct assertions; mutations: %d; "
          "failures: %d" % (len(TEMPLATES), len(CORRECTIONS), len(ASSERTIONS), n_mut, len(FAILED)))
    for f in FAILED:
        print("  FAILED:", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
