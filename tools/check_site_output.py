#!/usr/bin/env python
"""Required-output manifest + same-origin link-integrity gate.

Built for the AllyFind migration (docs/specs/allyfind-migration-... see
whatsapp-deals-bot's HANDOVER.md) but brand-agnostic: it works on either
domain's build output, local or live.

    python tools/check_site_output.py --dir <built output tree> --site https://allyfind.com --brand AllyFind
    python tools/check_site_output.py --live https://allyfind.com --brand AllyFind

Two modes:
  --dir DIR   check a local build output tree on disk (fast, pre-deploy gate)
  --live URL  re-run the same checks against a live site over real HTTP
              requests (slower, the "not enough to pass locally" step the
              spec asks for)

What it checks, either mode:
  1. Required-output manifest: every language's posts.html, every guide
     article for every content/*.json slug, plus terms.html, robots.txt,
     manifest.webmanifest, sitemap.xml, icon-192.png, icon-512.png. Fails
     loudly if anything is missing rather than silently emitting a link to
     nothing.
  2. Same-origin link integrity: parses every generated HTML file for
     <a href> "same-origin" targets (relative, or absolute matching --site)
     and confirms each one resolves to a real file (or, in --live mode, a
     real 200). Fragment targets (#id) are checked against the target page's
     actual ids.
  3. <html lang>/<dir> correctness per LANGS.
  4. Brand leakage: case-insensitive search for "fashionhotspot" in every
     page's visible HTML — skipped automatically when --brand is
     "fashionhotspot" itself, since that string is supposed to be there.

Exit code is non-zero if anything fails, so this is meant to sit in a
deploy script as a gate, not just a report.
"""
import argparse, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from langs import LANGS, DEFAULT  # noqa: E402
from i18n_schema import CONTENT  # noqa: E402


def load_slugs():
    return sorted(f.stem for f in CONTENT.glob("*.json"))


def required_files(slugs):
    """(relative_path, page_kind) for every file the finished build must have."""
    req = []
    for lang, cfg in LANGS.items():
        prefix = cfg["path"]
        req.append((f"{prefix}posts.html", "index"))
        if prefix:  # language landing page; English lives at the site root
            req.append((f"{prefix}index.html", "lang-home"))
        for slug in slugs:
            req.append((f"{prefix}post-{slug}.html", "guide"))
    for f in ("terms.html", "robots.txt", "manifest.webmanifest", "sitemap.xml",
              "icon-192.png", "icon-512.png"):
        req.append((f, "global"))
    return req


