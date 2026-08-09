"""What gets translated, and where translations live.

content/<slug>.json           canonical English, plus the untranslatable bits
                              (slug, prices, search terms, image prompts)
content/i18n/<lang>/<slug>.json  the same fields in that language, nothing else

Keeping prices and search terms out of the translated files matters: an Amazon
search term must stay in English to return anything, and a price band is a
number either way. Translating them would quietly break both.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
I18N = CONTENT / "i18n"

# Top-level string fields that get translated.
TOP_STR = ["title", "dek", "category", "how_we_pick"]
# Top-level list-of-strings fields.
TOP_LIST = ["intro"]
# Per-product fields: strings then lists.
PROD_STR = ["name", "tag", "body"]
PROD_LIST = ["pros", "cons"]
# Per-FAQ fields.
FAQ_STR = ["q", "a"]


def extract(guide):
    """The translatable subset of a guide, in a stable shape."""
    return {
        "slug": guide["slug"],
        **{k: guide.get(k, "") for k in TOP_STR},
        **{k: list(guide.get(k, [])) for k in TOP_LIST},
        "products": [
            {**{k: p.get(k, "") for k in PROD_STR},
             **{k: list(p.get(k, [])) for k in PROD_LIST}}
            for p in guide.get("products", [])
        ],
        "faq": [{k: f.get(k, "") for k in FAQ_STR} for f in guide.get("faq", [])],
    }


def merge(guide, tr):
    """English guide + a translation -> a guide rendered in that language.

    Falls back field by field, so a partial translation degrades to English on
    the missing pieces rather than rendering blanks.
    """
    if not tr:
        return guide
    out = dict(guide)
    for k in TOP_STR:
        if tr.get(k):
            out[k] = tr[k]
    for k in TOP_LIST:
        if tr.get(k) and len(tr[k]) == len(guide.get(k, [])):
            out[k] = tr[k]
    prods = []
    for i, p in enumerate(guide.get("products", [])):
        q = dict(p)
        tp = (tr.get("products") or [{}] * len(guide["products"]))
        tp = tp[i] if i < len(tp) else {}
        for k in PROD_STR:
            if tp.get(k):
                q[k] = tp[k]
        for k in PROD_LIST:
            if tp.get(k) and len(tp[k]) == len(p.get(k, [])):
                q[k] = tp[k]
        prods.append(q)
    out["products"] = prods
    faqs = []
    for i, f in enumerate(guide.get("faq", [])):
        g = dict(f)
        tf = (tr.get("faq") or [])
        tf = tf[i] if i < len(tf) else {}
        for k in FAQ_STR:
            if tf.get(k):
                g[k] = tf[k]
        faqs.append(g)
    out["faq"] = faqs
    return out


def load_translation(lang, slug):
    f = I18N / lang / f"{slug}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_translation(lang, slug, data):
    d = I18N / lang
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_words(tr):
    """Rough size of a translation payload, for progress reporting."""
    n = 0
    for k in TOP_STR:
        n += len(str(tr.get(k, "")).split())
    for k in TOP_LIST:
        n += sum(len(str(x).split()) for x in tr.get(k, []))
    for p in tr.get("products", []):
        for k in PROD_STR:
            n += len(str(p.get(k, "")).split())
        for k in PROD_LIST:
            n += sum(len(str(x).split()) for x in p.get(k, []))
    for f in tr.get("faq", []):
        for k in FAQ_STR:
            n += len(str(f.get(k, "")).split())
    return n
