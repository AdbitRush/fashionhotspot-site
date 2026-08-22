<?php
/**
 * What people searched for — the shopping list your visitors wrote for you.
 *
 * Every live search is recorded by api/search.php: the term, how many times it
 * has been asked, how many results the visitor actually SAW, and when it was
 * last typed. The rows with a high count and a low `found` are the ones worth
 * sourcing — people are asking and the catalogue has nothing.
 *
 *   https://fashionhotspot.site/api/searches.php?token=YOUR_TOKEN
 *   ...&format=json     the raw data
 *   ...&only=missing    just the terms that returned nothing
 *
 * ANONYMOUS BY DESIGN. There is no IP, user agent, session or per-visit
 * timestamp in this data — only the term and its counts. It cannot be tied back
 * to a person, which is the right default for a record of what people type.
 *
 * ACCESS. Requires `ADMIN_TOKEN` in api/config.php. If it is unset this page
 * refuses outright rather than defaulting to open: the failure mode of a
 * missing token must be "nobody gets in", not "everybody does".
 */

declare(strict_types=1);

$cfgFile = __DIR__ . '/config.php';
$cfg = is_file($cfgFile) ? (require $cfgFile) : [];
$token = (string)($cfg['ADMIN_TOKEN'] ?? '');

if ($token === '') {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Not configured.\n\n"
       . "Add to api/config.php:\n"
       . "    'ADMIN_TOKEN' => 'pick-a-long-random-string',\n\n"
       . "then reload with ?token=that-string";
    exit;
}
// hash_equals, not ===, so a wrong token cannot be discovered one character at
// a time by timing the response.
if (!hash_equals($token, (string)($_GET['token'] ?? ''))) {
    http_response_code(403);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Forbidden';
    exit;
}

$file = __DIR__ . '/searches.json';
$db = is_file($file) ? json_decode((string)file_get_contents($file), true) : [];
if (!is_array($db)) { $db = []; }

$rows = array_values($db);
if (($_GET['only'] ?? '') === 'missing') {
    $rows = array_values(array_filter($rows, static fn($r) => (int)($r['found'] ?? 0) === 0));
}
// Most-asked first; ties broken by how recently it was asked.
usort($rows, static fn($a, $b) =>
    ((int)$b['n'] <=> (int)$a['n']) ?: strcmp((string)$b['last'], (string)$a['last']));

if (($_GET['format'] ?? '') === 'json') {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($rows, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    exit;
}

$total = count($db);
$missing = count(array_filter($db, static fn($r) => (int)($r['found'] ?? 0) === 0));
$asks = array_sum(array_map(static fn($r) => (int)($r['n'] ?? 0), $db));
$esc = static fn($v) => htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8');

header('Content-Type: text/html; charset=utf-8');
?><!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Searches — fashionhotspot</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{--bg:oklch(.945 .019 80);--card:oklch(.978 .014 82);--ink:oklch(.21 .014 55);
  --ink2:oklch(.44 .014 65);--ink3:oklch(.52 .014 68);--line:rgba(0,0,0,.08);
  --accent:oklch(.55 .2 25)}
@media(prefers-color-scheme:dark){:root{--bg:#141013;--card:#1E181C;--ink:#F7F1EC;
  --ink2:#CBBFB8;--ink3:#9C8E88;--line:rgba(255,255,255,.09)}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Archivo,system-ui,sans-serif;background:var(--bg);color:var(--ink);padding:34px 22px 70px}
.wrap{max-width:940px;margin:0 auto}
h1{font-weight:900;letter-spacing:-.045em;font-size:clamp(28px,5vw,44px);line-height:.95}
.sub{color:var(--ink3);font-family:'JetBrains Mono','Segoe UI',Arial,monospace;font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;margin-top:10px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 18px}
.tl{font-family:'JetBrains Mono','Segoe UI',Arial,monospace;font-size:10px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink3)}
.tv{font-size:27px;font-weight:900;letter-spacing:-.035em;margin-top:6px;font-variant-numeric:tabular-nums}
.bar{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.bar a{font-size:13px;font-weight:700;text-decoration:none;color:var(--ink2);
  border:1px solid var(--line);border-radius:999px;padding:7px 15px}
.bar a.on{background:var(--accent);color:#fff;border-color:var(--accent)}
table{width:100%;border-collapse:collapse;font-size:14px;background:var(--card);
  border:1px solid var(--line);border-radius:16px;overflow:hidden}
th{text-align:left;font-family:'JetBrains Mono','Segoe UI',Arial,monospace;font-size:10px;
  letter-spacing:.1em;text-transform:uppercase;color:var(--ink3);padding:11px 13px;
  border-bottom:1px solid var(--line)}
td{padding:10px 13px;border-bottom:1px solid var(--line)}
tr:last-child td{border-bottom:0}
td.n{text-align:right;font-family:'JetBrains Mono','Segoe UI',Arial,monospace;font-variant-numeric:tabular-nums}
.miss{color:var(--accent);font-weight:800}
.dim{color:var(--ink3);font-size:12px}
.empty{padding:40px;text-align:center;color:var(--ink3)}
</style></head><body><div class="wrap">
<h1>What people searched for</h1>
<div class="sub"><?= $total ?> distinct terms · <?= $asks ?> searches · <?= $missing ?> found nothing</div>

<div class="tiles">
  <div class="tile"><div class="tl">Distinct terms</div><div class="tv"><?= $total ?></div></div>
  <div class="tile"><div class="tl">Total searches</div><div class="tv"><?= $asks ?></div></div>
  <div class="tile"><div class="tl">Found nothing</div><div class="tv miss"><?= $missing ?></div></div>
</div>

<div class="bar">
  <a class="<?= ($_GET['only'] ?? '') === 'missing' ? '' : 'on' ?>"
     href="?token=<?= $esc($_GET['token'] ?? '') ?>">All</a>
  <a class="<?= ($_GET['only'] ?? '') === 'missing' ? 'on' : '' ?>"
     href="?token=<?= $esc($_GET['token'] ?? '') ?>&amp;only=missing">Found nothing</a>
  <a href="?token=<?= $esc($_GET['token'] ?? '') ?>&amp;format=json">JSON</a>
</div>

<?php if (!$rows): ?>
  <div class="empty">Nothing recorded yet. Every live search from the site lands here.</div>
<?php else: ?>
<table><thead><tr>
  <th>Term</th><th class="n">Times asked</th><th class="n">Results</th>
  <th>Languages</th><th>First</th><th>Last</th>
</tr></thead><tbody>
<?php foreach (array_slice($rows, 0, 400) as $r): ?>
  <tr>
    <td><?= $esc($r['q'] ?? '') ?></td>
    <td class="n"><?= (int)($r['n'] ?? 0) ?></td>
    <td class="n <?= (int)($r['found'] ?? 0) === 0 ? 'miss' : '' ?>"><?= (int)($r['found'] ?? 0) ?></td>
    <td class="dim"><?= $esc(implode(', ', $r['langs'] ?? [])) ?></td>
    <td class="dim"><?= $esc($r['first'] ?? '') ?></td>
    <td class="dim"><?= $esc($r['last'] ?? '') ?></td>
  </tr>
<?php endforeach; ?>
</tbody></table>
<?php endif; ?>

<p class="dim" style="margin-top:22px">
  Rows with a high count and <span class="miss">0</span> results are the ones worth sourcing —
  people are asking and there is nothing to show them. No IP, session or per-visit timestamp is
  recorded here; only the term and its counts.
</p>
</div></body></html>
