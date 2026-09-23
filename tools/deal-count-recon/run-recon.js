// node run-recon.js <tag> <archive.json> <queue.json>   -> recon/out/<tag>/S*.json  + stage counts
const fs = require('fs'), path = require('path'), cp = require('child_process');
const [tag, arch, queue] = process.argv.slice(2);
const R = __dirname, code = path.join(R, 'code'), out = path.join(R, 'out', tag);
fs.mkdirSync(out, { recursive: true });
fs.copyFileSync(arch, path.join(code, 'workspace/skills/archive.json'));
fs.copyFileSync(queue, path.join(code, 'workspace/skills/queue.json'));
fs.mkdirSync(path.join(code, 'docs'), { recursive: true });
const env = { ...process.env, RECON_OUT: out, SITE_CONFIG: path.join(R, 'vps', 'site-config.json') };
const r = cp.spawnSync('node', ['build-static.js', '--no-publish'], { cwd: code, env, encoding: 'utf8', maxBuffer: 1 << 28 });
const lines = (r.stdout || '').split('\n').filter(l => /Deduped|dropped|quality gate|feed filter|amazon-switch|Building static|price ceiling|site-config|Amazon:|AliExpress:|Israel:|no-publish|Error/.test(l));
console.log(lines.join('\n'));
if (r.status) console.log('EXIT', r.status, (r.stderr || '').slice(-600));
const stages = fs.readdirSync(out).filter(f => /^S\d/.test(f)).sort();
for (const f of stages) console.log(f.padEnd(28), JSON.parse(fs.readFileSync(path.join(out, f))).length);
const dj = JSON.parse(fs.readFileSync(path.join(code, 'docs/deals.json'), 'utf8'));
fs.copyFileSync(path.join(code, 'docs/deals.json'), path.join(out, 'deals.json'));
console.log('docs/deals.json rows', dj.length, 'pricy', dj.filter(d => d.pricy).length);
