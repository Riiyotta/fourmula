#!/usr/bin/env python3
"""wrapper_gate.py - the automated whole-page-wrapper quality gate (R9). Called by extraction/verify_all.py [q].

Reads MEASURED heights from extraction/measured-values.json -> sectionHeights (recorded from the built clone in
headless Chromium at a 1440px viewport by extraction/measure_sections.mjs) and fails on any section that is
really a whole page in disguise:

  HERO     a hero-category section taller than 1800px warns; taller than 3000px is an error unless whitelisted
  SHARE    one in-flow section holding > 50% of its page warns; > 60% is an error unless whitelisted. Pages with
           fewer than 3 in-flow body sections are skipped; SHELL (chrome.*) is excluded, and fixed / sticky /
           absolute elements take no page height
  MISSING  a template section with no measurement on one of its routes is an error; so is a wrong viewport
  WHITELIST entries need section, route, reviewedBy, a justification of 30+ characters and a maxHeightPx above the
           measured height; stale or over-cap entries are errors, and a whitelisted hit still warns. An agent
           reviewer must say "agent attestation, not a human sign-off".

The thresholds are pinned HERE in code, not only in JSON.

    python3 extraction/wrapper_gate.py      exit 0 when there are no errors
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERO_WARN_PX = 1800
HERO_ERROR_PX = 3000
SHARE_WARN = 0.50
SHARE_ERROR = 0.60
MIN_IN_FLOW = 3
VIEWPORT_WIDTH = 1440
AGENT_PHRASE = "agent attestation, not a human sign-off"


def _instances(m):
    if isinstance(m.get("instances"), list):
        return [x["heightPx"] for x in m["instances"]]
    return [m["heightPx"]]


def gate(sh, templates, contracts):
    """(errors, warnings) for a sectionHeights block against the real templates and contracts."""
    errors, warnings = [], []
    if not isinstance(sh, dict) or not isinstance(sh.get("routes"), dict):
        return ["MISSING: no sectionHeights.routes block - heights must be measured, not assumed"], []
    if (sh.get("viewport") or {}).get("width") != VIEWPORT_WIDTH:
        errors.append("VIEWPORT: sectionHeights measured at %r, the gate requires width %d"
                      % ((sh.get("viewport") or {}).get("width"), VIEWPORT_WIDTH))
    wl = sh.get("whitelist", [])
    used = set()

    def whitelisted(sec, route, h):
        for i, w in enumerate(wl):
            if w.get("section") == sec and w.get("route") == route:
                used.add(i)
                if h > w.get("maxHeightPx", -1):
                    errors.append("WHITELIST: %s on %s measures %dpx, above its whitelisted maxHeightPx %r"
                                  % (sec, route, h, w.get("maxHeightPx")))
                return True
        return False

    for i, w in enumerate(wl):
        if not (isinstance(w.get("reviewedBy"), str) and w["reviewedBy"].strip()):
            errors.append("WHITELIST[%d]: no reviewedBy" % i)
        elif "agent" in w["reviewedBy"].lower() and AGENT_PHRASE not in w["reviewedBy"]:
            errors.append("WHITELIST[%d]: an agent reviewer must say %r" % (i, AGENT_PHRASE))
        if len(str(w.get("justification", "")).strip()) < 30:
            errors.append("WHITELIST[%d]: justification must be at least 30 characters" % i)
        if not isinstance(w.get("maxHeightPx"), (int, float)):
            errors.append("WHITELIST[%d]: no numeric maxHeightPx" % i)
    checked = 0
    for t in templates:
        for route in t["routes"]:
            rm = sh["routes"].get(route)
            if not isinstance(rm, dict) or not isinstance(rm.get("sections"), dict):
                errors.append("MISSING: route %s (template %s) has no measurement" % (route, t["id"]))
                continue
            secs, page = rm["sections"], rm.get("pageHeightPx")
            if not isinstance(page, (int, float)) or page <= 0:
                errors.append("MISSING: route %s has no pageHeightPx" % route)
                continue
            flow = []
            for n in t["nodes"]:
                sec = n["section"]
                m = secs.get(sec)
                if not isinstance(m, dict) or "heightPx" not in m:
                    errors.append("MISSING: %s on %s (template %s) has no measured height" % (sec, route, t["id"]))
                    continue
                checked += 1
                hs = _instances(m)
                if n.get("repeatable"):
                    c = n.get("count") or {}
                    if not c.get("min", 1) <= len(hs) <= c.get("max", 10 ** 6):
                        errors.append("MISSING: %s on %s has %d measured instances, template allows %s"
                                      % (sec, route, len(hs), c))
                if contracts.get(sec, {}).get("category") == "hero":
                    for h in hs:
                        if h > HERO_WARN_PX:
                            wl_ok = whitelisted(sec, route, h)
                            if h > HERO_ERROR_PX and not wl_ok:
                                errors.append("HERO: %s on %s is %dpx (> %dpx) - a hero is the page-opening "
                                              "composition only" % (sec, route, h, HERO_ERROR_PX))
                            else:
                                warnings.append("HERO: %s on %s is %dpx (> %dpx)%s" % (
                                    sec, route, h, HERO_WARN_PX, " [whitelisted]" if wl_ok else ""))
                if not sec.startswith("chrome.") and m.get("inFlow", True):
                    flow.extend((sec, h) for h in hs)
            if len(flow) < MIN_IN_FLOW:
                continue
            for sec, h in flow:
                share = h / float(page)
                if share > SHARE_WARN:
                    wl_ok = whitelisted(sec, route, h)
                    if share > SHARE_ERROR and not wl_ok:
                        errors.append("SHARE: %s holds %.0f%% of %s (%dpx of %dpx) - a whole page in one section"
                                      % (sec, share * 100, route, h, page))
                    else:
                        warnings.append("SHARE: %s holds %.0f%% of %s%s" % (
                            sec, share * 100, route, " [whitelisted]" if wl_ok else ""))
    for i, w in enumerate(wl):
        if i not in used:
            errors.append("WHITELIST[%d]: stale - %s on %s no longer trips the gate or is not measured"
                          % (i, w.get("section"), w.get("route")))
    return errors, warnings, checked


def run(root=ROOT):
    def j(*p):
        with open(os.path.join(root, *p), encoding="utf-8") as f:
            return json.load(f)
    sh = j("extraction", "measured-values.json").get("sectionHeights")
    tpls = j("templates", "templates.json")["templates"]
    contracts = {}
    for fn in sorted(os.listdir(os.path.join(root, "sections"))):
        if fn.endswith(".json"):
            d = j("sections", fn)
            contracts[d["id"]] = d
    out = gate(sh, tpls, contracts)
    return out if len(out) == 3 else (out[0], out[1], 0)


def main():
    errors, warnings, n = run()
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print("wrapper gate: %d measurements checked, %d error(s), %d warning(s) (HERO %d/%dpx, SHARE %d%%/%d%%, "
          "viewport %dpx)" % (n, len(errors), len(warnings), HERO_WARN_PX, HERO_ERROR_PX, SHARE_WARN * 100,
                              SHARE_ERROR * 100, VIEWPORT_WIDTH))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
