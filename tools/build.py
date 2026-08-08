#!/usr/bin/env python
"""Render the fashionhotspot buying guides from content/*.json.

    python tools/build.py            # every guide + the index + sitemap
    python tools/build.py coffee     # one guide (fast iteration)

Writes post-<slug>.html, he/post-<slug>.html, posts.html, he/posts.html and
sitemap.xml at the repo root. Content lives in content/*.json so the copy can
be edited without touching this file.
"""
import argparse, html, json, re, sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import CSS, FONTS, RTL_FONT  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SITE = "https://fashionhotspot.site"
AMZ_TAG = "fashionhots0f-20"
BRAND = "fashionhotspot"
AUTHOR = "The fashionhotspot editors"
AUTHOR_HE = "מערכת fashionhotspot"

# Order guides appear in on the index. Anything not listed lands at the end.
ORDER = ["tech", "smart-home", "kitchen", "coffee", "home-office", "fitness",
         "travel", "pets", "photography", "gaming", "outdoor", "beauty",
         "phone", "kids", "health", "storage", "car", "garden", "fashion",
         "back-to-school"]

e = lambda s: html.escape(str(s), quote=True)


def amazon(term):
    from urllib.parse import quote_plus
    return f"https://www.amazon.com/s?k={quote_plus(term)}&tag={AMZ_TAG}"


def aliexpress(term):
    from urllib.parse import quote_plus
    return f"https://www.aliexpress.com/wholesale?SearchText={quote_plus(term)}"


def fmt_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return date(y, m, d).strftime("%d %B %Y").lstrip("0")


def fmt_date_he(iso):
    months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי",
              "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} ב{months[m - 1]} {y}"


# --------------------------------------------------------------------------
# chrome
# --------------------------------------------------------------------------
NAV_EN = [("index.html", "Deals"), ("posts.html", "Guides"), ("about.html", "About"),
          ("contact.html", "Contact")]
NAV_HE = [("../index.html", "דילים"), ("posts.html", "מדריכים"),
          ("../about.html", "עלינו"), ("../contact.html", "צור קשר")]


def nav(items, current, prefix=""):
    links = "".join(
        f'<a href="{e(h)}"{" aria-current=\"page\"" if h.endswith(current) else ""}>{e(t)}</a>'
        for h, t in items)
    home = f"{prefix}index.html"
    return (f'<div class="nav"><div class="nav-in">'
            f'<a class="logo" href="{e(home)}">fashion<span>hotspot</span></a>'
            f'<nav class="nav-links">{links}</nav></div></div>')


def footer(he=False, prefix=""):
    if he:
        links = [("../about.html", "עלינו"), ("../contact.html", "צור קשר"),
                 ("../privacy.html", "פרטיות"), ("../terms.html", "תנאים"),
                 ("posts.html", "מדריכים")]
        disc = ("כשותפים של אמזון ושל עליאקספרס אנחנו מרוויחים עמלה מרכישות "
                "מזכות. זה לא מייקר עבורכם את המוצר.")
        sw = '<div class="langsw"><a href="../posts.html">English</a></div>'
    else:
        links = [(f"{prefix}about.html", "About"), (f"{prefix}contact.html", "Contact"),
                 (f"{prefix}privacy.html", "Privacy"), (f"{prefix}terms.html", "Terms"),
                 (f"{prefix}posts.html", "Guides")]
        disc = ("As an Amazon Associate and an AliExpress affiliate we earn from "
                "qualifying purchases. This never costs you more.")
        sw = '<div class="langsw"><a href="he/posts.html">עברית</a></div>'
    nl = "".join(f'<a href="{e(h)}">{e(t)}</a>' for h, t in links)
    return (f'<footer><nav>{nl}</nav><p>{e(disc)}</p>'
            f'<p style="margin-top:10px">© {date.today().year} {BRAND}</p>{sw}</footer>')


def page(title, desc, body, *, canonical, he=False, extra_head="", og_image=None):
    d = 'dir="rtl" lang="he"' if he else 'lang="en"'
    fonts = FONTS + (RTL_FONT if he else "")
    og = f'<meta property="og:image" content="{e(og_image)}">' if og_image else ""
    return f"""<!DOCTYPE html>
<html {d}>
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
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="/manifest.webmanifest">
{fonts}
<style>{CSS}</style>
{extra_head}
</head>
<body>
{body}
</body>
</html>
"""


