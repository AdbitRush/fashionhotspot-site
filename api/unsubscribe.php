<?php
/**
 * unsubscribe.php — take an address off the newsletter list.
 *
 * WHY A TOKEN
 *
 * The obvious version takes ?e=someone@example.com and deletes it. That lets
 * anyone unsubscribe anyone whose address they can guess, and — worse — lets a
 * script confirm whether an address is ON the list by watching which requests
 * report a removal. So the link carries an HMAC of the address, and without a
 * matching token the endpoint does nothing and says nothing useful.
 *
 * The key is ADMIN_TOKEN from api/config.php, the same secret searches.php and
 * stats.php already use. If it is missing this endpoint refuses to run rather
 * than falling back to trusting the address alone.
 *
 * WHAT IT ANSWERS
 *
 * The same JSON whether the address was on the list or not. "You are
 * unsubscribed" is the truthful answer in both cases, and the difference is
 * exactly what an enumeration attempt is looking for.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$cfgFile = __DIR__ . '/config.php';
$cfg = is_file($cfgFile) ? (array)require $cfgFile : [];
$secret = (string)($cfg['ADMIN_TOKEN'] ?? '');
if ($secret === '') {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'not_configured']);
    exit;
}

$email = trim((string)($_REQUEST['e'] ?? ''));
$token = trim((string)($_REQUEST['t'] ?? ''));
if ($email === '' || $token === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'missing_parameters']);
    exit;
}

$key = mb_strtolower($email, 'UTF-8');
$expected = substr(hash_hmac('sha256', $key, $secret), 0, 16);
// hash_equals, not ===: a timing-safe comparison is the whole reason the token
// is worth having.
if (!hash_equals($expected, $token)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'bad_token']);
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
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'busy']);
    exit;
}

$raw = stream_get_contents($fp);
$db = json_decode($raw ?: '{}', true);
if (!is_array($db)) { $db = []; }

if (isset($db[$key])) {
    unset($db[$key]);
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, json_encode($db, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    fflush($fp);
}

flock($fp, LOCK_UN);
fclose($fp);

// Deliberately the same answer either way — see the note at the top.
echo json_encode(['ok' => true, 'status' => 'unsubscribed']);
