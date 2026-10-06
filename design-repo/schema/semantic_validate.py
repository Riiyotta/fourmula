#!/usr/bin/env python3
"""Semantic validator for Fourmula PageSpecs - everything JSON Schema structurally cannot express.

Usage:  python3 schema/semantic_validate.py <pagespec.json>   exit 0 valid, 1 errors, 2 unreadable input
        python3 schema/semantic_validate.py --parity           graph rule id <-> RULES implementation parity
Import: from semantic_validate import validate, synthesize_control, graph_parity
        errors, warnings = validate(pagespec_dict, repo_root=None)

What validate() checks (schema errors and semantic errors are both returned in `errors`):
  SCHEMA  jsonschema Draft7Validator against schema/pagespec.schema.json
  GRAPH   every rule in compatibility/graph.json, honouring its severity and its named `template`
          exceptions. Each rule id has a function of the same name in the RULES dict below;
          graph_parity() proves the two sets agree in both directions and
          extraction/verify_all.py check [h] fails the run if they ever diverge.
  SEM-MOTION   node.motion.reducedMotionFallback present and non-empty; motion.pattern matches the
               section contract's own pattern; reducedMotionFallbackKind may only be `mirrored` for
               a section whose contract declares mirrored reduced-motion handling.
  SEM-WORDS    per-instance maxWords and contentMaxWordsTotal. A word count is ALWAYS len(text.split()).
  SEM-ASSET    assetRole is in the closed global enum AND in this slot's allowed subset; asset paths
               are local only; link fields are an inert hash, an in-page anchor or a real route.

The declared `template` is ALWAYS cross-referenced against that template's real node list in
templates/templates.json. nodes[] is never validated in isolation - a PageSpec that contradicts its
own template is rejected by TEMPLATE_NODE_MATCH.

Chrome-aware position semantics: on a chrome.* section mustBeFirst / mustBeLast are ABSOLUTE node
positions. On any other section, mustBeFirstInBody / mustBeLastInBody are relative to the page body,
i.e. the nodes after the last leading chrome.* node and before the first trailing chrome.* node.
"""
import glob
import json
import os
import re
import sys

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(SCHEMA_DIR)

LOCAL_PATH_RE = re.compile(r"^/(?!/)(?!.*\.\.)[A-Za-z0-9._~@%+()/-]+$")
# Two complementary rules, because a URL can be smuggled into a field OR into prose.
# (1) ANCHORED: a value that IS a scheme, a protocol-relative URL, or holds a `..` traversal.
EXTERNAL_RE = re.compile(r"(?i)^(?:[a-z][a-z0-9+.-]*:|//)|\.\.")
# (2) EMBEDDED: a known network-or-code scheme, a www. host, or a protocol-relative host
#     ANYWHERE in the string. Anchoring alone missed "See https://fourmula.ai for details."
#     inside a body-copy field, which is a real smuggling route a generator could take.
#     Deliberately NOT matching a bare host-shaped token: the company's own name is literally
#     "fourmula.ai" and it appears as real accessible-label copy, so a bare-domain rule would
#     reject correct content. A bare host with no scheme is not a working link anyway.
EMBEDDED_URL_RE = re.compile(
    r"(?i)(?:\b(?:https?|ftps?|mailto|tel|sms|data|file|javascript|vbscript|ws|wss|blob)\s*:"
    r"|(?<![\w/])//[A-Za-z0-9-]+\.[A-Za-z]{2,}"
    r"|(?<![\w@./-])www\.[A-Za-z0-9-]+\.[A-Za-z]{2,})")
# Structural node keys are ids and enum values, not author-supplied text: a section id like
# "showcase.ai-capabilities" must never be read as a hostname.
STRUCTURAL_KEYS = ("type", "variant", "id", "pattern", "reducedMotionFallbackKind", "assetRole",
                   "fsCc", "fsCcCheckbox", "anchorId", "slug", "style", "layout", "emphasis",
                   "arrangement", "inputType", "dataThemeState", "stepNumber", "icon",
                   "anchorPattern")
MAX_FALLBACK_WORDS = 60
INERT_HREFS = {"#", "/#", "/#what-is-fourmula", "/#pdp", "/#products", "/#video", "/#list"}


def wc(text):
    """The one word-count function used everywhere: whitespace-split token count."""
    return len(text.split())


# ------------------------------------------------------------------------------- repo loading
_CACHE = {}