class LinkExtractor(HTMLParser):
    """Collects <a href>, <link href> and the ids present on the page."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []   # (tag, href)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in ("a", "link") and d.get("href"):
            self.links.append((tag, d["href"]))
        if d.get("id"):
            self.ids.add(d["id"])


def extract(html_text):
    p = LinkExtractor()
    try:
        p.feed(html_text)
    except Exception as e:
        print(f"  ! HTML parse warning: {e}")
    return p.links, p.ids


def same_origin_target(href, site):
    """Return (path, fragment, root_absolute) for a same-origin link, or
    None if external, mailto:, tel:, javascript:, or anchor-only.

    root_absolute is True for a scheme-absolute URL (https://site/x) or a
    leading-slash path (/x) — both name a path from the site root, never
    relative to the page they're found on. A bare relative href (x.html,
    ../x.html) is root_absolute=False and resolves against the page's own
    directory instead.
    """
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    parsed = urlparse(href)
    if parsed.scheme in ("http", "https"):
        site_host = urlparse(site).netloc
        if parsed.netloc and parsed.netloc != site_host:
            return None  # genuinely external
        path = parsed.path.lstrip("/")
        root_absolute = True
    elif parsed.netloc:
        return None
    elif href.startswith("/"):
        path = parsed.path.lstrip("/")
        root_absolute = True
    else:
        path = parsed.path
        root_absolute = False
    return path, parsed.fragment, root_absolute


def resolve_link(page_rel_path, path, root_absolute):
    """Filesystem-relative target path for a link found on page_rel_path.

    Strips nothing the browser wouldn't strip (query strings are not part of
    the file path), and resolves page-relative hrefs against the directory
    the linking page lives in, not the site root.
    """
    if root_absolute:
        return path
    base = "/" + page_rel_path
    resolved = urljoin(base, path)
    return resolved.lstrip("/")


def check_local(out_dir, site, brand, slugs):
    out_dir = Path(out_dir).resolve()
    fails = []

    print(f"== 1. Required-output manifest ({len(required_files(slugs))} files) ==")
    missing = [rel for rel, _ in required_files(slugs) if not (out_dir / rel).is_file()]
    if missing:
        for m in missing:
            fails.append(f"MISSING required file: {m}")
        print(f"  {len(missing)} missing:")
        for m in missing[:30]:
            print(f"    - {m}")
        if len(missing) > 30:
            print(f"    ... and {len(missing) - 30} more")
    else:
        print("  all required files present")

    print("== 2/3/4. Link integrity, lang/dir, brand leakage ==")
    # _reference/ holds copies of pages this repo doesn't own (fetched from
    # the live site by build_brand.py purely so links INTO them resolve) —
    # not pages of this build, so they are not linted themselves.
    html_files = sorted(f for f in out_dir.rglob("*.html")
                         if "_reference" not in f.relative_to(out_dir).parts)
    page_ids = {}
    for f in html_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        _, ids = extract(text)
        page_ids[str(f.relative_to(out_dir)).replace("\\", "/")] = ids

    checked_links = 0
    for f in html_files:
        rel = str(f.relative_to(out_dir)).replace("\\", "/")
        text = f.read_text(encoding="utf-8", errors="replace")

        # lang/dir
        m = re.search(r'<html\s+lang="([^"]+)"\s+dir="([^"]+)"', text)
        if m:
            lang_attr, dir_attr = m.groups()
            expected_lang = None
            for code, cfg in LANGS.items():
                if rel == f"{cfg['path']}posts.html" or rel.startswith(f"{cfg['path']}post-") \
                   or rel == f"{cfg['path']}index.html":
                    expected_lang = code
                    break
            if expected_lang and lang_attr != expected_lang:
                fails.append(f"{rel}: <html lang> is {lang_attr!r}, expected {expected_lang!r}")
            if expected_lang:
                want_dir = "rtl" if LANGS[expected_lang]["dir"] == "rtl" else "ltr"
                if dir_attr != want_dir:
                    fails.append(f"{rel}: <html dir> is {dir_attr!r}, expected {want_dir!r}")

        # brand leakage
        if brand.lower() != "fashionhotspot" and re.search(r'fashionhotspot', text, re.I):
            n = len(re.findall(r'fashionhotspot', text, re.I))
            fails.append(f"{rel}: contains 'fashionhotspot' ({n}x) — brand leakage")

        # links
        links, _ = extract(text)
        for tag, href in links:
            parsed = same_origin_target(href, site)
            if parsed is None:
                continue
            path, frag, root_absolute = parsed
            path = path.split("?", 1)[0]  # query strings (?v=hash) are not part of the file path
            if not path:  # e.g. href="#frag" already filtered, href="" edge case
                continue
            target_rel = resolve_link(rel, path, root_absolute)
            checked_links += 1
            target_file = out_dir / target_rel
            if target_file.is_dir():
                target_file = target_file / "index.html"
                target_rel = target_rel.rstrip("/") + "/index.html"
            if not target_file.is_file():
                fails.append(f"{rel}: broken link -> {href} (resolved {target_rel})")
                continue
            if frag:
                ids = page_ids.get(target_rel)
                if ids is None:
                    text2 = target_file.read_text(encoding="utf-8", errors="replace")
                    _, ids = extract(text2)
                    page_ids[target_rel] = ids
                if frag not in ids:
                    fails.append(f"{rel}: fragment #{frag} missing on {target_rel}")

    print(f"  {len(html_files)} pages parsed, {checked_links} same-origin links checked")
    return fails


def check_live(base, brand, slugs):
    import urllib.request
    import urllib.error

    fails = []
    urls = []
    for rel, _ in required_files(slugs):
        if rel.endswith(".html") or rel == "sitemap.xml" or rel == "robots.txt":
            urls.append(rel)
    print(f"== Live production check: {len(urls)} required URLs against {base} ==")
    ok = 0
    for rel in urls:
        url = base.rstrip("/") + "/" + rel
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "allyfind-linkcheck/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
                body = r.read().decode("utf-8", errors="replace") if code == 200 else ""
        except urllib.error.HTTPError as e:
            code = e.code
            body = ""
        except Exception as e:
            fails.append(f"{rel}: request failed ({e})")
            continue
        if code != 200:
            fails.append(f"{rel}: HTTP {code} (expected 200)")
            continue
        ok += 1
        if brand.lower() != "fashionhotspot" and re.search(r'fashionhotspot', body, re.I):
            n = len(re.findall(r'fashionhotspot', body, re.I))
            fails.append(f"{rel}: LIVE page contains 'fashionhotspot' ({n}x)")
    print(f"  {ok}/{len(urls)} returned 200")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="local build output tree to check")
    ap.add_argument("--live", help="base URL to re-check over real HTTP, e.g. https://allyfind.com")
    ap.add_argument("--site", default="https://fashionhotspot.site",
                     help="canonical site URL used in the build (for same-origin detection in --dir mode)")
    ap.add_argument("--brand", default="fashionhotspot")
    args = ap.parse_args()

    if not args.dir and not args.live:
        sys.exit("pass --dir <tree> and/or --live <url>")

    slugs = load_slugs()
    fails = []
    if args.dir:
        fails += check_local(args.dir, args.site, args.brand, slugs)
    if args.live:
        fails += check_live(args.live, args.brand, slugs)

    print()
    if fails:
        print(f"FAILED — {len(fails)} problem(s):")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    print("PASSED — required-output manifest complete, no broken same-origin links, no brand leakage.")


if __name__ == "__main__":
    main()
