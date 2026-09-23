<?php
/**
 * api/go.php — /go/<id>?u=<affiliate url>  ->  302 to that exact URL, plus an
 * aggregate (never per-click) count of the redirect.
 *
 * WHY THIS EXISTS
 * The bot's WhatsApp messages sent the raw affiliate link directly, so there
 * was no way to know whether a shared deal was ever actually opened. This
 * hop answers "how many, for which deal, on which day" without adding a
 * per-click log — same privacy stance as api/track.php (aggregate counts
 * only, no IP/UA/timestamp/session stored), because a click hop is exactly
 * the kind of endpoint that tempts one into building a tracking log by
 * accident.
 *
 * THE URL TRAVELS VERBATIM
 * ?u= is url-decoded and redirected to exactly as given — never re-encoded,
 * never re-built from parts, never had a tag appended or stripped. The only
 * check is that its HOST is one this site actually sends people to (see
 * ALLOWED_HOSTS below); without that, this endpoint would be an open
 * redirect anyone could point at any URL using this site's good name.
 *
 * FAIL OPEN, NEVER FAIL CLOSED ON THE REDIRECT
 * A malformed id, a missing/disallowed u, or a logging failure never blocks
 * the redirect once u itself is present and validated — this hop existing
 * must never be the reason a real deal link stops working. The caller (the
 * bot) is expected to keep this behind a feature flag until proven live, and
 * to send the raw affiliate link directly whenever it cannot build a go link
 * for any reason — that flag is the actual "hop is down" fallback, not
 * anything in this file.
 */

declare(strict_types=1);

// Known destinations only. Add a host here before routing a new affiliate
// network through this hop.
const ALLOWED_HOSTS = [
    's.click.aliexpress.com',
    'a.aliexpress.com',
    'aliexpress.com',
    'www.aliexpress.com',
    'buyme.co.il',
    'www.buyme.co.il',
];

$id = (string)($_GET['id'] ?? '');
$id = preg_replace('/[^A-Za-z0-9._-]/', '', $id) ?? '';
$u = (string)($_GET['u'] ?? '');

if ($u === '') {
    http_response_code(400);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'missing u';
    exit;
}

$host = strtolower((string)(parse_url($u, PHP_URL_HOST) ?: ''));
$scheme = strtolower((string)(parse_url($u, PHP_URL_SCHEME) ?: ''));
$hostOk = $scheme === 'https' && in_array($host, ALLOWED_HOSTS, true);

if (!$hostOk) {
    http_response_code(400);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'disallowed target host';
    exit;
}

// Best-effort aggregate count. Any failure here (disk full, lock timeout,
// permissions) is swallowed -- the redirect below must happen regardless.
try {
    $file = __DIR__ . '/go-clicks.json';
    $fp = @fopen($file, 'c+');
    if ($fp && flock($fp, LOCK_EX)) {
        $db = json_decode(stream_get_contents($fp) ?: '{}', true);
        if (!is_array($db)) { $db = []; }
        foreach (['days', 'ids', 'hosts'] as $k) {
            if (!isset($db[$k]) || !is_array($db[$k])) { $db[$k] = []; }
        }
        $bump = static function (array &$bucket, string $key, int $cap): void {
            if ($key === '') { return; }
            if (!isset($bucket[$key]) && count($bucket) >= $cap) { $key = '_other'; }
            $bucket[$key] = (int)($bucket[$key] ?? 0) + 1;
        };
        $today = gmdate('Y-m-d');
        $db['days'][$today] = (int)($db['days'][$today] ?? 0) + 1;
        if (count($db['days']) > 800) {
            ksort($db['days']);
            $db['days'] = array_slice($db['days'], -800, null, true);
        }
        $bump($db['ids'], $id !== '' ? $id : 'unknown', 4000);
        $bump($db['hosts'], $host, 40);

        ftruncate($fp, 0);
        rewind($fp);
        fwrite($fp, json_encode($db, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        fflush($fp);
        flock($fp, LOCK_UN);
    }
    if ($fp) { fclose($fp); }
} catch (\Throwable $e) {
    // logging is best-effort; never let it block the redirect below
}

header('Location: ' . $u, true, 302);
exit;
