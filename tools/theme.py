"""Shared look for every generated page.

One stylesheet, inlined into each page.

2026-08-20 — rebuilt to the "Fashionhotspot Guides" design
(claude.ai/design project "Fashion Hotspot Design Overhaul"). What changed and
why it is not just a repaint:

  * Type. Fraunces (serif) is out, Archivo 900 is in for headings, with
    JetBrains Mono carrying every kicker, meta line and label. The serif read as
    "blog"; the guides are meant to read as a buying desk. Body copy keeps a
    sans, so the change is display-only and does not touch reading comfort.
  * Scale. h1 goes to clamp(38px,5.4vw,66px) with line-height .94 and negative
    tracking. The old h1 topped out at 46px, which on a 1440px screen looked
    like a paragraph that had been bolded.
  * Palette. Same warm cream family, moved onto oklch and pushed slightly
    warmer/darker (#FFF6EE -> oklch(.945 .019 80)) so the white cards actually
    separate from the page. The coral becomes a true red accent.

Kept deliberately, because the design file is a light-mode mock and the live
site is not:

  * The dark theme. Every design token still has a dark remix and the toggle
    still works. A design that only exists in light would have shipped a broken
    button for everyone who has ever pressed it.
  * Logical properties (margin-inline, inset-inline) throughout, because Hebrew
    is one of the six languages and the design has no RTL half.
"""

from pathlib import Path

# Archivo carries display + UI; JetBrains Mono carries kickers and meta.
# Weights are pruned to what is actually used — 400/600/800/900 and 400/600.
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Archivo:wght@400;500;600;800;900&'
         'family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')

# ── Theme boot script ──────────────────────────────────────────────────────
# ONE path for every page family: /fh-theme.js, a tiny blocking script in <head>
# (so the theme is applied before first paint). It is owned by the deals build
# (whatsapp-deals-bot/assets/fh-theme.js) and mirrored into this repo's root by
# the same sync that mirrors index.html; this generator only links it.
#
# Rules it implements (see the file itself): a saved choice wins; with no saved
# choice the page is LIGHT — the operating-system colour scheme is not consulted.
def asset_url(name):
    """/name?v=<content hash>, so the host's long TTL on .js/.css never serves a stale copy."""
    import hashlib
    p = Path(__file__).resolve().parent.parent / name
    if not p.exists():
        raise SystemExit(f"{name} is missing from the repo root. It is mirrored from "
                         "whatsapp-deals-bot/assets/ by the deals build; copy it in and rerun.")
    return f"/{name}?v={hashlib.sha1(p.read_bytes()).hexdigest()[:8]}"


THEME_BOOT = f'<script src="{asset_url("fh-theme.js")}"></script>'

# The toggle itself. aria-pressed + an accessible label because this is a real
# control, not decoration; the two glyphs swap purely in CSS so there is no
# scripted DOM churn on click.
THEME_TOGGLE = (
    '<button class="themetog" type="button" onclick="fhToggleTheme()" '
    'aria-label="Switch between light and dark" aria-pressed="false" title="Light / dark">'
    '<span class="tt-sun">☀</span><span class="tt-moon">☾</span></button>'
)

# Toggle + state sync now live in fh-theme.js; kept as an empty constant so importers do not change.
THEME_SCRIPT = ''

# ── Reading progress bar (article pages) ─────────────────────────────────────
# The design drives this off scroll position. Written as a plain listener rather
# than an animation-timeline so it works in every browser the site already
# supports, and it writes a CSS variable instead of an inline style so the
# reduced-motion rule below can still reach it.
GUIDE_SCRIPT = (
    '<script>(function(){var b=document.getElementById("prog");if(!b)return;'
    'var f=function(){var h=document.documentElement.scrollHeight-innerHeight;'
    'b.style.width=(h>0?Math.min(100,scrollY/h*100):0)+"%";};'
    'addEventListener("scroll",f,{passive:true});addEventListener("resize",f);f();})();</script>'
)

# ── Category filter (index page) ─────────────────────────────────────────────
# Progressive enhancement, deliberately: every card is in the HTML and visible
# before this runs, so the page is complete for a crawler and for anyone whose
# JS never arrives. The filter only ever hides. It also keeps the count line in
# sync, because a filter that leaves a stale "35 showing" underneath it looks
# broken even when it worked.
INDEX_SCRIPT = (
    '<script>(function(){var bar=document.getElementById("filters");'
    'if(!bar)return;var cards=[].slice.call(document.querySelectorAll(".gcard")),'
    'out=document.getElementById("shown"),tpl=out?out.dataset.tpl:"";'
    'bar.addEventListener("click",function(ev){'
    'var b=ev.target.closest(".chip");if(!b)return;'
    'var c=b.dataset.cat,n=0;'
    '[].forEach.call(bar.querySelectorAll(".chip"),function(x){'
    'x.setAttribute("aria-pressed",x===b?"true":"false");});'
    'cards.forEach(function(el){var hit=!c||el.dataset.cat===c;'
    'el.hidden=!hit;if(hit)n++;});'
    'if(out)out.textContent=tpl.replace("{n}",n);});})();</script>'
)

# The stylesheet is NOT inlined any more (FH-2): every guide page links the one shared
# /fh.css?v=<hash>, owned by the deals build (whatsapp-deals-bot/assets/fh.css) like fh-theme.js and
# mirrored into this repo's root. Guide rules live in its "GUIDES" section, scoped by html.fh-guides.
CSS_LINK = f'<link rel="stylesheet" href="{asset_url("fh.css")}">'


RTL_FONT = ('<link href="https://fonts.googleapis.com/css2?'
            'family=Heebo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">')
