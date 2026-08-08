"""Shared look for every generated page.

One stylesheet, inlined into each page. The palette is the site's existing
warm cream / blush / coral, kept deliberately so the guides feel like part of
fashionhotspot rather than a bolted-on blog.
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700;9..144,800&'
         'family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">')

CSS = """
:root{
  --bg:#FFF6EE; --surface:#fff; --ink:#2E1F26; --ink-2:#5A4550; --ink-3:#8C7580;
  --line:#F0DFD2; --line-2:#E6D2C2; --accent:#E14B4B; --accent-ink:#B02F2F;
  --deep:#3A2230; --shadow:0 1px 2px rgba(58,34,48,.04),0 8px 24px rgba(58,34,48,.06);
  --radius:16px; --maxw:760px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);
  color:var(--ink);line-height:1.7;font-size:17px;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:var(--accent-ink)}

/* ---------- chrome ---------- */
.nav{position:sticky;top:0;z-index:50;background:rgba(255,246,238,.88);
  backdrop-filter:saturate(1.4) blur(10px);border-bottom:1px solid var(--line)}
.nav-in{max-width:1080px;margin:0 auto;padding:12px 22px;display:flex;align-items:center;gap:20px}
.logo{font-family:Fraunces,Georgia,serif;font-weight:800;font-size:19px;color:var(--deep);
  text-decoration:none;letter-spacing:-.01em;white-space:nowrap}
.logo span{color:var(--accent)}
.nav-links{display:flex;gap:20px;margin-inline-start:auto;flex-wrap:wrap}
.nav-links a{font-size:14px;font-weight:600;color:var(--ink-2);text-decoration:none;
  padding:4px 0;border-bottom:2px solid transparent}
.nav-links a:hover{color:var(--accent-ink)}
.nav-links a[aria-current]{color:var(--accent-ink);border-bottom-color:var(--accent)}

.wrap{max-width:var(--maxw);margin:0 auto;padding:0 22px}
.wide{max-width:1080px;margin:0 auto;padding:0 22px}

/* ---------- article head ---------- */
.crumbs{font-size:13px;color:var(--ink-3);padding:22px 0 0}
.crumbs a{color:var(--ink-3);text-decoration:none}
.crumbs a:hover{color:var(--accent-ink);text-decoration:underline}
.kicker{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent);margin:26px 0 12px}
h1{font-family:Fraunces,Georgia,serif;font-size:clamp(31px,5.2vw,46px);font-weight:700;
  line-height:1.14;letter-spacing:-.02em;color:var(--deep)}
.dek{font-size:clamp(17px,2.4vw,20px);color:var(--ink-2);margin-top:16px;line-height:1.55}
.byline{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:22px;
  padding-bottom:24px;font-size:13.5px;color:var(--ink-3)}
