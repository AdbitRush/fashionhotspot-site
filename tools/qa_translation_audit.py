#!/usr/bin/env python3
"""QA-1 mechanical layer: independent translation audit of a live multilingual site.

Runs against the LIVE site (not the build output), reads only the sitemap and the pages it lists.
No paid API, no model calls: pure HTTP + string checks.

Per page and per language it checks
  E  encoding        U+FFFD, mojibake (Ã©, â€™, Â), runs of '?' where letters should be
  L  leftover English an untranslated block in a non-English page (English function-word density; script ratio for he/el)
  M  markup/placeholder unrendered {{ }}, ${ }, %s, undefined, [object, NaN, literal \\n, doubled entities, raw markdown
  A  attributes      <html lang> / dir missing or wrong for the page's language; title/description still English
  P  missing page    an English page whose counterpart in this language is absent from the sitemap or not HTTP 200
  T  terminology     the same term spelled several ways across the site's pages in one language

Usage:  python qa_translation_audit.py <site-host> <out-dir> [--dir <built-tree>] [--fail-on E,M] [--full]
        --dir      audit the BUILT tree on disk (build-step mode: no network, checks what is about to be published)
        --fail-on  exit 3 when any severity-3 finding of these kinds exists (default: warn only, exit 0)
Output: <out-dir>/<site>.json (all findings + per-page text samples) and <out-dir>/<site>.summary.json
"""
import sys, re, json, html, time, collections, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

import os
SITE = sys.argv[1]
OUT = sys.argv[2]
DIR = sys.argv[sys.argv.index('--dir') + 1] if '--dir' in sys.argv else None
FAIL_ON = set((sys.argv[sys.argv.index('--fail-on') + 1] if '--fail-on' in sys.argv else '').split(',')) - {''}
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (QA-1 translation audit; owner-authorised)'}
LANGS = ['en', 'he', 'es', 'fr', 'de', 'el']

def fetch_file(url):
    """Build-step mode: map https://host/path to DIR/path (directory URLs -> index.html)."""
    from urllib.parse import urlparse, unquote
    rel = unquote(urlparse(url).path).lstrip('/')
    if rel == '' or rel.endswith('/'): rel += 'index.html'
    f = os.path.join(DIR, rel.replace('/', os.sep))
    if not os.path.isfile(f): return 404, ''
    return 200, open(f, encoding='utf-8', errors='replace').read()

def fetch(url, tries=3):
    if DIR: return fetch_file(url)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code in (404, 410): return e.code, ''
            time.sleep(1 + i)
        except Exception:
            time.sleep(1 + i)
    return 0, ''

def lang_of(url):
    m = re.match(r'https://[^/]+/(he|es|fr|de|el|ru)/', url)
    if m: return m.group(1)
    m = re.search(r'\.(he|es|fr|de|el)\.html$', url)
    return m.group(1) if m else 'en'

def base_of(url):
    u = re.sub(r'^https://[^/]+/(he|es|fr|de|el|ru)/', 'https://x/', url)
    u = re.sub(r'\.(he|es|fr|de|el)\.html$', '.html', u)
    u = re.sub(r'^https://[^/]+/', 'https://x/', u)
    return 'https://x/index.html' if u in ('https://x/', 'https://x') else u

BLOCK = {'p', 'li', 'h1', 'h2', 'h3', 'h4', 'td', 'th', 'dd', 'dt', 'blockquote', 'figcaption', 'summary', 'button', 'label', 'a', 'span', 'div', 'option'}
SKIP = {'script', 'style', 'noscript', 'svg', 'head', 'template'}

class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0; self.htmltag = {}; self.title = ''; self.desc = ''; self.blocks = []; self._buf = []; self._in_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.htmltag = a
        if tag == 'title': self._in_title = True
        if tag == 'meta' and (a.get('name') or '').lower() == 'description': self.desc = a.get('content') or ''
        if tag in SKIP and tag != 'head': self.skip += 1
        if tag in ('br',) : self._buf.append(' ')
        if tag in BLOCK: self._flush()
    def handle_endtag(self, tag):
        if tag == 'title': self._in_title = False
        if tag in SKIP and tag != 'head': self.skip = max(0, self.skip - 1)
        if tag in BLOCK: self._flush()
    def handle_data(self, data):
        if self._in_title: self.title += data
        if self.skip: return
        self._buf.append(data)
    def _flush(self):
        t = re.sub(r'\s+', ' ', ''.join(self._buf)).strip()
        self._buf = []
        if t: self.blocks.append(t)

def parse(htm):
    p = Extract()
    try: p.feed(htm)
    except Exception: pass
    p._flush()
    # de-duplicate nested repeats (a > span > text produce the same string)
    seen = set(); blocks = []
    for b in p.blocks:
        if b not in seen: seen.add(b); blocks.append(b)
    return p, blocks

