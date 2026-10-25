<?php
/**
 * api/geo.php - the visitor's country for the regional privacy choice (assets/consent.js, data-geo="/api/geo.php").
 *
 * Looks the request's IPv4 address up in geo-v4.bin (built from DB-IP "IP to Country Lite", CC BY 4.0, by
 * tools/geo/build-geo-bin.py in the cruise-seniors repo) with a binary search over 10-byte records. Nothing is stored or
 * logged here. Without the data file, or for IPv6, it answers {"country":null} and the consent script asks first.
 * Same-origin JSON; never cached by shared caches.
 */
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, private');
header('X-Content-Type-Options: nosniff');
$ip = $_SERVER['REMOTE_ADDR'] ?? '';
$file = __DIR__ . '/geo-v4.bin';
$out = ['country' => null];
if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) && is_readable($file)) {
    $n = (int)(filesize($file) / 10);
    $x = sprintf('%u', ip2long($ip)) + 0;
    $fp = fopen($file, 'rb');
    $lo = 0; $hi = $n - 1; $hit = null;
    while ($fp && $lo <= $hi) {
        $mid = intdiv($lo + $hi, 2);
        fseek($fp, $mid * 10);
        $r = unpack('Nstart/Nend/a2cc', fread($fp, 10));
        $s = sprintf('%u', $r['start']) + 0; $e = sprintf('%u', $r['end']) + 0;
        if ($x < $s) { $hi = $mid - 1; } elseif ($x > $e) { $lo = $mid + 1; } else { $hit = $r['cc']; break; }
    }
    if ($fp) { fclose($fp); }
    if ($hit) { $out = ['country' => $hit, 'attribution' => 'IP Geolocation by DB-IP (https://db-ip.com), CC BY 4.0']; }
}
echo json_encode($out);
