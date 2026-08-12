#!/usr/bin/env python
"""Content checks for content/*.json.

Exists because the previous generation of these posts shipped with the English
word "deserves" sitting untranslated inside a Hebrew sentence, and with
"comfort, fun and comfort" where two English words collapsed onto one Hebrew
one. Both are the kind of thing a human skims straight past. Machines do not.

    python tools/lint.py            # exit 1 if anything is wrong
"""
import json, re, sys, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEB = r"֐-׿"

# Windows consoles default to cp1252 and cannot print the Hebrew in our own
# error messages, which would hide the very problems this script exists to find.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Brand and model names stay in Latin inside Hebrew copy — that is correct and
# is how Israelis write them. What we are hunting is the opposite: an ordinary
# English word left behind by a half-finished translation, e.g. the live site's
# "שדרוג תחושת ההקלדה שהשולחן שלך deserves".
#
# Heuristic: a Latin run is suspicious only when it looks like a common word —
# all lower case, three or more letters, not glued to a digit, and not a term we
# deliberately keep in Latin. Capitalised runs are treated as names.
LATIN_TECH = {
    "usb", "hdmi", "gps", "led", "ecg", "rtsp", "gan", "wifi", "wi-fi", "matter",
    "thread", "zigbee", "bluetooth", "mah", "hz", "rgb", "tv", "pc", "ai", "ssd",
    "hdr", "anc", "ip", "nfc", "oled", "lcd", "uv", "spf", "bpa", "led-", "app",
}

# English source only. The "_he" siblings that used to be required here moved
# out to content/i18n/he/<slug>.json when the site went to six languages, and
# are validated per-language further down.
REQUIRED_TOP = ["slug", "category", "title", "dek", "hero_image", "updated",
                "intro", "how_we_pick", "products", "faq"]
REQUIRED_PROD = ["name", "tag", "price", "search", "image", "body",
                 "pros", "cons"]

# Claims we must not make: we have not tested these products.
BANNED = [
    (re.compile(r"\bwe tested\b", re.I), "claims hands-on testing"),
    (re.compile(r"\bwe tried\b", re.I), "claims hands-on testing"),
    (re.compile(r"\bin our tests?\b", re.I), "claims hands-on testing"),
    (re.compile(r"\btested picks\b", re.I), "claims hands-on testing"),
    # "לא בדקנו בעצמנו" is a denial of testing and is exactly what we want, so
    # only flag the phrase when it is not negated.
    (re.compile(r"(?<!לא )בדקנו בעצמנו", 0), "claims hands-on testing (he)"),
    (re.compile(r"(?<!לא )ניסינו", 0), "claims hands-on testing (he)"),
    # "treat it as a rough band" is not a medical claim, so match a verb with an
    # actual condition after it rather than the bare word.
    (re.compile(r"\bcures?\b|\bclinically proven\b|\bmedical[- ]grade\b|"
                r"\btreats?\s+(?:acne|eczema|pain|hair loss|wrinkles|anxiety)\b",
                re.I), "medical efficacy claim"),
    (re.compile(r"\bdermatologist[- ]grade\b", re.I), "medical efficacy claim"),
    (re.compile(r"\bרמת רופא\b", 0), "medical efficacy claim (he)"),
]

errors, warnings = [], []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


def latin_in_hebrew(text):
    """Ordinary English words stranded inside an otherwise-Hebrew string."""
    if not re.search(f"[{HEB}]", text):
        return []
    bad = []
    heb = re.compile(f"[{HEB}]")
    for m in re.finditer(r"[A-Za-z][A-Za-z'\-]*", text):
        tok = m.group()
        before = text[m.start() - 1:m.start()]
        after = text[m.end():m.end() + 1]

        # A Latin run welded directly onto a Hebrew word — no space either side —
        # is a keyboard slip, not a brand name. This is how "ים-תיכוniים" and
        # "שולchan" get in, and both are short enough to duck the length rule
        # below, so check adjacency first and ignore length entirely.
        if heb.match(before or "") or heb.match(after or ""):
            s, e = max(0, m.start() - 30), min(len(text), m.end() + 30)
            bad.append((tok, text[s:e]))
            continue

        if tok.lower() in LATIN_TECH:
            continue
        if not tok.islower() or len(tok) < 3:
            continue                      # Anker, MX, AirTag, SE, FE — names
        if before.isdigit() or after.isdigit():
            continue                      # 4K, 65W, 1000XM6
        s, e = max(0, m.start() - 30), min(len(text), m.end() + 30)
        bad.append((tok, text[s:e]))
    return bad


