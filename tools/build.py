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
import argparse, html, json, re, sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import (CSS, FONTS, RTL_FONT, THEME_BOOT, THEME_TOGGLE,   # noqa: E402
                   THEME_SCRIPT, GUIDE_SCRIPT, INDEX_SCRIPT)
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

# Filter groups for the guides index.
#
# `category` in the content JSON is one per guide — 35 guides, 35 distinct
# categories — so filtering on it gives 35 chips that each narrow the page to a
# single card. That is a slow way to click a link, not a filter. These are the
# coarse buckets the chip row actually uses; the specific category still shows
# on every card, so nothing is hidden by the grouping.
#
# Keyed by slug rather than by category label so the mapping survives
# translation: the chips carry the key in data-cat and only the visible text is
# localised. A slug missing from here falls into "home", which is wrong-ish but
# visible, rather than vanishing from every filter.
GROUPS = {
    "grp_home": ["air", "bathroom", "cleaning", "garden", "laundry", "lighting",
                 "security", "smart-home", "storage", "tools"],
    "grp_kitchen": ["coffee", "grilling", "kitchen"],
    "grp_tech": ["audio", "gaming", "home-office", "phone", "photography", "tech"],
    "grp_health": ["fitness", "health", "running", "sleep"],
    "grp_beauty": ["beauty", "fashion", "haircare", "skincare"],
    "grp_family": ["baby", "back-to-school", "kids", "pets"],
    "grp_outdoors": ["car", "cycling", "outdoor", "travel"],
}
GROUP_OF = {slug: key for key, slugs in GROUPS.items() for slug in slugs}

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


def load_ali_links():
    """Pre-generated tracked AliExpress links, keyed by search term.

    Built by whatsapp-deals-bot/gen-aliexpress-guide-links.js, which calls
    aliexpress.affiliate.link.generate once per term and writes the resulting
    s.click.aliexpress.com URLs here. Generation is a separate step because it
    needs the API credentials from that repo's .env, which this one does not
    have and should not.

    Re-run it after adding or renaming a `search` value in content/*.json:
        node gen-aliexpress-guide-links.js
    """
    # data/, NOT content/ — build.py globs content/*.json expecting guide
    # documents and dies with KeyError: 'slug' on anything else in there.
    f = ROOT / "data" / "aliexpress-links.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


ALI_LINKS = load_ali_links()


def aliexpress(term):
    """A monetized AliExpress link for a search term.

    This used to return a bare /wholesale?SearchText= URL with no tracking of
    any kind, while amazon() directly above appended &tag=. Turning AliExpress
    on in the guides therefore added 350 links across 210 pages that sent
    AliExpress free traffic and earned nothing.

    Note the URL shape: affiliate.link.generate rejects /wholesale?SearchText=
    with 405 "The result is empty" but accepts /w/wholesale-<slug>.html, which
    is why the generator asks for that form.

    A missing entry falls back to the untracked URL — a working link that earns
    nothing is better than a dead one — so check the count after a rebuild if
    you have just edited content/*.json.
    """
    tracked = ALI_LINKS.get(term)
    if tracked:
        return tracked
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
    # The "/ guides" kicker beside the wordmark says which half of the site you
    # are in. It is decoration next to a link that already says the same thing,
    # so it is aria-hidden rather than read out twice, and it drops on mobile.
    return (f'<div class="nav"><div class="nav-in">'
            f'<a class="brand" href="{e(r)}index.html">'
            f'<span class="logo">fashion<span>hotspot</span></span>'
            f'<span class="mono navkick" aria-hidden="true">/ {e(t(lang, "guides")).lower()}</span>'
            f'</a>'
            f'<nav class="nav-links">{links}</nav>{THEME_TOGGLE}</div></div>')


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