.byline b{color:var(--ink-2);font-weight:600}
.dot{opacity:.45}
.hero{margin:8px 0 30px;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
.hero img{width:100%;aspect-ratio:1200/630;object-fit:cover}

/* ---------- body copy ---------- */
.body p{margin:0 0 20px;color:var(--ink-2)}
.body p.lead{font-size:19px;color:var(--ink)}
h2{font-family:Fraunces,Georgia,serif;font-size:27px;font-weight:700;color:var(--deep);
  letter-spacing:-.01em;margin:44px 0 14px;line-height:1.25}
h3{font-family:Fraunces,Georgia,serif;font-size:21px;font-weight:700;color:var(--deep);margin:0}

.note{background:#FFFBF6;border:1px solid var(--line);border-inline-start:3px solid var(--accent);
  border-radius:12px;padding:16px 18px;margin:26px 0;font-size:15px;color:var(--ink-2)}
.note b{color:var(--deep)}

/* ---------- comparison table ---------- */
.tablewrap{overflow-x:auto;margin:22px 0 8px;border:1px solid var(--line);
  border-radius:14px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:520px}
th,td{text-align:start;padding:12px 14px;border-bottom:1px solid var(--line)}
th{background:#FFFBF6;font-weight:700;color:var(--deep);font-size:12.5px;
  text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
td a{font-weight:600;text-decoration:none}
td a:hover{text-decoration:underline}
.rank{color:var(--ink-3);font-variant-numeric:tabular-nums;width:1%}

/* ---------- product card ---------- */
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  overflow:hidden;margin:26px 0;box-shadow:var(--shadow);scroll-margin-top:72px}
.card-img{width:100%;aspect-ratio:16/10;object-fit:cover;border-bottom:1px solid var(--line)}
.card-in{padding:22px}
.card-top{display:flex;gap:14px;align-items:flex-start}
.num{flex:0 0 34px;height:34px;border-radius:50%;background:var(--deep);color:#fff;
  font-family:Fraunces,Georgia,serif;font-weight:700;font-size:16px;
  display:flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}
.tag{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.05em;
  text-transform:uppercase;color:var(--accent-ink);background:#FDECEC;
  padding:4px 10px;border-radius:99px;margin-bottom:8px}
.price{font-size:14px;font-weight:600;color:var(--ink-3);margin-top:4px}
.card p{margin:14px 0 0;color:var(--ink-2);font-size:16px}
.pc{display:grid;grid-template-columns:1fr 1fr;gap:10px 22px;margin-top:18px;
  padding-top:16px;border-top:1px solid var(--line)}
.pc h4{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:7px}
.pc ul{list-style:none;font-size:14.5px;color:var(--ink-2)}
.pc li{position:relative;padding-inline-start:17px;margin-bottom:5px;line-height:1.5}
.pc li::before{position:absolute;inset-inline-start:0;font-weight:700}
.pros li::before{content:"+";color:#3E8E64}
.cons li::before{content:"–";color:#C4593F}
.buys{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}
.btn{text-decoration:none;font-size:14px;font-weight:700;padding:11px 18px;
  border-radius:10px;display:inline-block;transition:transform .1s,filter .1s}
.btn:hover{transform:translateY(-1px);filter:brightness(1.06)}
.btn-a{background:var(--accent);color:#fff}
.btn-b{background:#fff;color:var(--deep);border:1.5px solid var(--line-2)}

/* ---------- faq ---------- */
.faq{border-top:1px solid var(--line);margin-top:12px}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{cursor:pointer;list-style:none;padding:17px 30px 17px 0;position:relative;
  font-weight:600;color:var(--deep);font-size:16.5px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;inset-inline-end:4px;top:15px;
  font-size:21px;font-weight:400;color:var(--accent);line-height:1}
.faq details[open] summary::after{content:"–"}
.faq p{padding:0 0 18px;color:var(--ink-2);font-size:15.5px;margin:0}

/* ---------- guide index cards ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;margin:30px 0 10px}
.gcard{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--line);
  border-radius:var(--radius);overflow:hidden;text-decoration:none;color:inherit;
  box-shadow:var(--shadow);transition:transform .14s,box-shadow .14s}
.gcard:hover{transform:translateY(-3px);box-shadow:0 4px 10px rgba(58,34,48,.07),0 16px 34px rgba(58,34,48,.10)}
.gcard img{width:100%;aspect-ratio:1200/630;object-fit:cover}
.gcard-in{padding:18px 20px 20px;display:flex;flex-direction:column;flex:1}
.gcard h3{font-size:19px;line-height:1.3;margin:8px 0 0}
.gcard .sum{font-size:14.5px;color:var(--ink-2);margin-top:9px;flex:1}
.gcard .meta{font-size:12.5px;color:var(--ink-3);margin-top:14px}

/* ---------- footer ---------- */
.disc{font-size:13.5px;color:var(--ink-3);border-top:1px solid var(--line);
  padding-top:18px;margin-top:46px}
footer{border-top:1px solid var(--line);margin-top:56px;padding:34px 22px;
  text-align:center;color:var(--ink-3);font-size:13.5px;background:#FFFBF6}
footer nav{display:flex;gap:18px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}
footer a{color:var(--ink-2);text-decoration:none;font-weight:600}
footer a:hover{color:var(--accent-ink)}
.langsw{margin-top:12px;font-size:13px}

@media(max-width:600px){
  body{font-size:16px}
  .pc{grid-template-columns:1fr;gap:14px}
  .card-in{padding:18px}
  .nav-in{padding:10px 16px;gap:12px}
  .nav-links{gap:14px}
  .nav-links a{font-size:13px}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* ---------- rtl ---------- */
[dir=rtl] body,[dir=rtl] .logo,[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3{
  font-family:"Heebo","Assistant",Inter,system-ui,sans-serif}
[dir=rtl] .num{font-family:inherit}
"""

RTL_FONT = ('<link href="https://fonts.googleapis.com/css2?'
            'family=Heebo:wght@400;500;600;700;800&display=swap" rel="stylesheet">')
