// READ-ONLY: runs on the VPS from /tmp. Re-applies the store-cleanup's own liveness test and the refresh job's API detail call
// to records that left the live set. Writes nothing except stdout / one JSON in /tmp.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const ROOT = '/opt/whatsapp-deals-bot';
const axios = require(ROOT + '/node_modules/axios');
require(ROOT + '/node_modules/dotenv').config({ path: ROOT + '/.env', quiet: true });
const { isAlive } = require(ROOT + '/workspace/skills/cleanup-deadlinks.js');
const list = JSON.parse(fs.readFileSync('/tmp/fh_check_input.json', 'utf8'));
const KEY = process.env.ALIEXPRESS_APP_KEY, SEC = process.env.ALIEXPRESS_APP_SECRET, TID = process.env.ALIEXPRESS_TRACKING_ID;
const ts = () => new Date().toISOString().replace('T', ' ').replace(/\..+/, '');
const sign = p => crypto.createHmac('sha256', SEC).update(Object.keys(p).sort().map(k => k + p[k]).join('')).digest('hex').toUpperCase();
async function detail(ids) {
  const p = { app_key: KEY, method: 'aliexpress.affiliate.productdetail.get', product_ids: ids.join(','), target_currency: 'USD', target_language: 'EN', tracking_id: TID, country: 'IL', timestamp: ts(), sign_method: 'sha256', v: '2.0' };
  p.sign = sign(p);
  const { data } = await axios.get('https://api-sg.aliexpress.com/sync', { params: p, timeout: 25000 });
  return data?.aliexpress_affiliate_productdetail_get_response?.resp_result?.result?.products?.product || [];
}
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const api = new Map(); const ids = [...new Set(list.map(x => x.id).filter(Boolean))];
  for (let round = 1; round <= 2; round++) {          // two independent passes: the refresh job documents that a single batch can omit live products
    for (let i = 0; i < ids.length; i += 20) {
      let prods = []; try { prods = await detail(ids.slice(i, i + 20)); } catch (e) { console.error('api err', e.message); }
      for (const pr of prods) { const cur = api.get(String(pr.product_id)) || { seen: 0 }; api.set(String(pr.product_id), { seen: cur.seen + 1, sale: pr.target_sale_price, orders: pr.lastest_volume, rating: pr.evaluate_rate }); }
      await sleep(400);
    }
  }
  const out = [];
  for (const x of list) { const alive = await isAlive(x.link); const a = x.id ? api.get(x.id) : null; out.push({ i: x.i, class: x.class, id: x.id, title: x.title, storedPrice: x.price, vpsCleanupTestAlive: alive, apiReturnedInPasses: a ? a.seen : 0, apiSale: a && a.sale, apiOrders: a && a.orders, apiRating: a && a.rating }); await sleep(120); }
  fs.writeFileSync('/tmp/fh_check_output.json', JSON.stringify(out));
  const by = {};
  for (const o of out) { const s = by[o.class] = by[o.class] || { n: 0, vpsTestDead: 0, apiReturnedBothPasses: 0, apiReturnedOnce: 0, apiNever: 0 }; s.n++; if (!o.vpsCleanupTestAlive) s.vpsTestDead++; if (o.apiReturnedInPasses === 2) s.apiReturnedBothPasses++; else if (o.apiReturnedInPasses === 1) s.apiReturnedOnce++; else s.apiNever++; }
  console.log(JSON.stringify(by, null, 1));
})();
