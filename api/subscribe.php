<?php
/**
 * Mailing list sign-ups.
 *
 * The list is NOT RUNNING YET, and the page says so in as many words. That
 * matters: collecting addresses under an implied promise of "daily deals in
 * your inbox" and then sending nothing for months is the thing that gets a
 * sender marked as spam the day they finally do send. The copy promises only
 * what is true — we will keep the address and write when there is something to
 * write.
 *
 * WHAT IS STORED
 *   the address, the date, and the interface language
 * WHAT IS NOT
 *   no IP, no user agent, no referrer, no tracking of any kind. An email
 *   address is already personal data; there is no reason to attach a location
 *   and a device fingerprint to it as well.
 *
 * The file is under the web root so it is easy to retrieve, and .htaccess in
 * this directory denies .json over HTTP.
 *
 * NO THIRD PARTY. Nothing here talks to Mailchimp, Sendgrid or anyone else —
 * handing a list of addresses to a service the owner has not chosen is not a
 * decision to make on their behalf. Export the file when a real provider is
 * picked.
 */

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Access-Control-Allow-Origin: https://fashionhotspot.site');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Cache-Control: no-store');

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') { http_response_code(204); exit; }
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'post_required']);
    exit;
}

$in = json_decode((string)file_get_contents('php://input'), true);
if (!is_array($in)) { $in = $_POST; }
$email = trim((string)($in['email'] ?? ''));
$lang  = strtolower(preg_replace('/[^a-zA-Z]/', '', (string)($in['lang'] ?? 'en'))) ?: 'en';

// A honeypot field the real form leaves empty and a bot fills in. Cheaper and
// less hostile than a CAPTCHA, and it answers 200 so the bot does not learn it
// was caught.
if (trim((string)($in['website'] ?? '')) !== '') {
    echo json_encode(['ok' => true, 'status' => 'subscribed']);
    exit;
}

if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || mb_strlen($email) > 254) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'error' => 'invalid_email']);
    exit;
}

$file = __DIR__ . '/subscribers.json';
$fp = @fopen($file, 'c+');
if (!$fp) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'store_unavailable']);
    exit;
}
if (!flock($fp, LOCK_EX)) {
    fclose($fp);
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'busy']);
    exit;
}

$raw = stream_get_contents($fp);
$db = json_decode($raw ?: '{}', true);
if (!is_array($db)) { $db = []; }

// Keyed by lowercased address, so signing up twice is idempotent rather than
// creating a duplicate that would later be mailed twice.
$key = mb_strtolower($email, 'UTF-8');
$already = isset($db[$key]);
if (!$already) {
    $db[$key] = ['email' => $email, 'date' => gmdate('Y-m-d'), 'lang' => $lang];
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, json_encode($db, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    fflush($fp);
}
flock($fp, LOCK_UN);
fclose($fp);

echo json_encode([
    'ok' => true,
    'status' => $already ? 'already' : 'subscribed',
    'total' => count($db),
], JSON_UNESCAPED_UNICODE);
