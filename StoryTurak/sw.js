const CACHE_NAME = 'storyturak-v8';
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './styles/vars.css',
    './styles/main.css',
    './js/app.js',
    './js/router.js',
    './js/gps-manager.js',
    './js/story-engine.js',
    './js/audio-manager.js',
    './js/session-manager.js',
    './js/views/onboarding.js',
    './js/views/browser.js',
    './js/views/lobby.js',
    './js/views/game.js',
    './data/intro-01.json',
    './manifest.json'
    // Assets would be listed here too (images, audio)
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(ASSETS_TO_CACHE);
            })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cache hit or fetch network
                return response || fetch(event.request);
            })
    );
});

self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
