#!/usr/bin/env python
"""Render the fashionhotspot buying guides, in every language they exist in.

    python tools/build.py              # everything
    python tools/build.py coffee       # one guide, all languages
    python tools/build.py --lang en    # one language, all guides

English is canonical (content/<slug>.json). Other languages merge in
content/i18n/<lang>/<slug>.json field by field, so a partial translation falls
back to English per field rather than rendering blanks.

Output: post-<slug>.html and posts.html at the root for English, and the same
under <lang>/ for the rest, plus sitemap.xml covering all of them.
"""
import argparse, html, json, sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import CSS, FONTS, RTL_FONT                      # noqa: E402
from langs import (LANGS, DEFAULT, MONTHS, UI, AUTHOR, FONT_LINKS,  # noqa: E402
                   t, fmt_date, disclosure)
from i18n_schema import CONTENT, load_translation, merge     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://fashionhotspot.site"
AMZ_TAG = "fashionhots0f-20"
BRAND = "fashionhotspot"

ORDER = ["tech", "smart-home", "kitchen", "coffee", "home-office", "fitness",
         "travel", "pets", "photography", "gaming", "outdoor", "beauty",
         "phone", "kids", "health", "storage", "car", "garden", "fashion",
         "back-to-school"]

e = lambda s: html.escape(str(s), quote=True)


def load_affiliates():
    f = ROOT / "site-config.json"
    if not f.exists():
        return True, True
    a = json.loads(f.read_text(encoding="utf-8")).get("affiliates", {})
    return bool(a.get("amazon", True)), bool(a.get("aliexpress", True))


SHOW_AMZ, SHOW_ALI = load_affiliates()


def amazon(term):
    from urllib.parse import quote_plus
    return f"https://www.amazon.com/s?k={quote_plus(term)}&tag={AMZ_TAG}"


def aliexpress(term):
    from urllib.parse import quote_plus
    return f"https://www.aliexpress.com/wholesale?SearchText={quote_plus(term)}"


def url(lang, page):
    """Absolute URL of a page in a language."""
    return f"{SITE}/{LANGS[lang]['path']}{page}"


def rel_root(lang):
    """Relative path back to the site root from inside a language folder."""
    return "" if lang == DEFAULT else "../"


# --------------------------------------------------------------------------
# chrome
# --------------------------------------------------------------------------
def nav(lang, current):
    r = rel_root(lang)
    items = [(f"{r}index.html", t(lang, "deals")),
             ("posts.html", t(lang, "guides")),
             (f"{r}about.html", t(lang, "about")),
             (f"{r}contact.html", t(lang, "contact"))]
    links = "".join(
        f'<a href="{e(h)}"{" aria-current=\"page\"" if h.endswith(current) else ""}>{e(x)}</a>'
        for h, x in items)
    return (f'<div class="nav"><div class="nav-in">'
            f'<a class="logo" href="{e(r)}index.html">fashion<span>hotspot</span></a>'
            f'<nav class="nav-links">{links}</nav></div></div>')


def lang_switcher(lang, page):
    """Every other language this page exists in."""
    out = []
    for code, cfg in LANGS.items():
        if code == lang:
            continue
        href = f"{rel_root(lang)}{cfg['path']}{page}"
        out.append(f'<a href="{e(href)}" hreflang="{code}">{e(cfg["name"])}</a>')
    return f'<div class="langsw">{" · ".join(out)}</div>'


def footer(lang, page="posts.html"):
    r = rel_root(lang)
    links = [(f"{r}about.html", t(lang, "about")),
             (f"{r}contact.html", t(lang, "contact")),
             (f"{r}privacy.html", t(lang, "privacy")),
             (f"{r}terms.html", t(lang, "terms")),
             ("posts.html", t(lang, "guides"))]
    nl = "".join(f'<a href="{e(h)}">{e(x)}</a>' for h, x in links)
    disc = disclosure(lang, SHOW_AMZ, SHOW_ALI, short=True) + " " + t(lang, "no_extra_cost")
    return (f'<footer><nav>{nl}</nav><p>{e(disc)}</p>'
            f'<p style="margin-top:10px">© {date.today().year} {BRAND}</p>'
            f'{lang_switcher(lang, page)}</footer>')


