"""The languages the guides publish in, and the page chrome for each.

The homepage already shipped in six languages, so the guides match it. English
is canonical: content/<slug>.json is the source, and content/i18n/<lang>/<slug>.json
holds a translation of it.

Only the surrounding furniture lives here — nav labels, headings, dates,
disclosures. The guide copy itself is translated separately (tools/translate.py)
because it is ~23,000 words per language and needs a model, not a lookup table.
"""

# ISO code -> everything the builder needs to render that language.
#   path  : url prefix, "" for the canonical English at the root
#   dir   : ltr / rtl, drives <html dir> and the logical CSS properties
#   font  : extra webfont for non-Latin scripts, None to use the default
LANGS = {
    "en": {"name": "English",  "path": "",    "dir": "ltr", "font": None},
    "he": {"name": "עברית",    "path": "he/", "dir": "rtl", "font": "Heebo"},
    "es": {"name": "Español",  "path": "es/", "dir": "ltr", "font": None},
    "fr": {"name": "Français", "path": "fr/", "dir": "ltr", "font": None},
    "de": {"name": "Deutsch",  "path": "de/", "dir": "ltr", "font": None},
    "el": {"name": "Ελληνικά", "path": "el/", "dir": "ltr", "font": "Noto Sans"},
}
DEFAULT = "en"
TRANSLATED = [c for c in LANGS if c != DEFAULT]      # he, es, fr, de, el

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "he": ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי",
           "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"],
    "el": ["Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου",
           "Ιουνίου", "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου",
           "Νοεμβρίου", "Δεκεμβρίου"],
}

