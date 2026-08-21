<?php
/**
 * Template for api/config.php — the credentials api/search.php needs.
 *
 * TO ACTIVATE LIVE SEARCH
 * -----------------------
 *   1. Copy this file to api/config.php  (same directory, drop ".example")
 *   2. Paste the three values from whatsapp-deals-bot/.env — they are the same
 *      credentials the nightly deal fetch already uses:
 *          ALIEXPRESS_APP_KEY
 *          ALIEXPRESS_APP_SECRET
 *          ALIEXPRESS_TRACKING_ID
 *   3. bash deploy.sh
 *
 * Until config.php exists, api/search.php answers 503 {"error":"not_configured"}
 * and the site quietly falls back to the WhatsApp link, exactly as it did
 * before. Nothing breaks while this is unset — it just does not search live.
 *
 * WHY THIS IS A TEMPLATE AND NOT THE REAL FILE
 * --------------------------------------------
 * config.php holds an API secret. It is in .gitignore and must stay there: this
 * repo is public, and deploy.sh walks the whole tree, so a committed secret
 * would be both in git history and served from a public host. That combination
 * has already happened here once — see the deploy.sh comment about PW.txt and
 * HANDOFF.md being fetchable at fashionhotspot.site.
 *
 * config.php is still UPLOADED by deploy.sh (it excludes .md/.sh/.py, not .php),
 * so creating it locally is enough to put it on the host. PHP files are executed
 * rather than served, so the secret is not readable over HTTP even directly.
 */

return [
    'ALIEXPRESS_APP_KEY'    => 'PASTE_APP_KEY_HERE',
    'ALIEXPRESS_APP_SECRET' => 'PASTE_APP_SECRET_HERE',
    'ALIEXPRESS_TRACKING_ID' => 'PASTE_TRACKING_ID_HERE',
];
