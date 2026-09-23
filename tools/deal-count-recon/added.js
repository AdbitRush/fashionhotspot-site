const fs = require('fs'), path = require('path');
const O = (t, f) => JSON.parse(fs.readFileSync(path.join('out', t, f + '.json'), 'utf8'));
const S = ['S0_queue_plus_archive', 'S1_all_valid', 'S2_deduped', 'S3_after_delist', 'S4_enriched', 'S5_after_artifact', 'S6_after_quality', 'S7_after_feed', 'S8_after_amazon'];
const L = {}, V = {}; S.forEach(s => { L[s] = O('local', s); V[s] = O('vps', s); });
const find = (rows, r) => rows.find(x => x.k.some(k => r.k.includes(k)));
const after = V.S8_after_amazon, before = L.S8_after_amazon;
const added = after.filter(r => !find(before, r));
const reasons = {};
for (const r of added) {
  let last = -1, lrow = null; S.forEach((s, i) => { const x = find(L[s], r); if (x) { last = i; lrow = x; } });
  let why;
  if (last < 0) why = 'not in local data at all (VPS-only row)';
  else if (last === 1) why = 'local dedupe kept a different representative row of the same product (local removed this row as duplicate)';
  else if (last === 2) { why = lrow && lrow.pu ? 'local: flagged priceUnavailable (stale delist mark), VPS: flag cleared/not set' : 'local: dropped as delisted (product id in local dead set) - VPS not'; }
  else why = 'local stage ' + S[last] + ' -> next removed';
  (reasons[why] = reasons[why] || []).push(r.t.slice(0, 45) + ' | local orders ' + (lrow && lrow.o) + '/rating ' + (lrow && lrow.r) + ' vs vps ' + r.o + '/' + r.r);
}
for (const [k, v] of Object.entries(reasons)) { console.log(v.length + '  ' + k); v.slice(0, 3).forEach(x => console.log('     ' + x)); }
// double match: VPS rows matched by 2 local rows
const cnt = new Map();
for (const b of before) { const x = find(after, b); if (x) cnt.set(x, (cnt.get(x) || 0) + 1); }
const dbl = [...cnt].filter(([, n]) => n > 1);
console.log('VPS rows matched by >1 old row:', dbl.length, dbl.map(([x]) => x.t.slice(0, 50)));
