# Deal count 1,024 -> 926 (2026-09-21): exact reconciliation

Read-only investigation. Nothing was restored, published or edited on production for this document.
**Verdict: valid deals WERE removed. "No good deals silently deleted" is NOT provable - it is disproved for at least 96 records (list below). Nothing was fixed; owner decisions needed.**

## 1. What the two numbers counted
| number | where | definition | value |
|---|---|---|---|
| "1110+" (old hero) | `#hero-count` = `enriched.length` | every row in `deals.json`, incl. the 86 over the $75 ceiling, printed with a literal "+" | 1,110 |
| "1024 deals" (old list header) | `#deal-count` = `getFiltered().length` | usable-title rows that are NOT `pricy` (over $75), default filters | 1,110 - 86 = 1,024 |
| "926" (new hero AND list) | `liveTotal()` / `LIVE_EN` | same rule as the old list: usable title AND not `pricy` | 1,011 - 85 = 926 |

So the **list** number has the same definition before and after (1,024 -> 926). FH-3 changed only the hero: it now equals the list (old hero 1,110 -> new 926 = -99 dataset, -85 definition). FH-1/2/4 change no data. The drop 1,024 -> 926 is entirely a **dataset** change.

## 2. Why the dataset changed: two publishers, two datasets
- **Old live (13:09Z, 1,110 rows)** was published by the **Windows machine**, not the VPS: pm2 app `deal-fetcher` (`workspace/skills/fetch-more-deals.js --rebuild`, `cron_restart: 0 */4 * * *`, local time) scrapes `aliexpress-search` rows into the LOCAL `archive.json` and then runs `node build-static.js` = full publish (`~/.pm2/logs/deal-fetcher-out.log`: "Building static site with 1107 / 1110 unique deals ... Live host 46.202.156.169 - 5 file(s) published"; mirror commits `chore: auto-sync site build`, author "Your Name", +0300: 12:04 -> hero 1107, 16:09 -> hero 1110).
- The local archive is a **stale copy of the VPS archive (last `priceCheckedAt` 2026-09-11)** plus local scans (addedAt max 2026-09-21T13:09:51Z). It never received the VPS's daily refresh/cleanup.
- **New live (VPS)**: my publishes at 18:26Z / 19:26Z (and an unintended re-run at 20:19Z, see section 6) built from the VPS `archive.json` + empty `queue.json`: 1,011 rows, 85 pricy.
- VPS-side timeline, same day: 01:01Z nightly 1,043 -> 09:02Z scan build 1,083 (`journalctl -u site-build/deals-bot`) -> [Windows publishes 1,107 (09:04Z), 1,110 (13:09Z)] -> 18:26Z VPS 1,011.

## 3. Pipeline stage counts, same code, both datasets (`tools/deal-count-recon`)
| stage (build-static.js) | local (old live) | VPS now (new live) | delta |
|---|---|---|---|
| queue + archive rows | 19,873 | 18,963 | -910 |
| valid (image, price>0) | 19,437 | 18,559 | -878 |
| dedupe -> unique products | 1,966 | 1,855 | -111 |
| delisted (priceUnavailable) | -136 -> 1,830 | -136 -> 1,719 | -111 |
| scraper artifacts | -25 -> 1,805 | -25 -> 1,694 | -111 |
| quality gate (orders>=300, rating>=4.3) | -218 -> 1,587 | -208 -> 1,486 | -101 |
| feed filter | 0 | 0 | 0 |
| Amazon switch OFF | -477 -> **1,110** | -475 -> **1,011** | -99 |
| of which pricy / list | 86 / **1,024** | 85 / **926** | -1 / -98 |
Reproduced exactly: local data -> 1,110; VPS data -> 1,011 (= live `deals.json`, 85 pricy).
Isolation runs: local archive + empty queue = 1,110 (queue irrelevant); VPS archive + local queue = 1,031; VPS 10:21Z backup + queue.bak = 1,083 (= the 09:02Z journal build); backup + empty queue 1,077; now-archive + queue.bak 1,043; now 1,011.
VPS lineage today: 1,083 -> **-40** (10:21Z store cleanup of 320 archive rows) = 1,043 -> **-32** (14:32Z queue.json 200 rows -> `[]`) = 1,011.

## 4. Record-level reconciliation of the old live set (1,110) vs new (1,011)
Diff by `dealKeys()` (id / image / title key, any match = same product): 992 old rows kept, **118 removed, 20 added**; 1,110 - 118 + 20 = 1,012; residual -1 = old rows that match one VPS row on different keys (dup pairs). Full list: `DEAL-COUNT-REMOVED-RECORDS-2026-09-21.md`.

