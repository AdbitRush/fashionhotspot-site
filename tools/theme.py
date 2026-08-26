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

# Archivo carries display + UI; JetBrains Mono carries kickers and meta.
# Weights are pruned to what is actually used — 400/600/800/900 and 400/600.
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Archivo:wght@400;500;600;800;900&'
         'family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')

# ── Theme boot script ────────────────────────────────────────────────────────
# Must run BEFORE the browser paints, which is why it is inline in <head> and
# not a deferred file. If the theme were applied after first paint, a reader who
# chose dark would get a full-brightness cream flash on every navigation — the
# thing people actually notice and complain about.
#
# Order of precedence: an explicit saved choice always wins; otherwise follow the
# operating system. Someone who has never touched the toggle gets whatever their
# machine already says they prefer.
THEME_BOOT = (
    '<script>(function(){try{var t=localStorage.getItem("fh-theme");'
    'if(!t)t=matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light";'
    'document.documentElement.dataset.theme=t;}catch(e){}})();</script>'
)

# The toggle itself. aria-pressed + an accessible label because this is a real
# control, not decoration; the two glyphs swap purely in CSS so there is no
# scripted DOM churn on click.
THEME_TOGGLE = (
    '<button class="themetog" type="button" onclick="fhToggleTheme()" '
    'aria-label="Switch between light and dark" title="Light / dark">'
    '<span class="tt-sun">☀</span><span class="tt-moon">☾</span></button>'
)

THEME_SCRIPT = (
    '<script>function fhToggleTheme(){var d=document.documentElement,'
    'n=d.dataset.theme==="dark"?"light":"dark";d.dataset.theme=n;'
    'try{localStorage.setItem("fh-theme",n);}catch(e){}}'
    # Follow the OS if the reader has never expressed a preference here.
    'try{matchMedia("(prefers-color-scheme:dark)").addEventListener("change",'
    'function(ev){if(!localStorage.getItem("fh-theme"))'
    'document.documentElement.dataset.theme=ev.matches?"dark":"light";});}catch(e){}</script>'
)

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

