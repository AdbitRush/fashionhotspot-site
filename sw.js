// Service worker — offline fallback for assets, never a stale page.
//
// The previous version cached EVERY GET response, including HTML, under a
// cache name ('fhs-static-v1') that was never changed. It was network-first,
// so an online visitor normally got fresh content — but the moment a request
// was slow or flaky the fallback served an old page, and on iOS a site added
// to the Home Screen holds that cache hard. That is why deployed changes
// appeared to not exist.
//
// Two changes:
//
//   1. HTML is never cached. A page is either fetched fresh or, offline, shows
//      the browser's own error. A shopping site showing yesterday's prices from
//      cache is worse than showing nothing.
//   2. The cache name carries a version, and activate deletes every cache that
//      is not the current one. Bump VERSION on any release that must reach
//      people who already have the site open.
//
// Images, CSS and JS are still cached, because those are content-addressed
// enough that a stale copy is harmless and the offline win is real.

const VERSION = '2026-08-14a';
const CACHE = `fhs-static-${VERSION}`;

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    // Drop every cache from a previous version so old pages cannot resurface.
    const names = await caches.keys();
    await Promise.all(names.filter(n => n !== CACHE).map(n => caches.delete(n)));
    await clients.claim();
  })());
});

function isPage(request) {
  return request.mode === 'navigate'
      || (request.headers.get('accept') || '').includes('text/html');
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== location.origin) return;

  // Pages: always the network. No cache write, no cache fallback.
  if (isPage(req)) {
    e.respondWith(fetch(req));
    return;
  }

  // Assets: network first, fall back to cache when offline.
  e.respondWith(
    fetch(req).then((r) => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      return r;
    }).catch(() => caches.match(req))
  );
});
