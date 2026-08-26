<?php
/**
 * The numbers api/track.php collected.
 *
 *   https://fashionhotspot.site/api/stats.php?token=YOUR_TOKEN
 *   ...&format=json     the raw counters
 *
 * The question this page exists to answer is **which categories actually earn**.
 * Pageviews tell you people arrived; the outbound-click table tells you they
 * went to a merchant, and that is the closest thing to revenue this site can
 * see without the merchant reporting back.
 *
 * ANONYMOUS BY CONSTRUCTION. Everything here is a total. There are no rows, no
 * timestamps finer than a calendar day, no IP, no user agent and no session, so
 * there is nothing to correlate and no individual to find. See track.php.
 *
 * ACCESS. Same ADMIN_TOKEN as searches.php. If it is unset this page refuses
 * outright rather than defaulting to open.
 */

declare(strict_types=1);

$cfgFile = __DIR__ . '/config.php';
$cfg = is_file($cfgFile) ? (require $cfgFile) : [];
$token = (string)($cfg['ADMIN_TOKEN'] ?? '');

if ($token === '') {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Not configured.\n\nAdd to api/config.php:\n    'ADMIN_TOKEN' => 'pick-a-long-random-string',\n\nthen reload with ?token=that-string";
    exit;
}
// hash_equals, not ===, so a wrong token cannot be found one character at a
// time by timing the response.
if (!hash_equals($token, (string)($_GET['token'] ?? ''))) {
    http_response_code(403);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Forbidden';
    exit;
}

$file = __DIR__ . '/stats.json';
$db = is_file($file) ? json_decode((string)file_get_contents($file), true) : [];
if (!is_array($db)) { $db = []; }
foreach (['days', 'pages', 'langs', 'sources', 'clicks', 'cats'] as $k) {
    if (!isset($db[$k]) || !is_array($db[$k])) { $db[$k] = []; }
}

if (($_GET['format'] ?? '') === 'json') {
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($db, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    exit;
}

$days = $db['days'];
ksort($days);
$totalPv = 0; $totalCl = 0;
foreach ($days as $d) { $totalPv += (int)($d['pv'] ?? 0); $totalCl += (int)($d['cl'] ?? 0); }

// The share of visitors who went on to a merchant. Shown as "—" rather than 0%
// when there is nothing to divide by, because "no data" and "nobody clicked"
// are different findings and a 0% would read as the second.
$ctr = $totalPv > 0 ? round($totalCl / $totalPv * 100, 1) . '%' : '—';

$last = array_slice($days, -30, null, true);
$peak = 1;
foreach ($last as $d) { $peak = max($peak, (int)($d['pv'] ?? 0)); }

$top = static function (array $a, int $n = 12): array {
    arsort($a);
    return array_slice($a, 0, $n, true);
};
$esc = static fn($v) => htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8');
$sumOf = static fn(array $a): int => array_sum(array_map('intval', $a));

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
?><!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Stats — fashionhotspot</title>
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
h2{font-weight:800;letter-spacing:-.03em;font-size:19px;margin:30px 0 12px}
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
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;background:var(--card);
  border:1px solid var(--line);border-radius:16px;overflow:hidden}
th{text-align:left;font-family:'JetBrains Mono','Segoe UI',Arial,monospace;font-size:10px;
  letter-spacing:.1em;text-transform:uppercase;color:var(--ink3);padding:11px 13px;
  border-bottom:1px solid var(--line)}
td{padding:10px 13px;border-bottom:1px solid var(--line)}
tr:last-child td{border-bottom:0}
td.n,th.n{text-align:right;font-family:'JetBrains Mono','Segoe UI',Arial,monospace;font-variant-numeric:tabular-nums}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}
.empty{padding:40px;text-align:center;color:var(--ink3);background:var(--card);
  border:1px solid var(--line);border-radius:16px}
.dim{color:var(--ink3);font-size:12px}
/* One series, so no legend — the heading names it. Thin marks, 4px rounded
   ends anchored to the baseline, 2px gap between adjacent bars. */
.chart{display:flex;align-items:flex-end;gap:2px;height:132px;background:var(--card);
  border:1px solid var(--line);border-radius:16px;padding:14px}
.chart div{flex:1;min-width:4px;background:var(--accent);border-radius:4px 4px 0 0;min-height:2px}
</style></head><body><div class="wrap">
<h1>Stats</h1>
<div class="sub"><?= number_format($totalPv) ?> views · <?= number_format($totalCl) ?> outbound clicks · <?= $esc($ctr) ?> click-through</div>

