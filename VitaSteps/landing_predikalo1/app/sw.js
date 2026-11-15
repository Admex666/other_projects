const CACHE_NAME = 'kitero-pwa-v4';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './tour_m1.json',
  './manifest.json',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './assets/pois/hero_m1.jpg',
  './assets/pois/poi_1.jpg',
  './assets/pois/poi_2.jpg',
  './assets/pois/poi_3.jpg',
  './assets/pois/poi_4.jpg',
  './assets/pois/poi_5.jpg',
  './assets/pois/poi_6.jpg',
  './assets/pois/poi_7.jpg',
  './assets/pois/poi_8.jpg',
  './assets/pois/poi_9.jpg',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      for (const url of ASSETS_TO_CACHE) {
        try {
          await cache.add(url);
        } catch (err) {
          console.warn(`[SW] Pre-caching failed for ${url}:`, err);
        }
      }
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // 1. Audio és Range kérések kezelése (HTTP 206 Partial Content szintézis)
  const isAudio = url.pathname.includes('/audio/') || 
                  /\.(mp3|wav|ogg|m4a)$/i.test(url.pathname) || 
                  request.headers.has('range');
  if (isAudio) {
    event.respondWith(handleAudioRequest(request));
    return;
  }

  // 2. App Shell: Network-First (Offline Fallbackkel)
  // tour_m1.json, index.html, app.js, style.css vagy navigáció
  const isAppShell = request.mode === 'navigate' ||
                     url.pathname.endsWith('/index.html') ||
                     url.pathname.endsWith('/app.js') ||
                     url.pathname.endsWith('/style.css') ||
                     url.pathname.endsWith('/tour_m1.json') ||
                     url.pathname.endsWith('/manifest.json') ||
                     url.pathname.endsWith('/app/') ||
                     url.pathname.endsWith('/app');
  if (isAppShell) {
    event.respondWith(handleAppShell(request));
    return;
  }

  // 3. Statikus képek, Leaflet CDN és Esri térképcsempék (CORS engedélyezve, Cache-First)
  event.respondWith(handleCacheFirst(request));
});

/**
 * App Shell Network-First kezelő:
 * Először a friss hálózati változatot próbálja megszerezni; siker esetén frissíti a cache-t.
 * Ha hálózati hiba lép fel (offline), a cache-ből szolgálja ki.
 */
async function handleAppShell(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.status === 200) {
      const responseToCache = networkResponse.clone();
      caches.open(CACHE_NAME).then((cache) => {
        cache.put(request, responseToCache);
      }).catch((err) => console.warn('[SW] App Shell cache update failed:', err));
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    if (request.mode === 'navigate') {
      const fallback = await caches.match('./index.html');
      if (fallback) return fallback;
    }
    throw error;
  }
}

/**
 * Audio kérések kezelője:
 * A Range kérések nem akadhatnak el 206 Partial Content hibán.
 * A teljes fájl a cache-ben 200-ként tárolódik, és a range kéréseknél
 * az ArrayBuffer-ből szeletelünk érvényes 206 választ.
 */
async function handleAudioRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request.url);

  if (cachedResponse) {
    if (request.headers.has('range')) {
      return createPartialResponse(request, cachedResponse);
    }
    return cachedResponse;
  }

  try {
    // Tiszta GET kérés a teljes hanganyagra a cache-elhetőség érdekében
    const networkResponse = await fetch(request.url);
    if (networkResponse && networkResponse.status === 200) {
      const cloneToCache = networkResponse.clone();
      cache.put(request.url, cloneToCache).catch((err) => {
        console.warn('[SW] Audio caching failed:', err);
      });
      if (request.headers.has('range')) {
        return createPartialResponse(request, networkResponse);
      }
      return networkResponse;
    }
    return fetch(request);
  } catch (err) {
    if (cachedResponse) {
      if (request.headers.has('range')) {
        return createPartialResponse(request, cachedResponse);
      }
      return cachedResponse;
    }
    throw err;
  }
}

/**
 * HTTP 206 Partial Content válasz generálása ArrayBuffer szeleteléssel
 */
async function createPartialResponse(request, response) {
  const rangeHeader = request.headers.get('range');
  if (!rangeHeader) {
    return response;
  }
  const arrayBuffer = await response.arrayBuffer();
  const total = arrayBuffer.byteLength;
  const matches = /^bytes=(\d+)-(\d+)?$/g.exec(rangeHeader);
  if (!matches) {
    return new Response(arrayBuffer, {
      status: 200,
      headers: response.headers
    });
  }
  const start = parseInt(matches[1], 10);
  const end = matches[2] ? parseInt(matches[2], 10) : total - 1;

  if (start >= total || end >= total || start > end) {
    return new Response(null, {
      status: 416,
      statusText: 'Range Not Satisfiable',
      headers: {
        'Content-Range': `bytes */${total}`
      }
    });
  }

  const chunk = arrayBuffer.slice(start, end + 1);
  const headers = new Headers(response.headers);
  headers.set('Content-Type', response.headers.get('Content-Type') || 'audio/mpeg');
  headers.set('Content-Range', `bytes ${start}-${end}/${total}`);
  headers.set('Content-Length', chunk.byteLength.toString());
  headers.set('Accept-Ranges', 'bytes');

  return new Response(chunk, {
    status: 206,
    statusText: 'Partial Content',
    headers
  });
}

/**
 * Cache-First kezelő statikus eszközökhöz, térképcsempékhez és CDN-ekhez:
 * Engedélyezi a basic, cors és opaque válaszok tárolását.
 */
async function handleCacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  try {
    const networkResponse = await fetch(request);
    const isValidType = networkResponse.type === 'basic' || 
                        networkResponse.type === 'cors' || 
                        networkResponse.type === 'opaque';
    const isValidStatus = networkResponse.status === 200 || networkResponse.status === 0;

    if (networkResponse && isValidStatus && isValidType) {
      const responseToCache = networkResponse.clone();
      caches.open(CACHE_NAME).then((cache) => {
        cache.put(request, responseToCache);
      }).catch((err) => {
        console.warn('[SW] Cache put failed:', err);
      });
    }
    return networkResponse;
  } catch (error) {
    return cachedResponse || new Response('Offline resource unavailable', { 
      status: 503, 
      statusText: 'Service Unavailable' 
    });
  }
}