# Page furniture. Keys are stable; values are what the reader sees.
UI = {
    "en": {
        "deals": "Deals", "guides": "Guides", "about": "About",
        "contact": "Contact", "privacy": "Privacy", "terms": "Terms",
        "home": "Home", "buying_guide": "Buying guide", "updated": "Updated",
        "min_read": "min read", "picks": "picks", "how_we_picked": "How we picked",
        "at_a_glance": "At a glance", "the_picks": "The picks",
        "faq": "Common questions", "all_guides": "All guides",
        "why_here": "Why it is here", "worth_knowing": "Worth knowing",
        "product": "Product", "best_for": "Best for", "approx_price": "Approx. price",
        "check_amazon": "Check price on Amazon",
        "price_note": "Prices are approximate at the time of writing and change often.",
        "index_title": "What is actually worth buying",
        "index_dek": "In-depth guides to gear worth owning — what we picked, why, "
                     "and the trade-off you accept with each one.",
        "disclosure_label": "Disclosure.",
        "disclosure_body": "The links on this page are affiliate links. If you buy "
                           "through one we may earn a commission at no extra cost to "
                           "you. It does not affect what makes this list or the order "
                           "it is in.",
        "no_extra_cost": "This never costs you more.",
    },
    "he": {
        "deals": "דילים", "guides": "מדריכים", "about": "עלינו",
        "contact": "צור קשר", "privacy": "פרטיות", "terms": "תנאים",
        "home": "בית", "buying_guide": "מדריך קנייה", "updated": "עודכן",
        "min_read": "דקות קריאה", "picks": "מוצרים", "how_we_picked": "איך בחרנו",
        "at_a_glance": "השוואה מהירה", "the_picks": "הבחירות",
        "faq": "שאלות נפוצות", "all_guides": "כל המדריכים",
        "why_here": "בעד", "worth_knowing": "נגד",
        "product": "מוצר", "best_for": "הכי מתאים ל", "approx_price": "מחיר משוער",
        "check_amazon": "בדקו באמזון",
        "price_note": "המחירים הם הערכה נכון לזמן הכתיבה ומשתנים לעיתים קרובות.",
        "index_title": "מה באמת שווה לקנות",
        "index_dek": "מדריכים מעמיקים לציוד ששווה להחזיק — מה בחרנו, למה, "
                     "ומה ההתלבטות שאתם מקבלים על עצמכם.",
        "disclosure_label": "גילוי נאות.",
        "disclosure_body": "הקישורים בעמוד הזה הם קישורי שותפים. אם תקנו דרכם אנחנו "
                           "עשויים להרוויח עמלה, בלי תוספת עלות לכם. זה לא משפיע על "
                           "מה שנכנס לרשימה או על הסדר שלו.",
        "no_extra_cost": "זה לא מייקר עבורכם את המוצר.",
    },
    "es": {
        "deals": "Ofertas", "guides": "Guías", "about": "Quiénes somos",
        "contact": "Contacto", "privacy": "Privacidad", "terms": "Términos",
        "home": "Inicio", "buying_guide": "Guía de compra", "updated": "Actualizado",
        "min_read": "min de lectura", "picks": "productos",
        "how_we_picked": "Cómo lo elegimos", "at_a_glance": "De un vistazo",
        "the_picks": "Las recomendaciones", "faq": "Preguntas frecuentes",
        "all_guides": "Todas las guías", "why_here": "Por qué está aquí",
        "worth_knowing": "Conviene saber", "product": "Producto",
        "best_for": "Ideal para", "approx_price": "Precio aprox.",
        "check_amazon": "Ver precio en Amazon",
        "price_note": "Los precios son aproximados en el momento de escribir y cambian a menudo.",
        "index_title": "Lo que de verdad vale la pena comprar",
        "index_dek": "Guías detalladas del equipo que merece la pena tener: qué "
                     "elegimos, por qué y qué compromiso aceptas con cada uno.",
        "disclosure_label": "Aviso.",
        "disclosure_body": "Los enlaces de esta página son de afiliados. Si compras a "
                           "través de uno podemos ganar una comisión sin coste adicional "
                           "para ti. No influye en qué entra en esta lista ni en su orden.",
        "no_extra_cost": "Nunca te cuesta más.",
    },
    "fr": {
        "deals": "Offres", "guides": "Guides", "about": "À propos",
        "contact": "Contact", "privacy": "Confidentialité", "terms": "Conditions",
        "home": "Accueil", "buying_guide": "Guide d’achat", "updated": "Mis à jour le",
        "min_read": "min de lecture", "picks": "produits",
        "how_we_picked": "Comment nous avons choisi", "at_a_glance": "En un coup d’œil",
        "the_picks": "Notre sélection", "faq": "Questions fréquentes",
        "all_guides": "Tous les guides", "why_here": "Pourquoi il est là",
        "worth_knowing": "Bon à savoir", "product": "Produit",
        "best_for": "Idéal pour", "approx_price": "Prix indicatif",
        "check_amazon": "Voir le prix sur Amazon",
        "price_note": "Les prix sont indicatifs au moment de la rédaction et changent souvent.",
        "index_title": "Ce qui vaut vraiment la peine d’être acheté",
        "index_dek": "Des guides détaillés sur le matériel qui en vaut la peine : nos "
                     "choix, pourquoi, et le compromis que vous acceptez à chaque fois.",
        "disclosure_label": "Transparence.",
        "disclosure_body": "Les liens de cette page sont des liens affiliés. Si vous "
                           "achetez via l’un d’eux, nous pouvons percevoir une commission "
                           "sans surcoût pour vous. Cela n’influence ni le contenu de "
                           "cette liste ni son ordre.",
        "no_extra_cost": "Cela ne vous coûte jamais plus cher.",
    },
    "de": {
        "deals": "Angebote", "guides": "Ratgeber", "about": "Über uns",
        "contact": "Kontakt", "privacy": "Datenschutz", "terms": "AGB",
        "home": "Startseite", "buying_guide": "Kaufratgeber", "updated": "Aktualisiert",
        "min_read": "Min. Lesezeit", "picks": "Produkte",
        "how_we_picked": "Wie wir ausgewählt haben", "at_a_glance": "Auf einen Blick",
        "the_picks": "Die Empfehlungen", "faq": "Häufige Fragen",
        "all_guides": "Alle Ratgeber", "why_here": "Warum es hier steht",
        "worth_knowing": "Gut zu wissen", "product": "Produkt",
        "best_for": "Am besten für", "approx_price": "Ca.-Preis",
        "check_amazon": "Preis bei Amazon ansehen",
        "price_note": "Die Preise sind Näherungswerte zum Zeitpunkt der Erstellung und ändern sich häufig.",
        "index_title": "Was sich wirklich zu kaufen lohnt",
        "index_dek": "Ausführliche Ratgeber zu Ausrüstung, die sich lohnt — was wir "
                     "ausgewählt haben, warum, und welchen Kompromiss Sie jeweils eingehen.",
        "disclosure_label": "Hinweis.",
        "disclosure_body": "Die Links auf dieser Seite sind Affiliate-Links. Wenn Sie "
                           "darüber kaufen, erhalten wir unter Umständen eine Provision "
                           "ohne Mehrkosten für Sie. Das beeinflusst weder die Auswahl "
                           "noch die Reihenfolge dieser Liste.",
        "no_extra_cost": "Für Sie wird es dadurch nie teurer.",
    },
    "el": {
        "deals": "Προσφορές", "guides": "Οδηγοί", "about": "Σχετικά",
        "contact": "Επικοινωνία", "privacy": "Απόρρητο", "terms": "Όροι",
        "home": "Αρχική", "buying_guide": "Οδηγός αγοράς", "updated": "Ενημερώθηκε",
        "min_read": "λεπτά ανάγνωσης", "picks": "προϊόντα",
        "how_we_picked": "Πώς επιλέξαμε", "at_a_glance": "Με μια ματιά",
        "the_picks": "Οι επιλογές", "faq": "Συχνές ερωτήσεις",
        "all_guides": "Όλοι οι οδηγοί", "why_here": "Γιατί είναι εδώ",
        "worth_knowing": "Αξίζει να ξέρετε", "product": "Προϊόν",
        "best_for": "Ιδανικό για", "approx_price": "Ενδεικτική τιμή",
        "check_amazon": "Δείτε την τιμή στο Amazon",
        "price_note": "Οι τιμές είναι ενδεικτικές κατά τη συγγραφή και αλλάζουν συχνά.",
        "index_title": "Τι αξίζει πραγματικά να αγοράσετε",
        "index_dek": "Αναλυτικοί οδηγοί για εξοπλισμό που αξίζει — τι επιλέξαμε, "
                     "γιατί, και τι συμβιβασμό δέχεστε σε κάθε περίπτωση.",
        "disclosure_label": "Γνωστοποίηση.",
        "disclosure_body": "Οι σύνδεσμοι σε αυτή τη σελίδα είναι συνδεδεμένοι. Αν "
                           "αγοράσετε μέσω κάποιου, ενδέχεται να λάβουμε προμήθεια χωρίς "
                           "επιπλέον κόστος για εσάς. Δεν επηρεάζει το τι μπαίνει στη "
                           "λίστα ούτε τη σειρά της.",
        "no_extra_cost": "Δεν σας κοστίζει ποτέ περισσότερο.",
    },
}

