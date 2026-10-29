#!/usr/bin/env python3
"""build_leakage_patterns.py - derives schema/generation-leakage.json from the REAL source project.

The generation-mode rules in schema/semantic_validate.py (GENERATION_MODE_BRAND, _ASSET, _PERSON, _CUSTOMER,
_SCREENSHOT, _COPY, _CLAIM, _URL, _EMBED) read their patterns from that one registry. Nothing in it is typed
by hand: every term is FOUND in the source (src/**/*.jsx, index.html, CLONE_SPEC.md, public/assets/) and
carries file:line evidence, and the source copy is stored only as hashed, normalised 5-word shingles.

    python3 extraction/build_leakage_patterns.py           rewrite schema/generation-leakage.json
    python3 extraction/build_leakage_patterns.py --check   exit 1 if the shipped registry differs from a rebuild

It needs the sibling source project. Without it (a standalone copy of this package) it prints a notice and
exits 0: the shipped registry is then used as-is, and extraction/verify_all.py check [v] only verifies its
internal shape. Text is normalised with the SAME function the validator uses (semantic_validate.normalise:
NFKC, zero-width removal, curly quotes and dashes folded, lower-case, whitespace collapsed).

The only hand-chosen inputs are the SEED terms below, and the build FAILS if any seed is not found in the
source - a seed is a pointer to evidence, never a pattern invented without it. No human has reviewed the
resulting patterns; detection is string-based and can be evaded by paraphrase.
"""
import glob
import hashlib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "schema"))
from semantic_validate import normalise, words, shingle_hash, SHINGLE_N  # noqa: E402

OUT = os.path.join(ROOT, "schema", "generation-leakage.json")

# Seeds: pointers into the source. `match` = compact (all non-alphanumerics removed before a substring test,
# so "Four-mula" and "what-is-fourmula" are caught) or word (whole-word on normalised text).
BRAND_SEEDS = [
    ("fourmula", "compact", "The source brand: index.html <title> and data-wf-domain."),
    ("4mla", "word", "The brand's own abbreviation, printed on its product labels (product-shot alt text)."),
    ("arkena", "word", "A fourmula.ai product name on a real product shot."),
    ("silvane", "word", "A fourmula.ai product name on a real product shot."),
    ("aurexon", "word", "A fourmula.ai product name on a real product shot."),
]
CUSTOMER_SEEDS = [
    ("amila", "word", "A third-party garment brand legible in a real hero photograph."),
]
CLAIM_SEEDS = [
    ("awwwards", "word", "Third-party award shown as a fixed badge on every route (an award claim)."),
    ("13044361", "word", "The source company's real UK company registration number."),
    ("registered in england & wales", "word", "Legal-entity registration claim in the footer."),
]
# Short, generic interface vocabulary that also appears in the source but identifies nothing. Excluded from
# the exact-phrase set only (never from the 5-word shingles).
GENERIC_PHRASES = {"table of contents", "accept all", "privacy policy", "terms of service", "cookie policy",
                   "save changes", "back to site", "sign in", "get started", "scroll down", "cookie settings",
                   "close cookies modal", "how it works", "our features", "social media", "to continue", "inert placeholder form"}
MARKETING_FILES = ("Hero.jsx", "What.jsx", "AiSection.jsx", "How.jsx", "ListSection.jsx", "Faq.jsx",
                   "NotFoundContent.jsx", "Preloader.jsx")
PERSON_FILES = ("Hero.jsx", "Preloader.jsx")          # alt text there describes real, identifiable people
SCREENSHOT_FILES = ("AiSection.jsx", "ListSection.jsx", "NotFoundContent.jsx")  # alt text of product imagery
EMBED_TAGS = ("iframe", "script", "embed", "object", "svg", "video", "style", "form")
HOST_RE = re.compile(r"(?<![\w@-])((?:[a-z0-9-]+\.)+(?:ai|com|io|net|org|app|co|uk|dev))\b")
CLAIM_RE = re.compile(r"\b\d+\s*(?:\+|%|x\b)|\bno\.?:?\s*\d{6,}")


def source_present():
    return os.path.isfile(os.path.join(SRC_ROOT, "src", "App.jsx")) and os.path.isdir(os.path.join(SRC_ROOT, "public", "assets"))


def rel(p):
    return os.path.relpath(p, SRC_ROOT).replace(os.sep, "/")


def blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def jsx_segments(path):
    """[(line, text, kind)] visible text and accessible text of one JSX file, with real line numbers."""
    raw = open(path, encoding="utf-8").read()
    t = re.sub(r"/\*.*?\*/", blank, raw, flags=re.S)                   # block comments, incl. {/* */}
    t = re.sub(r"<svg\b.*?</svg>", blank, t, flags=re.S)               # inline artwork carries no copy
    t = re.sub(r"style=\{\{.*?\}\}", blank, t, flags=re.S)
    out = []
    for m in re.finditer(r'\b(alt|aria-label|placeholder|title)="([^"]+)"', t):
        out.append((t.count("\n", 0, m.start()) + 1, html.unescape(m.group(2)), "attr:" + m.group(1)))
    t2 = re.sub(r"<br\s*/?>|</?(?:span|a|strong|em|b|i)\b[^>]*>", lambda m: " " * len(m.group(0)), t)
    for m in re.finditer(r">([^<>]+)<", t2):
        seg = re.sub(r"\{[^{}]*\}", " ", m.group(1))
        if not re.search(r"[A-Za-z0-9]", seg) or "=>" in seg or "return" in seg:
            continue
        off = m.start(1) + (len(m.group(1)) - len(m.group(1).lstrip()))
        out.append((t2.count("\n", 0, off) + 1, html.unescape(" ".join(seg.split())), "text"))
    return out


def find_term(term, mode, files):
    ev = []
    for f in files:
        for i, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
            n = normalise(line)
            if mode == "compact":
                hit = term in re.sub(r"[^a-z0-9]", "", n)
            else:
                hit = re.search(r"(?<![a-z0-9])" + re.escape(" ".join(words(term))) + r"(?![a-z0-9])", " ".join(words(n)))
            if hit:
                ev.append("%s:%d" % (rel(f), i))
    return ev


