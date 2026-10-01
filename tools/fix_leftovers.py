"""AF-4: translate the generic (non-brand) product names, tags and short strings that the guide translation left in English.
Run on the VPS in /root/fh-af4 after find_english_leftovers.py. Free-tier Gemini via tools/translate.post (pacing/429 aware)."""
import json, re, sys, os, io
sys.path.insert(0, 'tools')
import translate as T
from i18n_schema import load_translation, save_translation
sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('/root/af4-leftovers.json', encoding='utf-8'))
MODEL = os.environ.get('TRANSLATE_MODEL', 'gemini-3.5-flash-lite')

FORCE = {'Aqara or Eve door and window sensors', 'Roborock or Dreame robot vacuum with self-empty', 'A Hawthorne strainer and fine mesh strainer', 'How do I train without annoying downstairs neighbours?'}

def generic(path, text):
    if text in FORCE: return True
    if path[-1] != 'name': return True
    toks = text.split()
    for w in toks[1:]:
        w2 = re.sub(r'[^A-Za-z]', '', w)
        if w2 and w2[0].isupper() and not w2.isupper() and len(w2) > 1: return False
    return True

def ask(lang, strings):
    prompt = ("Translate each of these short e-commerce product phrases/labels from English into %s.\n"
              "Natural, native wording as it would appear on a shopping guide; keep brand names, model numbers, units and acronyms (LED, USB-C, SSD, Wi-Fi...) as they are. "
              "Return ONLY a JSON array of strings with EXACTLY %d items, in the same order, nothing else.\n\n%s") % (
              T.prompt_language(lang), len(strings), json.dumps(strings, ensure_ascii=False, indent=1))
    body = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json', 'maxOutputTokens': 16000}}
    d = T.post(MODEL, body)
    txt = ''.join(p.get('text', '') for p in d['candidates'][0]['content']['parts'])
    arr = json.loads(txt)
    assert isinstance(arr, list) and len(arr) == len(strings), (len(arr), len(strings))
    return [str(x).strip() for x in arr]

def setpath(obj, path, val):
    for k in path[:-1]: obj = obj[k]
    obj[path[-1]] = val

for lang in ('th', 'hi', 'ar'):
    rows = [(s, p, t) for s, p, t in data[lang] if generic(p, t)]
    uniq = sorted({t for _, _, t in rows})
    print(lang, 'rows', len(rows), 'unique to translate', len(uniq), 'kept as brand names', len(data[lang]) - len(rows), flush=True)
    tr = {}
    for i in range(0, len(uniq), 50):
        chunk = uniq[i:i + 50]
        for attempt in range(3):
            try:
                out = ask(lang, chunk); break
            except T.DailyQuota: raise
            except Exception as e:
                print('  retry', str(e)[:80], flush=True)
        else:
            print('  gave up on a chunk'); continue
        for a, b in zip(chunk, out):
            if b and b != a: tr[a] = b
    changed = {}
    for slug, path, text in rows:
        if text not in tr: continue
        changed.setdefault(slug, load_translation(lang, slug))
        setpath(changed[slug], path, tr[text])
    for slug, d in changed.items(): save_translation(lang, slug, d)
    print(lang, 'strings translated', len(tr), 'files updated', len(changed), flush=True)