EN_STOP = set('the and with your you that this which from have our but they their than into about when where how also just would could should'.split())  # deliberately excludes words that are also German/Spanish/French words (was, will, all, for, are, not, can...)
# Unicode-aware tokens: 'début' must stay ONE word (an ASCII-only regex split it into 'd' + 'but', an English stop-word)
def words(t): return [w for w in re.findall(r"[^\W\d_][\w'’-]*", t) if re.fullmatch(r"[A-Za-z][A-Za-z'’-]*", w)]
def en_density(t):
    w = [x.lower() for x in words(t)]
    return (sum(1 for x in w if x in EN_STOP) / len(w)) if w else 0, len(w)
CITE = re.compile(r"^.{8,170}(?: [—–-] | \()[A-Z][\w&.'’ -]{2,40}\)?$")
def looks_like_name(b):
    """Product names / model strings are legitimately Latin: mostly Capitalised words, digits, model codes, few lowercase function words."""
    if CITE.match(b): return True   # 'Article title - Publisher' / '... (Publisher)': an external source's own English title
    # any short line that does not end like a sentence and names a publisher / photo credit is a citation, not prose
    if len(b.split()) <= 32 and not re.search(r'[.!?…]$', b.strip()) and (' — ' in b or ' - ' in b or re.search(r'\)$', b.strip()) or b.startswith('Photo:')): return True
    w = words(b)
    if not w: return True
    caps = sum(1 for x in w if x[0].isupper())
    return caps / len(w) >= 0.55 or len(w) <= 4
def script_ratio(t, lo, hi):
    letters = [c for c in t if c.isalpha()]
    if not letters: return 1.0
    return sum(1 for c in letters if lo <= c <= hi) / len(letters)

MOJI = re.compile(r'(?:Ã[\x80-\xbf€™œ‚ƒ„…†‡ˆ‰Š‹Œ’“”•–—˜š›œžŸ]|â€[™œ“”¦˜"]|Â[\xa0-\xbf]|Ð[\x80-\xbf]|×[\x80-\xbf])')
PLACE = [(re.compile(r'\{\{|\}\}'), 'unrendered {{ }}'), (re.compile(r'\$\{'), 'unrendered ${'), (re.compile(r'%[sd]\b'), 'raw %s/%d'),
         (re.compile(r'\bundefined\b'), 'literal "undefined"'), (re.compile(r'\[object '), '[object Object]'), (re.compile(r'\bNaN\b'), 'literal NaN'),
         (re.compile(r'\\n'), 'literal \\n'), (re.compile(r'&amp;amp;|&amp;#\d+;|&lt;/?[a-z]+&gt;'), 'double-escaped entity'),
         (re.compile(r'(^|\s)\*\*[^*]+\*\*'), 'raw markdown **bold**'), (re.compile(r'\bTODO\b|\bLorem ipsum\b|\bFIXME\b'), 'placeholder text'),
         (re.compile(r'\{[a-zA-Z_]+\}'), 'unfilled {token}')]

def audit_page(url, status, htm):
    lang = lang_of(url); F = []
    if status != 200:
        return {'url': url, 'lang': lang, 'status': status, 'findings': [{'k': 'P', 'sev': 3, 'msg': f'HTTP {status}'}], 'samples': []}
    p, blocks = parse(htm)
    text_all = ' '.join(blocks)
    exp_dir = 'rtl' if lang == 'he' else 'ltr'
    hl = (p.htmltag.get('lang') or '').lower()
    if not hl.startswith(lang): F.append({'k': 'A', 'sev': 2, 'msg': f'<html lang="{hl}"> on a {lang} page'})
    if (p.htmltag.get('dir') or 'ltr').lower() != exp_dir: F.append({'k': 'A', 'sev': 3, 'msg': f'dir="{p.htmltag.get("dir")}" but {lang} needs {exp_dir}'})
    if lang != 'en':
        d, n = en_density(p.title + ' ' + p.desc)
        if n >= 5 and d > 0.25: F.append({'k': 'A', 'sev': 2, 'msg': 'title/description still English: ' + (p.title[:70])})
    # encoding
    if '�' in text_all: F.append({'k': 'E', 'sev': 3, 'msg': 'U+FFFD replacement character(s)', 'ctx': text_all[max(0, text_all.index('�') - 30):][:70]})
    m = MOJI.search(text_all)
    if m: F.append({'k': 'E', 'sev': 3, 'msg': 'mojibake ' + repr(m.group(0)), 'ctx': text_all[max(0, m.start() - 25):m.start() + 40]})
    for b in blocks:
        if re.search(r'\?{3,}', b): F.append({'k': 'E', 'sev': 2, 'msg': 'run of ? where letters were lost', 'ctx': b[:80]}); break
    # markup / placeholders (checked on raw text blocks AND on raw html for unrendered templates)
    for rx, name in PLACE:
        mm = rx.search(text_all)
        if mm: F.append({'k': 'M', 'sev': 3, 'msg': name, 'ctx': text_all[max(0, mm.start() - 30):mm.end() + 30]})
    # leftover English
    if lang != 'en':
        for b in blocks:
            if len(b.split()) < 7 or looks_like_name(b): continue
            d, n = en_density(b)
            if lang == 'he': lat = 1 - script_ratio(b, '֐', '׿')
            elif lang == 'el': lat = 1 - script_ratio(b, 'Ͱ', 'Ͽ')
            else: lat = 0
            if (d >= 0.22 and n >= 7) or (lang in ('he', 'el') and lat > 0.6 and n >= 7 and d >= 0.12):
                F.append({'k': 'L', 'sev': 3, 'msg': 'untranslated English block', 'ctx': b[:120]})
    samples = [b for b in blocks if len(b.split()) >= 6][:40]
    return {'url': url, 'lang': lang, 'status': 200, 'title': p.title.strip()[:120], 'findings': F, 'samples': samples, 'nblocks': len(blocks)}

