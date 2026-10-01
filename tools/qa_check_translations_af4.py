import json, re, glob, os, sys, io, csv
sys.stdout.reconfigure(encoding='utf-8')
R = sys.argv[1]
RNG = {'th': '฀-๿', 'hi': 'ऀ-ॿ', 'ar': '؀-ۿ'}
slugs = sorted(os.path.basename(f)[:-5] for f in glob.glob(R + '/content/*.json'))
def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)
rows = []; bad = []
for slug in slugs:
    src = json.load(io.open(R + '/content/%s.json' % slug, encoding='utf-8'))
    row = {'guide': slug}
    for l in ('th', 'hi', 'ar'):
        f = R + '/content/i18n/%s/%s.json' % (l, slug)
        if not os.path.exists(f): row[l] = 'MISSING'; bad.append((l, slug, 'missing')); continue
        d = json.load(io.open(f, encoding='utf-8'))
        strs = [s for k, v in d.items() if k not in ('slug', 'hero', 'heroAlt', 'heroCredit') for s in strings(v)]
        txt = ' '.join(strs)
        own = len(re.findall('[' + RNG[l] + ']', txt)); lat = len(re.findall('[A-Za-z]', txt))
        ratio = own / max(1, own + lat)
        row[l] = len(strs)
        if ratio < 0.6: bad.append((l, slug, 'script ratio %.2f' % ratio))
        if any(not s.strip() for s in strs): bad.append((l, slug, 'empty string'))
        if re.search(r'\{\{|\$\{|undefined|\[object|NaN', txt): bad.append((l, slug, 'placeholder artefact'))
        if 'products' in src and len(d.get('products', [])) != len(src['products']): bad.append((l, slug, 'product count'))
    rows.append(row)
with io.open(R + '/af4-translation-counts.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['guide', 'th', 'hi', 'ar']); w.writeheader(); w.writerows(rows)
for l in ('th', 'hi', 'ar'):
    n = sum(1 for r in rows if r[l] != 'MISSING')
    print(l, 'guides', n, '/', len(slugs), '| text fields total', sum(r[l] for r in rows if r[l] != 'MISSING'))
print('problems:', len(bad))
for b in bad[:25]: print('  ', b)
