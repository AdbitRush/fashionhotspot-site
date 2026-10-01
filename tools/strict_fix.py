"""Strict re-check of the th/hi/ar translations and forced re-translation of the ones that fail.
Checks: same key structure as the extracted source, no empty strings, target-script share of letters >= 0.6.
Run on the VPS in /root/fh-af4 (needs GEMINI_API_KEY in the environment)."""
import json, re, sys, io, subprocess, os
sys.path.insert(0, 'tools')
from i18n_schema import CONTENT, extract, load_translation
sys.stdout.reconfigure(encoding='utf-8')
RNG = {'th': '฀-๿', 'hi': 'ऀ-ॿ', 'ar': '؀-ۿ'}

def shape(o):
    if isinstance(o, dict): return {k: shape(v) for k, v in o.items()}
    if isinstance(o, list): return [shape(v) for v in o]
    return None

def same_shape(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(same_shape(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(same_shape(x, y) for x, y in zip(a, b))
    return not isinstance(b, (dict, list))

def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)

def check():
    bad = []
    for f in sorted(CONTENT.glob('*.json')):
        g = json.loads(f.read_text(encoding='utf-8')); slug = g['slug']
        src = extract(g)
        for l in ('th', 'hi', 'ar'):
            t = load_translation(l, slug)
            if not t: bad.append((l, slug, 'missing')); continue
            t2 = {k: v for k, v in t.items() if k != 'slug'}
            s2 = {k: v for k, v in src.items() if k != 'slug'}
            why = []
            if not same_shape(s2, t2): why.append('key structure differs from source')
            txt = ' '.join(strings(t2))
            if any(not s.strip() for s in strings(t2)): why.append('empty string')
            own = len(re.findall('[' + RNG[l] + ']', txt)); lat = len(re.findall('[A-Za-z]', txt))
            if own / max(1, own + lat) < 0.6: why.append('script ratio %.2f' % (own / max(1, own + lat)))
            if why: bad.append((l, slug, '; '.join(why)))
    return bad

for rnd in range(1, 4):
    bad = check()
    print(f'round {rnd}: {len(bad)} failing', flush=True)
    for b in bad[:40]: print('   ', b, flush=True)
    if not bad: break
    if rnd == 3: sys.exit(1)
    by_lang = {}
    for l, s, _ in bad: by_lang.setdefault(l, []).append(s)
    for l, slugs in by_lang.items():
        cmd = [sys.executable, 'tools/translate.py', '--lang', l, '--force'] + [a for s in slugs for a in ('--slug', s)]
        print('  retranslating', l, len(slugs), flush=True)
        subprocess.run(cmd, env=dict(os.environ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print('strict check finished', 'CLEAN' if not check() else 'with failures')