# --------------------------------------------------------------------------
# a single guide
# --------------------------------------------------------------------------
def render_guide(g, he=False):
    slug = g["slug"]
    L = (lambda k: g.get(k + "_he") or g[k]) if he else (lambda k: g[k])
    pfx = "../" if he else ""
    title = L("title")
    dek = L("dek")
    canon = f"{SITE}/{'he/' if he else ''}post-{slug}.html"
    hero = f"{pfx}images/hero-{slug}.jpg"
    products = g["products"]

    def pl(p, k):
        return (p.get(k + "_he") or p[k]) if he else p[k]

    # --- head matter -----------------------------------------------------
    crumb = (f'<div class="crumbs"><a href="{pfx}index.html">'
             f'{"בית" if he else "Home"}</a> › '
             f'<a href="posts.html">{"מדריכים" if he else "Guides"}</a> › '
             f'{e(g["category"])}</div>')
    updated = fmt_date_he(g["updated"]) if he else fmt_date(g["updated"])
    mins = g.get("read_minutes", 8)
    byline = (f'<div class="byline"><b>{e(AUTHOR_HE if he else AUTHOR)}</b>'
              f'<span class="dot">·</span>'
              f'<span>{"עודכן" if he else "Updated"} '
              f'<time datetime="{e(g["updated"])}">{e(updated)}</time></span>'
              f'<span class="dot">·</span>'
              f'<span>{mins} {"דקות קריאה" if he else "min read"}</span>'
              f'<span class="dot">·</span>'
              f'<span>{len(products)} {"מוצרים" if he else "picks"}</span></div>')

    head = (f'{crumb}<div class="kicker">{e(g["category"])} · '
            f'{"מדריך קנייה" if he else "Buying guide"}</div>'
            f'<h1>{e(title)}</h1><p class="dek">{e(dek)}</p>{byline}')

    hero_html = (f'<div class="hero"><img src="{e(hero)}" alt="{e(title)}" '
                 f'width="1200" height="630" fetchpriority="high"></div>')

    # --- intro -----------------------------------------------------------
    paras = L("intro")
    intro = "".join(f'<p{" class=\"lead\"" if i == 0 else ""}>{e(p)}</p>'
                    for i, p in enumerate(paras))

    disclosure = (f'<div class="note">'
                  f'<b>{"גילוי נאות" if he else "Disclosure"}.</b> '
                  + ("הקישורים בעמוד הזה הם קישורי שותפים. אם תקנו דרכם אנחנו "
                     "עשויים להרוויח עמלה, בלי תוספת עלות לכם. זה לא משפיע על "
                     "מה שנכנס לרשימה או על הסדר שלו."
                     if he else
                     "The links on this page are affiliate links. If you buy through "
                     "one we may earn a commission at no extra cost to you. It does "
                     "not affect what makes this list or the order it is in.")
                  + '</div>')

    how = (f'<h2>{"איך בחרנו" if he else "How we picked"}</h2>'
           f'<p>{e(L("how_we_pick"))}</p>')

    # --- comparison table ------------------------------------------------
    hdrs = (["#", "מוצר", "הכי מתאים ל", "מחיר משוער"] if he
            else ["#", "Product", "Best for", "Approx. price"])
    rows = "".join(
        f'<tr><td class="rank">{i}</td>'
        f'<td><a href="#p{i}">{e(pl(p, "name"))}</a></td>'
        f'<td>{e(pl(p, "tag"))}</td>'
        f'<td>{e(p["price"])}</td></tr>'
        for i, p in enumerate(products, 1))
    table = (f'<h2>{"השוואה מהירה" if he else "At a glance"}</h2>'
             f'<div class="tablewrap"><table><thead><tr>'
             + "".join(f"<th>{e(h)}</th>" for h in hdrs)
             + f'</tr></thead><tbody>{rows}</tbody></table></div>'
             f'<p style="font-size:13.5px;color:var(--ink-3);margin-top:10px">'
             + ("המחירים הם הערכה נכון לזמן הכתיבה ומשתנים לעיתים קרובות."
                if he else
                "Prices are approximate at the time of writing and change often.")
             + "</p>")

    # --- product cards ---------------------------------------------------
    cards = []
    for i, p in enumerate(products, 1):
        img = f"{pfx}images/{slug}-{i:02d}.jpg"
        pros = "".join(f"<li>{e(x)}</li>" for x in (p.get("pros_he" if he else "pros") or p["pros"]))
        cons = "".join(f"<li>{e(x)}</li>" for x in (p.get("cons_he" if he else "cons") or p["cons"]))
        name = pl(p, "name")
        cards.append(
            f'<article class="card" id="p{i}">'
            f'<img class="card-img" src="{e(img)}" alt="{e(name)}" '
            f'width="600" height="375" loading="lazy" decoding="async">'
            f'<div class="card-in"><div class="card-top"><div class="num">{i}</div>'
            f'<div style="flex:1"><span class="tag">{e(pl(p, "tag"))}</span>'
            f'<h3>{e(name)}</h3>'
            f'<div class="price">{e(p["price"])}</div></div></div>'
            f'<p>{e(pl(p, "body"))}</p>'
            f'<div class="pc"><div class="pros"><h4>{"בעד" if he else "Why it is here"}</h4>'
            f'<ul>{pros}</ul></div>'
            f'<div class="cons"><h4>{"נגד" if he else "Worth knowing"}</h4>'
            f'<ul>{cons}</ul></div></div>'
            f'<div class="buys">'
            f'<a class="btn btn-a" rel="nofollow sponsored noopener" target="_blank" '
            f'href="{e(amazon(p["search"]))}">'
            f'{"בדקו באמזון" if he else "Check price on Amazon"}</a>'
            f'<a class="btn btn-b" rel="nofollow sponsored noopener" target="_blank" '
            f'href="{e(aliexpress(p["search"]))}">AliExpress</a>'
            f'</div></div></article>')

    picks_h = f'<h2>{"הבחירות" if he else "The picks"}</h2>'

    # --- faq -------------------------------------------------------------
    faq_items = "".join(
        f'<details><summary>{e(f.get("q_he") if he else f["q"])}</summary>'
        f'<p>{e(f.get("a_he") if he else f["a"])}</p></details>'
        for f in g.get("faq", []))
    faq = (f'<h2>{"שאלות נפוצות" if he else "Common questions"}</h2>'
           f'<div class="faq">{faq_items}</div>') if faq_items else ""

    other = f'<p style="margin-top:34px"><a href="posts.html">← {"כל המדריכים" if he else "All guides"}</a></p>'

    final_disc = (f'<p class="disc">'
                  + ("כשותפים של אמזון ושל עליאקספרס אנחנו מרוויחים עמלה מרכישות מזכות. "
                     "המחירים והזמינות נכונים לזמן הפרסום ועשויים להשתנות."
                     if he else
                     "As an Amazon Associate and an AliExpress affiliate we earn from "
                     "qualifying purchases. Prices and availability are accurate as of "
                     "the date of publication and may change.")
                  + "</p>")

    body = (nav(NAV_HE if he else NAV_EN, f"post-{slug}.html", pfx)
            + '<div class="wrap">' + head + hero_html
            + '<div class="body">' + intro + disclosure + how + table
            + picks_h + "".join(cards) + faq + other + final_disc
            + "</div></div>" + footer(he, pfx))

    ld = json_ld(g, he, canon, hero)
    alt = (f'<link rel="alternate" hreflang="en" href="{SITE}/post-{slug}.html">'
           f'<link rel="alternate" hreflang="he" href="{SITE}/he/post-{slug}.html">'
           f'<link rel="alternate" hreflang="x-default" href="{SITE}/post-{slug}.html">')
    return page(f"{title} — {BRAND}", dek, body, canonical=canon, he=he,
                extra_head=ld + alt, og_image=f"{SITE}/images/hero-{slug}.jpg")


