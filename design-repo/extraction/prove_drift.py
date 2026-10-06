#!/usr/bin/env python3
"""prove_drift.py - proves that extraction/verify_all.py actually FAILS on bad input.

A check that has never been seen to fail on bad input might not be checking anything, so every check
verify_all.py claims to perform is exercised here by injecting ONE real drift into a scratch copy of
this package and requiring a FAIL line from the intended check.

    python3 extraction/prove_drift.py

Exit code 0 only if (1) a baseline scratch copy passes, (2) EVERY injected drift is caught by the check
it targets, and (3) the real repository still passes verify_all.py afterwards.

Self-contained: the root is derived from this file, and it works with no sibling folders. Citation checks
need a source tree, so with no real source project beside this package the script builds a tiny SYNTHETIC
one, repoints every real source citation at this package's own README, and injects its probes into that.
When the real source project IS present, the real citations are corrupted instead, through read-only
symlinks of the real src/ and public/ into the scratch tree.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_SRC_ROOT = os.path.dirname(ROOT)
# Built by concatenation so this file itself holds no absolute path for check [l] to find.
ABS_PROBE = "/" + "Users" + "/someone/project/file.txt"

PROBE_JSX = "line one\nline two has the quote\nline three\n"
SELF_CIT = "design-repo/README.md:1-1"
_CIT = re.compile(r"^[\w./ -]+\.(?:jsx|js|css|json|md|html|py):\d+(?:-\d+)?$")


def jedit(dst, relp, fn):
    p = os.path.join(dst, *relp.split("/"))
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def tedit(dst, relp, fn):
    p = os.path.join(dst, *relp.split("/"))
    with open(p, encoding="utf-8") as f:
        t = f.read()
    with open(p, "w", encoding="utf-8") as f:
        f.write(fn(t))


def add_probe_citation(d):
    d["citations"].append({"id": "cit-probe-jsx", "source": "src/probe.jsx:2-3",
                           "quote": "line two has the quote", "kind": "declaration",
                           "note": "Synthetic probe used by prove_drift.py."})


def resync_counts(dst):
    """The probe citation changes the real citation count, so bring the manifest and the README
    counts block back in step. Without this the synthetic baseline fails check [f] and every count
    injection below would be 'caught' by the wrong signal."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "verify_all_scratch", os.path.join(dst, "extraction", "verify_all.py"))
    va = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(va)
    c = va.compute_counts()
    jedit(dst, "registry.manifest.json", lambda d: d.update({"counts": c}))
    block = va.counts_block(c)
    tedit(dst, "README.md", lambda t: re.sub(
        r"(<!-- counts:begin -->\n).*?(\n<!-- counts:end -->)",
        lambda mm: mm.group(1) + block + mm.group(2), t, flags=re.S))


def neutralize(dst):
    """Synthetic-source mode only: repoint every real source citation at this package's own README so
    that the ONLY source-tree citation left is the probe (a synthetic tree cannot hold the real files)."""
    def walk(o):
        if isinstance(o, dict):
            s = o.get("source")
            if isinstance(s, str) and _CIT.match(s) and not s.startswith("src/probe"):
                o["source"] = SELF_CIT
                o.pop("quote", None)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str) and _CIT.match(v):
                    o[i] = SELF_CIT
                else:
                    walk(v)
    for d, dirs, files in os.walk(dst):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if not f.endswith(".json"):
                continue
            p = os.path.join(d, f)
            with open(p, encoding="utf-8") as fh:
                j = json.load(fh)
            before = json.dumps(j, sort_keys=True)
            walk(j)
            if json.dumps(j, sort_keys=True) != before:
                with open(p, "w", encoding="utf-8") as fh:
                    json.dump(j, fh, indent=2, ensure_ascii=False)


def scratch(real_sibling=False):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "design-repo")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    with open(os.path.join(tmp, "package.json"), "w") as f:
        f.write("{}")
    if real_sibling:
        for name in ("src", "public", "index.html", "CLONE_SPEC.md"):
            src = os.path.join(REAL_SRC_ROOT, name)
            if os.path.exists(src):
                os.symlink(src, os.path.join(tmp, name))
        shutil.copy(os.path.join(REAL_SRC_ROOT, "package.json"), os.path.join(tmp, "package.json"))
    else:
        os.makedirs(os.path.join(tmp, "src"))
        with open(os.path.join(tmp, "src", "probe.jsx"), "w") as f:
            f.write(PROBE_JSX)
        neutralize(dst)
        jedit(dst, "extraction/measured-values.json", add_probe_citation)
        resync_counts(dst)
    return tmp, dst