def build():
    jsx = sorted(glob.glob(os.path.join(SRC_ROOT, "src", "**", "*.jsx"), recursive=True))
    texty = jsx + [os.path.join(SRC_ROOT, "index.html")] + sorted(glob.glob(os.path.join(SRC_ROOT, "CLONE_SPEC*.md")))
    reg = {"$description": "GENERATED by extraction/build_leakage_patterns.py from the real source - do not edit by hand "
                           "(verify_all.py check [v] rebuilds and compares it whenever the source project is beside this "
                           "package). Read by the GENERATION_MODE_* rules in schema/semantic_validate.py, which apply "
                           "ONLY to mode=generation PageSpecs. Detection is string-based on normalised text and can be "
                           "evaded by paraphrase; no human has reviewed these patterns.",
           "registryVersion": "1.0.0",
           "normalisation": "semantic_validate.normalise: Unicode NFKC, zero-width and soft-hyphen characters removed, "
                            "curly single/double quotes folded to ' and \", every dash and minus sign folded to '-', "
                            "lower-cased, whitespace collapsed.",
           "shingleSize": SHINGLE_N,
           "shingleHash": "sha256 of the space-joined normalised words, first 16 hex characters",
           "categories": {}}
    cat = reg["categories"]

    def terms(seeds):
        out = []
        for term, mode, why in seeds:
            ev = find_term(term, mode, texty)
            if not ev:
                raise SystemExit("seed %r was not found anywhere in the source - refusing to invent a pattern" % term)
            out.append({"term": term if mode == "compact" else " ".join(words(term)), "match": mode, "why": why, "occurrences": len(ev), "evidence": ev[:8]})
        return out

    cat["GENERATION_MODE_BRAND"] = {"rule": "No source brand name, abbreviation, product name or brand-bearing anchor id in any string.",
                                    "terms": terms(BRAND_SEEDS)}
    cat["GENERATION_MODE_CUSTOMER"] = {"rule": "No real third-party customer or partner brand, and no customer/partner logo role.",
                                       "terms": terms(CUSTOMER_SEEDS), "roles": ["trusted-partner-logo"]}
    hosts = {}
    for f in texty:
        for i, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
            for h in HOST_RE.findall(normalise(line)):
                if "fourmula" in h:
                    hosts.setdefault(h.lstrip("."), []).append("%s:%d" % (rel(f), i))
    cat["GENERATION_MODE_URL"] = {"rule": "No source host in any string, and any host name shown as text must use a reserved placeholder domain (.example or .invalid).",
                                  "hosts": [{"host": h, "evidence": ev[:6]} for h, ev in sorted(hosts.items())],
                                  "placeholderSuffixes": [".example", ".invalid"]}
    files = []
    for p in sorted(glob.glob(os.path.join(SRC_ROOT, "public", "assets", "**", "*"), recursive=True)):
        if os.path.isfile(p):
            files.append(rel(p)[len("public"):])
    cat["GENERATION_MODE_ASSET"] = {"rule": "Only generation-safe asset roles; no asset path or string may reuse a real file name from public/assets.",
                                    "assetFiles": [os.path.basename(f) for f in files],
                                    "assetFilesEvidence": "public/assets (%d files)" % len(files)}
    segs = {}
    for f in jsx:
        segs[f] = jsx_segments(f)

    def shingles(selected, kinds=None):
        hs, ev = set(), {}
        for f in selected:
            for line, text, kind in segs[f]:
                if kinds and not any(kind.startswith(k) for k in kinds):
                    continue
                w = words(text)
                for i in range(0, max(0, len(w) - SHINGLE_N + 1)):
                    h = shingle_hash(w[i:i + SHINGLE_N])
                    hs.add(h)
                    ev.setdefault(rel(f), set()).add(line)
        return sorted(hs), {k: "%d lines" % len(v) for k, v in sorted(ev.items())}

    by = lambda names: [f for f in jsx if os.path.basename(f) in names]
    ph, pe = shingles(by(PERSON_FILES), ["attr:alt"])
    cat["GENERATION_MODE_PERSON"] = {"rule": "No real-person photo role, and no 5-word run from the source's descriptions of real people.",
                                     "roles": ["hero-carousel-photo", "preloader-photo"], "shingles": ph, "evidence": pe}
    sh, se = shingles(by(SCREENSHOT_FILES), ["attr:alt"])
    cat["GENERATION_MODE_SCREENSHOT"] = {"rule": "No real product-imagery / screenshot role, and no 5-word run from the source's product-image descriptions.",
                                         "roles": ["product-shot-photo", "step-artwork", "not-found-artwork", "og-banner"],
                                         "shingles": sh, "evidence": se}
    ch, ce = shingles(jsx)
    exact = set()
    for f in by(MARKETING_FILES):
        for line, text, kind in segs[f]:
            w = words(text)
            if 3 <= len(w) <= 4 and " ".join(w) not in GENERIC_PHRASES:
                exact.add(shingle_hash(w))
    cat["GENERATION_MODE_COPY"] = {"rule": "No 5-word run of the source's visible or accessible copy (any page), and no exact 3-4 word marketing line.",
                                   "shingles": ch, "exactPhrases": sorted(exact), "evidence": ce,
                                   "genericPhrasesExcludedFromExact": sorted(GENERIC_PHRASES)}
    claims = terms(CLAIM_SEEDS)
    for f in by(MARKETING_FILES + ("Footer.jsx",)):
        for line, text, kind in segs[f]:
            n = normalise(text)
            for m in CLAIM_RE.finditer(n):
                claims.append({"term": " ".join(words(n)), "match": "word", "why": "A quantified or legal claim in the source copy.",
                               "occurrences": 1, "evidence": ["%s:%d" % (rel(f), line)]})
    seen, uniq = set(), []
    for c in claims:
        if c["term"] not in seen:
            seen.add(c["term"])
            uniq.append(c)
    cat["GENERATION_MODE_CLAIM"] = {"rule": "No real award, registration, statistic or quantified product claim from the source, and no award-badge role.",
                                    "terms": uniq, "roles": ["third-party-award-badge"]}
    tags = []
    for tag in EMBED_TAGS:
        ev = []
        for f in jsx + [os.path.join(SRC_ROOT, "index.html")]:
            for i, line in enumerate(open(f, encoding="utf-8"), 1):
                if re.search(r"<\s*%s\b" % tag, line, re.I):
                    ev.append("%s:%d" % (rel(f), i))
        tags.append({"tag": tag, "presentInSource": bool(ev), "evidence": ev[:3]})
    cat["GENERATION_MODE_EMBED"] = {"rule": "No raw markup or embed in any string, and no source media embed role (the produced videos, the award badge).",
                                    "tags": tags, "roles": ["showcase-video", "third-party-award-badge"]}
    return reg


def main(argv):
    if not source_present():
        print("build_leakage_patterns: the source project is not beside this package; the shipped "
              "schema/generation-leakage.json is used as-is.")
        return 0
    out = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        if cur != out:
            print("LEAKAGE REGISTRY DRIFT: schema/generation-leakage.json differs from a rebuild from the real source")
            return 1
        print("leakage registry up to date (%d categories, rebuilt from the real source)" % len(json.loads(out)["categories"]))
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    d = json.loads(out)["categories"]
    print("wrote schema/generation-leakage.json: %s" % ", ".join(
        "%s=%d" % (k.replace("GENERATION_MODE_", ""), sum(len(v) for kk, v in x.items() if isinstance(v, list)))
        for k, x in d.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