def alternates(page):
    """hreflang set — every language plus x-default pointing at English."""
    out = "".join(f'<link rel="alternate" hreflang="{c}" href="{url(c, page)}">'
                  for c in LANGS)
    return out + f'<link rel="alternate" hreflang="x-default" href="{url(DEFAULT, page)}">'


def page_shell(lang, title, desc, body, *, canonical, extra_head="", og_image=None):
    cfg = LANGS[lang]
    rtl = cfg["dir"] == "rtl"
    fonts = FONTS + (RTL_FONT if rtl else "")
    if cfg["font"] and cfg["font"] in FONT_LINKS and not rtl:
        fonts += FONT_LINKS[cfg["font"]]
    og = f'<meta property="og:image" content="{e(og_image)}">' if og_image else ""
    extra_css = ""
    if cfg["font"] == "Noto Sans":
        extra_css = ("<style>body,h1,h2,h3,.logo{font-family:'Noto Sans',"
                     "Inter,system-ui,sans-serif}</style>")
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{cfg['dir']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:site_name" content="{BRAND}">{og}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/icon-192.png" type="image/png">
<link rel="manifest" href="/manifest.webmanifest">
{fonts}
<style>{CSS}</style>{extra_css}
{extra_head}
</head>
<body>
{body}
</body>
</html>
"""


# --------------------------------------------------------------------------
# a guide
# --------------------------------------------------------------------------
def render_guide(g, lang):
    slug = g["slug"]
    r = rel_root(lang)
    page = f"post-{slug}.html"
    canon = url(lang, page)
    products = g["products"]

    crumb = (f'<div class="crumbs"><a href="{r}index.html">{e(t(lang, "home"))}</a> › '
             f'<a href="posts.html">{e(t(lang, "guides"))}</a> › {e(g["category"])}</div>')
    byline = (f'<div class="byline"><b>{e(AUTHOR.get(lang, AUTHOR[DEFAULT]))}</b>'
              f'<span class="dot">·</span><span>{e(t(lang, "updated"))} '
              f'<time datetime="{e(g["updated"])}">{e(fmt_date(g["updated"], lang))}</time></span>'
              f'<span class="dot">·</span>'
              f'<span>{g.get("read_minutes", 9)} {e(t(lang, "min_read"))}</span>'
              f'<span class="dot">·</span>'
              f'<span>{len(products)} {e(t(lang, "picks"))}</span></div>')
    head = (f'{crumb}<div class="kicker">{e(g["category"])} · {e(t(lang, "buying_guide"))}</div>'
            f'<h1>{e(g["title"])}</h1><p class="dek">{e(g["dek"])}</p>{byline}')
    hero = (f'<div class="hero"><img src="{r}images/hero-{slug}.jpg" '
            f'alt="{e(g["title"])}" width="1600" height="840" fetchpriority="high"></div>')

    intro = "".join(f'<p{" class=\"lead\"" if i == 0 else ""}>{e(p)}</p>'
                    for i, p in enumerate(g["intro"]))
    note = (f'<div class="note"><b>{e(t(lang, "disclosure_label"))}</b> '
            f'{e(t(lang, "disclosure_body"))}</div>')
    how = f'<h2>{e(t(lang, "how_we_picked"))}</h2><p>{e(g["how_we_pick"])}</p>'

    hdrs = ["#", t(lang, "product"), t(lang, "best_for"), t(lang, "approx_price")]
    rows = "".join(
        f'<tr><td class="rank">{i}</td><td><a href="#p{i}">{e(p["name"])}</a></td>'
        f'<td>{e(p["tag"])}</td><td>{e(p["price"])}</td></tr>'
        for i, p in enumerate(products, 1))
    table = (f'<h2>{e(t(lang, "at_a_glance"))}</h2><div class="tablewrap"><table><thead><tr>'
             + "".join(f"<th>{e(h)}</th>" for h in hdrs)
             + f'</tr></thead><tbody>{rows}</tbody></table></div>'
             f'<p style="font-size:13.5px;color:var(--ink-3);margin-top:10px">'
             f'{e(t(lang, "price_note"))}</p>')

    cards = []
    for i, p in enumerate(products, 1):
        pros = "".join(f"<li>{e(x)}</li>" for x in p.get("pros", []))
        cons = "".join(f"<li>{e(x)}</li>" for x in p.get("cons", []))
        buys = ""
        if SHOW_AMZ:
            buys += (f'<a class="btn btn-a" rel="nofollow sponsored noopener" target="_blank" '
                     f'href="{e(amazon(p["search"]))}">{e(t(lang, "check_amazon"))}</a>')
        if SHOW_ALI:
            buys += (f'<a class="btn btn-b" rel="nofollow sponsored noopener" target="_blank" '
                     f'href="{e(aliexpress(p["search"]))}">AliExpress</a>')
        cards.append(
            f'<article class="card" id="p{i}">'
            f'<img class="card-img" src="{r}images/{slug}-{i:02d}.jpg" alt="{e(p["name"])}" '
            f'width="1200" height="750" loading="lazy" decoding="async">'
            f'<div class="card-in"><div class="card-top"><div class="num">{i}</div>'
            f'<div style="flex:1"><span class="tag">{e(p["tag"])}</span>'
            f'<h3>{e(p["name"])}</h3><div class="price">{e(p["price"])}</div></div></div>'
            f'<p>{e(p["body"])}</p>'
            f'<div class="pc"><div class="pros"><h4>{e(t(lang, "why_here"))}</h4><ul>{pros}</ul></div>'
            f'<div class="cons"><h4>{e(t(lang, "worth_knowing"))}</h4><ul>{cons}</ul></div></div>'
            f'<div class="buys">{buys}</div></div></article>')

    faq_items = "".join(
        f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>'
        for f in g.get("faq", []))
    faq = (f'<h2>{e(t(lang, "faq"))}</h2><div class="faq">{faq_items}</div>'
           if faq_items else "")

    body = (nav(lang, page) + '<div class="wrap">' + head + hero
            + '<div class="body">' + intro + note + how + table
            + f'<h2>{e(t(lang, "the_picks"))}</h2>' + "".join(cards) + faq
            + f'<p style="margin-top:34px"><a href="posts.html">← {e(t(lang, "all_guides"))}</a></p>'
            + f'<p class="disc">{e(disclosure(lang, SHOW_AMZ, SHOW_ALI))}</p>'
            + "</div></div>" + footer(lang, page))

    return page_shell(lang, f'{g["title"]} — {BRAND}', g["dek"], body,
                      canonical=canon,
                      extra_head=json_ld(g, lang, canon) + alternates(page),
                      og_image=f"{SITE}/images/hero-{slug}.jpg")


def json_ld(g, lang, canon):
    blocks = [{
        "@context": "https://schema.org", "@type": "Article",
        "headline": g["title"], "description": g["dek"],
        "datePublished": g["updated"], "dateModified": g["updated"],
        "inLanguage": lang,
        "author": {"@type": "Organization", "name": AUTHOR.get(lang, AUTHOR[DEFAULT])},
        "publisher": {"@type": "Organization", "name": BRAND},
        "image": f"{SITE}/images/hero-{g['slug']}.jpg",
        "mainEntityOfPage": canon,
    }, {
        "@context": "https://schema.org", "@type": "ItemList",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(g["products"]),
        "itemListElement": [{"@type": "ListItem", "position": i, "name": p["name"],
                             "url": f"{canon}#p{i}"}
                            for i, p in enumerate(g["products"], 1)],
    }]
    if g.get("faq"):
        blocks.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                           for f in g["faq"]],
        })
    return "".join(
        f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
        for b in blocks)


def render_index(guides, lang):
    r = rel_root(lang)
    cards = []
    for g in guides:
        cards.append(
            f'<a class="gcard" href="post-{g["slug"]}.html">'
            f'<img src="{r}images/hero-{g["slug"]}.jpg" alt="{e(g["title"])}" '
            f'width="1600" height="840" loading="lazy" decoding="async">'
            f'<div class="gcard-in"><span class="tag">{e(g["category"])}</span>'
            f'<h3>{e(g["title"])}</h3><p class="sum">{e(g["dek"])}</p>'
            f'<div class="meta">{e(fmt_date(g["updated"], lang))} · '
            f'{len(g["products"])} {e(t(lang, "picks"))}</div></div></a>')
    body = (nav(lang, "posts.html") + '<div class="wide">'
            + f'<div class="kicker" style="margin-top:34px">{e(t(lang, "guides"))}</div>'
            + f'<h1>{e(t(lang, "index_title"))}</h1>'
            + f'<p class="dek" style="max-width:640px">{e(t(lang, "index_dek"))}</p>'
            + f'<div class="grid">{"".join(cards)}</div>'
            + f'<p class="disc" style="max-width:760px">'
              f'{e(disclosure(lang, SHOW_AMZ, SHOW_ALI, short=True))}</p></div>'
            + footer(lang, "posts.html"))
    return page_shell(lang, f'{t(lang, "index_title")} — {BRAND}', t(lang, "index_dek"),
                      body, canonical=url(lang, "posts.html"),
                      extra_head=alternates("posts.html"),
                      og_image=f"{SITE}/images/hero-{guides[0]['slug']}.jpg" if guides else None)


def render_sitemap(guides):
    today = date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    def entry(loc, pri, freq, page=None):
        alt = ""
        if page:
            alt = "".join(
                f'    <xhtml:link rel="alternate" hreflang="{c}" href="{url(c, page)}"/>\n'
                for c in LANGS)
        return (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n"
                f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n"
                f"{alt}  </url>")

    out.append(entry(f"{SITE}/", "1.0", "daily"))
    for p, pri in (("about.html", "0.5"), ("contact.html", "0.4"),
                   ("privacy.html", "0.3"), ("terms.html", "0.3")):
        out.append(entry(f"{SITE}/{p}", pri, "monthly"))
    for lang in LANGS:
        pri = "0.9" if lang == DEFAULT else "0.7"
        out.append(entry(url(lang, "posts.html"), pri, "weekly", "posts.html"))
    for g in guides:
        page = f"post-{g['slug']}.html"
        for lang in LANGS:
            pri = "0.8" if lang == DEFAULT else "0.6"
            out.append(entry(url(lang, page), pri, "monthly", page))
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def load_guides():
    gs = {}
    for f in sorted(CONTENT.glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        gs[g["slug"]] = g
    return gs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--lang", action="append", choices=list(LANGS))
    args = ap.parse_args()

    src = load_guides()
    if not src:
        sys.exit("no content/*.json found")
    ordered = ([src[s] for s in ORDER if s in src]
               + [g for s, g in src.items() if s not in ORDER])
    targets = [src[s] for s in args.slugs] if args.slugs else ordered
    langs = args.lang or list(LANGS)

    written = 0
    for lang in langs:
        out_dir = ROOT / LANGS[lang]["path"] if LANGS[lang]["path"] else ROOT
        out_dir.mkdir(parents=True, exist_ok=True)
        for g in targets:
            merged = merge(g, load_translation(lang, g["slug"])) if lang != DEFAULT else g
            (out_dir / f"post-{g['slug']}.html").write_text(
                render_guide(merged, lang), encoding="utf-8")
            written += 1
        idx = [merge(g, load_translation(lang, g["slug"])) if lang != DEFAULT else g
               for g in ordered]
        (out_dir / "posts.html").write_text(render_index(idx, lang), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(render_sitemap(ordered), encoding="utf-8")
    print(f"{written} guide pages across {len(langs)} languages "
          f"({', '.join(langs)}), plus {len(langs)} index pages and sitemap.xml")


if __name__ == "__main__":
    main()
