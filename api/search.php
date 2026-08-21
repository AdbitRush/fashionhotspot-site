<?php
/**
 * Live product search — the fallback when the published catalogue has no match.
 *
 * WHY THIS EXISTS
 * ---------------
 * The site publishes ~1,470 deals, rebuilt nightly. A visitor searching for
 * anything outside that set previously hit "No deals found" and a WhatsApp
 * link, which is a dead end dressed up as an answer. This asks AliExpress for
 * the thing they actually typed and returns real, affiliate-tracked products.
 *
 * WHY PHP, AND WHY HERE
 * ---------------------
 * The signature is an HMAC over the app secret, so it cannot be built in the
 * browser without publishing the secret. The site is static HTML on a host that
 * runs PHP, so a same-origin PHP endpoint is the only piece of server needed —
 * no CORS, no second service to keep alive, and it keeps working when the VPS
 * that runs the bot is down.
 *
 * NOT the scraper. external-search.js in the bot repo parses the AliExpress
 * search HTML; that is scraping, it breaks whenever the markup moves, and it
 * cannot produce a tracked link. aliexpress.affiliate.product.query returns the
 * price, the real discount, the image and promotion_link (already tracked), so
 * a click from here still earns.
 *
 * PARAMS THAT LOOK OPTIONAL AND ARE NOT
 * -------------------------------------
 *   target_currency=USD   prices come back in dollars, so nothing in this file
 *                         converts anything. The bug that priced a $12 product
 *                         at $150 was a conversion that should never have run.
 *                         Do not add one — the client converts at render time.
 *   min/max_sale_price    are in CENTS. Passing dollars does not error, it is
 *                         silently ignored. Measured in the bot repo: dollars
 *                         returned 0 usable rows out of 20.
 *   sign_method=sha256    and the signature is HMAC-SHA256 over the sorted
 *                         key+value concatenation, uppercase hex.
 */

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
// Same-origin only. This endpoint spends an API quota that belongs to this
// site, so there is no reason for another origin to be able to call it.
header('Access-Control-Allow-Origin: https://fashionhotspot.site');
header('Cache-Control: public, max-age=300');

// ── config ──────────────────────────────────────────────────────────────────
// config.php is gitignored and returns an array. If it is missing the endpoint
// reports that plainly rather than 500ing, so the front end can fall back to
// the WhatsApp link instead of showing a broken spinner forever.
$cfgFile = __DIR__ . '/config.php';
if (!is_file($cfgFile)) {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'not_configured', 'results' => []]);
    exit;
}
$cfg = require $cfgFile;
$KEY = $cfg['ALIEXPRESS_APP_KEY']    ?? '';
$SEC = $cfg['ALIEXPRESS_APP_SECRET'] ?? '';
$TID = $cfg['ALIEXPRESS_TRACKING_ID'] ?? 'default';
if ($KEY === '' || $SEC === '') {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'not_configured', 'results' => []]);
    exit;
}

// ── input ───────────────────────────────────────────────────────────────────
$q = trim((string)($_GET['q'] ?? ''));
// Strip control characters; keep every script, because the search box is used
// in six languages and Hebrew/Greek terms are normal input here.
$q = preg_replace('/[\x00-\x1F\x7F]/u', '', $q);
if (function_exists('mb_substr')) { $q = mb_substr($q, 0, 80, 'UTF-8'); }
if ($q === '' || mb_strlen($q, 'UTF-8') < 2) {
    echo json_encode(['ok' => true, 'query' => $q, 'results' => [], 'reason' => 'too_short']);
    exit;
}

$lang = strtoupper(preg_replace('/[^a-zA-Z]/', '', (string)($_GET['lang'] ?? 'EN')));
// Verified against the API in the bot repo: 'HE' returns Hebrew titles, 'IW'
// silently returns English. AliExpress wants the modern ISO code here.
$allowedLangs = ['EN', 'HE', 'ES', 'FR', 'DE', 'EL'];
if (!in_array($lang, $allowedLangs, true)) { $lang = 'EN'; }

// ── cache ───────────────────────────────────────────────────────────────────
// Two people searching "air fryer" a minute apart should cost one API call.
// sys_get_temp_dir() rather than a directory under the web root, so cache files
// are never fetchable — the same reasoning that keeps config.php out of reach.
$cacheDir = sys_get_temp_dir() . '/fh-search';
if (!is_dir($cacheDir)) { @mkdir($cacheDir, 0700, true); }
$cacheKey  = sha1(mb_strtolower($q, 'UTF-8') . '|' . $lang);
$cacheFile = $cacheDir . '/' . $cacheKey . '.json';
$CACHE_TTL = 1800; // 30 minutes

