/* MU61 Quiz — offline cache; bump CACHE_VERSION to refresh clients after changes */
const CACHE_VERSION = 'mu61-quiz-v2';
const CACHE_NAME = 'mu61-cache-' + CACHE_VERSION;

self.addEventListener('install', function (event) {
  event.waitUntil(
    (async function () {
      var scope = self.registration.scope;
      var urls = [
        new URL('index.html', scope).href,
        new URL('manifest.webmanifest', scope).href,
        new URL('favicon.svg', scope).href
      ];
      var cache = await caches.open(CACHE_NAME);
      await Promise.all(
        urls.map(function (u) {
          return cache.add(u).catch(function () {});
        })
      );
      await self.skipWaiting();
    })()
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    (async function () {
      var keys = await caches.keys();
      await Promise.all(
        keys.map(function (k) {
          return k !== CACHE_NAME ? caches.delete(k) : Promise.resolve();
        })
      );
      await self.clients.claim();
    })()
  );
});

function shouldStore(res) {
  return res && (res.ok || res.type === 'opaque');
}

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    (async function () {
      var cache = await caches.open(CACHE_NAME);
      var cached = await cache.match(event.request);
      if (cached) return cached;
      try {
        var res = await fetch(event.request);
        if (shouldStore(res)) {
          try {
            await cache.put(event.request, res.clone());
          } catch (_) {}
        }
        return res;
      } catch (err) {
        if (event.request.mode === 'navigate') {
          var fb = await cache.match(new URL('index.html', self.registration.scope));
          if (fb) return fb;
        }
        throw err;
      }
    })()
  );
});
