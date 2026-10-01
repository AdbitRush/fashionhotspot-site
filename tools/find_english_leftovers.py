import json, re, sys, os, glob
sys.path.insert(0, 'tools')
from i18n_schema import CONTENT, extract, load_translation, I18N
sys.stdout.reconfigure(encoding='utf-8')
STOP = set('the a an and or of with for to in on that your is are it if only no not by from at as be into than this these those you can will'.split())
def walk(s, t, path, out):
    if isinstance(s, dict) and isinstance(t, dict):
        for k in s:
            if k in t: walk(s[k], t[k], path + [k], out)
    elif isinstance(s, list) and isinstance(t, list):
        for i, (a, b) in enumerate(zip(s, t)): walk(a, b, path + [i], out)
    elif isinstance(s, str) and isinstance(t, str) and s.strip() and s.strip() == t.strip():
        w = s.split()
        if path and path[-1] == 'slug': return
        if len(w) >= 4 and sum(1 for x in w if x.lower() in STOP) >= 1:
            out.append((path, s))
res = {}
for l in ('th', 'hi', 'ar'):
    items = []
    for f in sorted(CONTENT.glob('*.json')):
        g = json.loads(f.read_text(encoding='utf-8')); t = load_translation(l, g['slug'])
        o = []
        walk(extract(g), t, [], o)
        for p, s in o: items.append((g['slug'], p, s))
    res[l] = items
    print(l, len(items), 'unique', len({s for _, _, s in items}))
    import collections
    print('   by field:', collections.Counter(str(p[-1]) if not isinstance(p[-1], int) else 'item' for _, p, _ in items).most_common(6))
    for slug, p, s in items[:4] + items[-3:]: print('   ', slug, p, '|', s[:90])
json.dump({l: [(a, b, c) for a, b, c in v] for l, v in res.items()}, open('/root/af4-leftovers.json', 'w', encoding='utf-8'), ensure_ascii=False)
