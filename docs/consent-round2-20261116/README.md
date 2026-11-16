# Regional privacy review patch, 16 November 2026

BRANCH ONLY. No production deployment, tracking activation, cron run, browser installation or database replacement.

## Current state verified
- November DB-IP already active at /opt/site-geo/db-2026-11; monthly refresh already installed and ran on November 3.
- Both geo endpoints are deployed, no-store/private.
- AllyFind track.php already deployed. Existing page attempts its beacon before consent even when third-party tools are blocked.
- AllyFind nightly passed November 16 at 02:15-02:16:23 UTC, exit 0. Browser therefore already operational.
- Neither homepage had DB-IP backlink despite use of country results.

## Patch
- Both consent scripts insert DB-IP footer backlink on geo-using pages and full source/license/version/change credit on privacy pages using the loader.
- AllyFind root privacy generator and eight translated privacy source pages get full static credit because they do not all load consent.js. Added technical credit is English, not reviewed native translation.
- Explicit accepted consent is required before first-party track.php requests in ALL regions. Missing consent, pending lookup, denial and GPC block calls. No old events queued or replayed. A visitor who accepts mid-page begins counting with subsequent actions, not a replayed pageview.
- A shared boolean exposes only permission, not identifiers. Rejection updates it immediately; storage changes across tabs update it and stop loaded third-party scripts by reload.
- Existing US third-party opt-out remains unchanged. First-party counters deliberately stricter than that policy.
- Israel classification is configurable with data-il-policy="optout" on the consent script; default or invalid values preserve current opt-in. DO NOT enable optout without the owner's resolved choice. Its privacy explanation and all affected languages must be updated if policy changes.
- Source label constrained to wa/sh before first-party counters. Server endpoint/log retention still needs separate review, not a claim of legal exemption.

## Verification
Fourteen region/state cases passed against copies of current production HTML and locally intercepted patched scripts: IL, DE, US, unknown, saved grant, saved denial, GPC. All external/track.php requests aborted, no synthetic analytics reached production. Fresh, denied, unknown and GPC yield zero first-party tracking attempts. Explicit accept allows a later click; reject blocks following calls. Footer backlinks checked. Mobile privacy credit screenshots inspected. JS syntax checks and git diff --check passed.

Not yet tested: full build of each site, every route/template, all translated output visually, geo cache/proxy edge cases, full hosting/CDN log retention, network loss, all cross-tab scenarios. This is a review patch, not a compliance certificate or publish-ready certification. Reconcile source/deploy revision before deployment; main Voyageworthy tree is heavily dirty/untracked. Do not reset it.

## License sources
- https://db-ip.com/db/download/ip-to-country-lite
- https://db-ip.com/db/lite.php
- https://creativecommons.org/licenses/by/4.0/

DB-IP requires a backlink on pages that display OR USE database results. Monthly refresh must also refresh the stated database version in privacy credit. Runtime credit depends on the same loader that performs country lookup; no-JS pages do not use the result. No new accounts, payments, terms acceptance or recipients.