def run_verify(dst):
    r = subprocess.run([sys.executable, os.path.join(dst, "extraction", "verify_all.py")],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def first_real_citation(dst, ext=".jsx"):
    """(relative json file, index into measuredFrom) of a real citation that carries a quote."""
    for sub in ("primitives", "components", "sections"):
        for fn in sorted(os.listdir(os.path.join(dst, sub))):
            with open(os.path.join(dst, sub, fn), encoding="utf-8") as f:
                d = json.load(f)
            for i, c in enumerate(d.get("measuredFrom", [])):
                if isinstance(c, dict) and c.get("source", "").split(":")[0].endswith(ext) and c.get("quote"):
                    return "%s/%s" % (sub, fn), i
    raise SystemExit("no real citation with a quote found")


# each case: (label, expected check tag, needs_real_source, injector)
def cases():
    out = []

    def phantom(dst):
        jedit(dst, "tokens/llm/component-allowlist.json",
              lambda d: (d["components"].append("component.ghost-phantom"),
                         d["counts"].update({"components": d["counts"]["components"] + 1,
                                             "total": d["counts"]["total"] + 1})))
    out.append(("(i) phantom allowlist id (listed, no contract file)", "[d]", False, phantom))

    def orphan(dst):
        shutil.copy(os.path.join(dst, "components", "component-faq-item.json"),
                    os.path.join(dst, "components", "component-orphan-extra.json"))
        jedit(dst, "components/component-orphan-extra.json", lambda d: d.update({"id": "component.orphan-extra"}))
    out.append(("(ii) orphan contract (file exists, not in the allowlist)", "[d]", False, orphan))

    def oor(dst):
        jedit(dst, "extraction/measured-values.json",
              lambda d: d["citations"][-1].update({"source": "src/probe.jsx:2-99"}))
    out.append(("(iii) out-of-range citation (synthetic source)", "[i]", False, oor))

    def wrongq(dst):
        jedit(dst, "extraction/measured-values.json",
              lambda d: d["citations"][-1].update({"quote": "text that is not on those lines"}))
    out.append(("(iv) in-range citation with the WRONG quote (synthetic source)", "[i]", False, wrongq))

    def real_oor(dst):
        f, i = first_real_citation(dst)
        jedit(dst, f, lambda d: d["measuredFrom"][i].update(
            {"source": d["measuredFrom"][i]["source"].split(":")[0] + ":99998-99999"}))
    out.append(("(iii-real) out-of-range citation on a REAL source file", "[i]", True, real_oor))

    def real_wrongq(dst):
        f, i = first_real_citation(dst)
        jedit(dst, f, lambda d: d["measuredFrom"][i].update({"quote": "this exact text is not in that file"}))
    out.append(("(iv-real) in-range but WRONG quote on a REAL source file", "[i]", True, real_wrongq))

    def count(dst):
        jedit(dst, "registry.manifest.json",
              lambda d: d["counts"].update({"sections": d["counts"]["sections"] + 1}))
    out.append(("(v) wrong manifest count (sections +1)", "[f]", False, count))

    def tokcount(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["counts"]["tokens"].update({"semantic": 1}))
    out.append(("(v-b) wrong manifest token-tier count", "[f]", False, tokcount))

    def readme_count(dst):
        tedit(dst, "README.md", lambda t: t.replace("Primitives 11", "Primitives 10", 1))
    out.append(("(v-c) README counts block edited by hand", "[f]", False, readme_count))

    def ver(dst):
        jedit(dst, "registry.manifest.json", lambda d: d.update({"allowlistVersion": "9.9.9"}))
    out.append(("(vi) allowlistVersion drift between the manifest and the allowlist", "[e]", False, ver))

    def abspath(dst):
        tedit(dst, "README.md", lambda t: t + "\nSee " + ABS_PROBE + "\n")
    out.append(("(vii) machine-local absolute path in the README", "[l]", False, abspath))

    def unpin(dst):
        def f(d):
            r = next(x for x in d["roles"] if x["complianceCritical"])
            r["generationPolicy"] = "may-generate-new"   # a VALID enum member, wrong for a pinned role
        jedit(dst, "assets/asset-roles.json", f)
    out.append(("(viii) PINNED compliance-critical role set to a DIFFERENT-BUT-VALID policy", "[j]", False, unpin))

    def unpin_form(dst):
        def f(d):
            r = next(x for x in d["roles"] if x["id"] == "auth-inert-form")
            r["generationPolicy"] = "must-reuse-exact"
            r["pinnedPolicy"] = "must-reuse-exact"      # both moved together: an enum check cannot see this
        jedit(dst, "assets/asset-roles.json", f)
    out.append(("(viii-b) PINNED auth-inert-form moved off must-not-wire-up (pinnedPolicy moved too)",
                "[j]", False, unpin_form))

    def badrole(dst):
        jedit(dst, "sections/hero-home.json", lambda d: d.update({"probeRole": {"assetRole": "stock-photo"}}))
    out.append(("(viii-c) an unlisted assetRole used in a contract", "[j]", False, badrole))

    def entry(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["entryPoints"]["docs"].append("../CLONE_SPEC.md"))
    out.append(("(ix) entryPoints entry pointing OUTSIDE the package with ../", "[m]", False, entry))

    def docs(dst):
        tedit(dst, "README.md", lambda t: t + "\nRun `extraction/not_built_script.py` to regenerate things.\n")
    out.append(("(ix-b) a doc claims a script exists that was never built", "[m]", False, docs))

    def routemap(dst):
        jedit(dst, "registry.manifest.json", lambda d: d["routeTemplateMap"].update({"/auth": "legal"}))
    out.append(("(x) a route mapped to the wrong template in the manifest", "[g]", False, routemap))

    def route_dup(dst):
        def f(d):
            t = {x["id"]: x for x in d["templates"]}
            t["home"]["routes"].append("/auth")
        jedit(dst, "templates/templates.json", f)
    out.append(("(xi) a route served by two templates (no longer 1:1)", "[g]", False, route_dup))

    def graph_ghost(dst):
        jedit(dst, "compatibility/graph.json",
              lambda d: d["rules"].append({"id": "GHOST_RULE", "severity": "error",
                                           "description": "x", "exceptions": []}))
    out.append(("(xii) a graph rule id with no validator implementation", "[h]", False, graph_ghost))

    def graph_stale(dst):
        jedit(dst, "compatibility/graph.json",
              lambda d: d["verifiedAgainst"]["sequences"]["home"].append("chrome.footer"))
    out.append(("(xii-b) graph verifiedAgainst sequences gone stale vs templates.json", "[h]", False, graph_stale))

    def tpl_node(dst):
        def f(d):
            t = {x["id"]: x for x in d["templates"]}
            t["legal"]["nodes"].insert(3, {"section": "faq.accordion", "required": True, "repeatable": False})
            t["legal"]["nodeCount"] = len(t["legal"]["nodes"])
        jedit(dst, "templates/templates.json", f)
    out.append(("(xii-c) a home-only section added to the legal template", "[g]", False, tpl_node))

    def note(dst):
        jedit(dst, "registry.manifest.json", lambda d: d.pop("versionFieldNote"))
    out.append(("(xiii) versionFieldNote removed", "[n]", False, note))

    def approved(dst):
        jedit(dst, "registry.manifest.json", lambda d: d.update({"productionApproved": True}))
    out.append(("(xiii-b) productionApproved flipped to true", "[n]", False, approved))

    def policy_cat(dst):
        jedit(dst, "tokens/llm/token-policy.json",
              lambda d: d["rawValueRestrictions"].update(
                  {"shadow": d["rawValueRestrictions"].pop("elevation")}))
    out.append(("(xiv) a policy category renamed to a label that is no catalog key", "[k]", False, policy_cat))

    def theme_gap(dst):
        jedit(dst, "tokens/themes/dark.json",
              lambda d: d["resolutions"].pop(sorted(d["resolutions"])[0]))
    out.append(("(xiv-b) the dark theme stops resolving one semantic role", "[k]", False, theme_gap))

    def bad_cit_id(dst):
        jedit(dst, "sections/hero-home.json",
              lambda d: d["evidence"].update({"probe": "backed by cit-does-not-exist"}))
    out.append(("(xiv-c) a cit- id referenced that is not in the ledger", "[k]", False, bad_cit_id))

    def flatten(dst):
        def f(d):
            for t in d["templates"]:
                t["evidenceLevel"] = "measured"
        jedit(dst, "templates/templates.json", f)
    out.append(("(xv) evidence levels flattened to 'measured' (laundering the composed pages)",
                "[o]", False, flatten))

    def evidence_mismatch(dst):
        jedit(dst, "extraction/measured-values.json",
              lambda d: d["perRouteEvidence"]["/start"].update({"evidenceLevel": "measured"}))
    out.append(("(xv-b) the ledger and templates.json disagree about one route's evidence level",
                "[o]", False, evidence_mismatch))

    def schema_drift(dst):
        jedit(dst, "schema/pagespec.schema.json",
              lambda d: d["definitions"]["motion"].update({"additionalProperties": True}))
    out.append(("(xvi) the motion schema opened up (additionalProperties true)", "[b]", False, schema_drift))

    def schema_stale(dst):
        jedit(dst, "sections/faq-accordion.json",
              lambda d: d["content"]["properties"]["eyebrow"].update({"maxWords": 9}))
    out.append(("(xvi-b) a contract edited without regenerating the schema", "[c]", False, schema_stale))

    def example_break(dst):
        jedit(dst, "schema/example.pagespec.json",
              lambda d: d["nodes"][4]["content"].update({"heading": "far too many words for this budget indeed"}))
    out.append(("(xvi-c) the bundled example pushed over a maxWords budget", "[b]", False, example_break))

    def colour(dst):
        jedit(dst, "tokens/00-foundation/color.json",
              lambda d: d["tokens"]["color.accent-hover"].update({"$value": "#ff6b03"}))
    out.append(("(xvii-real) a foundation colour that does not appear in the real source", "[k]", True, colour))

    return out


def main():
    bad, results = 0, []
    tmp, dst = scratch()
    try:
        rc, out = run_verify(dst)
        ok = rc == 0 and "PASS [i]" in out
        print("%-7s baseline scratch copy (synthetic source tree) passes verify_all: %s"
              % ("OK" if ok else "BROKEN", (out.strip().splitlines() or ["no output"])[-1]))
        bad += not ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    real_present = (os.path.isdir(os.path.join(REAL_SRC_ROOT, "src"))
                    and os.path.isfile(os.path.join(REAL_SRC_ROOT, "package.json")))
    for label, tag, needs_real, inject in cases():
        if needs_real and not real_present:
            print("SKIPPED %s (the real source project is not beside this folder)" % label)
            continue
        tmp, dst = scratch(real_sibling=needs_real)
        try:
            if needs_real:
                rc0, out0 = run_verify(dst)
                if rc0 != 0:
                    print("BROKEN  %s: an unmodified real-sibling scratch copy does not pass:\n%s" % (label, out0))
                    bad += 1
                    continue
            inject(dst)
            rc, out = run_verify(dst)
            lines = [l for l in out.splitlines() if l.startswith("FAIL") and tag in l]
            caught = rc != 0 and bool(lines)
            bad += not caught
            results.append((label, caught))
            print("%-7s %s\n          -> %s"
                  % ("CAUGHT" if caught else "MISSED", label,
                     lines[0][:170] if lines else "verify_all exited %d with no FAIL line for %s" % (rc, tag)))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    rc, out = run_verify(ROOT)
    print("%-7s the REAL repository still passes verify_all: %s"
          % ("OK" if rc == 0 else "FAILED", (out.strip().splitlines() or ["no output"])[-1]))
    bad += rc != 0
    print("SUMMARY: %d/%d injected drifts caught; baseline and real repository %s"
          % (sum(c for _, c in results), len(results), "pass" if not bad else "-- PROBLEMS, see above"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