<div class="tiles">
  <div class="tile"><div class="tl">Pageviews</div><div class="tv"><?= number_format($totalPv) ?></div></div>
  <div class="tile"><div class="tl">Outbound clicks</div><div class="tv"><?= number_format($totalCl) ?></div></div>
  <div class="tile"><div class="tl">Click-through</div><div class="tv"><?= $esc($ctr) ?></div></div>
  <div class="tile"><div class="tl">Days recorded</div><div class="tv"><?= count($days) ?></div></div>
</div>

<div class="bar"><a href="?token=<?= $esc($_GET['token'] ?? '') ?>&amp;format=json">JSON</a>
  <a href="searches.php?token=<?= $esc($_GET['token'] ?? '') ?>">Searches →</a></div>

<?php if (!$days): ?>
  <div class="empty">Nothing recorded yet. Every page view and every outbound click lands here.</div>
<?php else: ?>

<h2>Pageviews, last 30 days</h2>
<div class="chart">
<?php foreach ($last as $d => $row): $v = (int)($row['pv'] ?? 0); ?>
  <div style="height:<?= max(2, (int)round($v / $peak * 100)) ?>%" title="<?= $esc($d) ?>: <?= $v ?> views"></div>
<?php endforeach; ?>
</div>
<p class="dim" style="margin-top:8px">Peak day <?= number_format($peak) ?> ·
  <?= $esc((string)array_key_first($last)) ?> → <?= $esc((string)array_key_last($last)) ?>. Hover a bar for its date.</p>

<div class="grid2" style="margin-top:26px">
  <div>
    <h2>Where clicks went</h2>
    <?php if (!$db['clicks']): ?><div class="empty">No outbound clicks yet.</div><?php else: ?>
    <div class="scroll"><table><thead><tr><th>Merchant</th><th class="n">Clicks</th></tr></thead><tbody>
    <?php foreach ($top($db['clicks']) as $k => $v): ?>
      <tr><td><?= $esc($k) ?></td><td class="n"><?= number_format((int)$v) ?></td></tr>
    <?php endforeach; ?>
    </tbody></table></div><?php endif; ?>
  </div>
  <div>
    <h2>Which categories earn</h2>
    <?php if (!$db['cats']): ?><div class="empty">No outbound clicks yet.</div><?php else: ?>
    <div class="scroll"><table><thead><tr><th>Category</th><th class="n">Clicks</th></tr></thead><tbody>
    <?php foreach ($top($db['cats']) as $k => $v): ?>
      <tr><td><?= $esc($k) ?></td><td class="n"><?= number_format((int)$v) ?></td></tr>
    <?php endforeach; ?>
    </tbody></table></div><?php endif; ?>
  </div>
  <div>
    <h2>Top pages</h2>
    <div class="scroll"><table><thead><tr><th>Path</th><th class="n">Views</th></tr></thead><tbody>
    <?php foreach ($top($db['pages']) as $k => $v): ?>
      <tr><td><?= $esc($k) ?></td><td class="n"><?= number_format((int)$v) ?></td></tr>
    <?php endforeach; ?>
    </tbody></table></div>
  </div>
  <div>
    <h2>Where visitors came from</h2>
    <div class="scroll"><table><thead><tr><th>Channel</th><th class="n">Views</th><th class="n">Share</th></tr></thead><tbody>
    <?php $srcTotal = max(1, $sumOf($db['sources'])); foreach ($top($db['sources']) as $k => $v): ?>
      <tr><td><?= $esc($k === 'wa' ? 'wa — WhatsApp group' : $k) ?></td>
          <td class="n"><?= number_format((int)$v) ?></td>
          <td class="n"><?= round((int)$v / $srcTotal * 100) ?>%</td></tr>
    <?php endforeach; ?>
    </tbody></table></div>
  </div>
  <div>
    <h2>Language</h2>
    <div class="scroll"><table><thead><tr><th>Lang</th><th class="n">Views</th><th class="n">Share</th></tr></thead><tbody>
    <?php $lTotal = max(1, $sumOf($db['langs'])); foreach ($top($db['langs']) as $k => $v): ?>
      <tr><td><?= $esc($k) ?></td><td class="n"><?= number_format((int)$v) ?></td>
          <td class="n"><?= round((int)$v / $lTotal * 100) ?>%</td></tr>
    <?php endforeach; ?>
    </tbody></table></div>
  </div>
</div>
<?php endif; ?>

<p class="dim" style="margin-top:26px">
  No IP, user agent, referrer, cookie or session is recorded — only these totals, so there is no
  event log to correlate and no individual to find. <code>_other</code> in any table means the
  per-bucket key cap was reached and further distinct values were folded together; the totals
  above stay exact.
</p>
</div></body></html>