# ── Strings added by the 2026-08-20 guides redesign ──────────────────────────
# Kept in a separate table and merged in, rather than inserted into six blocks
# above, so that a later design change can be reviewed — or reverted — as one
# diff instead of six interleaved ones.
#
# Every label here describes something the page can actually prove:
#   `latest` / `recently_updated` sort by the guide's own `updated` date. The
#   design called this slot "most read this month", which would need analytics
#   the site does not collect, so it would have been a number we made up.
#   `tradeoff` labels the first entry of a pick's existing `cons` list. It is
#   not a new claim, it is a name for one we already publish.
UI_EXTRA = {
    "en": {"latest": "Latest guide", "recently_updated": "Recently updated",
           "all": "All", "showing": "{n} showing", "read_guide": "Read",
           "short_version": "The short version", "tradeoff": "Trade-off",
           "closer_title": "Today's deals",
           "closer_body": "See what is discounted right now.",
           "grp_home": "Home", "grp_kitchen": "Kitchen", "grp_tech": "Tech",
           "grp_health": "Health", "grp_beauty": "Beauty",
           "grp_family": "Family", "grp_outdoors": "Outdoors"},
    "he": {"latest": "המדריך האחרון", "recently_updated": "עודכנו לאחרונה",
           "all": "הכול", "showing": "{n} מוצגים", "read_guide": "לקריאה",
           "short_version": "בקצרה", "tradeoff": "על מה מוותרים",
           "closer_title": "הדילים של היום",
           "closer_body": "ראו מה מוזל עכשיו.",
           "grp_home": "בית", "grp_kitchen": "מטבח", "grp_tech": "טכנולוגיה",
           "grp_health": "בריאות", "grp_beauty": "טיפוח",
           "grp_family": "משפחה", "grp_outdoors": "בחוץ"},
    "es": {"latest": "Guía más reciente", "recently_updated": "Actualizadas hace poco",
           "all": "Todas", "showing": "{n} visibles", "read_guide": "Leer",
           "short_version": "En resumen", "tradeoff": "Lo que aceptas",
           "closer_title": "Ofertas de hoy",
           "closer_body": "Mira qué está rebajado ahora mismo.",
           "grp_home": "Hogar", "grp_kitchen": "Cocina", "grp_tech": "Tecnología",
           "grp_health": "Salud", "grp_beauty": "Belleza",
           "grp_family": "Familia", "grp_outdoors": "Aire libre"},
    "fr": {"latest": "Dernier guide", "recently_updated": "Mis à jour récemment",
           "all": "Tous", "showing": "{n} affichés", "read_guide": "Lire",
           "short_version": "En bref", "tradeoff": "Le compromis",
           "closer_title": "Les offres du jour",
           "closer_body": "Voyez ce qui est en promotion en ce moment.",
           "grp_home": "Maison", "grp_kitchen": "Cuisine", "grp_tech": "Tech",
           "grp_health": "Santé", "grp_beauty": "Beauté",
           "grp_family": "Famille", "grp_outdoors": "Plein air"},
    "de": {"latest": "Neuester Ratgeber", "recently_updated": "Kürzlich aktualisiert",
           "all": "Alle", "showing": "{n} sichtbar", "read_guide": "Lesen",
           "short_version": "Kurz gesagt", "tradeoff": "Der Kompromiss",
           "closer_title": "Angebote heute",
           "closer_body": "Sieh, was gerade reduziert ist.",
           "grp_home": "Zuhause", "grp_kitchen": "Küche", "grp_tech": "Technik",
           "grp_health": "Gesundheit", "grp_beauty": "Beauty",
           "grp_family": "Familie", "grp_outdoors": "Draußen"},
    "el": {"latest": "Πιο πρόσφατος οδηγός", "recently_updated": "Ενημερώθηκαν πρόσφατα",
           "all": "Όλα", "showing": "{n} εμφανίζονται", "read_guide": "Διαβάστε",
           "short_version": "Με λίγα λόγια", "tradeoff": "Ο συμβιβασμός",
           "closer_title": "Οι προσφορές σήμερα",
           "closer_body": "Δείτε τι είναι σε έκπτωση αυτή τη στιγμή.",
           "grp_home": "Σπίτι", "grp_kitchen": "Κουζίνα", "grp_tech": "Τεχνολογία",
           "grp_health": "Υγεία", "grp_beauty": "Ομορφιά",
           "grp_family": "Οικογένεια", "grp_outdoors": "Έξω"},
}
for _code, _extra in UI_EXTRA.items():
    UI[_code].update(_extra)

