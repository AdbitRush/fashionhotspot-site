<?php
// ---------------------------------------------------------------------------
// Serves the English homepage at "/".
//
// This file used to be six lines: three header() calls sending
// "no-cache, no-store, must-revalidate" + Pragma + Expires, and a readfile().
// Every one of those was working against the site.
//
//   no-store  forbids storing the response AT ALL, so a repeat visitor
//             re-downloaded the whole homepage — 297KB — on every single view,
//             and Hostinger's CDN reported x-hcdn-cache-status: DYNAMIC for
//             the most requested URL on the site.
//   readfile  sends no Last-Modified and no ETag, so even a browser willing to
//             revalidate had nothing to revalidate WITH. "/" was the only page
//             on the site with no Last-Modified; /he/, /es/ and the rest are
//             plain files and always had one.
//
// So the homepage was the one page that could never answer 304, on a site
// whose homepage is 90% of its traffic.
//
// Now: a short CDN TTL, a validator, and a real 304 for anyone who already has
// the page. The nightly build rewrites index.html roughly once a day, so five
// minutes of edge staleness is the whole cost.
// ---------------------------------------------------------------------------
$file = __DIR__ . '/index.html';

if (!is_readable($file)) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo "homepage unavailable\n";
    exit;
}

$mtime = filemtime($file);
$size  = filesize($file);
$etag  = '"' . dechex($mtime) . '-' . dechex($size) . '"';

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: public, max-age=300, must-revalidate');
header('Last-Modified: ' . gmdate('D, d M Y H:i:s', $mtime) . ' GMT');
header('ETag: ' . $etag);

// PHP sets these two by default in some configurations, and they are what an
// old HTTP/1.0 proxy reads instead of Cache-Control. Leaving them behind would
// undo the line above for exactly the caches least able to cope.
header_remove('Pragma');
header_remove('Expires');

$inm = isset($_SERVER['HTTP_IF_NONE_MATCH']) ? trim($_SERVER['HTTP_IF_NONE_MATCH']) : '';
$ims = isset($_SERVER['HTTP_IF_MODIFIED_SINCE']) ? $_SERVER['HTTP_IF_MODIFIED_SINCE'] : '';

// ETag wins when both are sent, which is what RFC 9110 asks for: it is exact,
// while a date is only good to the second.
if ($inm !== '') {
    // A revalidating client may send W/"..." or a list; a substring test is the
    // pragmatic match here and cannot produce a false 304 for a different build,
    // because the tag encodes both mtime and size.
    if (strpos($inm, $etag) !== false) {
        http_response_code(304);
        exit;
    }
} elseif ($ims !== '') {
    $since = strtotime($ims);
    if ($since !== false && $since >= $mtime) {
        http_response_code(304);
        exit;
    }
}

header('Content-Length: ' . $size);
readfile($file);
