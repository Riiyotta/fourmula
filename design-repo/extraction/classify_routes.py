#!/usr/bin/env python3
"""classify_routes.py - derives each real route's page-level node list from the SOURCE PROJECT's own JSX.

This is the first-party classifier the template set in templates/templates.json was derived from
(MASTER-GUIDE 3.22: a grouped template's claim of "identical composition" must be checked by running the
real classifier, not by trusting the grouping). It is shipped so the derivation can be re-run and audited.

    python3 extraction/classify_routes.py            print each route's node list and the shape grouping
    python3 extraction/classify_routes.py --check    compare the derivation against templates/templates.json

It reads src/App.jsx, src/layout/Layout.jsx and src/pages/*.jsx from the SIBLING source project. When that
tree is not present (a standalone copy of this package) it prints a notice and exits 0 WITHOUT failing - the
stored derivation in templates/templates.json carries `derivedNodeList` for exactly that case.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.dirname(ROOT)

# Layout.jsx composes global chrome in this fixed order. Each entry is (design-repo section id, Layout flag).
# `None` means the node is unconditional.
CHROME_BEFORE = [("chrome.preloader", "preloader"), ("chrome.cookie-consent", None)]
CHROME_IN_PAGE = [("chrome.header", None), ("chrome.menu", "menu")]
CHROME_AFTER_CONTENT = [("chrome.footer", "footer")]
CHROME_LAST = [("chrome.awards-badge", None)]

# The design-repo section id for each real section class name found in page/component JSX.
CLASS_TO_SECTION = {
    "hero": "hero.home",
    "what": "content.what-intro",
    "ai": "showcase.ai-capabilities",
    "how": "marquee.how-trusted",
    "list": "steps.pinned-list",
    "faq": "faq.accordion",
    "tech": "content.tech",
    "hero__404__wrap": "hero.not-found",
}
# Which content component each page renders, and the file that holds the <section>.
PAGE_FILES = {"Home": None, "Privacy": "PrivacyContent", "Terms": "TermsContent",
              "NotFound": "NotFoundContent", "Start": "Start", "Auth": "Auth"}


def source_present():
    return os.path.isdir(os.path.join(SRC_ROOT, "src", "pages")) and os.path.isfile(os.path.join(SRC_ROOT, "src", "App.jsx"))


def read(*p):
    with open(os.path.join(SRC_ROOT, *p), encoding="utf-8") as f:
        return f.read()


def routes_from_app():
    """[(route, PageComponent)] in App.jsx order. path="*" is recorded as the route id /404."""
    out = []
    for m in re.finditer(r'<Route\s+path="([^"]+)"\s+element=\{<(\w+)\s*/>\}', read("src", "App.jsx")):
        out.append(("/404" if m.group(1) == "*" else m.group(1), m.group(2)))
    return out


def layout_defaults():
    """{flag: bool} from Layout.jsx's own default parameter values."""
    sig = re.search(r"export default function Layout\(\{(.*?)\}\s*\)", read("src", "layout", "Layout.jsx"), re.S).group(1)
    d = {}
    for m in re.finditer(r"(\w+)\s*=\s*(true|false)", sig):
        d[m.group(1)] = m.group(2) == "true"
    return d


def layout_props(page_component):
    """{flag: bool} actually passed by this page, merged over Layout.jsx's defaults."""
    txt = read("src", "pages", page_component + ".jsx")
    m = re.search(r"<Layout\b([^>]*)>", txt, re.S)
    props = dict(layout_defaults())
    if not m:
        return props, None
    attrs = m.group(1)
    for flag in ("preloader", "menu", "footer"):
        if re.search(r"\b" + flag + r"=\{true\}", attrs):
            props[flag] = True
        elif re.search(r"\b" + flag + r"=\{false\}", attrs):
            props[flag] = False
        elif re.search(r"(?<![\w=\"])" + flag + r"(?![\w=])", attrs):
            props[flag] = True   # a bare JSX attribute (e.g. `<Layout preloader>`) means true
    cur = re.search(r'current="([^"]+)"', attrs)
    return props, (cur.group(1) if cur else None)


def content_sections(page_component):
    """The ordered list of design-repo section ids rendered as this page's own content."""
    if page_component == "Home":
        # Home renders one component per content section, in JSX order.
        txt = read("src", "pages", "Home.jsx")
        body = re.search(r"<Layout[^>]*>(.*?)</Layout>", txt, re.S).group(1)
        order = [m.group(1) for m in re.finditer(r"<(\w+)\s*/>", body)]
        comp_file = {c: os.path.join("src", "components", c + ".jsx") for c in order}
        out = []
        for c in order:
            t = read(comp_file[c])
            cls = re.search(r'<section[^>]*className="([^"]+)"', t).group(1).split()[0]
            out.append(CLASS_TO_SECTION[cls])
        return out
    f = PAGE_FILES[page_component]
    t = read("src", "pages", f + ".jsx")
    return [CLASS_TO_SECTION[re.search(r'<section[^>]*className="([^"]+)"', t).group(1).split()[0]]]


