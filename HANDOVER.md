# HANDOVER — fashionhotspot-site

Written so a different coding model can continue with zero chat history.
Rule: every work session ends with commit + push + a one-line update to "Current sprint status" below, even for partial work and especially before token limits. Deeper history (design system, HTML pitfalls, past incidents) lives in `HANDOFF.md` (Hebrew).

## 1. Architecture in 10 lines
1. Public repo, live site https://fashionhotspot.site (Hostinger). This repo is the **deploy target**, not the source of truth for most of it.
2. `index.html` and everything the homepage/deal feed needs (deals.json-derived pages, theme CSS/JS) are **generated** by `site-template.js` + `build-static.js` in the private `whatsapp-deals-bot` repo, then synced into this repo. **Never hand-edit generated files here** — the next build overwrites them.
3. Exceptions actually edited in THIS repo: `content/` (English guide source JSON) and `content/i18n/<lang>/` (per-field translations), `site-config.json` (affiliate on/off switches), and this file.
4. Guides are rendered from `content/` by `tools/build.py` (Python) — English canonical, other languages merge field-by-field over it so a partial translation still renders.
5. Deploy is `deploy.sh`: walks the whole tree and FTPs every file that should be public (curl + `.env.ftp`), skipping `.md`/`api/*.json`/credentials. It used to upload a hardcoded 7-file list and silently missed everything added since — if something "isn't updating on the site", check `deploy.sh` is walking the tree, not the deploy step itself.
6. Deploy pipeline end to end: `whatsapp-deals-bot: node build-static.js` (builds `docs/` and syncs it here) → `/root/bin/fashionhotspot-pull.sh` on the VPS (pulls this repo) → `fashionhotspot-site: bash deploy.sh` (FTP to the live host). The bot's nightly `site-build.timer` (01:00 UTC) runs this whole chain automatically.
7. `site-config.json` controls per-source affiliate switches (AliExpress/Amazon/Israel) at **build time** — a switched-off source's links are never written into the HTML at all (not hidden with CSS), so nothing looks like concealment in the page source. Toggle with `python tools/site_toggle.py <source> on|off` or `!site <source> on|off` from WhatsApp; either way the site rebuilds and redeploys in ~2 minutes.
8. Deal data (`deals.json`) is generated, not edited here; it is gitignored in the bot repo for weight and because it is the payload that changes `index.html` on every build. A local copy may exist in this checkout from an old sync — do not trust its row count as current; check the live site or the bot repo's `docs/recon/`.
9. Bilingual/multi-language: `he/ fr/ de/ es/ el/ ru` (or a subset) mirror the English pages; `tools/i18n_schema.py`/`langs.py` define the language set for guides.
10. Owner-only, code-excluded item: the Hostinger edge browser-check interstitial (FH-5, ~5.7s for first-time visitors) — a hPanel setting, not fixable here.

## 2. What works today
- Homepage/deal feed, search, WhatsApp CTAs, light/dark theme, list/card view toggle (FH-1/FH-2, 2026-09-21 sprint) — generated and deployed from the bot repo.
- Guides (`content/`, `tools/build.py`) in multiple languages; `site-config.json` affiliate switches.
- Deploy via `deploy.sh` (full-tree walk, FTP, `.deploy-manifest` skips unchanged files unless `--force`).
- See the bot repo's `HANDOVER.md` section 9 for the current, exact deal-count story (1,024 → 926 on 2026-09-21, root cause found and fixed 2026-09-22, ~90 live records restored — see `docs/recon/` there).

