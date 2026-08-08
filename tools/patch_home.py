#!/usr/bin/env python
"""Wire the buying guides into index.html.

Before this, index.html referenced posts.html exactly zero times — every guide
was an orphan page, unreachable from the homepage and barely crawlable. This
adds a nav link, a featured-guides strip and footer links, and registers the
i18n strings in all six languages so the new links are not blank for anyone.

Idempotent: running it twice changes nothing.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

GUIDES_LABEL = {
    "en": "📚 Guides", "he": "📚 מדריכים", "es": "📚 Guías",
    "fr": "📚 Guides", "de": "📚 Ratgeber", "el": "📚 Οδηγοί",
}
STRIP = {
    "en": ("Buying guides", "What is actually worth buying",
           "In-depth guides to gear worth owning — what we picked, why, and the "
           "trade-off you accept with each one.", "Read the guides →"),
    "he": ("מדריכי קנייה", "מה באמת שווה לקנות",
           "מדריכים מעמיקים לציוד ששווה להחזיק — מה בחרנו, למה, ומה ההתלבטות "
           "שאתם מקבלים על עצמכם.", "לכל המדריכים →"),
    "es": ("Guías de compra", "Lo que de verdad vale la pena",
           "Guías detalladas del equipo que merece la pena — qué elegimos, por "
           "qué, y qué compromiso aceptas.", "Ver las guías →"),
    "fr": ("Guides d’achat", "Ce qui vaut vraiment la peine",
           "Des guides détaillés du matériel qui en vaut la peine — nos choix, "
           "pourquoi, et le compromis accepté.", "Lire les guides →"),
    "de": ("Kaufratgeber", "Was sich wirklich lohnt",
           "Ausführliche Ratgeber zu lohnenswerter Ausrüstung — unsere Auswahl, "
           "warum, und der Kompromiss dabei.", "Zu den Ratgebern →"),
    "el": ("Οδηγοί αγορών", "Τι αξίζει πραγματικά",
           "Αναλυτικοί οδηγοί για εξοπλισμό που αξίζει — τι επιλέξαμε, γιατί, "
           "και τι συμβιβασμό δέχεστε.", "Δείτε τους οδηγούς →"),
}

s = INDEX.read_text(encoding="utf-8")
orig = s
done = []

# ---- 1. i18n keys ---------------------------------------------------------
m = re.search(r"^const I18N = (\{.*\});\s*$", s, re.M)
if not m:
    sys.exit("could not find the I18N dictionary")
i18n = json.loads(m.group(1))
added = False
for lang, obj in i18n.items():
    k, t, sub, cta = STRIP.get(lang, STRIP["en"])
    for key, val in (("nav_guides", GUIDES_LABEL.get(lang, GUIDES_LABEL["en"])),
                     ("g_kicker", k), ("g_title", t), ("g_sub", sub),
                     ("g_cta", cta), ("f_guides", GUIDES_LABEL.get(lang, "Guides").replace("📚 ", "")),
                     ("f_terms", {"he": "תנאי שימוש", "es": "Términos", "fr": "Conditions",
                                  "de": "AGB", "el": "Όροι"}.get(lang, "Terms"))):
        if key not in obj:
            obj[key] = val
            added = True
if added:
    s = s[:m.start()] + "const I18N = " + json.dumps(i18n, ensure_ascii=False) + ";" + s[m.end():]
    done.append("i18n keys in %d languages" % len(i18n))

# ---- 2. nav link ----------------------------------------------------------
nav_old = '    <a href="#deals" class="hdr-cta" data-i18n="todays_deals">🔥 Today\'s Deals</a>'
nav_new = ('    <a href="posts.html" class="lang-link" data-i18n="nav_guides" '
           'style="font-weight:700;white-space:nowrap;margin-inline-end:4px;">📚 Guides</a>\n'
           + nav_old)
if 'href="posts.html"' not in s and nav_old in s:
    s = s.replace(nav_old, nav_new, 1)
    done.append("nav link")

# ---- 3. featured guides strip, just above the footer ----------------------
STRIP_HTML = """
<!-- BUYING GUIDES -->
<section id="guides" style="max-width:1100px;margin:0 auto;padding:56px 22px 8px;">
  <div style="background:linear-gradient(135deg,#fff 0%,#FFF6EE 100%);border:1px solid #F0DFD2;
              border-radius:22px;padding:34px 30px;display:flex;gap:28px;align-items:center;
              flex-wrap:wrap;box-shadow:0 8px 30px rgba(58,34,48,.07);">
    <div style="flex:1 1 320px;min-width:280px;">
      <div style="font-size:11.5px;font-weight:800;letter-spacing:.09em;text-transform:uppercase;
                  color:#E14B4B;margin-bottom:9px;" data-i18n="g_kicker">Buying guides</div>
      <h2 style="font-size:clamp(24px,3.4vw,32px);line-height:1.2;color:#3A2230;margin:0 0 12px;
                 letter-spacing:-.02em;" data-i18n="g_title">What is actually worth buying</h2>
      <p style="color:#5A4550;font-size:16px;line-height:1.6;margin:0 0 20px;" data-i18n="g_sub">In-depth
        guides to gear worth owning — what we picked, why, and the trade-off you accept with each one.</p>
      <a href="posts.html" style="display:inline-block;background:#E14B4B;color:#fff;text-decoration:none;
         font-weight:700;font-size:15px;padding:12px 24px;border-radius:11px;"
         data-i18n="g_cta">Read the guides →</a>
    </div>
    <div style="flex:0 1 300px;display:grid;grid-template-columns:1fr 1fr;gap:10px;min-width:240px;">
      <a href="post-coffee.html" style="text-decoration:none;color:#3A2230;background:#fff;border:1px solid #F0DFD2;border-radius:12px;padding:13px 14px;font-size:13.5px;font-weight:600;line-height:1.35;">☕ Coffee</a>
      <a href="post-tech.html" style="text-decoration:none;color:#3A2230;background:#fff;border:1px solid #F0DFD2;border-radius:12px;padding:13px 14px;font-size:13.5px;font-weight:600;line-height:1.35;">📱 Tech</a>
      <a href="post-kitchen.html" style="text-decoration:none;color:#3A2230;background:#fff;border:1px solid #F0DFD2;border-radius:12px;padding:13px 14px;font-size:13.5px;font-weight:600;line-height:1.35;">🍳 Kitchen</a>
      <a href="post-smart-home.html" style="text-decoration:none;color:#3A2230;background:#fff;border:1px solid #F0DFD2;border-radius:12px;padding:13px 14px;font-size:13.5px;font-weight:600;line-height:1.35;">🏠 Smart home</a>
    </div>
  </div>
</section>

<!-- FOOTER -->"""
if 'id="guides"' not in s and "<!-- FOOTER -->" in s:
    s = s.replace("<!-- FOOTER -->", STRIP_HTML.lstrip("\n"), 1)
    done.append("featured guides strip")

# ---- 4. footer links ------------------------------------------------------
foot_old = '    <a href="privacy.html" class="lang-link" data-i18n="f_privacy">Privacy Policy</a>'
foot_new = (foot_old
            + '\n    <a href="terms.html" class="lang-link" data-i18n="f_terms">Terms</a>'
            + '\n    <a href="posts.html" class="lang-link" data-i18n="f_guides">Guides</a>')
if 'data-i18n="f_guides"' not in s and foot_old in s:
    s = s.replace(foot_old, foot_new, 1)
    done.append("footer links (guides + terms)")

INDEX.write_text(s, encoding="utf-8")
print("applied:", ", ".join(done) if done else "nothing (already patched)")
print("posts.html references in index.html:", s.count("posts.html"))
