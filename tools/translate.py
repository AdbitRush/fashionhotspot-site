#!/usr/bin/env python
"""Translate the guides into the languages the site publishes.

Deliberately not done by the model writing this repo: it is ~23,000 words per
language across 20 guides, which wants a resumable batch job against a
translation-capable model rather than anything interactive.

    python tools/translate.py --lang es                 # one language
    python tools/translate.py                           # every missing language
    python tools/translate.py --lang he --only-missing  # fill gaps, keep existing
    python tools/translate.py --dry-run                 # show what would be done

Resumable: a guide already translated is skipped unless --force. Interrupt it
and run it again.

Output is validated before it is saved — array lengths must match the source,
or the merge would silently drop pros, cons or FAQ answers.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from langs import LANGS, DEFAULT, TRANSLATED                    # noqa: E402
from i18n_schema import (CONTENT, TOP_STR, TOP_LIST, PROD_STR,  # noqa: E402
                         PROD_LIST, FAQ_STR, extract,
                         load_translation, save_translation, count_words)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

ENV = Path(r"C:\Users\AdBitRush\Documents\AdbitRush 22\2026\abri-brain\.env")
MODEL = os.environ.get("TRANSLATE_MODEL", "gemini-2.5-pro")
FALLBACK_MODEL = "gemini-2.5-flash"
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}"


def api_key():
    if os.environ.get("GOOGLE_API_KEY"):
        return os.environ["GOOGLE_API_KEY"]
    for p in (ENV, Path("/root/repos/abri-brain/.env")):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no GOOGLE_API_KEY")


PROMPT = """You are translating a published buying-guide article from English into {language} for a consumer shopping site.

Translate into natural, idiomatic {language} as a native editor would write it. This is the single most important instruction: do NOT produce a literal word-by-word rendering. If an English idiom has no equivalent, write what a {language} writer would actually say to mean the same thing.

The voice is direct, plainly written and sceptical. It tells readers when something is not worth buying and names the trade-off of every product. Keep that voice. Do not make it more formal, more promotional or more enthusiastic than the English.

Rules:
- Keep brand names, product names and model numbers in their original Latin form. "Baratza Encore ESP" stays "Baratza Encore ESP" in every language.
- Keep prices, numbers, units and measurements exactly as they are.
- Do NOT translate anything into a different currency.
- Preserve the meaning of hedged and cautious statements precisely. Where the English says evidence is weak, limited or unsupported, the translation must say the same. Never upgrade a cautious claim into a confident one.
- Keep any medical, safety or legal caveats intact and equally prominent.
- Return the SAME JSON structure you are given, with identical keys and identical array lengths. Translate only the string values.
- Do not add, remove, merge or reorder any array item.

Return only the JSON object, nothing else.