AUTHOR = {
    "en": "The fashionhotspot editors", "he": "מערכת fashionhotspot",
    "es": "La redacción de fashionhotspot", "fr": "La rédaction de fashionhotspot",
    "de": "Die fashionhotspot-Redaktion", "el": "Η σύνταξη του fashionhotspot",
}

# Networks named in the disclosure, per language.
#
# ── Why there are two Amazon wordings ────────────────────────────────────────
# "As an Amazon Associate we earn from qualifying purchases" is the sentence
# Amazon REQUIRES you to display — once you are actually an Associate. Saying it
# before approval is a false statement about a commercial relationship, on a
# site Amazon reads while deciding whether to approve you. It is the wrong claim
# to be making at exactly the moment it is most likely to be checked.
#
# So the Amazon line has two states, driven by `amazon_associate_status` in
# site-config.json:
#
#   "pending"  (default) — says the application is in, and that nothing is
#                          earned from Amazon links yet. True today.
#   "approved"           — the official required sentence. Flip the config value
#                          the day the acceptance email arrives; every page and
#                          all six languages follow from this one file.
#
# The price/availability tail is unrelated to membership — Amazon requires it
# next to any price you display, regardless — so it stays in both states.
NETWORKS = {
    "en": {"amazon_none": "We are not an Amazon Associate and earn nothing from Amazon links today.",
           "amazon": "Amazon Associate", "aliexpress": "AliExpress affiliate",
           "tpl": "As an {} we earn from qualifying purchases.", "join": " and an ",
           "amazon_pending": "We have applied to the Amazon Associates Program. "
                             "We are not an Amazon Associate yet and earn nothing "
                             "from Amazon links today.",
           "tail": " Prices and availability are accurate as of the date of "
                   "publication and may change."},
    "he": {"amazon_none": "איננו שותפים של אמזון ואיננו מרוויחים דבר מקישורים לאמזון.",
           "amazon": "שותפים של אמזון", "aliexpress": "שותפים של עליאקספרס",
           "tpl": "כ{} אנחנו מרוויחים עמלה מרכישות מזכות.", "join": " ו",
           "amazon_pending": "הגשנו בקשה להצטרף לתוכנית השותפים של אמזון. איננו שותפים של אמזון עדיין, ואיננו מרוויחים דבר מקישורים לאמזון בשלב זה.",
           "tail": " המחירים והזמינות נכונים לזמן הפרסום ועשויים להשתנות."},
    "es": {"amazon_none": "No somos Afiliados de Amazon y hoy no ganamos nada con los enlaces a Amazon.",
           "amazon": "Afiliados de Amazon", "aliexpress": "afiliados de AliExpress",
           "tpl": "Como {}, ganamos por las compras que cumplen los requisitos.",
           "amazon_pending": "Hemos solicitado unirnos al Programa de Afiliados de Amazon. Todavía no somos Afiliados de Amazon y hoy no ganamos nada con los enlaces a Amazon.",
           "join": " y ",
           "tail": " Los precios y la disponibilidad son correctos en la fecha de "
                   "publicación y pueden cambiar."},
    "fr": {"amazon_none": "Nous ne sommes pas Partenaire Amazon et ne percevons rien sur les liens Amazon.",
           "amazon": "Partenaire Amazon", "aliexpress": "affilié AliExpress",
           "tpl": "En tant que {}, nous percevons une commission sur les achats éligibles.",
           "amazon_pending": "Nous avons déposé une candidature au Programme Partenaires d'Amazon. Nous ne sommes pas encore Partenaire Amazon et ne percevons rien sur les liens Amazon à ce jour.",
           "join": " et ",
           "tail": " Les prix et la disponibilité sont exacts à la date de "
                   "publication et peuvent changer."},
    "de": {"amazon_none": "Wir sind kein Amazon-Partner und verdienen nichts an Amazon-Links.",
           "amazon": "Amazon-Partner", "aliexpress": "AliExpress-Affiliate",
           "tpl": "Als {} verdienen wir an qualifizierten Käufen.", "join": " und ",
           "amazon_pending": "Wir haben uns für das Amazon-Partnerprogramm beworben. Wir sind noch kein Amazon-Partner und verdienen derzeit nichts an Amazon-Links.",
           "tail": " Preise und Verfügbarkeit entsprechen dem Stand der "
                   "Veröffentlichung und können sich ändern."},
    "el": {"amazon_none": "Δεν είμαστε Συνεργάτες της Amazon και δεν κερδίζουμε τίποτα από συνδέσμους Amazon.",
           "amazon": "Συνεργάτες της Amazon", "aliexpress": "συνεργάτες της AliExpress",
           "tpl": "Ως {}, κερδίζουμε από επιλέξιμες αγορές.", "join": " και ",
           "amazon_pending": "Έχουμε υποβάλει αίτηση για το Πρόγραμμα Συνεργατών της Amazon. Δεν είμαστε ακόμη Συνεργάτες της Amazon και δεν κερδίζουμε τίποτα από συνδέσμους Amazon.",
           "tail": " Οι τιμές και η διαθεσιμότητα ισχύουν κατά την ημερομηνία "
                   "δημοσίευσης και ενδέχεται να αλλάξουν."},
}