## 3. Mid-work / not done
- Amazon Associates pre-submission fixes (backlog Q9): strip the "GENERATED FILE" comment from served HTML, refresh stale guide dates, fix 2 untagged Amazon deals, fix truncated Amazon titles. Not started here.
- Translation long tail (backlog F1): hundreds of deals still lack `title_en`, gating the bilingual search index.
- No feature branches in this repo currently; `main` is deployed directly (auto-sync commits from the bot's build + your own guide/config edits).

## 4. Build / deploy commands (exact)
```
# Guides (this repo, Python):
python tools/build.py                 # all guides, all languages
python tools/build.py <slug>          # one guide
python tools/site_toggle.py status    # check affiliate switches
python tools/site_toggle.py aliexpress on|off [--deploy]

# Full site (from the bot repo — see its HANDOVER.md section 4):
node build-static.js --no-publish     # preview, no FTP
sudo -u deals-bot node build-static.js --no-mirror   # VPS, real FTP publish, no repo push

# This repo's own deploy (after any content/ or site-config.json edit):
./deploy.sh --dry-run                 # list what would upload
./deploy.sh                           # real FTP publish
```
Verify against the LIVE site, never the build output: `curl -sI https://fashionhotspot.site/ | grep -i last-modified`.

## 5. FTP-serialization rule
Only ONE FTP deploy to Hostinger may run at a time, from either repo's deploy step. Check `systemctl list-timers site-build.timer` on the VPS before a manual publish — do not start one within a few minutes of the 01:00 UTC nightly run, and never run two deploys concurrently.

## 6. `.env.ftp` fields (names only, never values)
`FTP_HOST`, `FTP_USER`, `FTP_PASS`, `FTP_PATH`. File is gitignored (`.env.ftp*`). `api/config.php` (AliExpress app secret for the live search endpoint) is also gitignored — see `api/config.example.php` for its shape.

## 7. Current sprint status
Updated 2026-09-22.
- **AllyFind migration — this repo's own rebrand DONE and LIVE on allyfind.com, 2026-09-22** (commit `51ae20d`). Spec: `whatsapp-deals-bot/docs/specs/allyfind-migration-spec-22sep.txt` (this session worked from a copy at `filebin.net/allyfind-pages-22sep`). `tools/build.py`/`tools/langs.py` now read `GUIDES_SITE`/`GUIDES_BRAND`/`GUIDES_OUT` env vars (default = fashionhotspot's own values, so this repo's own build/deploy is byte-for-byte unaffected when unset) — also fixed the nav-logo wordmark split and the `AUTHOR` byline, both hardcoded "fashionhotspot" text a plain grep would have missed the same way the homepage rebrand session missed its split-tag logo. New `tools/build_brand.py` (assembles a second brand's full tree into a scratch dir, never this repo's working tree), `tools/check_site_output.py` (required-output manifest + same-origin link-integrity + brand-leakage gate, local or `--live`), `tools/deploy_brand.sh` (reuses `deploy.sh`'s chunked-curl FTP pattern, explicitly excludes the 7 files owned by `whatsapp-deals-bot/build-static.js` so it can never overwrite them with a stale fetch). Deployed: 330 guide pages (55 × 6 languages) + posts.html ×6 + 5 language homes + terms.html + robots.txt + manifest.webmanifest + sitemap.xml + icons + images/ = 754 files, to allyfind.com's own FTP-scoped document root (`.env.ftp.allyfind`, gitignored). Verified live: 344/344 required URLs return 200, 11,615 same-origin links checked with zero broken links, zero "fashionhotspot" text anywhere, he/ is `dir="rtl"` and the other 5 languages `dir="ltr"`. fashionhotspot.site spot-checked unchanged (still 200, still fashionhotspot-branded, same nav logo).
- FH-1..FH-4 (2026-09-21 sprint: light default, shared stylesheet, deal-count wording, search-suggestions overlay) are live and independently verified. FH-5 (Hostinger interstitial) is the owner's hPanel action, excluded from code work.
- Deal-count drop (1,024 → 926) root-caused and the underlying bug fixed in the bot repo (`workspace/skills/cleanup-deadlinks.js`, 2026-09-22): the store cleanup was deleting live products on a single blocked/redirected GET. Now tri-state with a two-separate-run confirmation and a 5% abort gate. ~90 of the wrongly-removed records were restored to `archive.json`; the next nightly build/publish carries them onto the live site — verify the live count afterward.
- Windows `deal-fetcher` pm2 job (the second publisher that caused the two-dataset split) has been stopped and deleted; the VPS is now the only publisher.
- Welcome share link now URL-encoded on the bot side (unrelated to this repo directly, but the WhatsApp CTA here points at the same bot).
- Next: AllyFind Workstream 3 (old-domain 301 redirects) — now unblocked, since allyfind.com's guides are live too, not just its homepage — is the bot repo's decision, not this one's. Then backlog Q9 (Amazon pre-submission fixes) once Q8's restoration is confirmed live; then F1 (translation long tail).

One-line status log (newest first):
- 2026-09-23 (later): es/fr/de/el translations for the 60 new guides finished (300/300, 0 failed) and deployed (commit `bd1d330`) minutes after the entry below shipped English-fallback for those 4 — all 6 languages now carry real translated text, spot-verified live (e-readers' `<h1>` in all 6). One residual gap: `fishing`'s Hebrew translation is still missing despite the run reporting 0 failed — worth a `--force --slug fishing --lang he` re-run, not investigated further.
- 2026-09-23: 60 new guides (owner-provided, 3 spec files) + guides-browser rebuild (search/chips/grid-list/URL-state, allyfind-guides-browser-spec) + Gifts/Seasonal group fix, all live on allyfind.com (commit `5a1a426`, deployed via allyfind-build.timer at 13:28 UTC) — verified: 200s + zero U+FFFD + correct images across en/he/es/fr/de/el for a sample guide, 788 real AliExpress affiliate links generated (data/aliexpress-links.json), guides browser's 115-guide chip counts live. Also see whatsapp-deals-bot HANDOVER for the currency-selector and title-glossary fixes deployed the same run.
- 2026-09-22 (later): AllyFind's own guides/terms/robots/manifest/sitemap rebrand done and deployed live (commit `51ae20d`) — see the migration entry above; next = hand off to whatsapp-deals-bot's HANDOVER for Workstream 3 (redirects), or Q9 here.
- 2026-09-22: wrote this HANDOVER.md; deal-count root cause fixed and ~90 records restored (bot repo); Windows deal-fetcher stopped; next = verify the restore is live, then Q9.
