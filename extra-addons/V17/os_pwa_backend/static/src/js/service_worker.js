
'use strict';
importScripts('/os_pwa_backend/static/src/js/workbox-sw.js');
const CACHE_NAME = '__OS__CACHE__NAME__';
var urlsToCache = [
    '/',
    '/pwa/offline',
    '/os_pwa_backend/static/src/img/offline_app.png',
];


self.addEventListener("message", (event) => {
    if (event.data && event.data.type === "SKIP_WAITING") {
        self.skipWaiting();
    }
});


// Service worker installation event, prefetch some data
// during installation of service worker
self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function (cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

if (workbox.navigationPreload.isSupported()) {
    workbox.navigationPreload.enable();
}

self.addEventListener('activate', function (evt) {
    evt.waitUntil(
        caches.keys().then(function (keyList) {
            return Promise.all(keyList.map(function (key) {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function (event) {
    event.respondWith(
        fetch(event.request) // Request from network
            .then(function (response) {
                // Check if we received a valid response
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                var requestMethod = event.request.method
                if (!requestMethod || requestMethod != 'POST') {
                    var responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                        .then(function (cache) {
                            cache.put(event.request, responseToCache);
                        });
                }
                return response;
            })
            .catch(function (err) {
                return caches.open(CACHE_NAME) // Search request from cache
                    .then(function (cache) {
                        return cache.match(event.request)
                            .then(function (response) {
                                if (response) {
                                    return response
                                }
                                return cache.match('/pwa/offline') || Promise.resolve()
                            })
                    });
            })
    );
});