if (is_file($cacheFile) && (time() - filemtime($cacheFile)) < $CACHE_TTL) {
    $hit = file_get_contents($cacheFile);
    if ($hit !== false && $hit !== '') {
        header('X-Cache: HIT');
        echo $hit;
        exit;
    }
}

// ── rate limit ──────────────────────────────────────────────────────────────
// Deliberately crude: this only needs to stop a stuck key-repeat or a scraper
// from spending the whole API quota. Cache hits above are served before this,
// so a popular query never counts against anyone.
$ip     = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$rlFile = $cacheDir . '/rl-' . sha1($ip);
$now    = time();
$hits   = is_file($rlFile) ? array_filter(
    (array)json_decode((string)file_get_contents($rlFile), true),
    static fn($t) => is_numeric($t) && ($now - (int)$t) < 60
) : [];
if (count($hits) >= 20) {
    http_response_code(429);
    echo json_encode(['ok' => false, 'error' => 'rate_limited', 'results' => []]);
    exit;
}
$hits[] = $now;
@file_put_contents($rlFile, json_encode(array_values($hits)), LOCK_EX);

// ── request ─────────────────────────────────────────────────────────────────
$params = [
    'app_key'         => $KEY,
    'method'          => 'aliexpress.affiliate.product.query',
    'timestamp'       => gmdate('Y-m-d H:i:s'),
    'sign_method'     => 'sha256',
    'v'               => '2.0',
    'keywords'        => $q,
    'page_no'         => '1',
    'page_size'       => '12',
    'tracking_id'     => $TID,
    'target_currency' => 'USD',
    'target_language' => $lang,
    'ship_to_country' => 'IL',
    'sort'            => 'LAST_VOLUME_DESC',
    'min_sale_price'  => '300',    // cents — see header
    'max_sale_price'  => '30000',
];
ksort($params);
$base = '';
foreach ($params as $k => $v) { $base .= $k . $v; }
$params['sign'] = strtoupper(hash_hmac('sha256', $base, $SEC));

$url = 'https://api-sg.aliexpress.com/sync?' . http_build_query($params);

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 15,
    CURLOPT_CONNECTTIMEOUT => 6,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_USERAGENT      => 'fashionhotspot/1.0 (+https://fashionhotspot.site)',
]);
$raw  = curl_exec($ch);
$err  = curl_error($ch);
$code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($raw === false || $code !== 200) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => 'upstream_failed',
                      'detail' => $err !== '' ? 'network' : ('http_' . $code), 'results' => []]);
    exit;
}

$data = json_decode((string)$raw, true);
$rr   = $data['aliexpress_affiliate_product_query_response']['resp_result'] ?? null;
if (!is_array($rr) || (int)($rr['resp_code'] ?? 0) !== 200) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => 'upstream_rejected', 'results' => []]);
    exit;
}
$products = $rr['result']['products']['product'] ?? [];
if (!is_array($products)) { $products = []; }

// ── normalise ───────────────────────────────────────────────────────────────
// Only the fields a card renders. Everything else — commission_rate especially —
// is internal and has no business being readable in a browser's network tab.
$out = [];
foreach ($products as $p) {
    $price = (float)($p['target_sale_price'] ?? 0);
    $orig  = (float)($p['target_original_price'] ?? 0);
    $link  = (string)($p['promotion_link'] ?? '');
    $title = trim((string)($p['product_title'] ?? ''));
    if ($price <= 0 || $link === '' || $title === '') { continue; }

    // Recompute rather than trusting the API's `discount` string, and drop the
    // ones the site already refuses to publish elsewhere: an "original price"
    // of exactly 2.00x is an AliExpress anchor, not a price anyone charged, and
    // anything over 70% off is the same artefact wearing a bigger number.
    $off = 0;
    if ($orig > $price) {
        $ratio = $orig / $price;
        $pct   = (int)round((1 - $price / $orig) * 100);
        if (abs($ratio - 2.0) > 0.01 && $pct <= 70) { $off = $pct; }
    }

    $out[] = [
        'title'  => $title,
        'price'  => round($price, 2),
        'orig'   => $off > 0 ? round($orig, 2) : null,
        'off'    => $off,
        'image'  => (string)($p['product_main_image_url'] ?? ''),
        'link'   => $link,
        'rating' => isset($p['evaluate_rate']) ? (string)$p['evaluate_rate'] : null,
        'orders' => isset($p['lastest_volume']) ? (int)$p['lastest_volume'] : null,
    ];
    if (count($out) >= 9) { break; }
}

$payload = json_encode([
    'ok'      => true,
    'query'   => $q,
    'source'  => 'aliexpress',
    'live'    => true,
    'results' => $out,
], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

@file_put_contents($cacheFile, $payload, LOCK_EX);
header('X-Cache: MISS');
echo $payload;