def load_repo(repo_root=None):
    root = os.path.abspath(repo_root or DEFAULT_REPO)
    if root in _CACHE:
        return _CACHE[root]

    def j(*p):
        with open(os.path.join(root, *p), encoding="utf-8") as f:
            return json.load(f)
    contracts = {}
    for f in sorted(glob.glob(os.path.join(root, "sections", "*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        contracts[d["id"]] = d
    tdoc = j("templates", "templates.json")
    tpls = {t["id"]: t for t in tdoc["templates"]}
    repo = {"root": root, "contracts": contracts, "templates": tpls,
            "graph": j("compatibility", "graph.json"), "roles": j("assets", "asset-roles.json"),
            "schema": j("schema", "pagespec.schema.json")}
    repo["role_set"] = set(repo["roles"]["assetRoleEnum"])
    repo["routes"] = sorted({r for t in tpls.values() for r in t["routes"]})
    repo["hero_sections"] = {i for i, d in contracts.items() if d.get("category") == "hero"}
    _CACHE[root] = repo
    return repo


def variant_keys(contract):
    v = contract.get("variants")
    return sorted(v.keys()) if isinstance(v, dict) else sorted(v or [])


class Ctx:
    def __init__(self, spec, repo):
        self.spec, self.repo = spec, repo
        self.nodes = [n for n in spec.get("nodes", []) if isinstance(n, dict)]
        self.types = [n.get("type") for n in self.nodes]
        # (section, variant) keys: structural rules use these so a section that legitimately repeats
        # with different variants can never be collapsed into one bucket.
        self.keys = [(n.get("type"), n.get("variant")) for n in self.nodes]
        self.template_id = spec.get("template")
        self.tpl = repo["templates"].get(self.template_id)
        self.route = spec.get("route")

    def idx(self, t):
        return [i for i, x in enumerate(self.types) if x == t]

    def body(self):
        """Indices of the page-body nodes: everything between the leading and trailing chrome runs."""
        lo = 0
        while lo < len(self.types) and str(self.types[lo]).startswith("chrome."):
            lo += 1
        hi = len(self.types) - 1
        while hi >= lo and str(self.types[hi]).startswith("chrome."):
            hi -= 1
        return list(range(lo, hi + 1))


RULES = {}


def rule(fn):
    RULES[fn.__name__] = fn
    return fn


# ------------------------------------------------------------------------------- graph rules
@rule
def TEMPLATE_SERVES_ROUTE(c, r):
    if c.tpl and c.route not in c.tpl["routes"]:
        return ["route %r is not served by template %r (it serves %s)" % (c.route, c.template_id, c.tpl["routes"])]
    return []


@rule
def TEMPLATE_NODE_MATCH(c, r):
    """The node list vs the DECLARED TEMPLATE's real node list - never nodes[] in isolation."""
    if not c.tpl:
        return ["unknown template %r" % c.template_id]
    msgs, pos, missing = [], 0, []
    for tn in c.tpl["nodes"]:
        sec = tn["section"]
        start = pos
        while pos < len(c.nodes) and c.types[pos] == sec and (tn["repeatable"] or pos == start):
            pos += 1
        cnt = pos - start
        if cnt == 0:
            if tn["required"]:
                if not missing:
                    missing.append((pos, c.types[pos] if pos < len(c.types) else "end of nodes"))
                missing.append(sec)
            continue
        if tn["repeatable"]:
            cc = tn.get("count") or {}
            lo, hi = cc.get("min", 1), cc.get("max", 10 ** 6)
            if cnt < lo or cnt > hi:
                msgs.append("node %r repeated %dx; template %r allows %d-%d" % (sec, cnt, c.template_id, lo, hi))
        elif cnt > 1:
            msgs.append("node %r appears %dx but template %r does not mark it repeatable" % (sec, cnt, c.template_id))
        if tn.get("variant"):
            for n in c.nodes[start:pos]:
                if n.get("variant") != tn["variant"]:
                    msgs.append("node %r variant %r must be %r in template %r"
                                % (sec, n.get("variant"), tn["variant"], c.template_id))
    if missing:
        (mp, mf), names = missing[0], missing[1:]
        msgs.insert(0, "required template node(s) missing or out of order: %s (first mismatch at position %d, "
                       "found %r; template %r)" % (", ".join(map(repr, names)), mp, mf, c.template_id))
    if pos < len(c.nodes):
        rest = ["%r@%d" % (c.types[i], i) for i in range(pos, len(c.nodes))]
        msgs.append("%d extra or out-of-order node(s) not allowed by template %r, starting at index %d: %s%s"
                    % (len(rest), c.template_id, pos, ", ".join(rest[:6]), " ..." if len(rest) > 6 else ""))
    return msgs


@rule
def ONE_HERO_PER_PAGE(c, r):
    n = len([t for t in c.types if t in c.repo["hero_sections"]])
    return [] if n == 1 else ["expected exactly one hero-category section, found %d" % n]


@rule
def COOKIE_CONSENT_ONCE(c, r):
    n = c.types.count("chrome.cookie-consent")
    return [] if n == 1 else ["chrome.cookie-consent must appear exactly once (found %d)" % n]


@rule
def HEADER_ONCE_AFTER_COOKIES(c, r):
    m = []
    n = c.types.count("chrome.header")
    if n != 1:
        return ["chrome.header must appear exactly once (found %d)" % n]
    if "chrome.cookie-consent" in c.types:
        want = c.types.index("chrome.cookie-consent") + 1
        got = c.types.index("chrome.header")
        if got != want:
            m.append("chrome.header (index %d) must be the node immediately after chrome.cookie-consent "
                     "(expected index %d)" % (got, want))
    return m


@rule
def PRELOADER_FIRST_WHEN_PRESENT(c, r):
    ix = c.idx("chrome.preloader")
    if not ix:
        return []
    m = []
    if len(ix) > 1:
        m.append("chrome.preloader must appear at most once (found %d)" % len(ix))
    if ix[0] != 0:
        m.append("chrome.preloader must be node index 0 when present (found index %d)" % ix[0])
    return m


@rule
def PRELOADER_ABSENT_ON_INNER_ROUTES(c, r):
    bad = r.get("restrictedRoutes", [])
    if c.route in bad and "chrome.preloader" in c.types:
        return ["route %r must not carry chrome.preloader (it passes no preloader prop, so it inherits "
                "Layout's preloader=false default)" % c.route]
    return []


@rule
def BADGE_LAST(c, r):
    n = c.types.count("chrome.awards-badge")
    if n != 1:
        return ["chrome.awards-badge must appear exactly once (found %d)" % n]
    if c.types[-1] != "chrome.awards-badge":
        return ["chrome.awards-badge must be the LAST node (found at index %d of %d)"
                % (c.types.index("chrome.awards-badge"), len(c.types) - 1)]
    return []


@rule
def MENU_FOLLOWS_HEADER(c, r):
    ix = c.idx("chrome.menu")
    if not ix:
        return []
    m = []
    if len(ix) > 1:
        m.append("chrome.menu must appear at most once (found %d)" % len(ix))
    if "chrome.header" in c.types and ix[0] != c.types.index("chrome.header") + 1:
        m.append("chrome.menu (index %d) must be the node immediately after chrome.header (index %d)"
                 % (ix[0], c.types.index("chrome.header")))
    return m


@rule
def FOOTER_PRESENT_AND_PRECEDES_BADGE(c, r):
    n = c.types.count("chrome.footer")
    if n != 1:
        return ["chrome.footer must be present exactly once (found %d)" % n]
    if len(c.types) < 2 or c.types[-2] != "chrome.footer":
        return ["chrome.footer must be the node immediately before chrome.awards-badge"]
    return []


@rule
def NO_EXTERNAL_LINKS(c, r):
    """Walk every string in the spec; reject any scheme, protocol-relative URL or '..' traversal."""
    m = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in STRUCTURAL_KEYS:
                    continue
                walk(v, path + "." + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + "[%d]" % i)
        elif isinstance(o, str):
            if EXTERNAL_RE.search(o):
                m.append("%s: %r is or contains a URL scheme, a protocol-relative URL or a '..' traversal - this "
                         "project is deliberately self-contained and generated output must never introduce one"
                         % (path, o[:90]))
            elif EMBEDDED_URL_RE.search(o):
                m.append("%s: %r has an external URL or hostname embedded in it - a link cannot be smuggled into a "
                         "text field either; this project is deliberately self-contained"
                         % (path, o[:90]))
    walk(c.spec.get("nodes", []), "nodes")
    return m


@rule
def NO_ADJACENT_SAME_SECTION(c, r):
    ok = {e["section"] for e in r.get("exceptions", []) if "section" in e}
    # keyed on (section, variant): one section repeating with DIFFERENT variants is not this rule's target
    return ["%r appears twice in a row at indices %d,%d" % (c.types[i], i - 1, i)
            for i in range(1, len(c.keys))
            if c.keys[i] == c.keys[i - 1] and c.types[i] not in ok]


@rule
def HOME_ONLY_SECTIONS(c, r):
    secs = set(r.get("sections", []))
    if c.route == "/":
        return []
    return ["section %r may appear only on '/' (found on route %r)" % (t, c.route)
            for t in sorted(set(c.types) & secs)]


@rule
def NOT_FOUND_ONLY_SECTIONS(c, r):
    secs = set(r.get("sections", []))
    if c.route == "/404":
        return []
    return ["section %r may appear only on '/404' (found on route %r)" % (t, c.route)
            for t in sorted(set(c.types) & secs)]


@rule
def TECH_VARIANT_MATCHES_ROUTE(c, r):
    want = r.get("perRoute", {}).get(c.route)
    m = []
    for i, n in enumerate(c.nodes):
        if n.get("type") != "content.tech":
            continue
        if want is None:
            m.append("nodes[%d]: content.tech is not admitted on route %r" % (i, c.route))
        elif n.get("variant") != want:
            m.append("nodes[%d]: content.tech variant %r must be %r on route %r"
                     % (i, n.get("variant"), want, c.route))
    return m


@rule
def INERT_FORM_ONLY_ON_AUTH(c, r):
    m = []
    for i, n in enumerate(c.nodes):
        if n.get("type") != "content.tech":
            continue
        has_form = isinstance(n.get("content"), dict) and "form" in n["content"]
        if n.get("variant") == "auth-form" and c.route != "/auth":
            m.append("nodes[%d]: the auth-form variant may appear only on '/auth' (found on %r)" % (i, c.route))
        if has_form and c.route != "/auth":
            m.append("nodes[%d]: a `form` slot may appear only on '/auth' (found on %r)" % (i, c.route))
        if has_form and n["content"]["form"].get("inert") is not True:
            m.append("nodes[%d].content.form.inert must be true - the /auth form is deliberately inert and must "
                     "never be wired up (assetRole auth-inert-form is pinned to must-not-wire-up)" % i)
        if has_form and n["content"]["form"].get("assetRole") != "auth-inert-form":
            m.append("nodes[%d].content.form.assetRole must be 'auth-inert-form' (found %r)"
                     % (i, n["content"]["form"].get("assetRole")))
    return m


@rule
def ROUTE_RESTRICTED_SECTIONS(c, r):
    m = []
    for t in sorted({x for x in c.types if x}):
        ct = c.repo["contracts"].get(t)
        allowed = ct.get("usedOn") if ct else None
        if allowed is not None and c.route not in allowed:
            m.append("section %r is not allowed on route %r (its contract's usedOn is %s)" % (t, c.route, allowed))
    return m


@rule
def SECTION_CONTRACT_CONSTRAINTS(c, r):
    m = []
    last = len(c.types) - 1
    body = c.body()
    for t in sorted({x for x in c.types if x in c.repo["contracts"]}):
        k = c.repo["contracts"][t].get("constraints", {})
        ix, chrome = c.idx(t), str(t).startswith("chrome.")
        if k.get("onePerPage") and len(ix) > 1:
            m.append("%s: onePerPage violated (%d instances)" % (t, len(ix)))
        if k.get("maxPerPage") is not None and len(ix) > k["maxPerPage"]:
            m.append("%s: maxPerPage %d exceeded (%d instances)" % (t, k["maxPerPage"], len(ix)))
        if k.get("mustBeFirst") and ix and ix[0] != 0:
            m.append("%s: mustBeFirst violated (index %d, expected 0)" % (t, ix[0]))
        if k.get("mustBeLast") and ix and ix[-1] != last:
            m.append("%s: mustBeLast violated (index %d, expected %d)" % (t, ix[-1], last))
        if k.get("mustBeFirstInBody") and ix and body and ix[0] != body[0]:
            m.append("%s: mustBeFirstInBody violated (index %d, body starts at %d)" % (t, ix[0], body[0]))
        if k.get("mustBeLastInBody") and ix and body and ix[-1] != body[-1]:
            m.append("%s: mustBeLastInBody violated (index %d, body ends at %d)" % (t, ix[-1], body[-1]))
        if k.get("mustFollowHeader") and ix and "chrome.header" in c.types \
                and ix[0] != c.types.index("chrome.header") + 1:
            m.append("%s: mustFollowHeader violated (index %d)" % (t, ix[0]))
        if k.get("mustPrecedeBadge") and ix and "chrome.awards-badge" in c.types \
                and ix[-1] != c.types.index("chrome.awards-badge") - 1:
            m.append("%s: mustPrecedeBadge violated (index %d)" % (t, ix[-1]))
        if k.get("noConsecutive") and any(b - a == 1 for a, b in zip(ix, ix[1:])):
            m.append("%s: noConsecutive violated" % t)
        if k.get("homeRouteOnly") and ix and c.route != "/":
            m.append("%s: homeRouteOnly violated (route %r)" % (t, c.route))
        if k.get("notFoundRouteOnly") and ix and c.route != "/404":
            m.append("%s: notFoundRouteOnly violated (route %r)" % (t, c.route))
        if chrome and not (k.get("onePerPage") or k.get("maxPerPage")):
            m.append("%s: a chrome section contract must declare onePerPage or maxPerPage" % t)
    return m


@rule
def VARIANT_MATCHES_ROUTE(c, r):
    m = []
    for i, n in enumerate(c.nodes):
        v, ct = n.get("variant"), c.repo["contracts"].get(n.get("type"))
        if v is None or not ct:
            continue
        vk = variant_keys(ct)
        if v not in vk:
            m.append("nodes[%d] %r: variant %r is not one of %s" % (i, n.get("type"), v, vk))
            continue
        entry = ct["variants"][v] if isinstance(ct.get("variants"), dict) else None
        if isinstance(entry, dict) and entry.get("routes") and c.route not in entry["routes"]:
            m.append("nodes[%d] %r: variant %r is evidenced only on %s, not %r"
                     % (i, n.get("type"), v, entry["routes"], c.route))
    return m


@rule
def COMPOSED_EVIDENCE_DISCLOSED(c, r):
    if c.tpl and c.tpl.get("evidenceLevel") == "composed-not-measured":
        return ["template %r has evidenceLevel 'composed-not-measured': its structure and copy are an original "
                "composition from this design system, NOT evidence about fourmula.ai. Do not cite this page as "
                "measured fact." % c.template_id]
    return []


def graph_parity(repo_root=None):
    """(graph rule ids with no implementation, implemented ids missing from the graph)."""
    ids = [x["id"] for x in load_repo(repo_root)["graph"]["rules"]]
    return sorted(set(ids) - set(RULES)), sorted(set(RULES) - set(ids))


# ------------------------------------------------------------------------------- content checks
def _walk(inst, sch, path, repo, out, tot):
    """Walk an instance beside its section-contract content schema: word budgets, roles, paths."""
    if not isinstance(sch, dict):
        return
    if "oneOf" in sch and isinstance(inst, dict):
        # pick the branch whose required set the instance satisfies; the schema layer already
        # guarantees exactly one matches, so this is a lookup, not a second validation
        best = None
        for b in sch["oneOf"]:
            if all(k in inst for k in b.get("required", [])):
                best = b
                break
        if best is not None:
            _walk(inst, best, path, repo, out, tot)
        return
    if isinstance(inst, str):
        if "maxWords" in sch:
            n = wc(inst)
            # Accessibility text (alt) carries its own per-field budget but is NOT visible page copy,
            # so a contract can set countsTowardTotal:false to keep it out of contentMaxWordsTotal.
            if sch.get("countsTowardTotal") is not False:
                tot[0] += n
            if n > sch["maxWords"]:
                out.append("SEM-WORDS %s: %d words exceeds maxWords %d" % (path, n, sch["maxWords"]))
        if sch.get("format") == "local-asset-path" and not LOCAL_PATH_RE.match(inst):
            out.append("SEM-ASSET %s: %r is not a local asset path (remote URLs, protocol-relative URLs, "
                       "schemes and '..' are forbidden)" % (path, inst))
        if sch.get("format") == "route-or-inert-hash" and inst not in INERT_HREFS and inst not in repo["routes"]:
            out.append("SEM-ASSET %s: %r must be an inert hash (%s), an in-page anchor, or one of the 6 routes %s"
                       % (path, inst, "#", repo["routes"]))
        en = sch.get("enum")
        if en and set(en) <= repo["role_set"]:
            if inst not in repo["role_set"]:
                out.append("SEM-ASSET %s: assetRole %r is not in the closed assetRole enum" % (path, inst))
            elif inst not in en:
                out.append("SEM-ASSET %s: assetRole %r is not allowed in this slot (allowed: %s)" % (path, inst, en))
    elif isinstance(inst, dict) and "properties" in sch:
        for k, v in inst.items():
            if k in sch["properties"]:
                _walk(v, sch["properties"][k], "%s.%s" % (path, k), repo, out, tot)
        role = inst.get("assetRole")
        for ref in ("assetRef", "themePairRef", "crossFadeTwinRef"):
            p = inst.get(ref)
            if isinstance(role, str) and isinstance(p, str) and p.startswith("/"):
                isvid = role == "showcase-video"
                if isvid != p.startswith("/assets/video/"):
                    out.append("SEM-ASSET %s.%s: role %r does not match path %r (only showcase-video lives under "
                               "/assets/video/)" % (path, ref, role, p))
    elif isinstance(inst, list) and "items" in sch:
        for i, x in enumerate(inst):
            _walk(x, sch["items"], "%s[%d]" % (path, i), repo, out, tot)


def content_checks(spec, repo):
    errs = []
    for i, n in enumerate(spec.get("nodes", [])):
        if not isinstance(n, dict):
            continue
        t = n.get("type")
        ct = repo["contracts"].get(t)
        m = n.get("motion")
        if not (isinstance(m, dict) and isinstance(m.get("reducedMotionFallback"), str)
                and m["reducedMotionFallback"].strip()):
            errs.append("SEM-MOTION nodes[%d] %s: reducedMotionFallback is REQUIRED (for every section except the "
                        "background-video slot it is a design rule this repository prescribes, because the source "
                        "ships no prefers-reduced-motion handling)" % (i, t))
        elif wc(m["reducedMotionFallback"]) > MAX_FALLBACK_WORDS:
            errs.append("SEM-WORDS nodes[%d].motion.reducedMotionFallback: %d words exceeds %d"
                        % (i, wc(m["reducedMotionFallback"]), MAX_FALLBACK_WORDS))
        if ct and isinstance(m, dict):
            if m.get("pattern") not in (None, ct["motion"]["pattern"]):
                errs.append("SEM-MOTION nodes[%d] %s: motion.pattern %r must be %r"
                            % (i, t, m.get("pattern"), ct["motion"]["pattern"]))
            kind = m.get("reducedMotionFallbackKind")
            declared = ct["motion"].get("reducedMotionFallbackKind", "")
            if kind == "mirrored" and not declared.startswith("mirrored"):
                errs.append("SEM-MOTION nodes[%d] %s: reducedMotionFallbackKind 'mirrored' is not honest here - "
                            "only the background-video slot genuinely reads prefers-reduced-motion "
                            "(public/motion/m27.js). This section's contract declares %r"
                            % (i, t, declared.split(" (")[0] or "design-rule"))
        if ct and isinstance(n.get("content"), dict):
            out, tot = [], [0]
            _walk(n["content"], ct["content"], "nodes[%d].content" % i, repo, out, tot)
            cap = ct.get("contentMaxWordsTotal")
            if cap is not None and tot[0] > cap:
                out.append("SEM-WORDS nodes[%d].content: %d total words exceeds contentMaxWordsTotal %d"
                           % (i, tot[0], cap))
            errs.extend("%s [%s]" % (e, t) for e in out)
    return errs


# ------------------------------------------------------------------------------- public API
def validate(pagespec, repo_root=None):
    """Return (errors, warnings). Schema errors and semantic errors are both in `errors`."""
    from jsonschema import Draft7Validator
    from jsonschema.exceptions import best_match
    repo = load_repo(repo_root)
    errors, warnings = [], []
    if not isinstance(pagespec, dict):
        return ["SCHEMA: a PageSpec must be a JSON object"], []
    for e in sorted(Draft7Validator(repo["schema"]).iter_errors(pagespec), key=lambda e: list(map(str, e.path))):
        while e.context:  # oneOf/anyOf: report a leaf error from the branch closest to matching
            groups = {}
            for sub in e.context:
                groups.setdefault(sub.relative_schema_path[0], []).append(sub)
            e = best_match(min(groups.values(), key=len)) or e.context[0]
        loc = "/".join(map(str, e.absolute_path)) or "<root>"
        errors.append("SCHEMA %s: %s" % (loc, e.message[:240]))
    if not isinstance(pagespec.get("nodes"), list):
        return errors, warnings
    c = Ctx(pagespec, repo)
    for r in repo["graph"]["rules"]:
        fn = RULES.get(r["id"])
        if fn is None:
            errors.append("GRAPH rule %s has no implementation" % r["id"])
            continue
        if any(e.get("template") == c.template_id for e in r.get("exceptions", [])):
            continue
        for msg in fn(c, r):
            (errors if r["severity"] == "error" else warnings).append("[%s] %s" % (r["id"], msg))
    errors.extend(content_checks(pagespec, repo))
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings))


# ------------------------------------------------------------------------------- control synthesizer
def _sample(sch, repo):
    if "const" in sch:
        return sch["const"]
    if "enum" in sch:
        return sch["enum"][0]
    t = sch.get("type")
    if t == "string":
        if sch.get("format") == "local-asset-path":
            return "/assets/control-asset.avif"
        if sch.get("format") == "route-or-inert-hash":
            return "#"
        if "pattern" in sch:
            return "control-id"
        return " ".join(["Sample", "text"][:max(1, min(2, sch.get("maxWords", 2)))])
    if t == "array":
        return [_sample(sch["items"], repo) for _ in range(sch.get("minItems", 0))]
    if t == "object":
        return _sample_obj(sch, repo)
    if t == "integer" or t == "number":
        if "enum" in sch:
            return sch["enum"][0]
        return sch.get("minimum", 0)
    if t == "boolean":
        return False
    if "oneOf" in sch:
        return _sample_obj(sch["oneOf"][0], repo)
    raise ValueError("cannot synthesize %r" % (sch,))


def _sample_obj(sch, repo):
    if "oneOf" in sch and "properties" not in sch:
        sch = sch["oneOf"][0]
    o = {}
    for k in sch.get("required", []):
        o[k] = _sample(sch["properties"][k], repo)
    role = o.get("assetRole")
    for ref in ("assetRef", "themePairRef", "crossFadeTwinRef"):
        if ref in o and role == "showcase-video":
            o[ref] = "/assets/video/control-asset.mp4"
    return o


def synthesize_control(template_id, repo_root=None, branch=None):
    """A minimal VALID PageSpec for a template, built from its own node list plus each section
    contract's required fields. Generic: a template added to templates.json is covered with no
    new code (MASTER-GUIDE 3.22)."""
    repo = load_repo(repo_root)
    tpl = repo["templates"][template_id]
    route = tpl["routes"][0]
    nodes = []
    for tn in tpl["nodes"]:
        if not tn["required"]:
            continue
        ct = repo["contracts"][tn["section"]]
        variant = tn.get("variant")
        if variant is None:
            vk = variant_keys(ct)
            if vk:
                variant = next((k for k in vk
                                if isinstance(ct["variants"].get(k), dict)
                                and route in ct["variants"][k].get("routes", [])), vk[0])
        content_sch = ct["content"]
        if "oneOf" in content_sch:
            want = branch
            if want is None and variant:
                want = (ct["variants"].get(variant) or {}).get("contentBranch", variant)
            pick = next((b for b in content_sch["oneOf"] if b.get("title") == want), content_sch["oneOf"][0])
            content_sch = pick
        n = {"type": tn["section"]}
        if variant:
            n["variant"] = variant
        n["content"] = _sample_obj(content_sch, repo)
        n["motion"] = {"pattern": ct["motion"]["pattern"],
                       "reducedMotionFallback": "Render the final state with no animation."}
        nodes.append(n)
    return {"pageSpecVersion": "1.0.0", "template": template_id, "route": route, "nodes": nodes}


def main(argv):
    if "--parity" in argv:
        a, b = graph_parity()
        print("graph rule ids with no implementation:", a)
        print("implemented RULES missing from graph.json:", b)
        if not a and not b:
            print("parity OK: %d rules" % len(RULES))
        return 1 if (a or b) else 0
    paths = [a for a in argv if not a.startswith("--")]
    if len(paths) != 1:
        print(__doc__)
        return 2
    try:
        with open(paths[0], encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:
        print("ERROR cannot read PageSpec %r: %s: %s" % (paths[0], type(e).__name__, e))
        return 2
    errors, warnings = validate(spec)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
