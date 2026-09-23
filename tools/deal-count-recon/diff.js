// Record-level diff: rows in the pre-sprint live set (local dataset -> 1110) vs the live set now (VPS dataset -> 1011).
const fs = require('fs'), path = require('path');
const O = (t, f) => JSON.parse(fs.readFileSync(path.join(__dirname, 'out', t, f), 'utf8'));
const STAGES = ['S0_queue_plus_archive', 'S1_all_valid', 'S2_deduped', 'S3_after_delist', 'S4_enriched', 'S5_after_artifact', 'S6_after_quality', 'S7_after_feed', 'S8_after_amazon'];
const A = { local: {}, vps: {}, vpsbak: {} };
for (const t of Object.keys(A)) for (const s of STAGES) A[t][s] = O(t, s + '.json');
const idx = (rows) => { const m = new Map(); rows.forEach((r, i) => r.k.forEach(k => { if (!m.has(k)) m.set(k, i); })); return m; };
const IDX = {}; for (const t of Object.keys(A)) { IDX[t] = {}; for (const s of STAGES) IDX[t][s] = idx(A[t][s]); }
const has = (t, s, row) => { for (const k of row.k) { const i = IDX[t][s].get(k); if (i !== undefined) return A[t][s][i]; } return null; };
const before = A.local.S8_after_amazon, after = A.vps.S8_after_amazon;
const removed = before.filter(r => !has('vps', 'S8_after_amazon', r));
const added = after.filter(r => !has('local', 'S8_after_amazon', r));
const kept = before.length - removed.length;
console.log(`BEFORE (local dataset) ${before.length} rows | AFTER (VPS dataset) ${after.length} rows | kept ${kept} | removed ${removed.length} | added ${added.length} | check ${before.length}-${removed.length}+${added.length}=${before.length - removed.length + added.length}`);

const cats = {}; const detail = [];
function cls(r) {
  // last VPS stage where the product still exists
  let last = -1; let vrow = null;
  for (let i = 0; i < STAGES.length; i++) { const x = has('vps', STAGES[i], r); if (x) { last = i; vrow = x; } }
  if (last >= 0) {
    const nxt = STAGES[last + 1];
    const why = { S0_queue_plus_archive: 'in VPS data but filtered at image/price gate (no image or price<=0)', S1_all_valid: 'collapsed by dedupe (a duplicate/relist of another VPS product)', S2_deduped: 'dropped as DELISTED on VPS (priceUnavailable / dead id)', S3_after_delist: 'n/a', S4_enriched: 'dropped as scraper-artifact title', S5_after_artifact: 'dropped by QUALITY GATE on VPS data (orders<300 or rating<4.3)', S6_after_quality: 'feed filter', S7_after_feed: 'Amazon switch' };
    return { cat: 'in_VPS_data_but_' + (nxt || 'final').replace('S', 'stage').slice(0, 40), why: why[STAGES[last]] || STAGES[last], vrow, last };
  }
  // not in VPS at all now; was it in the VPS pre-cleanup backup?
  const b = has('vpsbak', 'S0_queue_plus_archive', r);
  if (b) { return { cat: 'removed_from_VPS_archive_by_10:21_store_cleanup_or_later', why: 'present in VPS archive.json.bak (10:21Z), absent from VPS archive now', vrow: b, last: -2 }; }
  return { cat: 'never_in_VPS_data', why: 'not in VPS archive/queue now, nor in the 10:21Z backup', vrow: null, last: -3 };
}
for (const r of removed) { const c = cls(r); (cats[c.cat] = cats[c.cat] || []).push({ r, c }); }
console.log('\nREMOVED rows by classification:');
for (const [k, v] of Object.entries(cats).sort()) console.log('  ' + String(v.length).padStart(4) + '  ' + k + '  -- ' + v[0].c.why);

// deeper look at each category
function sample(v, n = 5) { return v.slice(0, n).map(({ r, c }) => `     - ${r.t.slice(0, 50)} | $${r.p} | orders ${r.o} rating ${r.r} | vps: ${c.vrow ? `orders ${c.vrow.o} rating ${c.vrow.r} pu=${c.vrow.pu}` : 'absent'}`).join('\n'); }
for (const [k, v] of Object.entries(cats)) { console.log('\n' + k + ' (' + v.length + ')'); console.log(sample(v)); }

// were any removed rows duplicates/relists of a KEPT row? check by title key and image key overlap with any VPS final row (dealKeys already includes img+ttl); plus fuzzy title prefix
const vpsTitles = new Map(after.map(r => [r.t.toLowerCase().replace(/[^a-z0-9֐-׿]/g, '').slice(0, 24), r]));
let fuzzy = 0; const fuzzyEx = [];
for (const r of removed) { const t = r.t.toLowerCase().replace(/[^a-z0-9֐-׿]/g, '').slice(0, 24); if (t.length >= 16 && vpsTitles.has(t)) { fuzzy++; if (fuzzyEx.length < 5) fuzzyEx.push(r.t.slice(0, 60)); } }
console.log(`\nremoved rows whose first-24-char normalised title equals a row still live: ${fuzzy}`, fuzzyEx);

// dead / delisted evidence for the 'never in VPS' + 'cleanup' groups: does the VPS bak row carry priceUnavailable?
for (const k of Object.keys(cats)) { const v = cats[k]; const pu = v.filter(x => x.c.vrow && x.c.vrow.pu).length; console.log(`${k}: rows flagged priceUnavailable in VPS data: ${pu}/${v.length}`); }

// full dump for the record
fs.writeFileSync(path.join(__dirname, 'removed_records.json'), JSON.stringify(removed.map(r => { const c = cls(r); return { title: r.t, price: r.p, orders: r.o, rating: r.r, src: r.src, id: r.id, link: r.l, class: c.cat, why: c.why, vps_orders: c.vrow && c.vrow.o, vps_rating: c.vrow && c.vrow.r, vps_priceUnavailable: c.vrow && c.vrow.pu, vps_price: c.vrow && c.vrow.p }; }), null, 1));
fs.writeFileSync(path.join(__dirname, 'added_records.json'), JSON.stringify(added.map(r => ({ title: r.t, price: r.p, orders: r.o, rating: r.r, id: r.id, link: r.l, in_local_stage: STAGES.filter(s => has('local', s, r)).pop() || 'absent from local data' })), null, 1));
const aCats = {}; for (const r of added) { const st = STAGES.filter(s => has('local', s, r)).pop() || 'absent'; aCats[st] = (aCats[st] || 0) + 1; }
console.log('\nADDED rows (in VPS-now, not in old live set) by last local stage where they exist:', aCats);
