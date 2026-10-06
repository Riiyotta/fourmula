#!/usr/bin/env python3
"""Regenerates schema/pagespec.schema.json from sections/*.json, templates/templates.json and
assets/asset-roles.json. The shipped schema is static JSON; this script exists so it can be
re-derived from the contracts and drift-checked against them.

    python3 extraction/build_pagespec_schema.py            rewrite schema/pagespec.schema.json
    python3 extraction/build_pagespec_schema.py --check     exit 1 if the shipped schema has drifted

Root is derived from this file's location, so it runs from a standalone copy with no siblings.
"""
import copy
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PATH = r"^/(?!/)(?!.*\.\.)[A-Za-z0-9._~@%+()/-]+$"
MAX_FALLBACK_WORDS = 60
# The in-page anchors that really exist in the source, plus the inert hashes.
INERT_HREFS = ["#", "/#", "/#what-is-fourmula", "/#pdp", "/#products", "/#video", "/#list"]
# Annotation keys that are for humans / the semantic validator only. `title` and `description` are
# NOT stripped: they are legal draft-07 annotations and `title` names each oneOf branch. Keys inside a
# `properties` map are PROPERTY NAMES, never schema keywords, so they are never stripped - a content
# contract that really has a property called "note" or "title" must survive into the schema.
STRIP = ("note", "bodyCopy", "countsTowardTotal", "allowEmpty")
NAME_MAPS = ("properties", "patternProperties", "definitions", "dependencies")