JSON to translate:
{payload}"""


def post(model, body, timeout=300):
    req = urllib.request.Request(
        API.format(model, api_key()),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def call_model(payload, language, model):
    body = {
        "contents": [{"role": "user", "parts": [{
            "text": PROMPT.format(language=language,
                                  payload=json.dumps(payload, ensure_ascii=False, indent=1))}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json",
                             "maxOutputTokens": 32000},
    }
    data = post(model, body)
    cand = (data.get("candidates") or [{}])[0]
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError(f"empty response ({cand.get('finishReason')})")
    return json.loads(text)


def shape_ok(src, out):
    """The merge trusts array lengths — a mismatch would silently drop content."""
    problems = []
    for k in TOP_LIST:
        if len(out.get(k, [])) != len(src.get(k, [])):
            problems.append(f"{k}: {len(out.get(k, []))} vs {len(src.get(k, []))}")
    if len(out.get("products", [])) != len(src.get("products", [])):
        problems.append("products count")
    else:
        for i, (a, b) in enumerate(zip(src["products"], out["products"]), 1):
            for k in PROD_LIST:
                if len(b.get(k, [])) != len(a.get(k, [])):
                    problems.append(f"p{i}.{k}")
            for k in PROD_STR:
                if not str(b.get(k, "")).strip():
                    problems.append(f"p{i}.{k} empty")
    if len(out.get("faq", [])) != len(src.get("faq", [])):
        problems.append("faq count")
    for k in TOP_STR:
        if not str(out.get(k, "")).strip():
            problems.append(f"{k} empty")
    return problems


def gap_payload(src, existing):
    """Only the fields a translation is missing, with enough context to translate.

    Hebrew was written by hand and reads better than a translation would, but it
    predates the category and pros/cons fields. Sending the whole guide back
    through a model to fill those gaps would overwrite good prose with adequate
    prose, so this asks for the gaps alone. Product names ride along untranslated
    purely as context for the pros and cons beneath them.
    """
    out, need = {"slug": src["slug"]}, False
    for k in TOP_STR:
        if src.get(k) and not str(existing.get(k, "")).strip():
            out[k] = src[k]
            need = True
    for k in TOP_LIST:
        if len(existing.get(k, [])) != len(src.get(k, [])):
            out[k] = src[k]
            need = True
    prods, any_prod = [], False
    for i, p in enumerate(src.get("products", [])):
        ex = (existing.get("products") or [])
        ex = ex[i] if i < len(ex) else {}
        item = {"_context_name": p.get("name", "")}
        hit = False
        for k in PROD_STR:
            if p.get(k) and not str(ex.get(k, "")).strip():
                item[k] = p[k]
                hit = True
        for k in PROD_LIST:
            if len(ex.get(k, [])) != len(p.get(k, [])):
                item[k] = p[k]
                hit = True
        any_prod = any_prod or hit
        prods.append(item)
    if any_prod:
        out["products"] = prods
        need = True
    faqs, any_faq = [], False
    for i, f in enumerate(src.get("faq", [])):
        ex = (existing.get("faq") or [])
        ex = ex[i] if i < len(ex) else {}
        item = {}
        for k in FAQ_STR:
            if f.get(k) and not str(ex.get(k, "")).strip():
                item[k] = f[k]
                any_faq = True
        faqs.append(item)
    if any_faq:
        out["faq"] = faqs
        need = True
    return out if need else None


def apply_gaps(existing, filled):
    """Merge a gap translation into what is already there, touching nothing else."""
    out = json.loads(json.dumps(existing))
    for k in TOP_STR:
        if filled.get(k):
            out[k] = filled[k]
    for k in TOP_LIST:
        if filled.get(k):
            out[k] = filled[k]
    for i, item in enumerate(filled.get("products", [])):
        while len(out.setdefault("products", [])) <= i:
            out["products"].append({})
        for k in PROD_STR + PROD_LIST:
            if item.get(k):
                out["products"][i][k] = item[k]
    for i, item in enumerate(filled.get("faq", [])):
        while len(out.setdefault("faq", [])) <= i:
            out["faq"].append({})
        for k in FAQ_STR:
            if item.get(k):
                out["faq"][i][k] = item[k]
    return out


def missing_fields(src, existing):
    """True if anything the source has is absent from the translation."""
    if not existing:
        return True
    for k in TOP_STR:
        if src.get(k) and not str(existing.get(k, "")).strip():
            return True
    for k in TOP_LIST:
        if len(existing.get(k, [])) != len(src.get(k, [])):
            return True
    if len(existing.get("products", [])) != len(src.get("products", [])):
        return True
    for a, b in zip(src.get("products", []), existing.get("products", [])):
        for k in PROD_STR:
            if a.get(k) and not str(b.get(k, "")).strip():
                return True
        for k in PROD_LIST:
            if len(b.get(k, [])) != len(a.get(k, [])):
                return True
    for a, b in zip(src.get("faq", []), existing.get("faq", [])):
        for k in FAQ_STR:
            if a.get(k) and not str(b.get(k, "")).strip():
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", choices=TRANSLATED)
    ap.add_argument("--slug", action="append")
    ap.add_argument("--force", action="store_true", help="retranslate even if present")
    ap.add_argument("--only-missing", action="store_true",
                    help="only guides with gaps (default unless --force)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    guides = {}
    for f in sorted(CONTENT.glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        guides[g["slug"]] = g
    slugs = args.slug or list(guides)
    langs = args.lang or TRANSLATED

    jobs = []
    for lang in langs:
        for slug in slugs:
            src = extract(guides[slug])
            existing = load_translation(lang, slug)
            if not args.force and existing and not missing_fields(src, existing):
                continue
            # A guide that is partly translated gets only its gaps sent, so we
            # never overwrite existing prose with a fresh machine pass.
            if existing and not args.force:
                gaps = gap_payload(src, existing)
                if gaps:
                    jobs.append((lang, slug, gaps, existing))
                continue
            jobs.append((lang, slug, src, None))

    total_words = sum(count_words(s) for _, _, s, _ in jobs)
    print(f"{len(jobs)} guide/language pairs to translate "
          f"(~{total_words:,} source words) using {args.model}")
    if args.dry_run:
        for lang, slug, s, prior in jobs:
            kind = "gaps only" if prior else "full"
            print(f"  {lang}/{slug}  ~{count_words(s):,} words  ({kind})")
        return 0
    if not jobs:
        print("nothing to do — everything is translated")
        return 0

    ok = fail = 0
    t0 = time.time()
    for n, (lang, slug, src, prior) in enumerate(jobs, 1):
        language = LANGS[lang]["name"]
        label = f"[{n}/{len(jobs)}] {lang}/{slug}"
        model = args.model
        for attempt in range(3):
            try:
                out = call_model(src, language, model)
                out["slug"] = slug
                if prior:
                    # Gap fill: only the requested pieces came back, so shape
                    # checking the whole guide would fail by design.
                    merged = apply_gaps(prior, out)
                    for p in merged.get("products", []):
                        p.pop("_context_name", None)
                    save_translation(lang, slug, merged)
                    print(f"{label} ok (gaps filled)")
                else:
                    problems = shape_ok(src, out)
                    if problems:
                        raise ValueError("shape mismatch: " + ", ".join(problems[:4]))
                    save_translation(lang, slug, out)
                    print(f"{label} ok ({count_words(out):,} words)")
                ok += 1
                break
            except Exception as ex:
                msg = str(ex)[:150]
                if attempt == 0 and ("404" in msg or "not found" in msg.lower()):
                    model = FALLBACK_MODEL
                    print(f"{label} {args.model} unavailable, falling back to {model}")
                    continue
                if attempt == 2:
                    print(f"{label} FAILED: {msg}")
                    fail += 1
                else:
                    time.sleep(3 + attempt * 5)

    print(f"\n{ok} translated, {fail} failed, {time.time() - t0:.0f}s")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