def json_ld(g, he, canon, hero):
    """Article + ItemList + FAQPage, so the guide is machine-legible."""
    L = (lambda k: g.get(k + "_he") or g[k]) if he else (lambda k: g[k])

    def pl(p, k):
        return (p.get(k + "_he") or p[k]) if he else p[k]

    blocks = [{
        "@context": "https://schema.org", "@type": "Article",
        "headline": L("title"), "description": L("dek"),
        "datePublished": g["updated"], "dateModified": g["updated"],
        "inLanguage": "he" if he else "en",
        "author": {"@type": "Organization", "name": AUTHOR_HE if he else AUTHOR},
        "publisher": {"@type": "Organization", "name": BRAND},
        "image": f"{SITE}/images/hero-{g['slug']}.jpg",
        "mainEntityOfPage": canon,
    }, {
        "@context": "https://schema.org", "@type": "ItemList",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(g["products"]),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": pl(p, "name"),
             "url": f"{canon}#p{i}"}
            for i, p in enumerate(g["products"], 1)],
    }]
    if g.get("faq"):
        blocks.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": f.get("q_he") if he else f["q"],
                 "acceptedAnswer": {"@type": "Answer",
                                    "text": f.get("a_he") if he else f["a"]}}
                for f in g["faq"]],
        })
    return "".join(f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
                   for b in blocks)