def page_shell(lang, title, desc, body, *, canonical, extra_head="", og_image=None,
               body_end=""):
    cfg = LANGS[lang]
    rtl = cfg["dir"] == "rtl"
    fonts = FONTS + (RTL_FONT if rtl else "")
    if cfg["font"] and cfg["font"] in FONT_LINKS and not rtl:
        fonts += FONT_LINKS[cfg["font"]]
    og = f'<meta property="og:image" content="{e(og_image)}">' if og_image else ""
    extra_css = ""
    if cfg["font"] == "Noto Sans":
        # Archivo is Latin-only, so Greek would fall through to a system font and
        # lose the 900 weight the whole design rests on. The mono classes are in
        # this list for the same reason — JetBrains Mono does cover Greek, but
        # mixing it with Noto Sans headings looked like two unrelated pages.
        extra_css = ("<style>body,h1,h2,h3,.logo,.chip,.mono,.sidenum,.rank,th,"
                     ".pc h4{font-family:'Noto Sans',system-ui,sans-serif}"
                     ".mono,th,.pc h4{letter-spacing:.08em}</style>")
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{cfg['dir']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{THEME_BOOT}
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
{THEME_SCRIPT}{body_end}
</body>
</html>
"""


# --------------------------------------------------------------------------
# a guide
# --------------------------------------------------------------------------
def render_guide(g, lang, siblings=()):
    slug = g["slug"]
    r = rel_root(lang)
    page = f"post-{slug}.html"
    canon = url(lang, page)
    products = g["products"]

    crumb = (f'<div class="crumbs mono"><a href="{r}index.html">{e(t(lang, "home"))}</a> › '
             f'<a href="posts.html">{e(t(lang, "guides"))}</a> › {e(g["category"])}</div>')
    # Category, length and freshness all live in the kicker now; the byline row
    # underneath the dek carries only who wrote it and how many picks there are.
    kicker = (f'<span class="kicker mono">{e(g["category"])} · '
              f'{g.get("read_minutes", 9)} {e(t(lang, "min_read"))} · '
              f'{e(t(lang, "updated"))} '
              f'<time datetime="{e(g["updated"])}">{e(fmt_date(g["updated"], lang))}</time>'
              f'</span>')
    byline = (f'<div class="byline mono"><span class="av" aria-hidden="true"></span>'
              f'<b>{e(AUTHOR.get(lang, AUTHOR[DEFAULT]))}</b>'
              f'<span class="end">{len(products)} {e(t(lang, "picks"))}</span></div>')
    head = (f'{crumb}{kicker}<h1>{e(g["title"])}</h1>'
            f'<p class="dek">{e(g["dek"])}</p>{byline}')
    # The lead image breaks out of the 760px reading column — it is the one
    # element on the page the design lets run to 1080px.
    hero = (f'<div class="hero"><img src="{r}images/hero-{slug}.jpg" '
            f'alt="{e(g["title"])}" width="1600" height="840" fetchpriority="high"></div>')
    # "The short version" is the number-one pick and its own tag, read straight
    # off the guide data. It is a pointer into the list below, not a separate
    # editorial claim that could go stale when the list is regenerated.
    short = ""
    if products:
        short = (f'<div class="short"><div class="mono">{e(t(lang, "short_version"))}</div>'
                 f'<div class="lead-pick">{e(products[0]["name"])}</div>'
                 f'<div class="lead-tag mono">{e(products[0]["tag"])}</div></div>')

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
        # The trade-off line is the first "con" promoted onto the price row,
        # which is where a reader deciding on price actually looks. It is the
        # same sentence that appears in the list below — surfaced, not invented.
        # A pick with no cons recorded simply gets no line rather than a blank
        # label, because "Trade-off:" followed by nothing reads as an omission.
        cons_list = p.get("cons", [])
        trade = (f'<span class="tradeoff mono"><b>{e(t(lang, "tradeoff"))}:</b> '
                 f'{e(cons_list[0])}</span>' if cons_list else "")
        cards.append(
            f'<article class="card" id="p{i}">'
            f'<img class="card-img" src="{r}images/{slug}-{i:02d}.jpg" alt="{e(p["name"])}" '
            f'width="1200" height="750" loading="lazy" decoding="async">'
            f'<div class="card-in">'
            f'<span class="badge mono">{i:02d} · {e(p["tag"])}</span>'
            f'<h3>{e(p["name"])}</h3>'
            f'<p>{e(p["body"])}</p>'
            f'<div class="priceline"><span class="price">{e(p["price"])}</span>{trade}</div>'
            f'<div class="pc"><div class="pros"><h4>{e(t(lang, "why_here"))}</h4><ul>{pros}</ul></div>'
            f'<div class="cons"><h4>{e(t(lang, "worth_knowing"))}</h4><ul>{cons}</ul></div></div>'
            f'<div class="buys">{buys}</div></div></article>')

    faq_items = "".join(
        f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>'
        for f in g.get("faq", []))
    faq = (f'<h2>{e(t(lang, "faq"))}</h2><div class="faq">{faq_items}</div>'
           if faq_items else "")

    # The closer sends the reader to the deals feed, which is the one thing the
    # site can promise here. The design's original wording offered to message
    # people when a product on the page hit a low — the guides carry no price
    # tracking and no signup, so that button would not have done what it said.
    closer = (f'<div class="closer"><h2>{e(t(lang, "closer_title"))}</h2>'
              f'<p>{e(t(lang, "closer_body"))}</p>'
              f'<a class="btn" href="{r}index.html">{e(t(lang, "deals"))} →</a></div>')

    prog = '<div class="progtrack"><div class="progbar" id="prog"></div></div>'

    body = (nav(lang, page) + prog + '<div class="wrap">' + head + '</div>' + hero
            + '<div class="wrap"><div class="body">' + intro + short + note + how + table
            + f'<h2>{e(t(lang, "the_picks"))}</h2>' + "".join(cards) + faq
            + related_guides(g, siblings, lang) + closer
            + f'<p class="mono" style="margin-top:34px">'
              f'<a href="posts.html">← {e(t(lang, "all_guides"))}</a></p>'
            + f'<p class="disc">{e(disclosure(lang, SHOW_AMZ, SHOW_ALI))}</p>'
            + "</div></div>" + footer(lang, page))

    # <title> and <h1> are deliberately different. The h1 keeps the editorial
    # headline ("Travel Gear That Earns Its Weight"); the title tag targets what
    # people actually type ("Best Travel Gear 2026..."). Nobody searches a
    # magazine headline, and a page whose title matches no query is invisible
    # however well it is written.
    #
    # seo_title is English-only for now. Translations fall back to the editorial
    # title, which is correct behaviour, not a gap to paper over — a machine
    # translation of an English keyword phrase does not match what a Hebrew or
    # Spanish speaker types. Those need their own keyword research.
    # English only. The merge fills untranslated fields from the English doc, so
    # without the lang check every Hebrew, Spanish, French, German and Greek
    # page got an English keyword title above a translated h1 — worse than the
    # editorial title, because it matches no query in any language AND looks
    # broken. Give the other languages their own seo_title when someone has
    # done keyword research for them; until then the translated title is right.
    head_title = (g.get("seo_title") if lang == "en" else None) or g["title"]

    return page_shell(lang, f'{head_title} — {BRAND}', g["dek"], body,
                      canonical=canon,
                      extra_head=json_ld(g, lang, canon) + alternates(page),
                      og_image=f"{SITE}/images/hero-{slug}.jpg",
                      body_end=GUIDE_SCRIPT)


def price_offer(raw):
    """Turn a human price string into an Offer, or None if it is not a price.

    Prices here are written as ranges for a reason — we do not hold live pricing
    and Amazon's changes hourly — so the honest schema type is AggregateOffer
    with lowPrice/highPrice, not Offer with a single invented number. Strings
    that carry no digits at all ("varies by size") get no offer rather than a
    guessed one.
    """
    if not raw:
        return None
    nums = [int(n) for n in re.findall(r"\d+", str(raw))]
    if not nums:
        return None
    lo, hi = min(nums), max(nums)
    offer = {"@type": "AggregateOffer", "priceCurrency": "USD",
             "lowPrice": lo, "highPrice": hi,
             "availability": "https://schema.org/InStock"}
    if lo == hi:
        offer = {"@type": "Offer", "priceCurrency": "USD", "price": lo,
                 "availability": "https://schema.org/InStock"}
    return offer


def json_ld(g, lang, canon):
    # Every product becomes a real Product node rather than a bare ListItem.
    # A ListItem with a name and a URL tells a search engine nothing it could
    # not read off the page; Product + AggregateOffer is what makes a roundup
    # eligible for price and availability treatment in results.
    #
    # Deliberately absent: aggregateRating and Review. The advice everywhere is
    # to add star ratings because they lift click-through, but this site does
    # not test products — lint.py actively fails any copy claiming it does — and
    # inventing ratings would be both a lie and a Google structured-data
    # violation for self-serving reviews. If real testing ever happens, add them
    # then.
    items = []
    for i, p in enumerate(g["products"], 1):
        node = {"@type": "Product", "name": p["name"],
                "description": p.get("tag") or p.get("body", "")[:160],
                "url": f"{canon}#p{i}"}
        offer = price_offer(p.get("price"))
        if offer:
            node["offers"] = offer
        items.append({"@type": "ListItem", "position": i, "item": node})

    blocks = [{
        "@context": "https://schema.org", "@type": "Article",
        "headline": g["title"], "description": g["dek"],
        "datePublished": g["updated"], "dateModified": g["updated"],
        "inLanguage": lang,
        "author": {"@type": "Organization", "name": AUTHOR.get(lang, AUTHOR[DEFAULT])},
        # Google will not show Article rich results without publisher.logo.
        "publisher": {"@type": "Organization", "name": BRAND,
                      "url": SITE,
                      "logo": {"@type": "ImageObject",
                               "url": f"{SITE}/icon-512.png",
                               "width": 512, "height": 512}},
        "image": f"{SITE}/images/hero-{g['slug']}.jpg",
        "mainEntityOfPage": canon,
    }, {
        "@context": "https://schema.org", "@type": "ItemList",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(g["products"]),
        "itemListElement": items,
    }, {
        # The crumbs were on the page visually but not in structured data, so
        # search results showed a bare URL where a path could have been.
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": t(lang, "home"),
             "item": f"{SITE}/{LANGS[lang]['path']}"},
            {"@type": "ListItem", "position": 2, "name": t(lang, "guides"),
             "item": f"{SITE}/{LANGS[lang]['path']}posts.html"},
            {"@type": "ListItem", "position": 3, "name": g["title"], "item": canon},
        ],
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


def related_guides(g, siblings, lang, limit=3):
    """Guides to read next, drawn from the same GROUPS bucket.

    Until this existed there were ZERO links from one guide to another across
    221 pages. Two things follow from that. A reader who finishes a guide has
    nowhere to go except away, and search engines see 221 orphans instead of a
    connected set of pages that are visibly about related subjects — internal
    links are how a site tells a crawler which of its pages belong together.

    `siblings` arrives already translated into `lang`, so the titles here are in
    the same language as the page they sit on. Passing the English list would
    put English headlines under a Hebrew guide.

    Same bucket first, since that is a real relationship rather than a guess.
    If the bucket is thin the row is topped up with the most recently updated
    other guides, because a short row of genuinely related pages plus a couple
    of good ones beats padding it with something arbitrary — and beats printing
    a heading above one link.
    """
    slug = g["slug"]
    grp = GROUP_OF.get(slug)
    pool = [x for x in siblings
            if x["slug"] != slug and GROUP_OF.get(x["slug"]) == grp] if grp else []
    pool.sort(key=lambda x: x.get("updated", ""), reverse=True)

    if len(pool) < limit:
        seen = {x["slug"] for x in pool} | {slug}
        extra = sorted((x for x in siblings if x["slug"] not in seen),
                       key=lambda x: x.get("updated", ""), reverse=True)
        pool += extra[: limit - len(pool)]

    picks = pool[:limit]
    if len(picks) < 2:          # not worth a heading
        return ""

    label = t(lang, grp) if grp else t(lang, "guides")
    head = t(lang, "related_same").replace("{grp}", label)
    r = rel_root(lang)
    items = "".join(
        f'<a class="relcard" href="post-{x["slug"]}.html">'
        f'<img src="{r}images/hero-{x["slug"]}.jpg" alt="" '
        f'width="1600" height="840" loading="lazy" decoding="async">'
        f'<span class="relcard-in"><b>{e(x["title"])}</b>'
        f'<span class="mono">{x.get("read_minutes", 9)} {e(t(lang, "min_read"))} · '
        f'{len(x["products"])} {e(t(lang, "picks"))}</span></span></a>'
        for x in picks)
    return (f'<div class="related"><div class="mono relhead">{e(t(lang, "read_next"))}'
            f' · {e(head)}</div><div class="relgrid">{items}</div></div>')


def render_lang_home(guides, lang):
    """A landing page at a language folder root: /he/, /es/, /fr/, /de/, /el/.

    Those five URLs answered 403 Forbidden. The folders held guide pages but no
    index, so the server refused to list the directory — a Hebrew reader who
    typed the folder, or followed a shortened link to it, got an error page. It
    also meant each language had no single entry point to link to or submit.

    Deliberately a thin page: a heading, a line, and a link straight into that
    language's guide index, which is the page that actually does the work. A
    second full grid here would compete with posts.html for the same queries.
    """
    r = rel_root(lang)
    n = len(guides)
    by_date = sorted(guides, key=lambda x: x.get("updated", ""), reverse=True)[:6]
    items = "".join(
        f'<a class="sideitem" href="post-{g["slug"]}.html">'
        f'<span class="sidenum">{i:02d}</span><span><b>{e(g["title"])}</b>'
        f'<span class="mono">{e(g["category"])} · {g.get("read_minutes", 9)} '
        f'{e(t(lang, "min_read"))}</span></span></a>'
        for i, g in enumerate(by_date, 1))

    body = (nav(lang, "index.html") + '<div class="wide">'
            + f'<div class="masthead"><div class="mono eyebrow">{n} · '
              f'{e(t(lang, "guides"))}</div>'
              f'<h1>{e(t(lang, "home_title"))}</h1>'
              f'<p class="dek">{e(t(lang, "home_intro"))}</p></div>'
            + f'<p class="mono" style="margin:0 0 26px">'
              f'<a class="btn" href="posts.html">{e(t(lang, "browse_all"))} →</a></p>'
            + f'<div class="sidelist"><div class="mono">'
              f'{e(t(lang, "recently_updated"))}</div>{items}</div>'
            + f'<p class="disc" style="max-width:760px;margin-top:30px">'
              f'{e(disclosure(lang, SHOW_AMZ, SHOW_ALI, short=True))}</p></div>'
            + footer(lang, "index.html"))

    # canonical points at THIS page, and the alternates list the same folder
    # root in every other language — not posts.html, which is a different page.
    return page_shell(lang, f'{t(lang, "home_title")} — {BRAND}',
                      t(lang, "home_intro"), body,
                      canonical=url(lang, "index.html"),
                      extra_head=alternates("index.html"),
                      og_image=f"{SITE}/images/hero-{by_date[0]['slug']}.jpg" if by_date else None)


def render_index(guides, lang):
    r = rel_root(lang)
    n = len(guides)

    # ── masthead ──────────────────────────────────────────────────────────
    # The eyebrow states the two things the index can support: how many guides
    # there are, and that every one of them names its trade-offs. The design's
    # line here was "written by us · never scraped", which is a claim about how
    # the copy is produced and not one this pipeline can stand behind.
    masthead = (f'<div class="masthead">'
                f'<div class="mono eyebrow">{n} · {e(t(lang, "guides"))}</div>'
                f'<h1>{e(t(lang, "index_title"))}</h1>'
                f'<p class="dek">{e(t(lang, "index_dek"))}</p></div>')

    # ── featured + recently updated ───────────────────────────────────────
    # "Latest" and the numbered side list both sort on the guide's own `updated`
    # field. The design labelled this slot "most read this month"; that needs
    # analytics the site does not collect, so the ordering would have been
    # decorative and the label untrue.
    by_date = sorted(guides, key=lambda x: x.get("updated", ""), reverse=True)
    lead, rest = by_date[0], by_date[1:6]
    side = "".join(
        f'<a class="sideitem" href="post-{g["slug"]}.html">'
        f'<span class="sidenum">{i:02d}</span><span><b>{e(g["title"])}</b>'
        f'<span class="mono">{e(g["category"])} · {g.get("read_minutes", 9)} '
        f'{e(t(lang, "min_read"))}</span></span></a>'
        for i, g in enumerate(rest, 1))
    feat = (f'<div class="feat">'
            f'<a class="feat-main" href="post-{lead["slug"]}.html">'
            f'<img src="{r}images/hero-{lead["slug"]}.jpg" alt="{e(lead["title"])}" '
            f'width="1600" height="840" fetchpriority="high" decoding="async">'
            f'<div class="feat-meta mono"><span class="pill">{e(t(lang, "latest"))}</span>'
            f'<span>{e(lead["category"])} · {lead.get("read_minutes", 9)} '
            f'{e(t(lang, "min_read"))}</span></div>'
            f'<h2>{e(lead["title"])}</h2><p>{e(lead["dek"])}</p></a>'
            f'<div class="sidelist"><div class="mono">'
            f'{e(t(lang, "recently_updated"))}</div>{side}</div></div>')

    # ── filter chips ──────────────────────────────────────────────────────
    # Categories in the order the guides are already sorted in, deduped. The
    # chips are <button>s inside the document, not links, because filtering
    # never changes the URL — every card stays in the HTML for crawlers.
    present = [k for k in GROUPS
               if any(GROUP_OF.get(g["slug"], "grp_home") == k for g in guides)]
    chips = (f'<button type="button" class="chip" data-cat="" aria-pressed="true">'
             f'{e(t(lang, "all"))}</button>')
    chips += "".join(
        f'<button type="button" class="chip" data-cat="{k}" aria-pressed="false">'
        f'{e(t(lang, k))}</button>' for k in present)
    tpl = t(lang, "showing")
    filters = (f'<div class="filters" id="filters">{chips}'
               f'<span class="mono count" id="shown" data-tpl="{e(tpl)}">'
               f'{e(tpl.replace("{n}", str(n)))}</span></div>')

    # ── grid ──────────────────────────────────────────────────────────────
    cards = []
    for g in guides:
        cards.append(
            f'<a class="gcard" href="post-{g["slug"]}.html" '
            f'data-cat="{GROUP_OF.get(g["slug"], "grp_home")}">'
            f'<div class="gcard-media">'
            f'<img src="{r}images/hero-{g["slug"]}.jpg" alt="{e(g["title"])}" '
            f'width="1600" height="840" loading="lazy" decoding="async">'
            f'<span class="mono gcard-cat">{e(g["category"])}</span></div>'
            f'<div class="gcard-in">'
            f'<h3>{e(g["title"])}</h3><p class="sum">{e(g["dek"])}</p>'
            f'<div class="mono gcard-foot">'
            f'<span>{g.get("read_minutes", 9)} {e(t(lang, "min_read"))} · '
            f'{len(g["products"])} {e(t(lang, "picks"))}</span>'
            f'<span class="go">{e(t(lang, "read_guide"))} ↗</span></div></div></a>')

    body = (nav(lang, "posts.html") + '<div class="wide">'
            + masthead + feat + filters
            + f'<div class="grid">{"".join(cards)}</div>'
            + f'<p class="disc" style="max-width:760px">'
              f'{e(disclosure(lang, SHOW_AMZ, SHOW_ALI, short=True))}</p></div>'
            + footer(lang, "posts.html"))
    return page_shell(lang, f'{t(lang, "index_title")} — {BRAND}', t(lang, "index_dek"),
                      body, canonical=url(lang, "posts.html"),
                      extra_head=alternates("posts.html"),
                      og_image=f"{SITE}/images/hero-{lead['slug']}.jpg" if guides else None,
                      body_end=INDEX_SCRIPT)


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
    # Language landing pages: /he/, /es/, /fr/, /de/, /el/. These answered 403
    # until 2026-08-25 and so were never listed here. English is excluded
    # because the site root is already listed above — it is the same URL.
    for lang in LANGS:
        if LANGS[lang]["path"]:
            out.append(entry(url(lang, "index.html"), "0.7", "weekly", "index.html"))
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
    homes = 0
    for lang in langs:
        out_dir = ROOT / LANGS[lang]["path"] if LANGS[lang]["path"] else ROOT
        out_dir.mkdir(parents=True, exist_ok=True)

        # Translate every guide once, up front. The guide pages need the whole
        # set — not just their own translation — because the "read next" row
        # prints sibling TITLES and they have to be in this page's language.
        idx = [merge(g, load_translation(lang, g["slug"])) if lang != DEFAULT else g
               for g in ordered]
        by_slug = {x["slug"]: x for x in idx}

        for g in targets:
            merged = by_slug.get(g["slug"]) or (
                merge(g, load_translation(lang, g["slug"])) if lang != DEFAULT else g)
            (out_dir / f"post-{g['slug']}.html").write_text(
                render_guide(merged, lang, idx), encoding="utf-8")
            written += 1

        (out_dir / "posts.html").write_text(render_index(idx, lang), encoding="utf-8")

        # A landing page at the language folder root. English lives at the site
        # root, where index.html is the deals homepage built by the other repo —
        # writing one here would overwrite it.
        if LANGS[lang]["path"]:
            (out_dir / "index.html").write_text(render_lang_home(idx, lang), encoding="utf-8")
            homes += 1

    (ROOT / "sitemap.xml").write_text(render_sitemap(ordered), encoding="utf-8")
    print(f"{written} guide pages across {len(langs)} languages "
          f"({', '.join(langs)}), plus {len(langs)} index pages, "
          f"{homes} language home pages and sitemap.xml")


if __name__ == "__main__":
    main()