def check_hebrew(where, text):
    for tok, ctx in latin_in_hebrew(text):
        err(where, f'untranslated Latin "{tok}" in Hebrew — …{ctx}…')
    # nikud is fine, but stray RTL/LTR marks usually mean a bad paste
    for ch in text:
        if unicodedata.category(ch) == "Cf" and ch not in "‏‎":
            warn(where, f"invisible control char U+{ord(ch):04X}")
    # The "נוחות, כיף ונוחות" failure: two different English words collapsing
    # onto one Hebrew word inside a single list. Strip the leading conjunction
    # or preposition first, or ונוחות will not match נוחות.
    for seg in re.split(r"[.!?\n]", text):
        if seg.count(",") < 1:
            continue                      # only lists produce this failure
        stems = [re.sub(f"^[והבלמשכ]", "", w)
                 for w in re.findall(f"[{HEB}]{{4,}}", seg)]
        dup = [w for w, n in Counter(stems).items() if n > 1]
        if dup and len(stems) <= 10:
            warn(where, f"word repeated in one list: {dup} — {seg.strip()[:70]}")


def check_text(where, text, he=False):
    if not text or not text.strip():
        err(where, "empty")
        return
    if "  " in text:
        warn(where, "double space")
    if re.search(r"\s+[,.;:]", text):
        warn(where, "space before punctuation")
    for pat, why in BANNED:
        if pat.search(text):
            err(where, f"{why} — {pat.pattern}")
    if he:
        if not re.search(f"[{HEB}]", text):
            err(where, "field marked Hebrew contains no Hebrew")
        else:
            check_hebrew(where, text)