# --------------------------------------------------------------------------
# guides index
# --------------------------------------------------------------------------
def render_index(guides, he=False):
    pfx = "../" if he else ""
    title = ("מדריכי קנייה — fashionhotspot" if he
             else f"Buying guides — {BRAND}")
    dek = ("מדריכים מפורטים למוצרים ששווים את הכסף, עם הסבר למה בחרנו בכל אחד "
           "ומה החיסרון שלו." if he else
           "In-depth guides to gear worth buying — what we picked, why, and the "
           "trade-off you are accepting with each one.")
    cards = []
    for g in guides:
        L = (lambda k: g.get(k + "_he") or g[k]) if he else (lambda k: g[k])
        upd = fmt_date_he(g["updated"]) if he else fmt_date(g["updated"])
        cards.append(
            f'<a class="gcard" href="post-{g["slug"]}.html">'
            f'<img src="{pfx}images/hero-{g["slug"]}.jpg" alt="{e(L("title"))}" '
            f'width="1200" height="630" loading="lazy" decoding="async">'
            f'<div class="gcard-in"><span class="tag">{e(g["category"])}</span>'
            f'<h3>{e(L("title"))}</h3>'
            f'<p class="sum">{e(L("dek"))}</p>'
            f'<div class="meta">{e(upd)} · {len(g["products"])} '
            f'{"מוצרים" if he else "picks"}</div></div></a>')

    body = (nav(NAV_HE if he else NAV_EN, "posts.html", pfx)
            + '<div class="wide">'
            + f'<div class="kicker" style="margin-top:34px">'
              f'{"מדריכי קנייה" if he else "Buying guides"}</div>'
            + f'<h1>{"מה באמת שווה לקנות" if he else "What is actually worth buying"}</h1>'
            + f'<p class="dek" style="max-width:640px">{e(dek)}</p>'
            + f'<div class="grid">{"".join(cards)}</div>'
            + '<p class="disc" style="max-width:760px">'
            + ("כשותפים של אמזון ושל עליאקספרס אנחנו מרוויחים עמלה מרכישות מזכות."
               if he else
               "As an Amazon Associate and an AliExpress affiliate we earn from "
               "qualifying purchases.")
            + "</p></div>" + footer(he, pfx))
    canon = f"{SITE}/{'he/' if he else ''}posts.html"
    alt = (f'<link rel="alternate" hreflang="en" href="{SITE}/posts.html">'
           f'<link rel="alternate" hreflang="he" href="{SITE}/he/posts.html">')
    return page(title, dek, body, canonical=canon, he=he, extra_head=alt,
                og_image=f"{SITE}/images/hero-{guides[0]['slug']}.jpg" if guides else None)


# --------------------------------------------------------------------------
def render_sitemap(guides):
    today = date.today().isoformat()
    urls = [("/", "1.0", "daily"), ("/posts.html", "0.9", "weekly"),
            ("/he/posts.html", "0.7", "weekly"), ("/about.html", "0.5", "monthly"),
            ("/contact.html", "0.4", "monthly"), ("/privacy.html", "0.3", "yearly"),
            ("/terms.html", "0.3", "yearly")]
    for g in guides:
        urls.append((f"/post-{g['slug']}.html", "0.8", "monthly"))
        urls.append((f"/he/post-{g['slug']}.html", "0.6", "monthly"))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for loc, pri, freq in urls:
        alt = ""
        m = re.match(r"^(?:/he)?/post-(.+)\.html$", loc)
        if m:
            s = m.group(1)
            alt = (f'    <xhtml:link rel="alternate" hreflang="en" href="{SITE}/post-{s}.html"/>\n'
                   f'    <xhtml:link rel="alternate" hreflang="he" href="{SITE}/he/post-{s}.html"/>\n')
        out.append(f"  <url>\n    <loc>{SITE}{loc}</loc>\n"
                   f"    <lastmod>{today}</lastmod>\n"
                   f"    <changefreq>{freq}</changefreq>\n"
                   f"    <priority>{pri}</priority>\n{alt}  </url>")
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
    args = ap.parse_args()

    gs = load_guides()
    if not gs:
        sys.exit("no content/*.json found")
    ordered = ([gs[s] for s in ORDER if s in gs]
               + [g for s, g in gs.items() if s not in ORDER])
    targets = [gs[s] for s in args.slugs] if args.slugs else ordered

    (ROOT / "he").mkdir(exist_ok=True)
    n = 0
    for g in targets:
        (ROOT / f"post-{g['slug']}.html").write_text(render_guide(g, False), encoding="utf-8")
        (ROOT / "he" / f"post-{g['slug']}.html").write_text(render_guide(g, True), encoding="utf-8")
        n += 2
        print(f"  post-{g['slug']}.html + he/")

    (ROOT / "posts.html").write_text(render_index(ordered, False), encoding="utf-8")
    (ROOT / "he" / "posts.html").write_text(render_index(ordered, True), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(render_sitemap(ordered), encoding="utf-8")
    print(f"\n{n} guide pages, posts.html x2, sitemap.xml ({len(ordered)} guides)")


if __name__ == "__main__":
    main()
