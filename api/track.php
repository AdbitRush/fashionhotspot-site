<?php
/**
 * First-party, cookieless analytics.
 *
 * WHY THIS EXISTS AND NOT GOOGLE ANALYTICS
 * ----------------------------------------
 * The site publishes in German, French, Spanish and Greek, so GDPR applies to a
 * real share of visitors. GA4 sets cookies and ships personal data to a third
 * country, which means a consent banner on every page — and a banner costs
 * conversions on a deals site where the first screen IS the product. This stores
 * counters instead, so there is nothing to consent to.
 *
 * WHAT IS STORED
 *   counts. That is the whole design.
 *     days    : how many pageviews and outbound clicks, per calendar day
 *     pages   : which paths were viewed, and how often
 *     langs   : which interface language
 *     sources : where the visit came from (?s=wa etc.), coarse
 *     clicks  : which merchant domain was clicked, and in which category
 *
 * WHAT IS NOT STORED
 *   no IP address, no user agent, no referrer URL, no cookie, no session id, no
 *   per-visit timestamp, no click id, nothing random assigned to a browser.
 *   There are no rows — only totals — so there is no event log to correlate and
 *   no way to reconstruct one person's path through the site. That is a
 *   deliberate ceiling on what this can ever be used for, not an oversight.
 *   It means you cannot ask "what did user X do"; you can only ask "how many".
 *
 * The user agent IS read, to drop obvious crawlers, and then discarded. Reading
 * is not storing: without it the numbers would mostly be bots and would answer
 * no question at all.
 *
 * WRITE SAFETY
 *   This is a public endpoint that writes to a file, so every bucket is capped.
 *   Past the cap a new key is folded into "_other" rather than added, which
 *   means a script posting a million distinct paths inflates one counter
 *   instead of growing the file without limit.
 *
 * Read the numbers at api/stats.php?token=… (same ADMIN_TOKEN as searches.php).
 */

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store, max-age=0');
header('Access-Control-Allow-Origin: https://fashionhotspot.site');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') { http_response_code(204); exit; }
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'post_required']);
    exit;
}

// Answer 204 to everything below. A beacon has nobody waiting for the reply,
// and a tracker must never be able to break or slow the page that called it.
$done = static function (): void { http_response_code(204); exit; };

// Same-origin only when the browser tells us the origin. sendBeacon always
// sends it, so in practice this rejects other sites posting into your counters
// while still tolerating a client that omits the header.
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && stripos($origin, 'fashionhotspot.site') === false) { $done(); }

// Crawlers would otherwise be most of the traffic. Read, match, discard —
// the string is never written anywhere.
$ua = $_SERVER['HTTP_USER_AGENT'] ?? '';
if ($ua === '' || preg_match('/bot|crawl|spider|slurp|bingpreview|headless|curl|wget|python-requests|facebookexternalhit|whatsapp|preview|monitor|uptime|lighthouse|pagespeed/i', $ua)) {
    $done();
}

$raw = (string)file_get_contents('php://input');
if (strlen($raw) > 2048) { $done(); }        // a real beacon is ~120 bytes
$in = json_decode($raw, true);
if (!is_array($in)) { $done(); }

/** Trim to a safe, short, single-line token. */
$clean = static function ($v, int $max): string {
    $s = trim((string)$v);
    $s = preg_replace('/[\x00-\x1F\x7F]/u', '', $s) ?? '';
    if (function_exists('mb_substr')) { $s = mb_substr($s, 0, $max, 'UTF-8'); }
    else { $s = substr($s, 0, $max); }
    return $s;
};

$type = $clean($in['t'] ?? '', 4);
if ($type !== 'pv' && $type !== 'cl') { $done(); }

$file = __DIR__ . '/stats.json';
$fp = @fopen($file, 'c+');
if (!$fp) { $done(); }
if (!flock($fp, LOCK_EX)) { fclose($fp); $done(); }

$db = json_decode(stream_get_contents($fp) ?: '{}', true);
if (!is_array($db)) { $db = []; }
foreach (['days', 'pages', 'langs', 'sources', 'clicks', 'cats'] as $k) {
    if (!isset($db[$k]) || !is_array($db[$k])) { $db[$k] = []; }
}

// Past the cap, count the event under "_other" rather than minting a key. The
// totals stay truthful; only the breakdown stops getting more detailed.
$bump = static function (array &$bucket, string $key, int $cap): void {
    if ($key === '') { return; }
    if (!isset($bucket[$key]) && count($bucket) >= $cap) { $key = '_other'; }
    $bucket[$key] = (int)($bucket[$key] ?? 0) + 1;
};

$today = gmdate('Y-m-d');
if (!isset($db['days'][$today]) || !is_array($db['days'][$today])) {
    $db['days'][$today] = ['pv' => 0, 'cl' => 0];
    // Keep roughly two years of daily rows, then drop the oldest.
    if (count($db['days']) > 800) {
        ksort($db['days']);
        $db['days'] = array_slice($db['days'], -800, null, true);
    }
}

$lang = strtolower(preg_replace('/[^a-zA-Z-]/', '', $clean($in['l'] ?? '', 8)) ?: 'xx');
$bump($db['langs'], $lang, 40);

if ($type === 'pv') {
    $db['days'][$today]['pv'] = (int)($db['days'][$today]['pv'] ?? 0) + 1;

    // Path only — never the query string, which is where personal data ends up
    // in URLs. ?s=wa is read separately below as a coarse channel label.
    $path = $clean($in['p'] ?? '/', 120);
    if ($path === '' || $path[0] !== '/') { $path = '/' . ltrim($path, '/'); }
    $path = explode('?', $path)[0];
    $path = explode('#', $path)[0];
    $bump($db['pages'], $path, 600);

    // Coarse channel, from ?s= on the landing URL. Alphanumeric and short by
    // construction, so it cannot carry an identifier.
    $src = strtolower(preg_replace('/[^a-z0-9_-]/i', '', $clean($in['s'] ?? '', 16)));
    $bump($db['sources'], $src !== '' ? $src : 'direct', 60);
} else {
    $db['days'][$today]['cl'] = (int)($db['days'][$today]['cl'] ?? 0) + 1;

    // Registrable-ish host of the destination, not the full affiliate URL —
    // affiliate URLs carry tracking ids, and there is no reason to keep those.
    $host = strtolower($clean($in['d'] ?? '', 80));
    $host = preg_replace('/^www\./', '', $host) ?? $host;
    if (!preg_match('/^[a-z0-9.-]+\.[a-z]{2,}$/', $host)) { $host = 'other'; }
    $bump($db['clicks'], $host, 200);

    $cat = strtolower(preg_replace('/[^a-z0-9_-]/i', '', $clean($in['c'] ?? '', 24)));
    $bump($db['cats'], $cat !== '' ? $cat : 'unknown', 80);
}

ftruncate($fp, 0);
rewind($fp);
fwrite($fp, json_encode($db, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
fflush($fp);
flock($fp, LOCK_UN);
fclose($fp);

$done();
