#!/usr/bin/env python3
"""Self-host AllyFind's web fonts (Or, 25.10.2026): fonts/af-fonts.css + fonts/*.woff2 + fonts/OFL-<family>.txt.

Before this, every page asked fonts.googleapis.com / fonts.gstatic.com for its fonts, so Google saw every visitor's IP address
before any consent. The files are the same Google Fonts (SIL Open Font License 1.1, which allows redistribution with the licence),
fetched once and served from allyfind.com. Only the subsets the site's nine languages need are kept; each @font-face keeps its
unicode-range, so a browser downloads only the files for the characters on the page.

    python3 tools/fetch_fonts.py            # rewrites fonts/ from the families below (re-run only to change a family or weight)
"""
import hashlib, os, re, sys, urllib.request

FAMILIES = [  # (Google family spec, licence folder in github.com/google/fonts/ofl)
    ('Archivo:wght@400;500;600;800;900', 'archivo'),
    ('JetBrains+Mono:wght@400;600', 'jetbrainsmono'),
    ('Heebo:wght@400;500;600;700;800;900', 'heebo'),
    ('Noto+Sans:wght@400;500;600;700;800', 'notosans'),
    ('Noto+Sans+Thai:wght@400;500;600;700;800', 'notosansthai'),
    ('Noto+Sans+Devanagari:wght@400;500;600;700;800', 'notosansdevanagari'),
    ('Noto+Sans+Arabic:wght@400;500;600;700;800', 'notosansarabic'),
]
KEEP = {'latin', 'latin-ext', 'hebrew', 'greek', 'greek-ext', 'thai', 'devanagari', 'arabic'}
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def main():
    os.makedirs(OUT, exist_ok=True)
    blocks, files = [], {}
    for spec, lic in FAMILIES:
        css = get('https://fonts.googleapis.com/css2?family=' + spec + '&display=swap').decode('utf-8')
        for subset, body in re.findall(r'/\*\s*([a-z-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})', css):
            if subset not in KEEP:
                continue
            url = re.search(r'url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)', body).group(1)
            if url not in files:
                data = get(url)
                fam = re.search(r"font-family:\s*'([^']+)'", body).group(1).lower().replace(' ', '-')
                name = f'{fam}-{subset}-{hashlib.sha1(data).hexdigest()[:8]}.woff2'
                with open(os.path.join(OUT, name), 'wb') as f:
                    f.write(data)
                files[url] = name
            blocks.append(f'/* {subset} */\n' + body.replace(url, files[url]))
        with open(os.path.join(OUT, f'OFL-{lic}.txt'), 'wb') as f:
            f.write(get(f'https://raw.githubusercontent.com/google/fonts/main/ofl/{lic}/OFL.txt'))
    head = ('/* AllyFind web fonts, self-hosted (tools/fetch_fonts.py). Archivo, JetBrains Mono, Heebo, Noto Sans, Noto Sans Thai,\n'
            '   Noto Sans Devanagari, Noto Sans Arabic: SIL Open Font License 1.1, see OFL-*.txt in this folder. */\n')
    with open(os.path.join(OUT, 'af-fonts.css'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(head + '\n'.join(blocks) + '\n')
    total = sum(os.path.getsize(os.path.join(OUT, n)) for n in files.values())
    print(f'{len(blocks)} @font-face rules, {len(files)} woff2 files, {total / 1024:.0f} KB -> {os.path.normpath(OUT)}')


if __name__ == '__main__':
    sys.exit(main())
