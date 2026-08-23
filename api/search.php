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

// ── search log ──────────────────────────────────────────────────────────────
// What people look for and do not find is the most useful signal this site
// produces: it is a shopping list, written by the visitors, of deals worth
// sourcing. Kept so those can be filled later.
//
// DELIBERATELY ANONYMOUS. No IP, no user agent, no session, no timestamp per
// visitor — only the term, how many times it has been asked, how many results
// it returned last time, and when it was last seen. There is no way to tie a
// row back to a person, which is the right default for something that records
// what people type. The rate limiter keeps IPs, but separately and only for 60
// seconds.
//
// Written under the web root so the owner can read it, and .htaccess denies it
// over HTTP — see the deny rule this ships with.
function fh_log_search(string $q, int $found, string $lang): void {
    $file = __DIR__ . '/searches.json';
    $fp = @fopen($file, 'c+');
    if (!$fp) { return; }
    // Locked, because two visitors searching at once would otherwise each read
    // the file, add their own row, and write back — losing one of them.
    if (!flock($fp, LOCK_EX)) { fclose($fp); return; }
    $raw = stream_get_contents($fp);
    $db = json_decode($raw ?: '[]', true);
    if (!is_array($db)) { $db = []; }
    $key = mb_strtolower(trim($q), 'UTF-8');
    if (isset($db[$key])) {
        $db[$key]['n'] = (int)$db[$key]['n'] + 1;
        $db[$key]['found'] = $found;
        $db[$key]['last'] = gmdate('Y-m-d');
        if (!in_array($lang, $db[$key]['langs'] ?? [], true)) { $db[$key]['langs'][] = $lang; }
    } else {
        $db[$key] = ['q' => trim($q), 'n' => 1, 'found' => $found,
                     'first' => gmdate('Y-m-d'), 'last' => gmdate('Y-m-d'),
                     'langs' => [$lang]];
    }
    // Cap it. An unbounded file that every search appends to is a slow leak,
    // and the tail is single-hit typos nobody will ever source.
    if (count($db) > 4000) {
        uasort($db, static fn($a, $b) => ($b['n'] <=> $a['n']) ?: strcmp($b['last'], $a['last']));
        $db = array_slice($db, 0, 3000, true);
    }
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, json_encode($db, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    fflush($fp);
    flock($fp, LOCK_UN);
    fclose($fp);
}

// ── content gate ────────────────────────────────────────────────────────────
// Two checks, because they fail differently. The QUERY is checked so we never
// send an adult search upstream at all; the TITLES are checked because a clean
// query can still surface something explicit — "toy" and "massage" both do it.
//
// Whole-word matching with an allowlist checked first. Substring matching would
// block "analysis" for containing a slur and "grape" for containing another,
// and without the allowlist a breast pump and a cocktail shaker are refused.
// See api/blocklist.php.
$BL = @include __DIR__ . '/blocklist.php';
$BLOCK = is_array($BL) && isset($BL['block']) ? $BL['block'] : [];
$ALLOW = is_array($BL) && isset($BL['allow']) ? $BL['allow'] : [];

function fh_is_blocked(string $text, array $block, array $allow): bool {
    $t = ' ' . preg_replace('/[^\p{L}\p{N}]+/u', ' ', mb_strtolower($text, 'UTF-8')) . ' ';
    // Allowlist first: a phrase that is a real product wins over any word
    // inside it. Removing it before matching means "breast pump" cannot be
    // caught by "breast".
    foreach ($allow as $ok) {
        $t = str_replace(' ' . $ok . ' ', ' ', $t);
        $t = str_replace($ok, ' ', $t);
    }
    foreach ($block as $bad) {
        if (mb_strpos($t, ' ' . $bad . ' ') !== false) { return true; }
    }
    return false;
}

if (fh_is_blocked($q, $BLOCK, $ALLOW)) {
    // Answer normally rather than erroring: the front end shows "nothing
    // found", which is the right experience and gives nothing away.
    echo json_encode(['ok' => true, 'query' => $q, 'results' => [],
                      'reason' => 'blocked'], JSON_UNESCAPED_UNICODE);
    exit;
}

// -- query translation -------------------------------------------------------
// AliExpress does not keyword-match Hebrew or Greek. Measured on the live
// endpoint: "coffee machine" typed in Hebrew returned a sleep mask, and the
// Greek for "coffee maker" returned an anime makeup bag. The API ignores the
// terms and returns something arbitrary. target_language only translates the
// TITLES that come back; it does nothing for the search itself.
//
// So the query is translated to English before it is sent, while
// target_language stays set to the reader's language so titles still come back
// in Hebrew or Greek. A plain lookup table, not a model: costs nothing, adds no
// latency, cannot invent a word, and covers what people actually type into a
// deals site. An unknown word passes through untouched and the relevance filter
// still protects the result.
$TERMS = [
    'מכונת קרח'=>'ice maker','קרח'=>'ice cube','מקפיא'=>'freezer','גריל'=>'grill',
    'מיחם'=>'urn','מסננת'=>'strainer','קרשים'=>'boards','סכין'=>'knife',
    'תנור'=>'oven','כיריים'=>'stove','שואב רובוטי'=>'robot vacuum',
    'מדיח'=>'dishwasher','מכונת כביסה'=>'washing machine','מייבש'=>'dryer',
    'טלוויזיה'=>'tv','מסך מחשב'=>'monitor','דיסק'=>'ssd','זיכרון'=>'memory card',
    'מכונת קפה'=>'coffee machine','מכונת אספרסו'=>'espresso machine',
    'אספרסו'=>'espresso','קפה'=>'coffee','מכונת'=>'machine','מכונה'=>'machine',
    'קומקום'=>'kettle','אלחוטי'=>'wireless','אלחוטיות'=>'wireless','חשמלי'=>'electric',
    'נייד'=>'portable','קטן'=>'small','גדול'=>'large','גיימינג'=>'gaming',
    'משרדי'=>'office','עור'=>'leather','טובה'=>'',
    'מיקסר'=>'mixer','בלנדר'=>'blender','סיר'=>'pot','מחבת'=>'pan','צלחות'=>'plates',
    'סכינים'=>'knives','טוסטר'=>'toaster','מיקרוגל'=>'microwave','מקרר'=>'fridge',
    'אוזניות גיימינג'=>'gaming headset','אוזניות'=>'earbuds','אוזניה'=>'earphone',
    'בלוטות'=>'bluetooth','רמקול'=>'speaker','מטען'=>'charger','כבל'=>'cable',
    'מקלדת'=>'keyboard','עכבר'=>'mouse','מסך'=>'monitor','מצלמה'=>'camera',
    'טלפון'=>'phone','שעון חכם'=>'smart watch','שעון יד'=>'wristwatch','שעון'=>'watch',
    'מחשב'=>'computer','נייד'=>'laptop','סוללה'=>'power bank','נורה'=>'bulb',
    'מנורה'=>'lamp','מקרן'=>'projector',
    'שואב אבק'=>'vacuum cleaner','שואב'=>'vacuum','מאוורר'=>'fan','מזגן'=>'air conditioner',
    'כיסא'=>'chair','כסא'=>'chair','שולחן'=>'desk','מזרן'=>'mattress','כרית'=>'pillow',
    'שמיכה'=>'blanket','וילון'=>'curtain','שטיח'=>'rug','מדף'=>'shelf','ארון'=>'cabinet',
    'נעלי ריצה'=>'running shoes','נעליים'=>'shoes','חולצה'=>'shirt','מכנסיים'=>'trousers',
    'מעיל'=>'jacket','תיק'=>'bag','ארנק'=>'wallet','משקפיים'=>'glasses',
    'מברשת שיניים'=>'toothbrush','מייבש שיער'=>'hair dryer','מכונת גילוח'=>'shaver',
    'צעצוע'=>'toy','כלב'=>'dog','חתול'=>'cat','אופניים'=>'bicycle','קורקינט'=>'scooter',
    'רכב'=>'car','כלים'=>'tools','מקדחה'=>'drill','משחק'=>'game','ילדים'=>'kids',
    'καφετιέρα'=>'coffee maker','ακουστικά'=>'headphones','πληκτρολόγιο'=>'keyboard',
    'φορτιστής'=>'charger','καρέκλα'=>'chair','παπούτσια'=>'shoes','ρολόι'=>'watch',
];
$qSearch = $q;
if (preg_match('/[\x{0590}-\x{05FF}\x{0370}-\x{03FF}]/u', $q)) {
    $t = ' ' . $q . ' ';
    // Longest key first, so a two-word term wins over its parts.
    $keys = array_keys($TERMS);
    usort($keys, static fn($a, $b) => mb_strlen($b, 'UTF-8') <=> mb_strlen($a, 'UTF-8'));
    foreach ($keys as $src) {
        $t = str_replace($src, ' ' . $TERMS[$src] . ' ', $t);
    }
    $t = trim(preg_replace('/\s+/u', ' ', $t));
    // Only swap it in if something was actually translated. An untouched
    // Hebrew string is no better sent than the original.
    if ($t !== '' && $t !== $q && preg_match('/[a-z]/i', $t)) {
        $qSearch = $t;
    }
}

// ── cache ───────────────────────────────────────────────────────────────────
// Two people searching "air fryer" seconds apart should cost one API call.
// sys_get_temp_dir() rather than a directory under the web root, so cache files
// are never fetchable — the same reasoning that keeps config.php out of reach.
$cacheDir = sys_get_temp_dir() . '/fh-search';
if (!is_dir($cacheDir)) { @mkdir($cacheDir, 0700, true); }
// Bump CACHE_VERSION whenever ranking, translation or the response shape
// changes. Without it a code fix is invisible for up to the TTL on every query
// anyone has already run — which made three separate fixes look like they had
// not worked, because the endpoint kept serving pre-fix answers.
const CACHE_VERSION = 16;
$cacheKey  = sha1(CACHE_VERSION . '|' . mb_strtolower($q, 'UTF-8') . '|' . $lang);
$cacheFile = $cacheDir . '/' . $cacheKey . '.json';
// 90 seconds. The cache exists to stop a burst costing a burst of API calls —
// a debounced keystroke run, a double-click, two people typing the same
// trending term. All of that happens inside a minute or two. Thirty minutes
// bought nothing extra and cost the thing the feature is for: a SEARCH is
// expected to be current, prices and stock move, and a shopper who retries
// after seeing a bad result got the same bad result served back for half an
// hour. It also hid three code fixes in a row during development.
$CACHE_TTL = 90;

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

// Which language the TITLES should come back in - see the note at
// target_language below. Computed here because it has to run before the
// request array is built.
$sentLang = 'EN';
if ($qSearch === $q) {
    if (preg_match('/[\x{0590}-\x{05FF}]/u', $qSearch))       { $sentLang = 'HE'; }
    elseif (preg_match('/[\x{0370}-\x{03FF}]/u', $qSearch))   { $sentLang = 'EL'; }
    elseif (!in_array(strtolower($lang), ['he', 'el'], true)) { $sentLang = $lang; }
}

// ── request ─────────────────────────────────────────────────────────────────
$params = [
    'app_key'         => $KEY,
    'method'          => 'aliexpress.affiliate.product.query',
    'timestamp'       => gmdate('Y-m-d H:i:s'),
    'sign_method'     => 'sha256',
    'v'               => '2.0',
    'keywords'        => $qSearch,
    'page_no'         => '1',
    'page_size'       => '12',
    'tracking_id'     => $TID,
    'target_currency' => 'USD',
    // Titles come back in the language we SEARCHED in, not the reader's.
    //
    // These have to agree or the relevance filter cannot work: with English
    // keywords and Hebrew titles, no English word appears in any title, every
    // row scores zero and the reader gets an empty page. Measured: lang=he
    // returned 0 of 12 rows the API had supplied, for both English and
    // translated queries.
    //
    // The trade-off is deliberate. A Hebrew reader whose query was translated
    // sees English product titles — but sees the RIGHT products. AliExpress's
    // Hebrew titles are machine-translated anyway, and a relevant product with
    // an English name beats an empty result or an eye mask.
    // Titles come back in the language of the WORDS WE ACTUALLY SENT, decided
    // by the SCRIPT of those words — not by the interface language.
    //
    // Keying it off the interface was wrong in both directions. Hebrew typed on
    // an English interface asked for English titles and then hunted for a
    // Hebrew word in them: "קרח" returned 9 results on the Hebrew site and 0 on
    // the English one, off the same 12 rows from the API. A visitor does not
    // change the site language before typing in their own.
    //
    //   we translated it   -> we sent English   -> EN
    //   Hebrew characters  -> we sent Hebrew    -> HE
    //   Greek characters   -> we sent Greek     -> EL
    //   Latin characters   -> EN, unless the interface is another Latin
    //                         language, in which case that one
    'target_language' => $sentLang,
    'ship_to_country' => 'IL',
    // NO 'sort' PARAMETER, deliberately. The nightly deal fetch uses
    // LAST_VOLUME_DESC because it is building a discovery feed and units sold
    // is a decent proxy for "actually good". That is the wrong ranking for a
    // SEARCH: it sorts by popularity across a loose keyword match, so someone
    // asking for "gaming chair" got a high-volume car seat pad, and a Hebrew
    // search for a water filter returned a sensory squeeze toy. Leaving sort
    // unset lets the API rank by relevance, which is what a person typing a
    // specific product wants.
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
$rawCount = is_array($products) ? count($products) : 0;
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
    // A clean query can still surface something explicit.
    if (fh_is_blocked($title, $BLOCK, $ALLOW)) { continue; }

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

// ── relevance ranking ───────────────────────────────────────────────────────
// The API matches loosely and, worse, ranks ACCESSORIES FOR a thing as if they
// were the thing. Measured on the live endpoint:
//   "coffee machine"  -> a pump cleaning tool and a drip tray replacement
//   "running shoes"   -> roller skates
//   "baby stroller"   -> a white noise machine
// A word filter cannot fix that, because "Nespresso Coffee Machine Drip Tray"
// contains both query words. So score and sort instead of filtering:
//
//   + every query word found in the title
//   + a large bonus when ALL of them are (roller skates lack "running")
//   - accessory markers, but only when the visitor did not ask for one.
//     Someone searching "phone case" should still get cases.
// Score against BOTH the original query and the translated one.
//
// These two fixes collided. The query is translated to English before it is
// sent, but target_language keeps the TITLES in the reader's language — so with
// lang=he the filter was matching English words against Hebrew titles, every
// row scored zero, and a Hebrew reader got an empty result for every search.
// Measured: lang=he returned 0 for both "coffee machine" and "מכונת קפה", while
// lang=en returned 9 for the same queries.
//
// Taking the union means a Hebrew title matches on "קפה" and an English title
// matches on "coffee", and a row has to match neither to be dropped.
$stop  = ['the','and','for','with','a','an','of','to','in','my','best','cheap'];
$words = [];
foreach ([$q, $qSearch] as $src) {
    foreach (preg_split('/[\s,]+/u', mb_strtolower($src, 'UTF-8'), -1, PREG_SPLIT_NO_EMPTY) as $w) {
        if (mb_strlen($w, 'UTF-8') >= 3 && !in_array($w, $stop, true)) {
            $words[] = $w;
        }
    }
}
$words = array_values(array_unique($words));
// The accessory guard checks "did the visitor ask for this?", so it has to see
// both forms too — someone typing the Hebrew for "phone case" should still get
// cases, not have them penalised.
$ql = mb_strtolower($q . ' ' . $qSearch, 'UTF-8');

$ACCESSORY = ['replacement','compatible','spare','accessor','keycap','decal',
              'sticker','protector','protective','repair','refill','cartridge',
              'drip tray','cleaning','adapter','bracket','mosquito',
              'mount for','parts for','cover for','case for','fit for',
              'suitable for','storage bag','carry bag','carrying case','mat bag',
              'dust cover','net for','sleeve for','strap for','stand for',
              'holder for','cushion for','organizer for','keycaps','phone case'];

if ($words) {
    $scored = [];
    foreach ($out as $row) {
        $t = mb_strtolower($row['title'], 'UTF-8');
        $found = 0;
        foreach ($words as $w) { if (mb_strpos($t, $w) !== false) { $found++; } }
        if ($found === 0) { continue; }          // nothing in common at all
        $score = $found * 10;
        // A title cannot contain both the Hebrew and the English form, so
        // requiring every word would make the bonus unreachable whenever a
        // translation happened. Half the union counts as a full match.
        $need = ($qSearch !== $q) ? max(1, (int)ceil(count($words) / 2)) : count($words);
        if ($found >= $need) { $score += 20; }
        foreach ($ACCESSORY as $a) {
            if (mb_strpos($t, $a) !== false && mb_strpos($ql, $a) === false) { $score -= 32; }
        }
        // "X for Y" is the accessory shape even when no keyword above appears.
        // The real accessory tell is not the word "for" - it is "for <Brand>":
        // "for Garmin", "for Samsung S25", "for CHANA Changan". Keying on bare
        // "for" was both too broad (it fires on "Warm Bed for Large Dogs", a
        // genuine product) and too narrow, because it was disabled whenever the
        // QUERY contained "for" - so a search for "phone holder for bike"
        // switched the protection off and returned phone cases. A capital after
        // "for" is checked on the ORIGINAL-CASE title and needs no query guard.
        if (preg_match('/\bfor\s+[A-Z0-9]/u', $row['title'])) { $score -= 25; }
        $row['_score'] = $score;
        $scored[] = $row;
    }
    // Always use the scored list, even when it is short or empty.
    //
    // This previously kept the UNFILTERED results whenever fewer than three
    // survived — "a short list of loosely-related products beats an empty one".
    // That reasoning was wrong, and it defeated the filter at exactly the moment
    // the results were worst. Measured on the live endpoint: a Hebrew search for
    // "מכונת קפה" (coffee machine) returned a sleep mask, and the Greek
    // "καφετιέρα" returned an anime makeup bag — AliExpress keyword-matches
    // Hebrew and Greek poorly, every row scored zero, and the fallback then
    // published the junk it had just rejected.
    //
    // Nothing found is a true answer; a shirt for "coffee machine" is not. The
    // front end already handles an empty result properly — it shows the
    // catalogue message and the WhatsApp link.
    usort($scored, static function ($a, $b) { return $b['_score'] <=> $a['_score']; });

    // CROSS-LANGUAGE ESCAPE HATCH, and it is narrow on purpose.
    //
    // The filter compares the words of the query against the words of the
    // title. That only works when both are in the same language. Across
    // languages it cannot tell a coffee machine from a shirt, so it rejects
    // everything and the reader gets an empty page — measured: Spanish
    // "cafetera" returned 12 rows from the API and kept 0, because the titles
    // came back in English.
    //
    // So: when the interface is NOT English and strict filtering removed
    // everything, defer to the API's own ranking rather than showing nothing.
    // We cannot verify relevance across a language boundary, and the source's
    // best guess beats a blank result.
    //
    // English keeps the strict behaviour with no fallback, because there the
    // filter CAN judge — and that is the path where "coffee machine" was
    // returning a shirt.
    if (!$scored && $rawCount > 0 && strtolower($lang) !== 'en') {
        $out = array_slice($out, 0, 9);
    } else {
        $out = $scored;
    }
}
// Internal ranking signal — not something a browser needs to see.
foreach ($out as $i => $row) { unset($out[$i]['_score']); }
$out = array_values($out);

// Logged with the count the VISITOR saw, not the count the API returned — a
// term that came back with 12 rows and showed 0 after filtering is exactly the
// kind of gap worth sourcing, and recording 12 would hide it.
fh_log_search($q, count($out), strtolower($lang));

$payload = json_encode([
    'ok'      => true,
    'query'   => $q,
    'searched_as' => ($qSearch !== $q ? $qSearch : null),
    'raw_count' => $rawCount,   // rows the API gave us, before our ranking
    'source'  => 'aliexpress',
    'live'    => true,
    'results' => $out,
], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

@file_put_contents($cacheFile, $payload, LOCK_EX);
header('X-Cache: MISS');
echo $payload;