def load(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


def conv(node, routes, roles):
    """Turn a contract content fragment into a pure draft-07 fragment."""
    if isinstance(node, list):
        return [conv(x, routes, roles) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k in NAME_MAPS and isinstance(v, dict):
            out[k] = {pk: conv(pv, routes, roles) for pk, pv in v.items()}
            continue
        if k in STRIP:
            continue
        out[k] = conv(v, routes, roles)
    fmt = node.get("format")
    if fmt == "local-asset-path":
        out.pop("format", None)
        out["pattern"] = LOCAL_PATH
    elif fmt == "route-or-inert-hash":
        out.pop("format", None)
        out["enum"] = INERT_HREFS + routes
    if (node.get("type") == "string" and "maxWords" in node and "enum" not in node
            and "const" not in node and not node.get("allowEmpty")):
        out["minLength"] = 1
    return out


def close_asset_roles(node, roles, where):
    """Any *assetRole* property keeps its own subset enum AND must satisfy the global closed enum."""
    if isinstance(node, dict):
        for k in list(node):
            v = node[k]
            if k.lower().endswith("assetrole") and isinstance(v, dict) and "enum" in v:
                bad = [x for x in v["enum"] if x not in roles]
                assert not bad, "%s: assetRole enum has values outside the closed registry: %s" % (where, bad)
                node[k] = {"type": "string",
                           "allOf": [{"$ref": "#/definitions/assetRole"}, {"enum": v["enum"]}]}
            else:
                close_asset_roles(v, roles, where)
    elif isinstance(node, list):
        for x in node:
            close_asset_roles(x, roles, where)


def content_schema(sid, contract, routes, roles):
    c = contract["content"]
    if "oneOf" in c:
        # POLYMORPHIC: a oneOf of FULLY INDEPENDENT closed schemas. Deliberately NOT a shared base
        # plus allOf patches - in draft-07 additionalProperties:false on a shared base is evaluated
        # only against that base's own `properties` and cannot see a sibling branch's additions.
        branches = []
        for b in c["oneOf"]:
            s = conv(copy.deepcopy(b), routes, roles)
            assert s.get("additionalProperties") is False, "%s oneOf branch is not closed" % sid
            assert "properties" in s and "required" in s, "%s oneOf branch is not self-contained" % sid
            branches.append(s)
        return {"oneOf": branches}
    s = conv(copy.deepcopy(c), routes, roles)
    assert s.get("additionalProperties") is False, "%s content is not closed" % sid
    return s


def main():
    tpl = load("templates", "templates.json")["templates"]
    routes = sorted({r for t in tpl for r in t["routes"]})
    ar = load("assets", "asset-roles.json")
    roles = set(ar["assetRoleEnum"])
    secs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "sections", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        secs[d["id"]] = d
    sids = sorted(secs)
    patterns = sorted({d["motion"]["pattern"] for d in secs.values()})

    branches = []
    for sid in sids:
        d = secs[sid]
        cs = content_schema(sid, d, routes, roles)
        close_asset_roles(cs, roles, sid)
        then = {"properties": {"content": cs,
                               "motion": {"properties": {"pattern": {"const": d["motion"]["pattern"]}}}}}
        vkeys = sorted(d["variants"].keys())
        if not vkeys:
            # a section with no variants must not carry one
            then["not"] = {"required": ["variant"]}
        else:
            then["properties"]["variant"] = {"type": "string", "enum": vkeys}
            then["required"] = ["variant"]
        branches.append({"if": {"properties": {"type": {"const": sid}}, "required": ["type"]},
                         "then": then})

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Fourmula PageSpec",
        "description":
            "A generated page: one of the 5 closed templates, one of the 6 closed routes, and an ordered list of "
            "section instances. There is deliberately NO per-instance token or style override field - styling is "
            "owned entirely by the section and component contracts. The non-standard keywords maxWords and "
            "maxWordsTotal are annotations enforced by schema/semantic_validate.py, where a word count is always "
            "len(text.split()). Media use only local absolute paths and the closed assetRole enum from "
            "assets/asset-roles.json; remote, protocol-relative and '..' paths are rejected by pattern. "
            "EVERY length in the underlying token system is a rem on a FLUID root font-size - see "
            "tokens/00-foundation/typography.json before converting anything to px. "
            "Generated from the section contracts by extraction/build_pagespec_schema.py.",
        "type": "object",
        "additionalProperties": False,
        "required": ["pageSpecVersion", "template", "route", "nodes"],
        "properties": {
            "$schema": {"type": "string"},
            "pageSpecVersion": {"const": "1.0.0"},
            "template": {"type": "string", "enum": [t["id"] for t in tpl]},
            "route": {"type": "string", "enum": routes},
            "nodes": {"type": "array", "minItems": 5, "maxItems": 12,
                      "items": {"$ref": "#/definitions/node"},
                      "description": "The real templates range from 5 nodes (not-found) to 12 (home)."},
        },
        "allOf": [{"if": {"properties": {"template": {"const": t["id"]}}, "required": ["template"]},
                   "then": {"properties": {"route": {"enum": t["routes"]}}}} for t in tpl],
        "definitions": {
            "assetRole": {"type": "string", "enum": ar["assetRoleEnum"],
                          "description": "Closed enum from assets/asset-roles.json. One member "
                                         "(auth-inert-form) describes a behaviour slot, not a file."},
            "motion": {
                "type": "object",
                "additionalProperties": False,
                "required": ["pattern", "reducedMotionFallback"],
                "description":
                    "CLOSED to the only fields a real section contract carries per instance: pattern "
                    "(const-locked per section type by the allOf branches below) and reducedMotionFallback. The "
                    "contracts' detailed reveal/marquee/trigger descriptions are owned by the section contract and "
                    "are never restated per instance. additionalProperties is false on purpose: leaving it open "
                    "would let a generated PageSpec smuggle in an invented motion field and still validate.",
                "properties": {
                    "pattern": {"type": "string", "enum": patterns},
                    "reducedMotionFallback": {
                        "type": "string", "minLength": 1, "maxWords": MAX_FALLBACK_WORDS,
                        "description":
                            "REQUIRED on every node. For every section except the background-video slot this is a "
                            "DESIGN RULE prescribed by this repository, not mirrored behaviour: public/motion/m27.js "
                            "is the only script in the whole project that reads prefers-reduced-motion, and no "
                            "stylesheet contains a prefers-reduced-motion rule."},
                    "reducedMotionFallbackKind": {
                        "type": "string",
                        "enum": ["design-rule", "mirrored", "mixed"],
                        "description": "Which of the two the fallback is for this node. Only the background-video "
                                       "slot can honestly claim `mirrored`."},
                },
            },
            "node": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "content", "motion"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
                    "type": {"type": "string", "enum": sids},
                    "variant": {"type": "string"},
                    "content": {"type": "object"},
                    "motion": {"$ref": "#/definitions/motion"},
                },
                "allOf": branches,
            },
        },
    }
    out = json.dumps(schema, indent=1, ensure_ascii=False) + "\n"
    path = os.path.join(ROOT, "schema", "pagespec.schema.json")
    if "--check" in sys.argv:
        cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
        if cur == out:
            print("schema up to date (%d sections, %d templates, %d motion patterns)"
                  % (len(sids), len(tpl), len(patterns)))
            return 0
        print("SCHEMA DRIFT: schema/pagespec.schema.json does not match the contracts")
        return 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote schema/pagespec.schema.json %d bytes; %d sections, %d templates, %d motion patterns"
          % (len(out), len(sids), len(tpl), len(patterns)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
