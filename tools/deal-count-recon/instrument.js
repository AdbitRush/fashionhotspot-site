// Patches the SCRATCH copy of build-static.js (recon/code) so every filter stage dumps the surviving rows.
// Nothing here touches the real repo or any production system.
const fs = require('fs'), path = require('path');
const f = path.join(__dirname, 'code', 'build-static.js');
let s = fs.readFileSync(f, 'utf8').replace(/\r\n/g, '\n');
function ins(before, tag, expr) {
  const i = s.indexOf(before);
  if (i < 0 || s.indexOf(before, i + 1) >= 0 && before.length < 40) throw new Error('anchor: ' + before.slice(0, 50));
  s = s.slice(0, i) + `__dump('${tag}', ${expr});\n` + s.slice(i);
}
s = s.replace("const fs   = require('fs');", `const fs   = require('fs');
const __PK = require('./workspace/skills/product-key.js'), __PI = require('./workspace/skills/product-id.js');
function __dump(tag, arr) {
  const out = arr.map(d => ({ k: __PK.dealKeys(d), id: __PI.knownId(d), t: String(d.storeTitle || d.title || d.text || '').slice(0, 70), p: d.price, pl: d.platform || null, src: d.source || null, o: d.orders, r: d.rating, pu: !!d.priceUnavailable, pricy: d.pricy === undefined ? null : !!d.pricy, at: d.addedAt || d.publishedAt || null, l: String(d.link || d.finalLink || '').slice(0, 90) }));
  fs.writeFileSync(path.join(process.env.RECON_OUT || '.', tag + '.json'), JSON.stringify(out));
}`);
ins('// Sort newest-first BEFORE deduping', 'S1_all_valid', 'deals');
ins("console.log(`Deduped ${beforeDedup}", 'S2_deduped', 'deals');
ins('\nlet enriched = deals.map(d => {', 'S3_after_delist', 'deals');
ins('// ─── SCRAPER ARTIFACTS', 'S4_enriched', 'enriched');
ins('// --- QUALITY GATE (AliExpress rows only)', 'S5_after_artifact', 'enriched');
ins('// Sort newest first\n// ─── AFFILIATE FILTER', 'S6_after_quality', 'enriched');
ins('// Fix 3 (2026-09-15): a pure newest-first sort', 'S7_after_feed', 'enriched');
ins('// ── Coupon section switch', 'S8_after_amazon', 'enriched');
// also dump "all" (queue+archive before the image/price filter)
ins("// telesco.pe thumbnails are Telegram CDN links", 'S0_queue_plus_archive', 'all');
fs.writeFileSync(f, s);
console.log('instrumented', f);
