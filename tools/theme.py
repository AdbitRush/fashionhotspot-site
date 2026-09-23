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

# ── Guides browser (search, chips, sections, grid/list) ─────────────────────
# Progressive enhancement, deliberately: every card is server-rendered inside
# its group's <section>, visible and complete before this runs, so the page
# works with JS off (the .gbrowse toolbar ships `hidden` and is only revealed
# here). Filtering only ever toggles the `hidden` attribute — it never removes
# a card from the DOM or rebuilds one — and each card's searchable text is
# precomputed once at load (data-search, written by build.py) rather than
# re-read from the DOM on every keystroke.
#
# Spec: allyfind-guides-browser-spec-2026-09-23.txt. Ranking in flat (search
# or chip-filtered) mode is done with the CSS `order` property rather than
# moving DOM nodes — title matches first, then topic/group, then summary,
# ties keeping the original editorial order — which keeps the "only toggle
# hidden, never rebuild" rule intact.
GUIDES_BROWSER_SCRIPT = (
'<script>(function(){'
'var root=document.getElementById("gbrowse"),results=document.getElementById("gresults");'
'if(!root||!results)return;'
'var input=document.getElementById("gq"),clearBtn=document.getElementById("gqc"),'
'filters=document.getElementById("filters"),topics=document.getElementById("topics"),'
'shown=document.getElementById("shown"),empty=document.getElementById("gempty"),'
'emptyMsg=document.getElementById("gempty-msg"),emptyClear=document.getElementById("gempty-clear"),'
'gview=root.querySelector(".gview");'

'function stripDiacritics(s){return s.normalize("NFD").replace(/[\\u0300-\\u036f]/g,"");}'
'function norm(s){return stripDiacritics(String(s||"")).toLowerCase();}'

'var sections=[].slice.call(results.querySelectorAll(".gsection"));'
'var cards=[].slice.call(results.querySelectorAll(".gcard")).map(function(el,i){'
'return{el:el,cat:el.dataset.cat,topic:el.dataset.topic,'
'search:norm(el.dataset.search),title:norm(el.querySelector("h3").textContent),'
'idx:i,defaultHidden:el.hidden};});'
'var sectionHasMore={};'
'cards.forEach(function(c){if(c.defaultHidden)sectionHasMore[c.cat]=true;});'

'var state={q:"",cat:"",topic:"",view:"grid"};'

'function parseURL(){'
'var p=new URLSearchParams(location.search);'
'state.q=p.get("q")||"";state.cat=p.get("cat")||"";state.topic=p.get("topic")||"";'
'}'
'function writeURL(push){'
'var p=new URLSearchParams();'
'if(state.q)p.set("q",state.q);if(state.cat)p.set("cat",state.cat);'
'if(state.topic)p.set("topic",state.topic);'
'var qs=p.toString(),url=location.pathname+(qs?"?"+qs:"");'
'if(push)history.pushState(state,"",url);else history.replaceState(state,"",url);'
'}'

'function matchesQuery(card,words){'
'if(!words.length)return{hit:true,tier:2};'
'for(var i=0;i<words.length;i++){'
'if(card.search.indexOf(words[i])===-1)return{hit:false,tier:9};'
'}'
'var tier=card.title.indexOf(words[0])!==-1?0:'
'(norm(card.topic).indexOf(words[0])!==-1?1:2);'
'return{hit:true,tier:tier};'
'}'

'function render(){'
'var words=norm(state.q).split(/\\s+/).filter(Boolean);'
'var flat=!!(state.q||state.cat);'
'var visibleTotal=0;'
'var groupCounts={};'
'cards.forEach(function(c){'
'var m=matchesQuery(c,words);if(!m.hit)return;'
'groupCounts[c.cat]=(groupCounts[c.cat]||0)+1;'
'});'
'[].forEach.call(filters.querySelectorAll(".chip"),function(chip){'
'var cat=chip.dataset.cat,n=cat?(groupCounts[cat]||0):Object.keys(groupCounts).length'
'?cards.filter(function(c){var m=matchesQuery(c,words);return m.hit;}).length:0;'
'var nEl=chip.querySelector(".n");if(nEl)nEl.textContent=n;'
'chip.setAttribute("aria-pressed",cat===state.cat?"true":"false");'
'chip.setAttribute("aria-disabled",n===0?"true":"false");'
'});'
'topics.innerHTML="";var topicList=[];'
'if(state.cat){'
'var seen={};'
'cards.forEach(function(c){if(c.cat!==state.cat)return;'
'if(!seen[c.topic]){seen[c.topic]=0;topicList.push(c.topic);}seen[c.topic]++;});'
'}'
'if(state.cat&&topicList.length>1){'
'var allBtn=document.createElement("button");'
'allBtn.type="button";allBtn.className="chip";allBtn.dataset.topic="";'
'allBtn.setAttribute("aria-pressed",state.topic?"false":"true");'
'allBtn.textContent=(topics.dataset.all||"All").replace("{grp}",'
'((filters.querySelector(\'[data-cat="\'+state.cat+\'"]\')||{}).dataset||{}).label||"");'
'topics.appendChild(allBtn);'
'topicList.forEach(function(top){'
'var b=document.createElement("button");b.type="button";b.className="chip";'
'b.dataset.topic=top;b.setAttribute("aria-pressed",state.topic===top?"true":"false");'
'b.textContent=top;topics.appendChild(b);});'
'topics.hidden=false;'
'}else{topics.hidden=true;state.topic="";}'

'if(!flat){'
'results.classList.remove("is-flat");'
'sections.forEach(function(sec){sec.hidden=false;'
'var more=sec.querySelector(".gmore");if(more)more.hidden=!sectionHasMore[sec.dataset.section];'
'});'
'cards.forEach(function(c){c.el.hidden=c.defaultHidden;c.el.style.order="";visibleTotal++;});'
'shown.textContent=shown.dataset.tplGrouped;'
'empty.hidden=true;'
'}else{'
'results.classList.add("is-flat");'
'var matched=[];'
'cards.forEach(function(c){'
'var groupOk=!state.cat||c.cat===state.cat;'
'var topicOk=!state.topic||c.topic===state.topic;'
'var m=matchesQuery(c,words);'
'var hit=groupOk&&topicOk&&m.hit;'
'c.el.hidden=!hit;'
'c.el.style.order=hit?(m.tier*100000+c.idx):"";'
'if(hit){matched.push(c);visibleTotal++;}'
'});'
'sections.forEach(function(sec){'
'var anyVisible=matched.some(function(c){return sec.contains(c.el);});'
'sec.hidden=!anyVisible;'
'var more=sec.querySelector(".gmore");if(more)more.hidden=true;'
'});'
'var tpl=shown.dataset.tplCount;'
'shown.textContent=tpl.replace("{n}",visibleTotal).replace("{total}",shown.dataset.total);'
'empty.hidden=visibleTotal!==0;'
'if(visibleTotal===0){'
'emptyMsg.textContent=results.dataset.tplEmpty.replace("{q}",state.q);'
'}'
'}'
'}'

'var debounceTimer;'
'function onInput(){'
'clearBtn.hidden=!input.value;'
'clearTimeout(debounceTimer);'
'debounceTimer=setTimeout(function(){'
'state.q=input.value;writeURL(false);render();'
'},120);'
'}'
'input&&input.addEventListener("input",onInput);'
'input&&input.addEventListener("keydown",function(ev){'
'if(ev.key==="Escape"){input.value="";state.q="";clearBtn.hidden=true;'
'writeURL(false);render();}'
'});'
'clearBtn&&clearBtn.addEventListener("click",function(){'
'input.value="";input.focus();state.q="";clearBtn.hidden=true;writeURL(false);render();'
'});'
'emptyClear&&emptyClear.addEventListener("click",function(){'
'input.value="";state.q="";state.cat="";state.topic="";clearBtn.hidden=true;'
'writeURL(true);render();'
'});'

'filters.addEventListener("click",function(ev){'
'var b=ev.target.closest(".chip");if(!b||b.getAttribute("aria-disabled")==="true")return;'
'state.cat=b.dataset.cat;state.topic="";writeURL(true);render();'
'});'
'topics.addEventListener("click",function(ev){'
'var b=ev.target.closest(".chip");if(!b)return;'
'state.topic=b.dataset.topic;writeURL(true);render();'
'});'
'results.addEventListener("click",function(ev){'
'var b=ev.target.closest(".gmore");if(!b)return;'
'var sec=b.closest(".gsection");'
'var toShow=[].slice.call(sec.querySelectorAll(".gcard[hidden]"));'
'toShow.forEach(function(c){c.hidden=false;});'
'b.hidden=true;'
'if(toShow[0])toShow[0].setAttribute("tabindex","-1"),toShow[0].focus();'
'});'

'if(gview){'
'var grids=[].slice.call(results.querySelectorAll(".grid"));'
'function setView(v){'
'state.view=v;'
'grids.forEach(function(g){g.classList.toggle("is-list",v==="list");});'
'[].forEach.call(gview.querySelectorAll(".chip"),function(c){'
'c.setAttribute("aria-pressed",c.dataset.view===v?"true":"false");});'
'try{localStorage.setItem("fhg-view",v);}catch(e){}'
'}'
'gview.addEventListener("click",function(ev){'
'var b=ev.target.closest(".chip");if(!b)return;setView(b.dataset.view);'
'});'
'var savedView;try{savedView=localStorage.getItem("fhg-view");}catch(e){}'
'if(savedView==="list")setView("list");'
'}'

'window.addEventListener("popstate",function(){parseURL();'
'if(input)input.value=state.q;clearBtn.hidden=!state.q;render();});'

'parseURL();'
'if(input)input.value=state.q;'
'clearBtn.hidden=!state.q;'
'root.hidden=false;'
'render();'
'if(state.q||state.cat){root.scrollIntoView({block:"start"});}'
'})();</script>'
)

# The stylesheet is NOT inlined any more (FH-2): every guide page links the one shared
# /fh.css?v=<hash>, owned by the deals build (whatsapp-deals-bot/assets/fh.css) like fh-theme.js and
# mirrored into this repo's root. Guide rules live in its "GUIDES" section, scoped by html.fh-guides.
CSS_LINK = f'<link rel="stylesheet" href="{asset_url("fh.css")}">'


RTL_FONT = ('<link href="https://fonts.googleapis.com/css2?'
            'family=Heebo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">')
