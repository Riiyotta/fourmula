#!/usr/bin/env python3
"""verify_all.py - one-shot integrity check for this design-repo. Exit code 0 only if every check passes.

Usage:  python3 extraction/verify_all.py              run every check; print PASS/FAIL/WARN and a summary
        python3 extraction/verify_all.py --emit-counts  print the recomputed counts (JSON + the README block)

The repo root is derived from this file's location: no absolute paths, so this runs unchanged from a
standalone copy of the folder with no sibling directories. Checks:

  [a] json-parse          every *.json in the package parses
  [b] schema-example      pagespec.schema.json is valid Draft-07; example.pagespec.json has 0 schema
                          errors and 0 semantic errors
  [c] schema-uptodate     extraction/build_pagespec_schema.py --check (the shipped schema still matches
                          the contracts it is generated from)
  [d] allowlist-parity    component-allowlist.json <-> primitive/component/section contract ids, BOTH
                          directions, plus file-name and folder coherence
  [e] allowlist-version   allowlistVersion in the allowlist == registry.manifest.json
  [f] manifest-counts     the manifest `counts` block RECOMPUTED from the real files, plus the catalog's
                          own counts and the README counts block
  [g] route-template      6 routes <-> 5 templates 1:1, manifest routeTemplateMap, schema enums, and
                          route/section admission over EVERY route
  [h] template-graph      template node sections all have contracts; schema section enum == contracts;
                          graph rule ids <-> validator RULES in both directions; severities are valid
  [i] citations           every path:line[-line] citation resolves against the real source file AND its
                          stored quote really sits in that range (WARN-skipped with no sibling source tree)
  [j] asset-roles         closed role enum, closed policy enum, and a PINNED-VALUE check for every
                          compliance-critical role (membership in the enum is NOT sufficient)
  [k] token-refs          token refs resolve; catalog/policy category names match; BOTH themes resolve
                          every semantic role and nothing else; colour provenance in the real source
  [l] no-absolute-paths   no machine-local absolute path in any shipped file
  [m] entrypoints-docs    entryPoints exist INSIDE the package with no `..`, cover every file, and every
                          file any doc or docstring claims exists really exists
  [n] version-note        versionFieldNote is present and honest about machine-checked vs documentation-only
  [o] evidence-levels     every route and template carries an evidence level from the closed set, and the
                          composed-not-measured routes are never described as measured
  [p] word-budgets        every declared contentMaxWordsTotal is REACHABLE (strictly below the sum of its own
                          per-field maxWords at maxItems), so no total cap is a check that can never fire;
                          every text-bearing field carries a maxWords; and the shipped example sits under
                          every cap with real headroom
  [q] wrapper-gate        extraction/wrapper_gate.py over the MEASURED sectionHeights (HERO 1800/3000px,
                          single-section share 50%/60%, missing measurement, whitelist hygiene)
  [r] policy-binding      registry.manifest.json category + designPolicy binding, policy/design-policy.json
                          present and consistent, contentHash == sha256 over the policy's enforcedBy files
  [s] provenance          every section contract validates against the CLOSED schema/section-contract.schema.json;
                          semantic.id == id, source.id != id; the source tag really sits on the first cited
                          line of the real file (and build_provenance.py --check agrees) when the source is present
  [t] retrieval-pin       RETRIEVAL_INELIGIBLE pinned here == semantic_validate's pin == contracts' false set ==
                          the allowlist's retrievalIneligible list; runtime-UI-looking ids must be in the pin
  [u] availability-pin    PINNED_AVAILABILITY here == semantic_validate's pin == assets/asset-roles.json; every
                          non-generation-safe role has generation-safe substitutes; contracts' generatedAssetRoles
                          are generation-safe and wired into their slots
  [v] generation-mode     schema mode enum is closed {clone, generation} and required; one generation example
                          per template passes with 0 errors; the clone example passes; the leakage registry has
                          every GENERATION_MODE_* category with evidence, and rebuilds identically from source
  [w] token-registration  token-catalog / token-policy / motion-patterns registered in the manifest; each
                          catalog category equals its sourceFile's ids; motion-patterns == contracts == schema;
                          the policy names every TOKEN_* rule the validator implements

Drift proof for these checks: python3 extraction/prove_drift.py
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.dirname(ROOT)  # the sibling source project, present only beside its own tree

# Built by concatenation so this file itself contains no absolute path for check [l] to find.
_ABS_PATTERNS = [re.compile(p) for p in (
    "/" + "Users" + "/", "/" + "home" + "/[A-Za-z0-9_.-]+/",
    "(?<![A-Za-z0-9])[A-Za-z]:" + "\\\\" + "[A-Za-z]", "/private" + "/(?:var|tmp)/")]

RESULTS = []
CHECKS = []

# Pinned in code, independently of the registries (R3 / R8). semantic_validate.py holds its own copy; both
# must equal assets/asset-roles.json and the section contracts, or checks [t] / [u] fail.
PINNED_AVAILABILITY = {
    "hero-carousel-photo": "clone-only", "preloader-photo": "clone-only", "product-shot-photo": "clone-only",
    "step-artwork": "clone-only", "showcase-video": "clone-only", "not-found-artwork": "clone-only",
    "brand-wordmark": "clone-only", "favicon": "clone-only", "third-party-award-badge": "clone-only",
    "trusted-partner-logo": "blocked-for-generation", "brand-typeface-file": "blocked-for-generation",
    "og-banner": "blocked-for-generation",
    "ui-icon-glyph": "generation-safe", "form-control-checkmark": "generation-safe",
    "auth-inert-form": "generation-safe", "placeholder-brand-mark": "generation-safe",
    "user-supplied-asset": "generation-safe", "generated-illustration": "generation-safe",
    "placeholder-screenshot": "generation-safe", "fictional-person-avatar": "generation-safe",
    "placeholder-customer-logo": "generation-safe", "placeholder-url": "generation-safe",
    "original-copy": "generation-safe",
}
RETRIEVAL_INELIGIBLE = {"chrome.cookie-consent", "chrome.preloader", "chrome.menu", "chrome.awards-badge"}
RUNTIME_UI_RE = re.compile(r"cookie|consent|modal|dialog|drawer|popup|preloader|loader|overlay|toast|menu|badge")
GENERATION_CATEGORIES = ("GENERATION_MODE_BRAND", "GENERATION_MODE_ASSET", "GENERATION_MODE_PERSON",
                         "GENERATION_MODE_CUSTOMER", "GENERATION_MODE_SCREENSHOT", "GENERATION_MODE_COPY",
                         "GENERATION_MODE_CLAIM", "GENERATION_MODE_URL", "GENERATION_MODE_EMBED")
TOKEN_RULES = ("TOKEN_UNKNOWN", "TOKEN_RAW_COLOR", "TOKEN_ARBITRARY_SPACING", "TOKEN_UNSUPPORTED_FONT",
               "TOKEN_THEME_MISMATCH", "TOKEN_CATEGORY_MISMATCH")


def policy_hash(root, files):
    import hashlib
    h = hashlib.sha256()
    for f in sorted(files):
        with open(os.path.join(root, f), "rb") as fh:
            h.update(("%s\n%s\n" % (f, hashlib.sha256(fh.read()).hexdigest())).encode())
    return "sha256:" + h.hexdigest()


def example_files():
    return [os.path.join(ROOT, "schema", "example.pagespec.json")] + sorted(
        glob.glob(os.path.join(ROOT, "schema", "examples", "*.pagespec.json")))


def rel(p):
    return os.path.relpath(p, ROOT)


def jload(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


def all_files():
    out = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git")]
        for f in files:
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            out.append(os.path.join(d, f))
    return sorted(out)


def json_files():
    return [p for p in all_files() if p.endswith(".json")]


def contract_files():
    return {k: sorted(glob.glob(os.path.join(ROOT, k, "*.json")))
            for k in ("primitives", "components", "sections")}


def contract_ids():
    ids = {}
    for kind, files in contract_files().items():
        for f in files:
            with open(f, encoding="utf-8") as fh:
                ids[json.load(fh)["id"]] = (kind, f)
    return ids


TIER_DIR = {"foundation": "00-foundation", "semantic": "10-semantic",
            "component": "20-component", "layout": "30-layout"}


def token_tiers():
    tiers = {k: {} for k in TIER_DIR}
    for tier, d in TIER_DIR.items():
        for f in sorted(glob.glob(os.path.join(ROOT, "tokens", d, "*.json"))):
            with open(f, encoding="utf-8") as fh:
                tiers[tier].update(json.load(fh).get("tokens", {}))
    return tiers


def compute_counts():
    tiers = token_tiers()
    tpl = jload("templates", "templates.json")["templates"]
    cf = contract_files()
    t = {k: len(v) for k, v in tiers.items()}
    t["total"] = sum(t.values())
    cat = jload("tokens", "llm", "token-catalog.json")["categories"]
    return {
        "tokens": t,
        "catalogEntries": sum(len(v["tokens"]) for v in cat.values()),
        "primitives": len(cf["primitives"]),
        "components": len(cf["components"]),
        "sections": len(cf["sections"]),
        "templates": len(tpl),
        "routes": len({r for x in tpl for r in x["routes"]}),
        "graphRules": len(jload("compatibility", "graph.json")["rules"]),
        "assetRoles": len(jload("assets", "asset-roles.json")["roles"]),
        "citations": len(jload("extraction", "measured-values.json")["citations"]),
        "motionPatterns": len(jload("schema", "pagespec.schema.json")
                              ["definitions"]["motion"]["properties"]["pattern"]["enum"]),
        "examplePageSpecs": len(example_files()),
        "retrievalIneligibleSections": len(jload("tokens", "llm", "component-allowlist.json")
                                           .get("retrievalIneligible", [])),
    }


def counts_block(c):
    t = c["tokens"]
    return ("- Tokens: %d total (foundation %d, semantic %d, component %d, layout %d); catalog entries %d\n"
            "- Primitives %d, components %d, sections %d\n"
            "- Templates %d, routes %d (1:1), graph rules %d, motion patterns %d, asset roles %d, "
            "ledger citations %d\n- Example PageSpecs %d, retrieval-ineligible sections %d" % (
                t["total"], t["foundation"], t["semantic"], t["component"], t["layout"], c["catalogEntries"],
                c["primitives"], c["components"], c["sections"], c["templates"], c["routes"],
                c["graphRules"], c["motionPatterns"], c["assetRoles"], c["citations"],
                c["examplePageSpecs"], c["retrievalIneligibleSections"]))


def check(name):
    def deco(fn):
        def run():
            try:
                fails, warns, info = fn()
            except Exception as e:  # a crashing check is a failing check
                fails, warns, info = ["check crashed: %s: %s" % (type(e).__name__, e)], [], ""
            for w in warns:
                RESULTS.append(("WARN", name, w))
            if fails:
                for m in fails[:12]:
                    RESULTS.append(("FAIL", name, m))
                if len(fails) > 12:
                    RESULTS.append(("FAIL", name, "... and %d more" % (len(fails) - 12)))
            else:
                RESULTS.append(("PASS", name, info))
        run.__name__ = fn.__name__
        CHECKS.append(run)
        return fn
    return deco


def walk_strings(o, fn, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            walk_strings(v, fn, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_strings(v, fn, path + "[%d]" % i)
    elif isinstance(o, str):
        fn(path, o)


# ----------------------------------------------------------------------------------- [a]
@check("[a] json-parse")
def c_a():
    fails, n = [], 0
    for p in json_files():
        n += 1
        try:
            with open(p, encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            fails.append("%s: %s" % (rel(p), e))
    return fails, [], "%d json files parse" % n


# ----------------------------------------------------------------------------------- [b]
@check("[b] schema-example")
def c_b():
    from jsonschema import Draft7Validator
    fails = []
    schema = jload("schema", "pagespec.schema.json")
    try:
        Draft7Validator.check_schema(schema)
    except Exception as e:
        return ["pagespec.schema.json is not a valid Draft-07 schema: %s" % str(e)[:200]], [], ""
    if schema.get("$schema", "").rstrip("#") != "http://json-schema.org/draft-07/schema":
        fails.append("schema $schema is not draft-07: %r" % schema.get("$schema"))
    if schema["definitions"]["motion"].get("additionalProperties") is not False:
        fails.append("definitions.motion must be additionalProperties:false")
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    nw = 0
    for fp in example_files():
        with open(fp, encoding="utf-8") as f:
            ex = json.load(f)
        for e in list(Draft7Validator(schema).iter_errors(ex))[:5]:
            fails.append("%s schema error at %s: %s" % (rel(fp), "/".join(map(str, e.absolute_path)), e.message[:160]))
        errors, warnings = sv.validate(ex, ROOT)
        nw += len(warnings)
        fails.extend("%s semantic error: %s" % (rel(fp), e) for e in errors[:8])
    return fails, [], ("Draft-07 schema valid, motion closed; all %d example PageSpecs have 0 schema errors and 0 "
                       "semantic errors (%d warning(s))" % (len(example_files()), nw))


# ----------------------------------------------------------------------------------- [c]
@check("[c] schema-uptodate")
def c_c():
    script = os.path.join(ROOT, "extraction", "build_pagespec_schema.py")
    if not os.path.isfile(script):
        return ["extraction/build_pagespec_schema.py is missing"], [], ""
    r = subprocess.run([sys.executable, script, "--check"], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return ["build_pagespec_schema.py --check exit %d: %s" % (r.returncode, out[:200])], [], ""
    return [], [], out


# ----------------------------------------------------------------------------------- [d]
@check("[d] allowlist-parity")
def c_d():
    fails = []
    al = jload("tokens", "llm", "component-allowlist.json")
    names = al["components"]
    ids = contract_ids()
    if len(names) != len(set(names)):
        fails.append("the allowlist has duplicate entries")
    for a in sorted(set(names) - set(ids)):
        fails.append("phantom allowlist id (no contract file): %s" % a)
    for i in sorted(set(ids) - set(names)):
        fails.append("orphan contract (not in the allowlist): %s (%s)" % (i, rel(ids[i][1])))
    for i, (kind, f) in ids.items():
        if os.path.basename(f) != i.replace(".", "-") + ".json":
            fails.append("file name %s does not match id %s" % (rel(f), i))
        prefix = i.split(".")[0]
        want = {"primitive": "primitives", "component": "components"}.get(prefix, "sections")
        if kind != want:
            fails.append("%s lives in %s but belongs in %s" % (i, kind, want))
    claim = al.get("counts", {})
    real = {"primitives": sum(1 for i in ids if i.startswith("primitive.")),
            "components": sum(1 for i in ids if i.startswith("component.")),
            "sections": sum(1 for i in ids if not i.startswith(("primitive.", "component."))),
            "total": len(ids)}
    if claim != real:
        fails.append("allowlist `counts` %s != recomputed %s" % (claim, real))
    return fails, [], "%d allowlist ids == %d contract ids, both directions; names, folders and counts agree" % (
        len(set(names)), len(ids))


# ----------------------------------------------------------------------------------- [e]
@check("[e] allowlist-version")
def c_e():
    a = jload("tokens", "llm", "component-allowlist.json").get("allowlistVersion")
    m = jload("registry.manifest.json").get("allowlistVersion")
    if not a or a != m:
        return ["allowlistVersion mismatch: allowlist=%r manifest=%r" % (a, m)], [], ""
    return [], [], "allowlistVersion %s matches in the allowlist and the manifest" % a


# ----------------------------------------------------------------------------------- [f]
@check("[f] manifest-counts")
def c_f():
    fails = []
    got = compute_counts()
    claim = jload("registry.manifest.json").get("counts")
    if not isinstance(claim, dict):
        return ["the manifest has no counts block"], [], ""

    def cmp(path, a, b):
        if isinstance(a, dict) or isinstance(b, dict):
            if not (isinstance(a, dict) and isinstance(b, dict)):
                fails.append("counts.%s: shape differs (disk %r vs manifest %r)" % (path, a, b))
                return
            for k in sorted(set(a) | set(b)):
                cmp(path + "." + k if path else k, a.get(k, "<absent>"), b.get(k, "<absent>"))
        elif a != b:
            fails.append("counts.%s: disk=%s manifest=%s" % (path, a, b))
    cmp("", got, claim)
    cat = jload("tokens", "llm", "token-catalog.json")
    tiers = token_tiers()
    by_tier = {}
    for name, v in cat["categories"].items():
        if v["count"] != len(v["tokens"]):
            fails.append("catalog %s states count %d but holds %d entries" % (name, v["count"], len(v["tokens"])))
        by_tier.setdefault(v["tier"], set()).update(t["id"] for t in v["tokens"])
    for tier, ids in tiers.items():
        if by_tier.get(tier, set()) != set(ids):
            fails.append("catalog tier %s ids differ from disk (only-catalog %s, only-disk %s)" % (
                tier, sorted(by_tier.get(tier, set()) - set(ids))[:4],
                sorted(set(ids) - by_tier.get(tier, set()))[:4]))
    if cat.get("counts") and {k: v["count"] for k, v in cat["categories"].items()} != cat["counts"]:
        fails.append("the catalog `counts` block differs from its own categories")
    rp = os.path.join(ROOT, "README.md")
    if os.path.isfile(rp):
        with open(rp, encoding="utf-8") as f:
            t = f.read()
        m = re.search(r"<!-- counts:begin -->\n(.*?)\n<!-- counts:end -->", t, re.S)
        if not m:
            fails.append("README.md has no <!-- counts:begin/end --> block")
        elif m.group(1).strip() != counts_block(got).strip():
            fails.append("the README.md counts block differs from the recomputed counts")
    else:
        fails.append("README.md is missing")
    return fails, [], ("manifest counts == disk (%d tokens, %d sections, %d templates, %d routes, %d citations); "
                       "catalog and README block agree" % (got["tokens"]["total"], got["sections"],
                                                           got["templates"], got["routes"], got["citations"]))


# ----------------------------------------------------------------------------------- [g]
@check("[g] route-template")
def c_g():
    fails = []
    man = jload("registry.manifest.json")
    tdoc = jload("templates", "templates.json")
    tpls = tdoc["templates"]
    schema = jload("schema", "pagespec.schema.json")
    served = {}
    for t in tpls:
        for r in t["routes"]:
            served.setdefault(r, []).append(t["id"])
    for r, ts in sorted(served.items()):
        if len(ts) != 1:
            fails.append("route %s is served by %d templates %s (must be exactly 1)" % (r, len(ts), ts))
    mp = man.get("routeTemplateMap")
    if not isinstance(mp, dict):
        fails.append("the manifest has no routeTemplateMap")
        mp = {}
    if set(mp) != set(served):
        fails.append("manifest routeTemplateMap routes differ from the templates (only-manifest %s, "
                     "only-templates %s)" % (sorted(set(mp) - set(served)), sorted(set(served) - set(mp))))
    for r, ts in served.items():
        if mp.get(r) != ts[0]:
            fails.append("route %s: the manifest says template %r, templates.json says %r" % (r, mp.get(r), ts[0]))
    if len(served) != man.get("counts", {}).get("routes") or len(served) != 6:
        fails.append("expected exactly 6 routes, found %d (the manifest claims %s)"
                     % (len(served), man.get("counts", {}).get("routes")))
    tdm = tdoc.get("routeTemplate1to1", {}).get("map")
    if tdm != {r: ts[0] for r, ts in served.items()}:
        fails.append("templates.json's own routeTemplate1to1.map disagrees with its templates[] routes")
    props = schema["properties"]
    if set(props["route"]["enum"]) != set(served):
        fails.append("the schema route enum differs from the template routes")
    if set(props["template"]["enum"]) != {t["id"] for t in tpls}:
        fails.append("the schema template enum differs from the template ids")
    contracts = {i: json.load(open(f, encoding="utf-8"))
                 for i, (k, f) in contract_ids().items() if k == "sections"}
    checked = 0
    # route admission, run UNSCOPED over EVERY route x EVERY node of its template
    for t in tpls:
        for r in t["routes"]:
            for n in t["nodes"]:
                s = n["section"]
                if s not in contracts:
                    continue
                checked += 1
                allowed = contracts[s].get("usedOn")
                if allowed is not None and r not in allowed:
                    fails.append("route %s: template %s requires section %s, which its contract's usedOn (%s) "
                                 "does not admit on that route" % (r, t["id"], s, allowed))
                v = n.get("variant")
                ct = contracts[s]
                if v:
                    if not isinstance(ct.get("variants"), dict) or v not in ct["variants"]:
                        fails.append("route %s: template %s pins %s variant %r, which the contract does not declare"
                                     % (r, t["id"], s, v))
                    else:
                        vr = ct["variants"][v].get("routes")
                        if vr and r not in vr:
                            fails.append("route %s: %s variant %r is evidenced only on %s" % (r, s, v, vr))
                elif isinstance(ct.get("variants"), dict) and ct["variants"]:
                    fails.append("route %s: template %s leaves %s without a variant although the contract declares "
                                 "%s" % (r, t["id"], s, sorted(ct["variants"])))
    return fails, [], ("%d routes <-> %d templates 1:1; the manifest map, templates.json's own map and both schema "
                       "enums agree; %d route/section admissions consistent"
                       % (len(served), len(tpls), checked))


# ----------------------------------------------------------------------------------- [h]
@check("[h] template-graph")
def c_h():
    fails = []
    tpls = jload("templates", "templates.json")["templates"]
    sec_ids = {i for i, (k, f) in contract_ids().items() if k == "sections"}
    used = set()
    for t in tpls:
        q = [n["section"] for n in t["nodes"]]
        for s in q:
            used.add(s)
            if s not in sec_ids:
                fails.append("template %s node %r has no section contract" % (t["id"], s))
        if t.get("nodeCount") not in (None, len(q)):
            fails.append("template %s states nodeCount %s but has %d nodes" % (t["id"], t.get("nodeCount"), len(q)))
        if t.get("derivedNodeList") is not None and t["derivedNodeList"] != q:
            fails.append("template %s derivedNodeList is stale relative to its own nodes[]" % t["id"])
        if q[0] != "chrome.cookie-consent" and q[0] != "chrome.preloader":
            fails.append("template %s does not start with chrome.preloader or chrome.cookie-consent" % t["id"])
        if q[-1] != "chrome.awards-badge":
            fails.append("template %s does not end with chrome.awards-badge" % t["id"])
    schema = jload("schema", "pagespec.schema.json")
    enum = set(schema["definitions"]["node"]["properties"]["type"]["enum"])
    if enum != sec_ids:
        fails.append("the schema section enum != the section contracts (only-schema %s, only-contracts %s)"
                     % (sorted(enum - sec_ids), sorted(sec_ids - enum)))
    for s in sorted(sec_ids - used):
        fails.append("section %s is used by no template" % s)
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    un, miss = sv.graph_parity(ROOT)
    if un:
        fails.append("graph rule ids with no validator implementation: %s" % un)
    if miss:
        fails.append("validator RULES missing from graph.json: %s" % miss)
    graph = jload("compatibility", "graph.json")
    for r in graph["rules"]:
        if r.get("severity") not in ("error", "warn"):
            fails.append("graph rule %s has severity %r" % (r["id"], r.get("severity")))
        if "exceptions" not in r:
            fails.append("graph rule %s has no exceptions field" % r["id"])
    if not any(r["severity"] == "warn" for r in graph["rules"]):
        fails.append("every graph rule is fatal: at least one rule should be severity warn")
    # the graph's recorded verifiedAgainst sequences must still match the real templates
    va = graph.get("verifiedAgainst", {}).get("sequences")
    real = {t["id"]: [n["section"] for n in t["nodes"]] for t in tpls}
    if va != real:
        fails.append("graph.json verifiedAgainst.sequences is stale relative to templates.json")
    # controls: every template must synthesize a PageSpec with zero errors
    for t in sorted(real):
        try:
            errs, _ = sv.validate(sv.synthesize_control(t, ROOT), ROOT)
        except Exception as e:
            fails.append("synthesize_control(%s) crashed: %s: %s" % (t, type(e).__name__, e))
            continue
        if errs:
            fails.append("synthesize_control(%s) produced %d error(s): %s" % (t, len(errs), errs[0][:140]))
    return fails, [], ("%d template node sections all have contracts; schema enum == %d sections; %d graph rules "
                       "<-> validator RULES both ways; verifiedAgainst sequences current; all %d templates "
                       "synthesize cleanly" % (len(used), len(sec_ids), len(graph["rules"]), len(real)))


# ----------------------------------------------------------------------------------- [i]
_CIT = re.compile(r"^([\w./ -]+\.(?:jsx|js|css|json|md|html|py|otf|avif|webp|mp4|svg|png)):(\d+)(?:-(\d+))?$")
_TEXT_CACHE = {}


def _read(path):
    if path not in _TEXT_CACHE:
        with open(path, encoding="utf-8") as f:
            _TEXT_CACHE[path] = f.read()
    return _TEXT_CACHE[path]


def collect_citations():
    """[(json file, source string, owning dict or None)] for every path:line[-line] in every json file."""
    out = []

    def walk(o, f):
        if isinstance(o, dict):
            s = o.get("source")
            if isinstance(s, str) and _CIT.match(s):
                out.append((f, s, o))
            for k, v in o.items():
                if not (k == "source" and isinstance(v, str)):
                    walk(v, f)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, str) and _CIT.match(v):
                    out.append((f, v, None))
                else:
                    walk(v, f)
    for p in json_files():
        with open(p, encoding="utf-8") as fh:
            walk(json.load(fh), rel(p))
    return out


def source_tree_present():
    return (os.path.isdir(os.path.join(SRC_ROOT, "src"))
            and os.path.isfile(os.path.join(SRC_ROOT, "package.json")))


@check("[i] citations")
def c_i():
    allc = collect_citations()
    if not allc:
        return ["no citations found at all (is the ledger empty?)"], [], ""
    selfc = [c for c in allc if c[1].startswith("design-repo/")]
    cits = [c for c in allc if not c[1].startswith("design-repo/")]
    have_src = source_tree_present()
    warns = []
    if not have_src:
        warns.append("the source project is not beside this package, so %d source-tree citations were NOT resolved "
                     "(self-contained mode; a warning, not a failure). Re-run next to the source project to verify "
                     "them." % len(cits))
        cits = []
    fails, ok = [], 0
    for f, s, d in cits + selfc:
        m = _CIT.match(s)
        path, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        fp = (os.path.join(ROOT, path[len("design-repo/"):]) if path.startswith("design-repo/")
              else os.path.join(SRC_ROOT, path))
        if not os.path.isfile(fp):
            fails.append("%s: %s -> that file does not exist" % (f, s))
            continue
        txt = _read(fp)
        lines = txt.split("\n")  # NOT splitlines(): JSX can hold U+2028 / form feed, which editors do not count
        if lines and lines[-1] == "":
            lines.pop()
        if a < 1 or a > b or b > len(lines):
            fails.append("%s: %s is out of range (that file has %d lines)" % (f, s, len(lines)))
            continue
        hay = "\n".join(lines[a - 1:b])
        if d is not None and isinstance(d.get("quote"), str) and d["quote"]:
            q = d["quote"]
            if q not in hay:
                fails.append("%s: %s quote %r is not present at those lines" % (f, s, q[:60]))
                continue
        if d is not None and isinstance(d.get("absenceOf"), str) and d["absenceOf"]:
            # An ABSENCE claim is a real check, not a comment: the named string must NOT be there.
            if d["absenceOf"] in hay:
                fails.append("%s: %s claims absenceOf %r but that string IS present at those lines"
                             % (f, s, d["absenceOf"][:60]))
                continue
        ok += 1
    info = ("%d/%d citations resolve against the real files: line range, stored quote, and absenceOf asserted "
            "in reverse" % (ok, len(cits) + len(selfc)))
    if not have_src:
        info = ("%d/%d resolved (%d point into this package and are always checked); %d source-tree citations skipped"
                % (ok, len(allc), len(selfc), len(allc) - len(selfc)))
    return fails, warns, info


# ----------------------------------------------------------------------------------- [j]
def _role_strings(o, key_hit=False, acc=None, path=""):
    acc = [] if acc is None else acc
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("$ref", "type", "description", "note", "format", "pattern", "title"):
                continue
            _role_strings(v, key_hit or k in ("assetRole", "assetRoles"), acc, path + "/" + k)
    elif isinstance(o, list):
        for v in o:
            _role_strings(v, key_hit, acc, path)
    elif isinstance(o, str) and key_hit:
        acc.append((path, o))
    return acc


@check("[j] asset-roles")
def c_j():
    fails = []
    ar = jload("assets", "asset-roles.json")
    enum, pol = ar["assetRoleEnum"], ar["generationPolicyEnum"]
    if len(enum) != len(set(enum)) or not enum:
        fails.append("assetRoleEnum has duplicates or is empty")
    if ar.get("closed") is not True:
        fails.append("assets/asset-roles.json is not marked closed")
    if len(pol) != len(set(pol)) or not pol:
        fails.append("generationPolicyEnum has duplicates or is empty")
    if set(pol) != set(ar.get("generationPolicyMeaning", {})):
        fails.append("generationPolicyEnum and generationPolicyMeaning do not cover the same values")
    roles = {r["id"]: r for r in ar["roles"]}
    if set(roles) != set(enum) or len(ar["roles"]) != len(enum):
        fails.append("roles[] ids differ from assetRoleEnum")
    pinned_declared = set(ar.get("pinnedRoles", []))
    critical = {i for i, r in roles.items() if r.get("complianceCritical")}
    if pinned_declared != critical:
        fails.append("pinnedRoles %s != the complianceCritical roles %s"
                     % (sorted(pinned_declared ^ critical), sorted(critical)))
    if set(ar.get("unpinnedRoles", [])) != set(enum) - critical:
        fails.append("unpinnedRoles does not complement pinnedRoles over the enum")
    for i, r in sorted(roles.items()):
        if r["generationPolicy"] not in pol:
            fails.append("role %s generationPolicy %r is not in the closed policy set" % (i, r["generationPolicy"]))
        if not r.get("licensing"):
            fails.append("role %s has no licensing guidance" % i)
        if r.get("complianceCritical"):
            # PINNED VALUE, not just enum membership (MASTER-GUIDE 3.23). may-generate-new is a valid
            # enum member that would be wrong for every one of these roles.
            if r.get("pinnedPolicy") not in pol:
                fails.append("PINNED role %s has an invalid pinnedPolicy %r" % (i, r.get("pinnedPolicy")))
            if r["generationPolicy"] != r.get("pinnedPolicy"):
                fails.append("PINNED role %s: generationPolicy %r != pinnedPolicy %r"
                             % (i, r["generationPolicy"], r.get("pinnedPolicy")))
            if r.get("pinnedPolicy") == "may-generate-new":
                fails.append("PINNED role %s is pinned to may-generate-new, which no compliance-critical role may be" % i)
            if r.get("realCompanyAssets") and r["generationPolicy"] not in (
                    "must-not-fabricate", "must-reuse-exact", "must-not-redistribute", "must-not-wire-up"):
                fails.append("PINNED role %s covers real-company assets but its policy permits generation" % i)
        elif "pinnedPolicy" in r and r["pinnedPolicy"] != r["generationPolicy"]:
            fails.append("role %s carries a pinnedPolicy that differs from its generationPolicy" % i)
    # the inert /auth form is the single most compliance-relevant slot: pin it by name
    af = roles.get("auth-inert-form")
    if af is None:
        fails.append("the auth-inert-form behaviour role is missing from the registry")
    else:
        if af.get("generationPolicy") != "must-not-wire-up" or af.get("pinnedPolicy") != "must-not-wire-up":
            fails.append("auth-inert-form must be pinned to must-not-wire-up (found generationPolicy %r, "
                         "pinnedPolicy %r)" % (af.get("generationPolicy"), af.get("pinnedPolicy")))
        if not af.get("complianceCritical"):
            fails.append("auth-inert-form must be complianceCritical")
    tf = roles.get("brand-typeface-file")
    if tf and tf.get("generationPolicy") != "must-not-redistribute":
        fails.append("brand-typeface-file must be pinned to must-not-redistribute (Apple-licensed SF Pro Display)")
    tp = roles.get("trusted-partner-logo")
    if tp and tp.get("generationPolicy") != "must-not-fabricate":
        fails.append("trusted-partner-logo must be pinned to must-not-fabricate (real third-party trademarks)")
    # closure: every role named anywhere in the package is in the enum
    used = set()
    for p in json_files():
        if rel(p) == os.path.join("assets", "asset-roles.json"):
            continue
        with open(p, encoding="utf-8") as fh:
            j = json.load(fh)
        for path, s in _role_strings(j):
            used.add(s)
            if s not in enum:
                fails.append("%s%s: assetRole %r is not in the closed enum" % (rel(p), path, s))

        def enums(o, pth=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "enum" and isinstance(v, list) and any(x in enum for x in v if isinstance(x, str)):
                        for x in v:
                            if x not in enum:
                                fails.append("%s%s: an enum mixes asset roles with the non-role %r" % (rel(p), pth, x))
                    enums(v, pth + "/" + str(k))
            elif isinstance(o, list):
                for v in o:
                    enums(v, pth)
        enums(j)
    sch = jload("schema", "pagespec.schema.json")
    if set(sch["definitions"]["assetRole"]["enum"]) != set(enum):
        fails.append("schema definitions.assetRole enum != assetRoleEnum")
    if not ar.get("globalRules", {}).get("realCompany"):
        fails.append("asset-roles.json has no realCompany licensing rule (the source IS a real live company)")
    return fails, [], ("%d-role enum closed, %d-policy set closed, %d compliance-critical roles PINNED by value "
                       "(generationPolicy == pinnedPolicy, including auth-inert-form -> must-not-wire-up); "
                       "%d roles referenced in contracts and schema are all in the enum"
                       % (len(enum), len(pol), len(critical), len(used)))


# ----------------------------------------------------------------------------------- [k]
@check("[k] token-refs")
def c_k():
    fails, warns, n = [], [], 0
    tiers = token_tiers()
    allids = {i for t in tiers.values() for i in t}
    cat = jload("tokens", "llm", "token-catalog.json")
    pol = jload("tokens", "llm", "token-policy.json")
    if set(pol["rawValueRestrictions"]) != set(cat["categories"]):
        fails.append("token-policy category names differ from the catalog keys (only-policy %s, only-catalog %s)"
                     % (sorted(set(pol["rawValueRestrictions"]) - set(cat["categories"])),
                        sorted(set(cat["categories"]) - set(pol["rawValueRestrictions"]))))
    for tier, toks in tiers.items():
        for i, t in sorted(toks.items()):
            if not isinstance(t, dict):
                continue
            for key in ("$ref", "$refDark", "$refLight"):
                if isinstance(t.get(key), str):
                    n += 1
                    if t[key] not in allids:
                        fails.append("token %s %s -> unknown token %r" % (i, key, t[key]))
            for s in t.get("stops", []):
                n += 1
                if s not in allids:
                    fails.append("token %s gradient stop -> unknown token %r" % (i, s))
    for cname, c in cat["categories"].items():
        for t in c["tokens"]:
            if "resolvesTo" in t:
                n += 1
                if t["resolvesTo"] not in allids:
                    fails.append("catalog %s resolvesTo the unknown token %r" % (t["id"], t["resolvesTo"]))
            if t["id"] not in allids:
                fails.append("catalog lists %r, which is on no disk tier" % t["id"])
    sem = set(tiers["semantic"])
    themes = jload("registry.manifest.json").get("schemaValidatedThemes", [])
    for th in themes:
        tp = os.path.join(ROOT, "tokens", "themes", th + ".json")
        if not os.path.isfile(tp):
            fails.append("schemaValidatedThemes lists %r but tokens/themes/%s.json is missing" % (th, th))
            continue
        res = jload("tokens", "themes", th + ".json")["resolutions"]
        for i, r in sorted(res.items()):
            n += 1
            if r.get("resolvesTo") not in allids:
                fails.append("theme %s: %s resolvesTo the unknown token %r" % (th, i, r.get("resolvesTo")))
        for i in sorted(sem - set(res)):
            fails.append("theme %s does not resolve the semantic token %s" % (th, i))
        for i in sorted(set(res) - sem):
            fails.append("theme %s resolves %s, which is not a semantic token" % (th, i))
    for i, (kind, f) in sorted(contract_ids().items()):
        with open(f, encoding="utf-8") as fh:
            tk = json.load(fh).get("tokens")
        for v in (tk if isinstance(tk, list) else []):
            n += 1
            if not isinstance(v, str) or v not in allids:
                fails.append("%s: the token reference %r does not exist" % (rel(f), v))
    led = {c["id"] for c in jload("extraction", "measured-values.json")["citations"]}
    for p in json_files():
        if rel(p).startswith("extraction"):
            continue
        with open(p, encoding="utf-8") as fh:
            j = json.load(fh)

        def chk(path, s, p=p):
            for m in re.findall(r"\bcit-[A-Za-z0-9-]*[A-Za-z0-9](?![-*A-Za-z0-9])", s):
                if m not in led:
                    fails.append("%s%s: evidence id %s is not in the citation ledger" % (rel(p), path, m))
        walk_strings(j, chk)
    # colour provenance: every foundation colour literal must really appear in the real source.
    # This needs the real STYLESHEET, not merely a src/ directory - a standalone copy of this package
    # can sit next to an unrelated src/ tree, and so can prove_drift.py's synthetic probe tree.
    if os.path.isfile(os.path.join(SRC_ROOT, "src", "styles", "fourmula-base.css")):
        hay = ""
        for rp in ("src/styles/fourmula-base.css", "src/styles/fourmula-head.css",
                   "src/components/Footer.jsx", "index.html"):
            fp = os.path.join(SRC_ROOT, rp)
            if os.path.isfile(fp):
                hay += open(fp, encoding="utf-8").read().lower()
        for mp in sorted(glob.glob(os.path.join(SRC_ROOT, "public", "motion", "*.js"))):
            hay += open(mp, encoding="utf-8").read().lower()
        nc = 0
        for i, t in sorted(tiers["foundation"].items()):
            if not i.startswith("color.") or not isinstance(t, dict):
                continue
            v = str(t.get("$value", "")).strip().lower()
            if not v:
                continue
            nc += 1
            if v not in hay:
                fails.append("colour provenance: %s = %r does not appear in the real source" % (i, v))
        n += nc
    else:
        warns.append("colour provenance NOT checked: src/styles/fourmula-base.css is not beside this package "
                     "(self-contained mode, not a failure)")
    return fails, warns, ("%d token / theme / catalog / contract / colour-provenance references resolve; policy "
                          "categories == %d catalog keys; theme(s) %s each resolve all %d semantic roles exactly; "
                          "every cit- id resolves in the ledger"
                          % (n, len(cat["categories"]), ",".join(themes), len(sem)))


# ----------------------------------------------------------------------------------- [l]
@check("[l] no-absolute-paths")
def c_l():
    fails, n = [], 0
    for p in all_files():
        n += 1
        try:
            t = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        for pat in _ABS_PATTERNS:
            m = pat.search(t)
            if m:
                line = t.count("\n", 0, m.start()) + 1
                fails.append("%s:%d contains a machine-local absolute path (%s)"
                             % (rel(p), line, t[m.start():m.start() + 26].replace("\n", " ")))
                break
    return fails, [], "no machine-local absolute paths in %d shipped files" % n


# ----------------------------------------------------------------------------------- [m]
_DOC_PATH = re.compile(r"(?<![\w/.-])((?:[A-Za-z0-9_-]+/)+[A-Za-z0-9_.-]+\.(?:py|json|md|sh))\b")
_DOC_BARE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_-]+\.(?:py|sh))\b")
_EXTERNAL = ("src/", "public/", "tools/", "dist/", "node_modules/", "assets/fonts/", "assets/video/")


def python_doc_text(src):
    import ast
    import io
    import tokenize
    parts = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d:
                parts.append(d)
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            parts.append(tok.string)
    return "\n".join(parts)


@check("[m] entrypoints-docs")
def c_m():
    fails = []
    man = jload("registry.manifest.json")
    eps = man.get("entryPoints")
    if not eps:
        return ["the manifest has no entryPoints"], [], ""
    flat = []

    def collect(o):
        if isinstance(o, str):
            flat.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(eps)
    files = [rel(p) for p in all_files()]
    for e in flat:
        if os.path.isabs(e) or ".." in e.replace("\\", "/").split("/") or e.startswith(("~", "./..")):
            fails.append("entryPoint %r is absolute or contains `..` - an entry point is a promise about THIS "
                         "package's own contents" % e)
            continue
        target = os.path.normpath(os.path.join(ROOT, e))
        if not (target == ROOT or target.startswith(ROOT + os.sep)):
            fails.append("entryPoint %r resolves outside the package" % e)
        elif not os.path.exists(target):
            fails.append("entryPoint %r does not exist inside the package" % e)
    norm = [os.path.normpath(e) for e in flat]
    for f in files:
        if not any(f == e or f.startswith(e.rstrip("/") + os.sep) for e in norm):
            fails.append("shipped file %s is covered by no entryPoint" % f)
    basenames = {os.path.basename(f) for f in files}
    for p in [x for x in all_files() if x.endswith((".md", ".py", ".json"))]:
        t = open(p, encoding="utf-8").read()
        if p.endswith(".py"):
            t = python_doc_text(t)
        for m in _DOC_PATH.finditer(t):
            d = m.group(1)
            if d.startswith("design-repo/"):
                d = d[len("design-repo/"):]
            if d.startswith(_EXTERNAL) or "*" in d or "<" in d:
                continue
            if not os.path.exists(os.path.join(ROOT, d)):
                fails.append("%s documents %s but no such file is shipped" % (rel(p), d))
        for m in _DOC_BARE.finditer(t):
            if m.group(1) not in basenames and not re.search(r"(?:\w+/)" + re.escape(m.group(1)), t):
                fails.append("%s mentions the script %s but no such file is shipped" % (rel(p), m.group(1)))
    return fails, [], ("%d entryPoints all exist inside the package with no `..` and cover all %d files; every file "
                       "any doc or docstring claims exists really does" % (len(flat), len(files)))


# ----------------------------------------------------------------------------------- [n]
@check("[n] version-note")
def c_n():
    fails = []
    man = jload("registry.manifest.json")
    note = man.get("versionFieldNote")
    if not isinstance(note, str) or len(note) < 60:
        return ["manifest.versionFieldNote is missing or too short"], [], ""
    low = note.lower()
    for f in ("allowlistVersion", "repositoryVersion", "pageSpecVersion"):
        if f not in note:
            fails.append("versionFieldNote does not mention %s" % f)
        if f not in man:
            fails.append("the manifest has no %s field" % f)
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(man.get(f, ""))):
            fails.append("%s is not semver: %r" % (f, man.get(f)))
    if "machine" not in low or "documentation" not in low:
        fails.append("versionFieldNote must say which fields are machine-checked and which are documentation-only")
    if not re.search(r"allowlistVersion[^.;]*machine", note, re.I):
        fails.append("versionFieldNote must state that allowlistVersion is machine-checked")
    if not re.search(r"(repositoryVersion|pageSpecVersion)[^.;]*documentation", note, re.I):
        fails.append("versionFieldNote must state that repositoryVersion/pageSpecVersion are documentation-only")
    if man.get("status") != "design-review-pending" or man.get("productionApproved") is not False:
        fails.append("the manifest status must be design-review-pending with productionApproved false")
    if not man.get("repositoryId"):
        fails.append("the manifest has no repositoryId")
    if not man.get("defaultTheme") or not man.get("schemaValidatedThemes"):
        fails.append("the manifest has no real theme declaration")
    return fails, [], ("versionFieldNote separates machine-checked (allowlistVersion) from documentation-only "
                       "(repositoryVersion, pageSpecVersion); status design-review-pending, productionApproved false")


# ----------------------------------------------------------------------------------- [o]
LEVELS = {"measured", "measured-scaffolding-placeholder-prose", "composed-not-measured"}


@check("[o] evidence-levels")
def c_o():
    fails = []
    tdoc = jload("templates", "templates.json")
    tpls = tdoc["templates"]
    led = jload("extraction", "measured-values.json")
    if set(tdoc.get("evidenceLevels", {})) - {"rule"} != LEVELS:
        fails.append("templates.json evidenceLevels keys differ from the closed set %s" % sorted(LEVELS))
    if set(led.get("evidenceLevels", {})) - {"rule"} != LEVELS:
        fails.append("measured-values.json evidenceLevels keys differ from the closed set %s" % sorted(LEVELS))
    per = led.get("perRouteEvidence", {})
    served = {r: t["id"] for t in tpls for r in t["routes"]}
    if set(per) != set(served):
        fails.append("perRouteEvidence routes differ from the real routes (only-ledger %s, only-templates %s)"
                     % (sorted(set(per) - set(served)), sorted(set(served) - set(per))))
    for t in tpls:
        lvl = t.get("evidenceLevel")
        if lvl not in LEVELS:
            fails.append("template %s has evidenceLevel %r, which is not in the closed set" % (t["id"], lvl))
        if not t.get("evidence"):
            fails.append("template %s has no evidence prose" % t["id"])
        for r in t["routes"]:
            if per.get(r, {}).get("evidenceLevel") != lvl:
                fails.append("route %s: the ledger says evidenceLevel %r but its template %s says %r"
                             % (r, per.get(r, {}).get("evidenceLevel"), t["id"], lvl))
            if per.get(r, {}).get("template") != t["id"]:
                fails.append("route %s: the ledger binds it to template %r, templates.json says %r"
                             % (r, per.get(r, {}).get("template"), t["id"]))
    # a composed route must never be described as measured anywhere in the package
    composed = sorted(r for r, v in per.items() if v.get("evidenceLevel") == "composed-not-measured")
    for t in tpls:
        if t.get("evidenceLevel") == "composed-not-measured":
            if "COMPOSED, NOT MEASURED" not in (t.get("evidence") or ""):
                fails.append("template %s is composed-not-measured but its evidence prose does not say so plainly"
                             % t["id"])
    # the content.tech contract must keep a per-variant evidence level, never one flattened level
    ct = os.path.join(ROOT, "sections", "content-tech.json")
    if os.path.isfile(ct):
        d = json.load(open(ct, encoding="utf-8"))
        pv = d.get("evidence", {}).get("perVariant", {})
        if set(pv) != set(d.get("variants", {})):
            fails.append("content.tech evidence.perVariant does not cover exactly its declared variants")
        for v, meta in d.get("variants", {}).items():
            if meta.get("evidenceLevel") not in LEVELS:
                fails.append("content.tech variant %s has evidenceLevel %r" % (v, meta.get("evidenceLevel")))
    return fails, [], ("%d templates and %d routes all carry an evidence level from the closed 3-value set; the "
                       "ledger and templates.json agree route by route; the %d composed-not-measured route(s) %s "
                       "are labelled plainly and never flattened"
                       % (len(tpls), len(served), len(composed), composed))


# ----------------------------------------------------------------------------------- [p]
def _max_fill(sch):
    """Upper bound of a content schema's running word total: every budgeted field at its maxWords,
    every array at its maxItems. Fields marked countsTowardTotal:false are excluded, as the
    validator excludes them."""
    if not isinstance(sch, dict):
        return 0
    if "oneOf" in sch:
        return max(_max_fill(b) for b in sch["oneOf"])
    t = sch.get("type")
    if t == "string":
        return 0 if sch.get("countsTowardTotal") is False else sch.get("maxWords", 0)
    if t == "array":
        return sch.get("maxItems", 0) * _max_fill(sch.get("items", {}))
    if t == "object":
        return sum(_max_fill(v) for v in sch.get("properties", {}).values())
    return 0


def _unbudgeted_strings(sch, path, out):
    """Text-bearing fields with no maxWords and no enum/const - a budget hole."""
    if not isinstance(sch, dict):
        return
    if "oneOf" in sch:
        for i, b in enumerate(sch["oneOf"]):
            _unbudgeted_strings(b, "%s/oneOf[%d]" % (path, i), out)
        return
    t = sch.get("type")
    if t == "string":
        if not any(k in sch for k in ("maxWords", "enum", "const", "pattern", "format")):
            out.append(path)
    elif t == "array":
        _unbudgeted_strings(sch.get("items", {}), path + "[]", out)
    elif t == "object":
        for k, v in sch.get("properties", {}).items():
            _unbudgeted_strings(v, path + "." + k, out)


@check("[p] word-budgets")
def c_p():
    fails, warns = [], []
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    repo = sv.load_repo(ROOT)
    ex = jload("schema", "example.pagespec.json")
    n_caps = 0
    for sid, ct in sorted(repo["contracts"].items()):
        cap = ct.get("contentMaxWordsTotal")
        mf = _max_fill(ct["content"])
        if cap is not None:
            n_caps += 1
            if cap >= mf:
                fails.append("%s: contentMaxWordsTotal %d is VACUOUS - the per-field budgets cannot exceed %d, so "
                             "this cap can never reject anything" % (sid, cap, mf))
        elif "contentMaxWordsTotalNote" not in ct:
            fails.append("%s declares no contentMaxWordsTotal and no note explaining why" % sid)
        holes = []
        _unbudgeted_strings(ct["content"], sid, holes)
        allowed = ct.get("unbudgetedFields", [])
        for h in holes:
            if h not in allowed:
                fails.append("%s: text field %s has no maxWords and is not listed in unbudgetedFields" % (sid, h))
    # the shipped example must sit under every cap, with headroom, not scrape it
    for i, n in enumerate(ex["nodes"]):
        ct = repo["contracts"][n["type"]]
        cap = ct.get("contentMaxWordsTotal")
        if cap is None:
            continue
        out, tot = [], [0]
        sv._walk(n["content"], ct["content"], "x", repo, out, tot)
        if tot[0] > cap:
            fails.append("the example node %d (%s) totals %d words, over its cap of %d" % (i, n["type"], tot[0], cap))
        elif tot[0] == cap:
            warns.append("the example node %d (%s) sits exactly on its cap of %d with no headroom"
                         % (i, n["type"], cap))
    return fails, warns, ("all %d declared contentMaxWordsTotal caps are reachable (strictly below their own "
                          "per-field maximum); every text field is budgeted or explicitly exempted; the example "
                          "sits under every cap" % n_caps)


# ----------------------------------------------------------------------------------- [q]
@check("[q] wrapper-gate")
def c_q():
    script = os.path.join(ROOT, "extraction", "wrapper_gate.py")
    if not os.path.isfile(script):
        return ["extraction/wrapper_gate.py is missing"], [], ""
    sys.path.insert(0, os.path.join(ROOT, "extraction"))
    import importlib
    import wrapper_gate as wg
    importlib.reload(wg)
    if (wg.HERO_WARN_PX, wg.HERO_ERROR_PX, wg.SHARE_WARN, wg.SHARE_ERROR, wg.MIN_IN_FLOW, wg.VIEWPORT_WIDTH) != (
            1800, 3000, 0.50, 0.60, 3, 1440):
        return ["wrapper_gate thresholds are not the pinned 1800/3000px, 50%/60%, 3 in-flow, 1440px"], [], ""
    errors, warnings, n = wg.run(ROOT)
    return errors, warnings, ("%d measured section heights gated at 1440px: 0 HERO > 3000px, 0 single-section "
                              "share > 60%%, no missing measurement, whitelist clean" % n)


# ----------------------------------------------------------------------------------- [r]
@check("[r] policy-binding")
def c_r():
    fails = []
    man = jload("registry.manifest.json")
    dp = man.get("designPolicy")
    if not man.get("category"):
        fails.append("the manifest has no category")
    if not isinstance(dp, dict):
        return fails + ["the manifest has no designPolicy binding"], [], ""
    for k in ("ref", "policyId", "policyVersion", "commonIrVersion", "enforcementMode", "contentHash"):
        if not dp.get(k):
            fails.append("designPolicy.%s is missing" % k)
    if dp.get("commonIrVersion") != "0.5" or dp.get("enforcementMode") != "hard-and-soft":
        fails.append("designPolicy must bind commonIrVersion 0.5 with enforcementMode hard-and-soft")
    ref = os.path.join(ROOT, str(dp.get("ref", "")))
    if not os.path.isfile(ref):
        return fails + ["designPolicy.ref %r does not exist inside the package" % dp.get("ref")], [], ""
    pol = jload(*dp["ref"].split("/"))
    for k in ("policyId", "policyVersion", "commonIrVersion"):
        if pol.get(k) != dp.get(k):
            fails.append("designPolicy.%s %r != %s's %r" % (k, dp.get(k), dp["ref"], pol.get(k)))
    cl = pol.get("classification", {})
    saas = cl.get("isSaaS")
    if saas is True and (dp.get("policyId") != "n0-saas-design-constraints-common" or dp.get("policyVersion") != "0.1.0"):
        fails.append("a SaaS classification must bind n0-saas-design-constraints-common 0.1.0")
    if saas is False and (dp.get("policyId") == "n0-saas-design-constraints-common"
                          or "n0-saas-design-constraints-common" not in pol.get("notBoundTo", {})):
        fails.append("a non-SaaS classification must NOT bind the SaaS policy and must say so in notBoundTo")
    if saas is not None and cl.get("productCategory") != man.get("category"):
        fails.append("manifest category %r != policy productCategory %r" % (man.get("category"), cl.get("productCategory")))
    if len(cl.get("evidence", [])) < 3:
        fails.append("the classification needs at least 3 pieces of cited evidence")
    ap = pol.get("approval", {})
    if ap.get("policyDecision") != "defined-pending-architecture-review" or ap.get("architectureDecisionRecorded") is not False:
        fails.append("policy approval must stay defined-pending-architecture-review / architectureDecisionRecorded false")
    eb = pol.get("enforcedBy", [])
    missing = [f for f in eb if not os.path.isfile(os.path.join(ROOT, f))]
    if missing or not eb:
        fails.append("policy enforcedBy files missing: %s" % (missing or "none listed"))
    elif policy_hash(ROOT, eb) != dp.get("contentHash"):
        fails.append("designPolicy.contentHash %s != recomputed %s over %d enforcedBy files"
                     % (dp.get("contentHash"), policy_hash(ROOT, eb), len(eb)))
    return fails, [], ("category %s bound to %s %s (commonIr 0.5, hard-and-soft); %s present; contentHash matches %d "
                       "enforcedBy files" % (man.get("category"), dp.get("policyId"), dp.get("policyVersion"),
                                             dp.get("ref"), len(eb)))


# ----------------------------------------------------------------------------------- [s]
@check("[s] provenance")
def c_s():
    from jsonschema import Draft7Validator
    fails, n = [], 0
    sch = jload("schema", "section-contract.schema.json")
    Draft7Validator.check_schema(sch)
    if sch.get("additionalProperties") is not False:
        fails.append("schema/section-contract.schema.json is not closed")
    v = Draft7Validator(sch)
    have_src = os.path.isfile(os.path.join(SRC_ROOT, "src", "App.jsx"))
    for f in contract_files()["sections"]:
        d = json.load(open(f, encoding="utf-8"))
        for e in list(v.iter_errors(d))[:3]:
            fails.append("%s: %s at %s" % (rel(f), e.message[:140], "/".join(map(str, e.absolute_path))))
        src, sem = d.get("source") or {}, d.get("semantic") or {}
        if sem.get("id") != d.get("id") or sem.get("category") != d.get("category"):
            fails.append("%s: semantic {id, category} must equal the contract's id and category" % rel(f))
        if src.get("id") == d.get("id"):
            fails.append("%s: source.id must not equal the contract id (provenance is not taxonomy)" % rel(f))
        if have_src and src.get("file"):
            fp = os.path.join(SRC_ROOT, src["file"])
            m = re.match(r"^(\d+)-(\d+)$", str(src.get("lines", "")))
            if not os.path.isfile(fp) or not m:
                fails.append("%s: source %s:%s does not resolve" % (rel(f), src.get("file"), src.get("lines")))
                continue
            lines = _read(fp).split("\n")
            a, b = int(m.group(1)), int(m.group(2))
            if not (1 <= a <= b <= len(lines)) or src.get("tag", "\0") not in lines[a - 1]:
                fails.append("%s: tag %r is not on line %d of %s" % (rel(f), src.get("tag"), a, src["file"]))
            n += 1
    warns = []
    if have_src:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "extraction", "build_provenance.py"), "--check"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails.append("build_provenance.py --check: %s" % (r.stdout.strip().splitlines() or ["?"])[0][:200])
    else:
        warns.append("source ranges NOT re-read: the source project is not beside this package (self-contained mode)")
    return fails, warns, ("%d section contracts valid against the closed section-contract schema; semantic.id == id, "
                          "source.id != id; %d source tags found on their cited line" % (
                              len(contract_files()["sections"]), n))


# ----------------------------------------------------------------------------------- [t]
@check("[t] retrieval-pin")
def c_t():
    fails = []
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    if set(sv.RETRIEVAL_INELIGIBLE) != RETRIEVAL_INELIGIBLE:
        fails.append("semantic_validate.RETRIEVAL_INELIGIBLE %s != verify_all's pin %s"
                     % (sorted(sv.RETRIEVAL_INELIGIBLE), sorted(RETRIEVAL_INELIGIBLE)))
    false_set = set()
    for f in contract_files()["sections"]:
        d = json.load(open(f, encoding="utf-8"))
        if not isinstance(d.get("retrievalEligible"), bool):
            fails.append("%s: retrievalEligible is not a closed boolean" % rel(f))
        if d.get("retrievalEligible") is False:
            false_set.add(d["id"])
            if len(str(d.get("retrievalReason", ""))) < 30:
                fails.append("%s: retrievalEligible false needs a 30+ character retrievalReason" % rel(f))
        if RUNTIME_UI_RE.search(d["id"]) and d["id"] not in RETRIEVAL_INELIGIBLE:
            fails.append("%s looks like runtime UI but is not in the RETRIEVAL_INELIGIBLE pin" % d["id"])
    if false_set != RETRIEVAL_INELIGIBLE:
        fails.append("contracts' retrievalEligible:false set %s != the pin %s" % (sorted(false_set), sorted(RETRIEVAL_INELIGIBLE)))
    al = set(jload("tokens", "llm", "component-allowlist.json").get("retrievalIneligible", []))
    if al != RETRIEVAL_INELIGIBLE:
        fails.append("allowlist retrievalIneligible %s != the pin %s" % (sorted(al), sorted(RETRIEVAL_INELIGIBLE)))
    return fails, [], ("%d runtime-UI sections pinned retrievalEligible:false in both validators, every contract and "
                       "the allowlist agree" % len(RETRIEVAL_INELIGIBLE))


# ----------------------------------------------------------------------------------- [u]
@check("[u] availability-pin")
def c_u():
    fails = []
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    ar = jload("assets", "asset-roles.json")
    roles = {r["id"]: r for r in ar["roles"]}
    if sv.PINNED_AVAILABILITY != PINNED_AVAILABILITY:
        fails.append("semantic_validate.PINNED_AVAILABILITY differs from verify_all's pin")
    if set(ar.get("availabilityEnum", [])) != {"clone-only", "generation-safe", "blocked-for-generation"}:
        fails.append("availabilityEnum is not the closed {clone-only, generation-safe, blocked-for-generation}")
    for rid in sorted(set(roles) | set(PINNED_AVAILABILITY)):
        r = roles.get(rid, {})
        if r.get("availability") != PINNED_AVAILABILITY.get(rid):
            fails.append("role %s availability %r != pinned %r" % (rid, r.get("availability"), PINNED_AVAILABILITY.get(rid)))
        if not r:
            continue
        if not r.get("generatedModeGuidance"):
            fails.append("role %s has no generatedModeGuidance" % rid)
        subs = r.get("generationSafeSubstitutes")
        if not isinstance(subs, list):
            fails.append("role %s has no generationSafeSubstitutes list" % rid)
            continue
        bad = [x for x in subs if PINNED_AVAILABILITY.get(x) != "generation-safe"]
        if bad:
            fails.append("role %s lists substitutes that are not generation-safe: %s" % (rid, bad))
        if r.get("availability") != "generation-safe" and not subs and len(r.get("noSubstituteReason", "")) < 30:
            fails.append("role %s is not generation-safe but has no substitute and no noSubstituteReason" % rid)
        if r.get("availability") != "generation-safe" and r.get("generationPolicy") == "may-generate-new":
            fails.append("role %s is %s but its policy is may-generate-new" % (rid, r.get("availability")))
    for rid in ("brand-wordmark", "favicon", "trusted-partner-logo", "third-party-award-badge"):
        if PINNED_AVAILABILITY.get(rid) == "generation-safe":
            fails.append("a real logo/wordmark/award role (%s) can never be generation-safe" % rid)
    need = {"placeholder-brand-mark", "user-supplied-asset", "generated-illustration", "placeholder-screenshot",
            "fictional-person-avatar", "placeholder-customer-logo", "placeholder-url", "original-copy"}
    if need - set(roles):
        fails.append("missing generation-safe roles: %s" % sorted(need - set(roles)))

    def slot_roles(o, acc):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "assetRole" and isinstance(v, dict) and "enum" in v:
                    acc.update(v["enum"])
                else:
                    slot_roles(v, acc)
        elif isinstance(o, list):
            for v in o:
                slot_roles(v, acc)
    for f in contract_files()["sections"]:
        d = json.load(open(f, encoding="utf-8"))
        acc = set()
        slot_roles(d["content"], acc)
        g = d.get("generatedAssetRoles")
        if not isinstance(g, list):
            fails.append("%s has no generatedAssetRoles" % rel(f))
            continue
        if set(g) != {x for x in acc if PINNED_AVAILABILITY.get(x) == "generation-safe"}:
            fails.append("%s generatedAssetRoles %s != the generation-safe roles its slots admit" % (rel(f), g))
        for x in acc:
            if PINNED_AVAILABILITY.get(x) != "generation-safe" and not (set(roles[x]["generationSafeSubstitutes"]) & acc) \
                    and roles[x]["generationSafeSubstitutes"]:
                fails.append("%s: slot admits %s but none of its generation-safe substitutes" % (rel(f), x))
    return fails, [], ("%d roles: availability pinned in BOTH validators == registry; every clone-only / blocked role "
                       "has generation-safe substitutes wired into its slots; no real mark is generation-safe"
                       % len(roles))


# ----------------------------------------------------------------------------------- [v]
@check("[v] generation-mode")
def c_v():
    fails, warns = [], []
    sch = jload("schema", "pagespec.schema.json")
    if sch["properties"].get("mode", {}).get("enum") != ["clone", "generation"] or "mode" not in sch.get("required", []):
        fails.append("the PageSpec schema must REQUIRE a closed mode enum [clone, generation]")
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    tpls = {t["id"] for t in jload("templates", "templates.json")["templates"]}
    gen, clone = {}, 0
    for fp in example_files():
        d = json.load(open(fp, encoding="utf-8"))
        if d.get("mode") == "generation":
            gen[d.get("template")] = fp
        elif d.get("mode") == "clone":
            clone += 1
    if set(gen) != tpls:
        fails.append("generation examples cover %s, templates are %s" % (sorted(gen), sorted(tpls)))
    if not clone:
        fails.append("no clone-mode example PageSpec (clone mode must still validate real content)")
    led = jload("schema", "generation-leakage.json")
    cats = led.get("categories", {})
    for c in GENERATION_CATEGORIES:
        if c not in cats:
            fails.append("leakage registry has no %s category" % c)
        elif c not in sv.RULES:
            fails.append("%s has no validator implementation" % c)
    for c, d in cats.items():
        for t in d.get("terms", []) + d.get("hosts", []):
            if not t.get("evidence"):
                fails.append("%s term %r carries no file:line evidence" % (c, t.get("term") or t.get("host")))
    if not cats.get("GENERATION_MODE_COPY", {}).get("shingles"):
        fails.append("GENERATION_MODE_COPY has no hashed shingles")
    if fails:
        return fails, warns, ""
    # the clone example must FAIL in generation mode (the rules really fire on real content)
    ex = jload("schema", "example.pagespec.json")
    ex["mode"] = "generation"
    errs, _ = sv.validate(ex, ROOT)
    fired = {c for c in GENERATION_CATEGORIES if any("[%s]" % c in e for e in errs)}
    if fired != set(GENERATION_CATEGORIES):
        fails.append("the real clone content relabelled generation did not trip %s" % sorted(set(GENERATION_CATEGORIES) - fired))
    if os.path.isfile(os.path.join(SRC_ROOT, "src", "App.jsx")):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "extraction", "build_leakage_patterns.py"), "--check"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails.append("build_leakage_patterns.py --check: %s" % r.stdout.strip()[:200])
    else:
        warns.append("leakage registry NOT rebuilt: the source project is not beside this package (self-contained mode)")
    return fails, warns, ("mode required and closed; %d generation examples (one per template) and %d clone example(s) "
                          "pass; all 9 GENERATION_MODE_* categories carry evidence and fire on the real content; "
                          "registry rebuilds identically from source" % (len(gen), clone))


# ----------------------------------------------------------------------------------- [w]
@check("[w] token-registration")
def c_w():
    fails = []
    man = jload("registry.manifest.json")
    eps = json.dumps(man.get("entryPoints", {}))
    for f in ("tokens/llm/token-catalog.json", "tokens/llm/token-policy.json", "tokens/00-foundation/motion-patterns.json",
              "tokens/llm/component-allowlist.json"):
        if f not in eps:
            fails.append("%s is not registered in registry.manifest.json entryPoints" % f)
    reg = man.get("tokenRegistration", {})
    cat = jload("tokens", "llm", "token-catalog.json")
    if reg.get("catalogEntries") != sum(len(v["tokens"]) for v in cat["categories"].values()):
        fails.append("manifest tokenRegistration.catalogEntries != the catalog")
    for name, c in cat["categories"].items():
        fp = os.path.join(ROOT, c.get("sourceFile", ""))
        if not os.path.isfile(fp):
            fails.append("catalog category %s sourceFile %r is missing" % (name, c.get("sourceFile")))
            continue
        ids = set(json.load(open(fp, encoding="utf-8")).get("tokens", {}))
        mine = {t["id"] for t in c["tokens"]}
        if not mine <= ids:
            fails.append("catalog category %s lists ids not in %s: %s" % (name, c["sourceFile"], sorted(mine - ids)[:4]))
    mp = jload("tokens", "00-foundation", "motion-patterns.json")["patterns"]
    real = {}
    for f in contract_files()["sections"]:
        d = json.load(open(f, encoding="utf-8"))
        real.setdefault(d["motion"]["pattern"], []).append(d["id"])
    if {k: sorted(v["sections"]) for k, v in mp.items()} != {k: sorted(v) for k, v in real.items()}:
        fails.append("motion-patterns.json drifted from the section contracts")
    if set(mp) != set(jload("schema", "pagespec.schema.json")["definitions"]["motion"]["properties"]["pattern"]["enum"]):
        fails.append("motion-patterns.json != the schema motion.pattern enum")
    pol = json.dumps(jload("tokens", "llm", "token-policy.json"))
    sys.path.insert(0, os.path.join(ROOT, "schema"))
    import semantic_validate as sv
    for rname in TOKEN_RULES:
        if rname not in pol:
            fails.append("token-policy.json does not name the enforced rule %s" % rname)
        if rname not in sv.RULES:
            fails.append("%s is not implemented in semantic_validate.py" % rname)
    return fails, [], ("token catalog (%d entries), token policy, motion patterns (%d) and allowlist registered; every "
                       "catalog category resolves in its sourceFile; %d TOKEN_* rules named in the policy and "
                       "implemented" % (reg.get("catalogEntries", 0), len(mp), len(TOKEN_RULES)))


# ----------------------------------------------------------------------------------- main
def main(argv):
    if "--emit-policy-hash" in argv:
        pol = jload(*jload("registry.manifest.json")["designPolicy"]["ref"].split("/"))
        print(policy_hash(ROOT, pol["enforcedBy"]))
        return 0
    if "--emit-counts" in argv:
        c = compute_counts()
        print(json.dumps(c, indent=2))
        print(counts_block(c))
        return 0
    for run in CHECKS:
        run()
    npass = nfail = nwarn = 0
    for status, name, msg in RESULTS:
        print("%-4s %s%s" % (status, name, (" - " + msg) if msg else ""))
        npass += status == "PASS"
        nfail += status == "FAIL"
        nwarn += status == "WARN"
    failed = len({n for s, n, m in RESULTS if s == "FAIL"})
    print("SUMMARY: %d/%d checks passed, %d failed, %d warning(s)"
          % (len(CHECKS) - failed, len(CHECKS), failed, nwarn))
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
