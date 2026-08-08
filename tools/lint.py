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

REQUIRED_TOP = ["slug", "category", "title", "title_he", "dek", "dek_he",
                "hero_image", "updated", "intro", "intro_he", "how_we_pick",
                "how_we_pick_he", "products", "faq"]
REQUIRED_PROD = ["name", "name_he", "tag", "tag_he", "price", "search",
                 "image", "body", "body_he", "pros", "cons"]

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
    for m in re.finditer(r"[A-Za-z][A-Za-z'\-]*", text):
        tok = m.group()
        before = text[m.start() - 1:m.start()]
        after = text[m.end():m.end() + 1]
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
            if k + "_he" in g:
                check_text(f"{w}.{k}_he", g[k + "_he"], he=True)
        for i, p in enumerate(g.get("intro", [])):
            check_text(f"{w}.intro[{i}]", p)
        for i, p in enumerate(g.get("intro_he", [])):
            check_text(f"{w}.intro_he[{i}]", p, he=True)
        if len(g.get("intro", [])) != len(g.get("intro_he", [])):
            err(w, "intro and intro_he have different paragraph counts")

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
                if k + "_he" in p:
                    check_text(f"{pw}.{k}_he", p[k + "_he"], he=True)
            if "name_he" in p:
                check_text(f"{pw}.name_he", p["name_he"], he=True)
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
                check_text(f"{w}.faq{i}.{k}_he", q.get(k + "_he", ""), he=True)

        total = (sum(len(p.get("body", "").split()) for p in prods)
                 + sum(len(x.split()) for x in g.get("intro", []))
                 + len(g.get("how_we_pick", "").split()))
        if total < 800:
            err(w, f"~{total} English words — below the 800 bar")
        print(f"{w:14} {len(prods):2} products  ~{total:4} en words")

    print()
    for x in warnings:
        print("WARN ", x)
    for x in errors:
        print("ERROR", x)
    print(f"\n{len(files)} guides · {len(errors)} errors · {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