FONT_LINKS = {
    "Heebo": ('<link href="https://fonts.googleapis.com/css2?'
              'family=Heebo:wght@400;500;600;700;800&display=swap" rel="stylesheet">'),
    "Noto Sans": ('<link href="https://fonts.googleapis.com/css2?'
                  'family=Noto+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'),
}


def t(lang, key):
    """UI string, falling back to English rather than rendering an empty label."""
    return UI.get(lang, {}).get(key) or UI[DEFAULT][key]


def fmt_date(iso, lang):
    y, m, d = (int(x) for x in iso.split("-"))
    month = MONTHS.get(lang, MONTHS[DEFAULT])[m - 1]
    if lang == "he":
        return f"{d} ב{month} {y}"
    if lang in ("es", "fr"):
        return f"{d} {month} {y}"
    if lang == "de":
        return f"{d}. {month} {y}"
    if lang == "el":
        return f"{d} {month} {y}"
    return f"{d} {month} {y}"


def amazon_status():
    """'not_applied' | 'pending' | 'approved', from site-config.json.

    Three states, not two. The earlier version returned "pending" for anything
    that was not "approved", which meant `not_applied` in the config still
    printed "We have applied to the Amazon Associates Program" on every guide
    page in all six languages. That is the same false claim HANDOFF.md records
    being removed from the homepage on 2026-08-14; the guides were built from a
    different table and never got the fix.

    Unknown values fall back to not_applied. Guessing in that direction
    understates a relationship, which costs nothing. Guessing the other way puts
    a false claim of Amazon membership on a public page — on the very site
    Amazon reads when you do eventually apply.
    """
    import json
    import pathlib
    try:
        cfg = json.loads((pathlib.Path(__file__).resolve().parent.parent
                          / "site-config.json").read_text(encoding="utf-8"))
        v = cfg.get("amazon_associate_status")
        return v if v in ("not_applied", "pending", "approved") else "not_applied"
    except Exception:
        return "not_applied"


def disclosure(lang, show_amazon=True, show_ali=True, short=False):
    n = NETWORKS.get(lang, NETWORKS[DEFAULT])
    status = amazon_status()
    approved = status == "approved"

    # Until Amazon approves, the Associate sentence cannot be used at all — not
    # even in the "as an X and a Y" combined form, because the combined form
    # still asserts membership. The application notice is emitted as its own
    # sentence and any other network keeps its normal wording.
    if show_amazon and not approved:
        parts = [n["amazon_pending"] if status == "pending" else n["amazon_none"]]
        if show_ali:
            parts.append(n["tpl"].format(n["aliexpress"]))
        base = " ".join(parts)
        return base if short else base + n["tail"]

    names = [n[k] for k, on in (("amazon", show_amazon and approved),
                                ("aliexpress", show_ali)) if on]
    if not names:
        return ""
    base = n["tpl"].format(n["join"].join(names))
    return base if short else base + n["tail"]