| op (before -> after) | rows | evidence | valid deal lost? |
|---|---|---|---|
| A. Local-scan rows never on the VPS: 56 `aliexpress-search` (added Sep 14-21 by the Windows scanner), 9 on VPS at the Sep 11 snapshot but gone before 10:21Z, 3 from the old local queue | 1,110 -> 1,042 (-68) | not in VPS archive/queue nor 10:21Z backup; API returns 66/68 | **yes (66/68 still listed by the API, 0 fail the cleanup test)** |
| B. VPS store cleanup 10:21Z ("removed 320 dead deals"); 28 of the 320 were in the old live set | -28 | rows present in `archive.json.bak`, absent now; API returns 28/28 | **yes (0/28 dead by the cleanup's own test now)** |
| C. Delisted on VPS (`priceMisses>=3` -> `priceUnavailable`) | -20 | 20/20 flagged; API returns 1/20 | 19 legitimately gone; 1 flapping (API returns it twice) |
| D. Dedupe: VPS keeps another representative of the same product | -1 | key overlap with a live row | no (duplicate) |
| E. Quality gate on refreshed data (orders 301 -> 285 < 300) | -1 | row values | no (gate working) |
| F. Rows the VPS set has that the old set dropped | +20 | 13 stale delist flags on local, 4 dedupe representatives, 2 VPS-only, 1 local dead id | n/a |
| residual (multi-key matches) | -1 | | |
| **Total live rows** | **1,110 -> 1,011 (-99)** | list 1,024 -> 926 (-98; pricy 86 -> 85) | |

## 5. Are they dead? Independent evidence (run on the VPS 20:40Z, read-only)
`tools/deal-count-recon/vps_check.js`: (a) the store cleanup's own `isAlive()` on the stored link; (b) `aliexpress.affiliate.productdetail.get` for the product id, two passes (the refresh job documents that one batch can omit live products).
- 118 removed rows: 0/118 dead by `isAlive`; API returned 96/118 (A 66/68, B 28/28, C 1/20, D 1/1, E 1/1).
- **All 320 rows the 10:21Z cleanup removed: 0/320 dead by the same test now; API returns 299/320.**
- **All 200 queue rows emptied at 14:32Z (`queue.json.bak` written by `cleanup-deadlinks.js`): 0/200 dead; API returns 179/200.**
- From the Windows machine (Israel) the affiliate links of the 118 all resolved to a 200 `/item/<id>.html` page at the stored price.
Daily journal: "Store cleanup: removed N dead deals" = 780, 312, 427, 333, 317, 454, 304, 202, 316, 320, 328, 513, 320 (Sep 11-21) with no re-adds and `archive.json` receiving no new VPS rows since 2026-09-16.

**Conclusion.** The cleanup (404/410 or AliExpress off-`/item/` redirect on ONE GET from the VPS IP, no retry, no per-record log) is removing products that pass the same test minutes-to-hours later. Whether they were transiently blocked/redirected at removal time cannot be proven: the cleanup logs only a total, and `.bak` keeps a single generation (overwritten by the next removal).

## 6. Not verified / owner decisions (nothing changed)
1. **Second publisher.** Windows pm2 `deal-fetcher` (`pm2 jlist`: cron `0 */4 * * *`, args `--rebuild`, currently `stopped` between runs) will publish its stale dataset over the VPS build at its next new-deal run and can collide with a VPS FTP deploy. Smallest fix: `pm2 stop deal-fetcher` + drop `--rebuild`/`cron_restart` (or point it at the VPS). Not done here.
2. **Cleanup false positives.** Suggested: log removed links, require 2-3 consecutive failures (as `refresh-daily.js` does with `MISSES_BEFORE_DELISTING`), keep dated backups. Not done here. **Preserve evidence first:** the VPS `.bak` files are overwritten by the next removal; local copies (md5) `vps-bak/archive.json 3ef26687...`, `vps-bak/queue.json 786d633a...` are in `Documents/redesign-notes/sites-audit-2026-09-21/recon/`.
3. Unproven: exactly why the cleanup judged those links dead at 10:21Z/14:32Z; whether the old Windows-published set was ever served exactly as reconstructed (no CDN log; reconstruction reproduces 1,110 and the mirror hero=1110).
4. **Disclosure:** during this investigation a mistyped command (`node build-static.js --help`, which has no arg parsing) ran a normal build+FTP publish as `deals-bot` at 20:19Z. It used the same VPS dataset and code as the 19:26Z publish (live still 1,011 rows / 85 pricy, no mirror push happened); no concurrent FTP was running.

## Reproduce
`node instrument.js` (patches a scratch copy of `build-static.js` to dump each stage), `node run-recon.js <tag> <archive.json> <queue.json>`, `node diff.js`, `node added.js`, `node snap.js`, `vps_check.js` on the VPS as `deals-bot` (needs `/tmp/fh_check_input.json`). Paths are the Windows scratch layout; adjust `code/`, `vps/`, `local/`.
Journal: `journalctl -u site-build.service --since 2026-09-01 | grep -E "Deduped|dropped|quality gate|amazon-switch|Building"`, `journalctl -u deals-bot | grep -E "Store cleanup|Price refresh|Auto-archived"`.