CSS = """
/* ---------- tokens ---------- */
:root, :root[data-theme="light"]{
  --bg:oklch(0.945 0.019 80); --surface:oklch(0.978 0.014 82);
  --ink:oklch(0.21 0.014 55); --ink-2:oklch(0.44 0.014 65); --ink-3:oklch(0.52 0.014 68);
  --line:rgba(0,0,0,.08); --line-2:rgba(0,0,0,.13);
  --accent:oklch(0.55 0.2 25); --accent-ink:oklch(0.45 0.18 25);
  --deep:oklch(0.21 0.014 55);
  --shadow:0 1px 2px rgba(60,40,30,.05),0 10px 30px rgba(60,40,30,.07);
  --card-hover:0 26px 60px rgba(60,40,30,.13);
  --nav-bg:rgba(246,238,228,.9);
  --pro:#2F7D55; --con:#B04A2E; --chip:oklch(0.915 0.045 42); --note-bg:oklch(0.965 0.016 81);
  --on-accent:oklch(0.985 0.012 84); --on-deep:oklch(0.985 0.012 84);
  --radius:22px; --maxw:760px; --navh:60px;
}
/* Dark is a re-mix of the same palette, not an inversion. The red has to be
   lightened to stay legible on near-black, and surfaces stay lifted from the
   background so cards keep the edge they have in light mode without borders. */
:root[data-theme="dark"]{
  --bg:#141013; --surface:#1E181C; --ink:#F7F1EC; --ink-2:#CBBFB8; --ink-3:#9C8E88;
  --line:rgba(255,255,255,.09); --line-2:rgba(255,255,255,.15);
  --accent:oklch(0.72 0.2 25); --accent-ink:oklch(0.82 0.16 25);
  --deep:#F7F1EC;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.35);
  --card-hover:0 26px 60px rgba(0,0,0,.5);
  --nav-bg:rgba(20,16,19,.9);
  --pro:#5FC98D; --con:#FF8B6B; --chip:#3A2028; --note-bg:#1B1519;
  --on-accent:#170a0b; --on-deep:#141013;
}
html{color-scheme:light dark;-webkit-text-size-adjust:100%}
:root[data-theme="dark"] img{filter:brightness(.94)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Archivo,system-ui,-apple-system,"Segoe UI",sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.65;font-size:17px;
  -webkit-font-smoothing:antialiased;overflow-x:clip}
/* height:auto is load-bearing. The width/height attributes on every <img> are
   there to reserve layout space and stop the page jumping as images load, but
   they map to presentational CSS height — which pins the element at its
   attribute height and stops aspect-ratio ever being applied. Without this the
   hero and card images render at 630px tall regardless of column width. */
img{max-width:100%;display:block;height:auto}
a{color:var(--accent-ink)}
::selection{background:var(--accent);color:var(--on-accent)}

/* Every kicker, meta line and label in the design is mono, uppercase and
   widely tracked. One class, so the RTL and Greek overrides at the bottom have
   a single thing to reach for. */
.mono{font-family:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  text-transform:uppercase;letter-spacing:.14em;font-size:10.5px;font-weight:600;
  color:var(--ink-3);font-variant-numeric:tabular-nums}
.mono a{color:inherit;text-decoration:none}

/* ---------- chrome ---------- */
.nav{position:sticky;top:0;z-index:90;background:var(--nav-bg);
  backdrop-filter:saturate(1.4) blur(18px);border-bottom:1px solid var(--line)}
.nav-in{max-width:1280px;margin:0 auto;padding:13px 28px;display:flex;
  align-items:center;gap:20px}
.brand{display:flex;align-items:baseline;gap:10px;text-decoration:none}
.logo{font-weight:900;font-size:19px;color:var(--ink);letter-spacing:-.045em;
  text-decoration:none;white-space:nowrap}
.logo span{color:var(--accent)}
.navkick{color:var(--accent-ink);white-space:nowrap}
.nav-links{display:flex;gap:24px;margin-inline-start:auto;flex-wrap:wrap;align-items:center}
.nav-links a{font-size:13.5px;font-weight:600;color:var(--ink-2);text-decoration:none;
  padding:4px 0;border-bottom:2px solid transparent}
.nav-links a:hover{color:var(--ink)}
.nav-links a[aria-current]{color:var(--ink);border-bottom-color:var(--accent)}
.themetog{margin-inline-start:2px;background:transparent;border:1px solid var(--line-2);
  color:var(--ink-2);border-radius:999px;width:34px;height:34px;cursor:pointer;
  font-size:15px;line-height:1;display:inline-flex;align-items:center;
  justify-content:center;flex:0 0 auto;transition:border-color .15s,color .15s}
.themetog:hover{border-color:var(--accent-ink);color:var(--accent-ink)}
.themetog .tt-moon{display:none}
:root[data-theme="dark"] .themetog .tt-sun{display:none}
:root[data-theme="dark"] .themetog .tt-moon{display:inline}

.wrap{max-width:var(--maxw);margin:0 auto;padding:0 28px}
.wide{max-width:1280px;margin:0 auto;padding:0 28px}

/* ---------- index: masthead ---------- */
.masthead{padding:78px 0 44px;border-bottom:1px solid var(--line)}
.masthead h1{max-width:15ch}
.masthead .dek{max-width:560px}

h1{font-size:clamp(42px,6.4vw,96px);line-height:.88;letter-spacing:-.05em;
  font-weight:900;color:var(--ink);text-wrap:balance}
.dek{font-size:clamp(17px,2.2vw,20px);color:var(--ink-2);margin-top:22px;
  line-height:1.5;text-wrap:pretty}
.eyebrow{margin-bottom:18px;letter-spacing:.22em;color:var(--accent-ink)}

/* ---------- index: featured + side list ---------- */
.feat{display:grid;grid-template-columns:1.15fr .85fr;gap:44px;
  align-items:start;padding:52px 0 4px}
.feat-main{text-decoration:none;color:inherit;display:block}
.feat-main img{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:26px;
  border:1px solid var(--line);box-shadow:var(--shadow)}
.feat-meta{display:flex;gap:12px;align-items:center;margin:22px 0 12px;flex-wrap:wrap}
.pill{padding:6px 11px;border-radius:999px;background:var(--chip);
  color:var(--accent-ink);font-weight:600}
.feat-main h2{font-size:clamp(28px,3.2vw,44px);line-height:.99;letter-spacing:-.04em;
  font-weight:900;margin:0 0 14px;max-width:22ch;color:var(--ink)}
.feat-main p{font-size:17px;line-height:1.55;color:var(--ink-2);max-width:60ch;
  text-wrap:pretty}
/* ── Read next ─────────────────────────────────────────────────────────────
   The row at the foot of every guide that links to related guides. Before it
   existed no guide linked to any other, so a reader who finished one had
   nowhere to go and a crawler saw 221 unconnected pages. Sits above the deals
   CTA: another guide is a smaller ask than leaving for a shop. */
.related{margin-top:44px;padding-top:26px;border-top:1px solid var(--line)}
.relhead{letter-spacing:.18em;color:var(--ink-3);margin-bottom:16px}
.relgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}
.relcard{display:flex;flex-direction:column;border-radius:16px;overflow:hidden;
  background:var(--surface);border:1px solid var(--line);text-decoration:none;
  color:inherit;transition:transform .25s ease,border-color .25s ease}
.relcard:hover{transform:translateY(-3px);border-color:var(--accent)}
.relcard img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.relcard-in{display:flex;flex-direction:column;gap:6px;padding:13px 15px 15px}
.relcard-in b{font-size:15px;font-weight:700;line-height:1.3;letter-spacing:-.015em;
  color:var(--ink)}
.relcard-in .mono{font-size:11px;letter-spacing:.1em;color:var(--ink-3)}
[dir=rtl] .relhead,[dir=rtl] .relcard-in .mono{letter-spacing:.03em}
@media (prefers-reduced-motion:reduce){.relcard,.relcard:hover{transition:none;transform:none}}

.sidelist{display:flex;flex-direction:column;gap:10px}
.sidelist>.mono{letter-spacing:.2em;padding-bottom:6px}
.sideitem{display:grid;grid-template-columns:34px 1fr;gap:14px;align-items:start;
  padding:15px 16px;border-radius:16px;background:var(--surface);
  border:1px solid var(--line);text-decoration:none;color:inherit;
  transition:transform .25s ease,border-color .25s ease}
.sideitem:hover{transform:translateX(4px);border-color:var(--accent)}
[dir=rtl] .sideitem:hover{transform:translateX(-4px)}
.sidenum{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:15px;
  color:var(--accent-ink);font-weight:600;font-variant-numeric:tabular-nums}
.sideitem b{font-size:15px;font-weight:700;line-height:1.28;letter-spacing:-.015em;
  display:block;color:var(--ink)}
.sideitem .mono{margin-top:7px;letter-spacing:.1em}

/* ---------- index: filters ---------- */
.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;
  border-top:1px solid var(--line);margin-top:44px;padding-top:26px}
.chip{font-size:13px;font-weight:700;letter-spacing:-.01em;padding:9px 16px;
  border-radius:999px;cursor:pointer;background:var(--surface);color:var(--ink-2);
  border:1px solid var(--line-2);font-family:inherit;transition:background .2s,color .2s,border-color .2s}
.chip:hover{border-color:var(--accent)}
.chip[aria-pressed="true"]{background:var(--accent-ink);color:var(--on-accent);
  border-color:var(--accent-ink)}
.count{margin-inline-start:auto;letter-spacing:.1em}

/* ---------- index: grid ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
  gap:22px;margin:30px 0 10px}
.gcard{display:flex;flex-direction:column;background:var(--surface);
  border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;
  text-decoration:none;color:inherit;
  transition:transform .3s cubic-bezier(.22,1,.36,1),box-shadow .3s ease}
.gcard:hover{transform:translateY(-6px);box-shadow:var(--card-hover)}
.gcard[hidden]{display:none}
.gcard-media{position:relative}
.gcard-media img{width:100%;aspect-ratio:5/3;object-fit:cover}
.gcard-cat{position:absolute;top:12px;inset-inline-start:12px;padding:6px 10px;
  border-radius:999px;background:var(--nav-bg);backdrop-filter:blur(6px);
  color:var(--ink-2);font-size:9.5px;letter-spacing:.12em}
.gcard-in{padding:20px 20px 22px;display:flex;flex-direction:column;gap:10px;flex:1}
.gcard h3{font-size:19px;font-weight:800;line-height:1.18;letter-spacing:-.028em;
  color:var(--ink)}
.gcard .sum{font-size:14px;line-height:1.5;color:var(--ink-2);text-wrap:pretty}
.gcard-foot{margin-top:auto;padding-top:14px;display:flex;align-items:center;
  justify-content:space-between;gap:10px;border-top:1px solid var(--line);
  letter-spacing:.1em}
.gcard-foot .go{color:var(--accent-ink)}

/* ---------- article: progress ---------- */
.progtrack{position:sticky;top:var(--navh);z-index:80;height:3px;background:var(--line)}
.progbar{height:100%;width:0;background:var(--accent);transition:width .1s linear}

/* ---------- article head ---------- */
.crumbs{padding:26px 0 0;letter-spacing:.1em}
.crumbs a:hover{color:var(--accent-ink)}
.kicker{display:block;color:var(--accent-ink);letter-spacing:.18em;margin:26px 0 16px}
.wrap h1{font-size:clamp(34px,5.2vw,62px);line-height:.94;letter-spacing:-.045em}
.byline{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:26px;
  padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  letter-spacing:.08em}
.byline .av{width:30px;height:30px;border-radius:50%;background:var(--chip);
  border:1px solid var(--line-2);flex:0 0 auto}
.byline b{color:var(--ink-2);font-weight:600}
.byline .end{margin-inline-start:auto}
.dot{opacity:.45}
/* The design runs the lead image wider than the column it sits under. */
.hero{margin:30px auto;max-width:1080px;padding:0 28px}
.hero img{width:100%;aspect-ratio:21/9;object-fit:cover;border-radius:26px;
  border:1px solid var(--line);box-shadow:var(--shadow)}

/* ---------- body copy ---------- */
.body{font-size:17.5px}
.body p{margin:0 0 22px;color:var(--ink-2);line-height:1.68;text-wrap:pretty}
.body p.lead{font-size:19px;color:var(--ink)}
h2{font-size:clamp(26px,3vw,34px);font-weight:900;color:var(--ink);
  letter-spacing:-.035em;margin:48px 0 16px;line-height:1.05}
h3{font-size:22px;font-weight:800;color:var(--ink);letter-spacing:-.03em;
  line-height:1.15;margin:0}

/* The takeaway block. Body text is the number-one pick and its tag — both read
   straight off the guide's own data, so this cannot drift from the list below
   it the way a hand-written summary would. */
.short{padding:26px 28px;border-radius:20px;background:var(--chip);
  border:1px solid color-mix(in oklab,var(--accent) 25%,transparent);margin:30px 0 40px}
.short .mono{color:var(--accent-ink);letter-spacing:.18em;margin-bottom:12px}
.short .lead-pick{font-size:20px;line-height:1.35;font-weight:800;
  letter-spacing:-.025em;color:var(--ink);text-wrap:pretty}
.short .lead-tag{margin-top:8px;color:var(--accent-ink);letter-spacing:.12em}

.note{background:var(--note-bg);border:1px solid var(--line);
  border-inline-start:3px solid var(--accent);border-radius:14px;padding:16px 18px;
  margin:26px 0;font-size:15px;color:var(--ink-2)}
.note b{color:var(--ink)}

/* ---------- comparison table ---------- */
.tablewrap{overflow-x:auto;margin:22px 0 8px;border:1px solid var(--line);
  border-radius:16px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:520px}
th,td{text-align:start;padding:13px 15px;border-bottom:1px solid var(--line)}
th{background:var(--note-bg);font-weight:700;color:var(--ink);font-size:11px;
  text-transform:uppercase;letter-spacing:.1em;white-space:nowrap;
  font-family:"JetBrains Mono",ui-monospace,monospace}
tbody tr:last-child td{border-bottom:0}
td a{font-weight:600;text-decoration:none}
td a:hover{text-decoration:underline}
.rank{color:var(--accent-ink);font-variant-numeric:tabular-nums;width:1%;
  font-family:"JetBrains Mono",ui-monospace,monospace}

/* ---------- a pick ---------- */
/* The design puts a small square thumbnail beside the text rather than a full
   bleed image above it. With ten picks on a page that is the difference between
   a list you can scan and ten screens of scrolling. */
.card{display:grid;grid-template-columns:150px 1fr;gap:24px;padding:28px 0;
  border-top:1px solid var(--line);scroll-margin-top:88px}
.card-img{width:150px;aspect-ratio:1;object-fit:cover;border-radius:16px;
  border:1px solid var(--line);background:var(--surface)}
.card-in{min-width:0}
.badge{display:block;color:var(--accent-ink);letter-spacing:.16em;margin-bottom:9px}
.card h3{margin-bottom:10px}
.card p{margin:0 0 14px;color:var(--ink-2);font-size:16px;line-height:1.6;
  text-wrap:pretty}
.priceline{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.price{font-size:21px;font-weight:900;letter-spacing:-.03em;color:var(--ink)}
.tradeoff{letter-spacing:.06em;text-transform:none;font-size:11px;color:var(--ink-3)}
.tradeoff b{font-weight:600;text-transform:uppercase;letter-spacing:.12em}
.num{display:none}
.tag{display:none}
.pc{display:grid;grid-template-columns:1fr 1fr;gap:10px 22px;margin-top:18px;
  padding-top:16px;border-top:1px solid var(--line)}
.pc h4{font-size:10.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:7px;
  font-family:"JetBrains Mono",ui-monospace,monospace}
.pc ul{list-style:none;font-size:14.5px;color:var(--ink-2)}
.pc li{position:relative;padding-inline-start:17px;margin-bottom:5px;line-height:1.5}
.pc li::before{position:absolute;inset-inline-start:0;font-weight:700}
.pros li::before{content:"+";color:var(--pro)}
.cons li::before{content:"–";color:var(--con)}
.buys{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}
.btn{text-decoration:none;font-size:14px;font-weight:700;padding:12px 20px;
  border-radius:999px;display:inline-block;transition:transform .15s,filter .15s}
.btn:hover{transform:translateY(-2px);filter:brightness(1.06)}
.btn-a{background:var(--accent-ink);color:var(--on-accent)}
.btn-b{background:var(--surface);color:var(--ink);border:1px solid var(--line-2)}

/* ---------- faq ---------- */
.faq{border-top:1px solid var(--line);margin-top:12px}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{cursor:pointer;list-style:none;padding:18px 30px 18px 0;position:relative;
  font-weight:700;color:var(--ink);font-size:16.5px;letter-spacing:-.015em}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;inset-inline-end:4px;top:16px;
  font-size:21px;font-weight:400;color:var(--accent-ink);line-height:1}
.faq details[open] summary::after{content:"–"}
.faq p{padding:0 0 18px;color:var(--ink-2);font-size:15.5px;margin:0}

/* ---------- closer ---------- */
.closer{margin-top:46px;padding:34px 30px;border-radius:22px;
  border:1px dashed var(--line-2);text-align:center}
.closer h2{font-size:clamp(22px,3vw,28px);margin:0 0 10px;letter-spacing:-.03em}
.closer p{font-size:16px;color:var(--ink-2);margin:0 0 22px}
.closer .btn{padding:15px 28px;font-size:15px;font-weight:800;
  background:var(--deep);color:var(--on-deep)}

/* ---------- footer ---------- */
.disc{font-size:13.5px;color:var(--ink-3);border-top:1px solid var(--line);
  padding-top:18px;margin-top:46px}
footer{border-top:1px solid var(--line);margin-top:56px;padding:34px 28px;
  text-align:center;color:var(--ink-3);font-size:13.5px;background:var(--note-bg)}
footer nav{display:flex;gap:18px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}
footer a{color:var(--ink-2);text-decoration:none;font-weight:600}
footer a:hover{color:var(--accent-ink)}
.langsw{margin-top:12px;font-size:13px}

/* ---------- responsive ---------- */
@media(max-width:900px){
  .feat{grid-template-columns:1fr;gap:34px}
  .masthead{padding:52px 0 34px}
}
@media(max-width:600px){
  body{font-size:16px}
  .wrap,.wide,.hero{padding-inline:18px}
  .nav-in{padding:10px 18px;gap:12px}
  .nav-links{gap:14px}
  .nav-links a{font-size:13px}
  .navkick{display:none}
  /* The thumbnail column collapses rather than shrinking to a stamp. */
  .card{grid-template-columns:1fr;gap:16px;padding:24px 0}
  .card-img{width:100%;aspect-ratio:16/10}
  .pc{grid-template-columns:1fr;gap:14px}
  .hero img{aspect-ratio:16/10}
  .count{margin-inline-start:0;width:100%;padding-top:8px}
}
/* The chips are the one genuinely new tap target the redesign adds, and at the
   design's 9px padding they land at 34px — under the 44px minimum. Scoped to
   coarse pointers so the mouse version keeps the tighter proportions the design
   draws, and applied by min-height rather than padding so the label stays
   vertically centred either way. */
@media(pointer:coarse){
  .chip{min-height:44px;padding-inline:18px}
  .nav-links a{min-height:44px;display:inline-flex;align-items:center}
  .themetog{width:44px;height:44px}
  .sideitem{padding:18px 16px}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* ---------- rtl / non-latin ---------- */
/* Archivo and JetBrains Mono have no Hebrew, and wide tracking on Hebrew is
   unreadable rather than merely wrong. Hebrew keeps Heebo everywhere and drops
   the mono treatment, so the design's rhythm survives without the typography
   that cannot cross the script. */
[dir=rtl] body,[dir=rtl] .logo,[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3,
[dir=rtl] .chip,[dir=rtl] .mono,[dir=rtl] .sidenum,[dir=rtl] .rank,
[dir=rtl] th,[dir=rtl] .pc h4{
  font-family:"Heebo","Assistant",system-ui,sans-serif}
[dir=rtl] .mono,[dir=rtl] th,[dir=rtl] .pc h4{letter-spacing:.02em;font-size:11.5px}
[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] .feat-main h2{letter-spacing:-.01em;line-height:1.1}
/* A number with no Hebrew beside it still flips inside dir=rtl — "35 -> 35"
   is fine but "10 min" and "-58%" are not. Isolate every numeric run. */
[dir=rtl] .sidenum,[dir=rtl] .rank,[dir=rtl] .price,[dir=rtl] .count,
[dir=rtl] .byline .end,[dir=rtl] time{unicode-bidi:isolate}
"""

RTL_FONT = ('<link href="https://fonts.googleapis.com/css2?'
            'family=Heebo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">')