def structural_slots(page_component):
    """The STRUCTURAL SLOTS a page's own content fills, which is what decides page shape.

    Two pages that render the same section id are the same shape only if they fill the same slots.
    Raw tag counts are instance content, not shape: /privacy-policy happens to contain two tables and
    /terms-of-service none, but both are the same long-form legal rich-text slot. A <form>, by contrast,
    is a different content contract, so /auth is NOT the same shape as /start.
    """
    f = PAGE_FILES[page_component]
    if f is None:
        return []
    t = read("src", "pages", f + ".jsx")
    n = lambda tag: len(re.findall(r"<%s[\s>/]" % tag, t))
    slots = []
    if n("form") or n("input"):
        slots.append("inertForm")
    if n("h2") >= 5 and n("p") >= 20:
        slots.append("longFormProse")
    if re.search(r'href="#[a-z]', t):
        slots.append("anchorIndex")
    if re.search(r'className="(?:btn-primary|btn-outline)', t):
        slots.append("ctaRow")
    if n("table"):
        slots.append("proseTable")
    return slots


def derive():
    rows = []
    for route, page in routes_from_app():
        props, current = layout_props(page)
        nodes = []
        for sec, flag in CHROME_BEFORE:
            if flag is None or props.get(flag):
                nodes.append(sec)
        for sec, flag in CHROME_IN_PAGE:
            if flag is None or props.get(flag):
                nodes.append(sec)
        nodes.extend(content_sections(page))
        for sec, flag in CHROME_AFTER_CONTENT:
            if flag is None or props.get(flag):
                nodes.append(sec)
        for sec, flag in CHROME_LAST:
            nodes.append(sec)
        rows.append({"route": route, "page": page, "layoutCurrent": current,
                     "layoutFlags": {k: props.get(k) for k in ("preloader", "menu", "footer")},
                     "nodes": nodes, "structuralSlots": structural_slots(page)})
    return rows


def main(argv):
    if not source_present():
        print("classify_routes: the source project is not beside this package, so routes cannot be re-derived.")
        print("                 The stored derivation is templates/templates.json -> derivedNodeList (per template).")
        return 0
    rows = derive()
    print("=== per-route derivation (from the real JSX) ===")
    for r in rows:
        print("%-20s page=%-9s flags=%-46s" % (r["route"], r["page"], r["layoutFlags"]))
        print("    nodes: %s" % " -> ".join(r["nodes"]))
        if r["structuralSlots"]:
            print("    structural slots: %s" % " ".join(r["structuralSlots"]))
    print("\n=== grouping by (node list) alone ===")
    by_nodes = {}
    for r in rows:
        by_nodes.setdefault(tuple(r["nodes"]), []).append(r["route"])
    for k, v in by_nodes.items():
        print("  %-60s %s" % (" -> ".join(k)[:60], v))
    print("\n=== grouping by (node list + structural slots) == the real shape set ===")
    by_both = {}
    for r in rows:
        key = (tuple(r["nodes"]), tuple(sorted(set(r["structuralSlots"]) - {"proseTable"})))
        by_both.setdefault(key, []).append(r["route"])
    for (n, fp), v in by_both.items():
        print("  slots=%-28s nodes=%d  %s" % (",".join(fp) or "-", len(n), v))
    print("\n%d routes, %d shapes by node list alone, %d shapes once structural slots are compared"
          % (len(rows), len(by_nodes), len(by_both)))
    print("proseTable is excluded from the shape key on purpose: /privacy-policy has two tables and")
    print("/terms-of-service none, but both fill the same long-form legal rich-text slot, so a table is")
    print("instance content rather than a different page shape.")
    if "--check" not in argv:
        return 0
    tpl = {t["id"]: t for t in json.load(open(os.path.join(ROOT, "templates", "templates.json")))["templates"]}
    bad = 0
    for r in rows:
        tid = next((t["id"] for t in tpl.values() if r["route"] in t["routes"]), None)
        if tid is None:
            print("FAIL route %s is served by no template" % r["route"]); bad += 1; continue
        want = [n["section"] for n in tpl[tid]["nodes"]]
        if want != r["nodes"]:
            print("FAIL route %s: template %s nodes %s != derived %s" % (r["route"], tid, want, r["nodes"])); bad += 1
        stored = tpl[tid].get("derivedNodeList")
        if stored is not None and stored != r["nodes"]:
            print("FAIL template %s derivedNodeList is stale: %s != %s" % (tid, stored, r["nodes"])); bad += 1
    print("--check: %s" % ("OK - every route's real node list matches its template" if not bad else "%d problem(s)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
