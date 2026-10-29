#!/usr/bin/env python3
"""build_provenance.py - writes the closed `source` / `semantic` objects of every section contract (R7).

`source` {id, tag, file, lines} says WHAT DOM the contract was read from and is traceable to a real line range;
`semantic` {id, category} is what an AI sees. semantic.id equals the contract id; source.id never does, so a
wrapper or class name can never decide the AI-facing taxonomy.

    python3 extraction/build_provenance.py           rewrite source/semantic in sections/*.json
    python3 extraction/build_provenance.py --check   exit 1 if any contract's source/semantic differs from a rebuild

The line ranges are COMPUTED from the real files (the opening tag's line through its closing tag, or through
the line before the next semantic boundary for the decomposed legal units). Needs the sibling source project;
without it, prints a notice and exits 0 (extraction/verify_all.py check [s] still checks the shape).
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.dirname(ROOT)

# contract id -> (file, opening tag text as it appears in the source, how the range ends)
MAP = {
    "chrome.preloader": ("src/components/Preloader.jsx", '<section className="preloader">', "section"),
    "chrome.cookie-consent": ("src/components/Cookies.jsx", '<section className="cookies">', "section"),
    "chrome.header": ("src/components/Header.jsx", '<section className="header">', "section"),
    "chrome.menu": ("src/components/Menu.jsx", '<section className="menu">', "section"),
    "hero.home": ("src/components/Hero.jsx", '<section id="hero" className="hero">', "section"),
    "content.what-intro": ("src/components/What.jsx", '<section id="what-is-fourmula" className="what">', "section"),
    "showcase.ai-capabilities": ("src/components/AiSection.jsx", '<section className="ai">', "section"),
    "marquee.how-trusted": ("src/components/How.jsx", '<section className="how">', "section"),
    "steps.pinned-list": ("src/components/ListSection.jsx", '<section className="list">', "section"),
    "faq.accordion": ("src/components/Faq.jsx", '<section className="faq">', "section"),
    "chrome.footer": ("src/components/Footer.jsx", '<section className="footer">', "section"),
    "chrome.awards-badge": ("src/components/AwwwardsBadge.jsx", '<div id="awwwards"', "last-div"),
    "hero.not-found": ("src/pages/NotFoundContent.jsx", '<section id="hero" className="hero__404__wrap">', "section"),
    "content.tech": ("src/pages/Start.jsx", '<section className="tech">', "section"),
    "content.legal-header": ("src/pages/PrivacyContent.jsx", '<section className="tech">', "before-first-embed"),
    "content.legal-chapter": ("src/pages/PrivacyContent.jsx", '<div className="w-embed">', "before-next-embed"),
}


def source_present():
    return os.path.isfile(os.path.join(SRC_ROOT, "src", "App.jsx"))


def span(path, tag, how):
    lines = open(os.path.join(SRC_ROOT, path), encoding="utf-8").read().split("\n")
    start = next(i for i, l in enumerate(lines, 1) if tag in l)
    if how == "section":
        end = next(i for i, l in enumerate(lines, 1) if i >= start and "</section>" in l)
    elif how == "last-div":
        end = max(i for i, l in enumerate(lines, 1) if "</div>" in l)
    elif how == "before-first-embed":
        end = next(i for i, l in enumerate(lines, 1) if i > start and '<div className="w-embed">' in l) - 1
    else:
        end = next(i for i, l in enumerate(lines, 1) if i > start and '<div className="w-embed">' in l) - 1
    return start, end


def build(d):
    f, tag, how = MAP[d["id"]]
    a, b = span(f, tag, how)
    stem = os.path.splitext(os.path.basename(f))[0]
    m = re.search(r'className="([^"]+)"|id="([^"]+)"', tag)
    sid = "dom:%s:%s" % (stem, (m.group(1) or m.group(2)).split()[0])
    if how == "before-next-embed":
        sid += ":chapter"
    elif how == "before-first-embed":
        sid += ":header"
    return ({"id": sid, "tag": tag, "file": f, "lines": "%d-%d" % (a, b)},
            {"id": d["id"], "category": d["category"]})


def main(argv):
    if not source_present():
        print("build_provenance: the source project is not beside this package; nothing to rebuild.")
        return 0
    bad = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "sections", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        src, sem = build(d)
        if "--check" in argv:
            if d.get("source") != src or d.get("semantic") != sem:
                print("PROVENANCE DRIFT %s: stored %s / %s, rebuilt %s / %s" % (
                    os.path.basename(p), d.get("source"), d.get("semantic"), src, sem))
                bad += 1
            continue
        out = {}
        for k, v in d.items():
            out[k] = v
            if k == "category":
                out["source"], out["semantic"] = src, sem
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("provenance %s for %d section contracts" % ("checked, %d drift(s)" % bad if "--check" in argv else "written",
                                                      len(glob.glob(os.path.join(ROOT, "sections", "*.json")))))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