def main():
    files = sorted((ROOT / "content").glob("*.json"))
    if not files:
        sys.exit("no content/*.json found")
    slugs = set()

    for f in files:
        try:
            g = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            err(f.name, f"invalid JSON: {ex}")
            continue
        w = g.get("slug", f.stem)

        for k in REQUIRED_TOP:
            if k not in g:
                err(w, f"missing field {k}")
        if g.get("slug") in slugs:
            err(w, "duplicate slug")
        slugs.add(g.get("slug"))
        if g.get("slug") != f.stem:
            err(w, f"slug does not match filename {f.stem}")

        for k in ("title", "dek", "how_we_pick"):
            if k in g:
                check_text(f"{w}.{k}", g[k])
        for i, p in enumerate(g.get("intro", [])):
            check_text(f"{w}.intro[{i}]", p)

        prods = g.get("products", [])
        if len(prods) != 10:
            err(w, f"{len(prods)} products, expected 10")
        for i, p in enumerate(prods, 1):
            pw = f"{w}.p{i}"
            for k in REQUIRED_PROD:
                if k not in p:
                    err(pw, f"missing {k}")
            for k in ("tag", "body"):
                if k in p:
                    check_text(f"{pw}.{k}", p[k])
            wc = len(p.get("body", "").split())
            if wc < 85:
                err(pw, f"body only {wc} words — thin content risk")
            elif wc > 190:
                warn(pw, f"body {wc} words — long")
            if not p.get("pros") or not p.get("cons"):
                err(pw, "needs at least one pro and one con")
            if "price" in p and not re.search(r"[\d]", str(p["price"])):
                err(pw, f"price has no number: {p['price']}")

        faq = g.get("faq", [])
        if len(faq) < 3:
            err(w, f"{len(faq)} FAQ entries, want at least 3")
        for i, q in enumerate(faq, 1):
            for k in ("q", "a"):
                check_text(f"{w}.faq{i}.{k}", q.get(k, ""))

        # Translations live in content/i18n/<lang>/<slug>.json, one file per
        # language. This used to look for "title_he" / "body_he" keys sitting
        # inline in the English file, which is the schema from before the split
        # — so it reported 860 errors against 20 fully-translated guides and
        # buried every real finding underneath. A check that is wrong 860 times
        # is not a check.
        for lang in ("he", "es", "fr", "de", "el"):
            tf = ROOT / "content" / "i18n" / lang / f"{f.stem}.json"
            if not tf.exists():
                err(w, f"no {lang} translation at content/i18n/{lang}/{f.stem}.json")
                continue
            try:
                tr = json.loads(tf.read_text(encoding="utf-8"))
            except json.JSONDecodeError as ex:
                err(f"{w}[{lang}]", f"invalid JSON: {ex}")
                continue
            tw = f"{w}[{lang}]"
            for k in ("title", "dek", "how_we_pick"):
                if not str(tr.get(k, "")).strip():
                    err(tw, f"{k} is empty")
                elif lang == "he":
                    check_text(f"{tw}.{k}", tr[k], he=True)
            if len(tr.get("intro", [])) != len(g.get("intro", [])):
                err(tw, f"intro has {len(tr.get('intro', []))} paragraphs, "
                        f"English has {len(g.get('intro', []))}")
            if len(tr.get("products", [])) != len(prods):
                err(tw, f"{len(tr.get('products', []))} products, English has {len(prods)}")
            for i, tp in enumerate(tr.get("products", []), 1):
                for k in ("name", "tag", "body"):
                    if not str(tp.get(k, "")).strip():
                        err(f"{tw}.p{i}", f"{k} is empty")
                    elif lang == "he":
                        check_text(f"{tw}.p{i}.{k}", tp[k], he=True)
            if len(tr.get("faq", [])) != len(faq):
                err(tw, f"{len(tr.get('faq', []))} FAQ entries, English has {len(faq)}")
            for i, tq in enumerate(tr.get("faq", []), 1):
                for k in ("q", "a"):
                    if not str(tq.get(k, "")).strip():
                        err(f"{tw}.faq{i}", f"{k} is empty")

        total = (sum(len(p.get("body", "").split()) for p in prods)
                 + sum(len(x.split()) for x in g.get("intro", []))
                 + len(g.get("how_we_pick", "").split()))
        if total < 800:
            err(w, f"~{total} English words — below the 800 bar")
        print(f"{w:14} {len(prods):2} products  ~{total:4} en words")

    # ── Amazon membership claims ─────────────────────────────────────────────
    # The site shipped "As an Amazon Associate we earn from qualifying
    # purchases" on all 146 pages in six languages while the application was
    # still under review. That is a false statement about a commercial
    # relationship, sitting on the exact site Amazon reads to decide whether to
    # approve you. It is easy to reintroduce by hand-editing one page, so it is
    # checked rather than remembered.
    claims = [
        "as an amazon associate",
        "participant in the amazon services",
        "afiliado de amazon, gan",
        "amazon-partner verdien",
        "partenaire amazon, je réalise",
        "partenaire amazon, nous réalis",
        "συνεργάτης της amazon κερδ",
        "כשותפים של אמזון",
    ]
    approved = False
    try:
        cfg = json.loads((ROOT / "site-config.json").read_text(encoding="utf-8"))
        approved = cfg.get("amazon_associate_status") == "approved"
    except Exception:
        pass
    if not approved:
        pages = list(ROOT.glob("*.html"))
        for d in ("he", "es", "fr", "de", "el"):
            pages += list((ROOT / d).glob("*.html"))
        for page in pages:
            low = page.read_text(encoding="utf-8", errors="replace").lower()
            for c in claims:
                if c in low:
                    err(page.name, f'claims Amazon membership ("{c}") while '
                                   f'site-config.json says the application is pending')
                    break

    print()
    for x in warnings:
        print("WARN ", x)
    for x in errors:
        print("ERROR", x)
    print(f"\n{len(files)} guides · {len(errors)} errors · {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
