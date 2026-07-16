// Minimal service worker — just enough for "Add to Home Screen" installability.
// Deliberately does NOT cache task data: this is a live dashboard, and stale
// offline data (or a sync conflict) would be worse than requiring a connection.

self.addEventListener('install', function (event) {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function (event) {
    event.respondWith(fetch(event.request));
});