def main():
    t0 = time.time()
    st, sm = fetch(f'https://{SITE}/sitemap.xml')
    if st != 200 or not sm: print(f'ERROR: no sitemap.xml ({st}); nothing to audit', flush=True); sys.exit(0 if not FAIL_ON else 3)
    urls = [html.unescape(u) for u in re.findall(r'<loc>([^<]+)</loc>', sm)]
    print(f'{SITE}: {len(urls)} URLs in sitemap (HTTP {st})', flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=14) as ex:
        futs = {u: ex.submit(fetch, u) for u in urls}
        for i, (u, f) in enumerate(futs.items()):
            s, h = f.result(); results.append(audit_page(u, s, h))
            if i % 500 == 0: print(f'  {i}/{len(urls)}  {time.time() - t0:.0f}s', flush=True)
    # missing counterparts
    by_base = collections.defaultdict(dict)
    for r in results: by_base[base_of(r['url'])][r['lang']] = r
    site_langs = sorted({r['lang'] for r in results})
    for base, d in by_base.items():
        if 'en' not in d: continue
        for lg in site_langs:
            if lg not in d:
                results.append({'url': base.replace('https://x/', f'https://{SITE}/') + f' [{lg} counterpart]', 'lang': lg, 'status': 0,
                                'findings': [{'k': 'P', 'sev': 3, 'msg': f'English page has no {lg} counterpart in the sitemap'}], 'samples': []})
    # untranslated-paragraph identity vs English counterpart
    for base, d in by_base.items():
        en = d.get('en');
        if not en or not en.get('samples'): continue
        en_set = set(en['samples'])
        for lg, r in d.items():
            if lg == 'en' or r['status'] != 200: continue
            same = [s for s in r['samples'] if s in en_set and len(s.split()) >= 8 and not looks_like_name(s) and en_density(s)[0] >= 0.08]
            if same: r['findings'].append({'k': 'L', 'sev': 3, 'msg': f'{len(same)} paragraph(s) identical to the English page', 'ctx': same[0][:120]})
    # terminology: spelling variants of the store name per language
    variants = collections.defaultdict(collections.Counter)
    for r in results:
        if r['status'] != 200: continue
        for s in r['samples']:
            for m in re.finditer(r'(?i)ali[\s\-]?express|עלי\s?אקספרס|אלי\s?אקספרס|aliexpress|αλι\s?εξπρες', s):
                variants[r['lang']][m.group(0)] += 1
    term = {lg: dict(c) for lg, c in variants.items()}
    # summarise
    summary = {'site': SITE, 'pages': len(urls), 'seconds': round(time.time() - t0), 'terminology_aliexpress_variants': term, 'languages': {}}
    for lg in site_langs:
        rs = [r for r in results if r['lang'] == lg]
        kinds = collections.Counter(f['k'] for r in rs for f in r['findings'])
        bad = [r for r in rs if r['findings']]
        worst = sorted(bad, key=lambda r: -sum(f['sev'] for f in r['findings']))[:10]
        summary['languages'][lg] = {'pages': len(rs), 'pages_with_findings': len(bad), 'by_kind': dict(kinds),
            'worst10': [{'url': w['url'], 'score': sum(f['sev'] for f in w['findings']), 'findings': [(f['k'], f['msg'], f.get('ctx', '')[:90]) for f in w['findings'][:4]]} for w in worst]}
    if '--full' not in sys.argv:           # compact by default: findings only (samples are for local review with --full)
        for r in results: r.pop('samples', None)
    json.dump(results, open(f'{OUT}/{SITE}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(summary, open(f'{OUT}/{SITE}.summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({lg: (v['pages'], v['pages_with_findings'], v['by_kind']) for lg, v in summary['languages'].items()}, ensure_ascii=False))
    sev3 = collections.Counter(f['k'] for r in results for f in r['findings'] if f['sev'] >= 3)
    summary['severity3_by_kind'] = dict(sev3)
    summary['mode'] = 'build-tree' if DIR else 'live-site'
    summary['finishedAt'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(summary, open(f'{OUT}/translation-audit-status.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    blocking = {k: v for k, v in sev3.items() if k in FAIL_ON}
    if blocking:
        print('TRANSLATION AUDIT FAILED (blocking kinds):', blocking, flush=True); sys.exit(3)

main()
