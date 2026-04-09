// Service Worker for MU61 Quiz - Full Offline Caching
const CACHE_NAME = 'mu61-quiz-v2';

// Install event - cache core assets and all HTML pages
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching core assets');
        return cache.addAll([
          '/',
          '/index.html',
          '/manifest.json',
          '/gyn/index.html',
          '/Cardio/index.html'
        ]);
      })
      .catch((error) => {
        console.error('Failed to cache core assets:', error);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - cache-first strategy with network fallback
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') {
    return;
  }

  const requestUrl = new URL(event.request.url);
  
  // Skip cross-origin requests
  if (requestUrl.origin !== location.origin) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(event.request)
          .then((networkResponse) => {
            if (!networkResponse || networkResponse.status !== 200) {
              return networkResponse;
            }

            const responseToCache = networkResponse.clone();

            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          })
          .catch((error) => {
            console.error('Fetch failed:', error);
            if (event.request.mode === 'navigate' || 
                (event.request.headers.get('accept') && 
                 event.request.headers.get('accept').includes('text/html'))) {
              return caches.match('/index.html');
            }
          });
      })
  );
});
