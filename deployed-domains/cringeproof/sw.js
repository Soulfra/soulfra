/**
 * CringeProof Service Worker
 *
 * Offline-first architecture:
 * - Caches static assets
 * - Queues API calls when Flask backend is offline
 * - Background Sync for voice uploads
 * - Auto-retry when connection restored
 */

const CACHE_VERSION = 'cringeproof-v1';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `dynamic-${CACHE_VERSION}`;

// Files to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/record-simple.html',
  '/wordmap.html',
  '/css/soulfra.css',
  '/config.js',
  '/llm-emoji-map.js',
  '/queue-manager.js',
  '/connection-monitor.js'
];

// Install - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS.filter(url => url !== '/'));
      })
      .then(() => self.skipWaiting())
  );
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch - network first with fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip Chrome extension requests
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // API requests: Network-first with queue on failure
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response for cache
          const responseClone = response.clone();

          if (response.ok) {
            caches.open(DYNAMIC_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }

          return response;
        })
        .catch(async (error) => {
          console.log('[SW] API call failed, checking cache:', url.pathname);

          // Try to return cached response
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            console.log('[SW] Serving cached response');
            return cachedResponse;
          }

          // If this is a POST/PUT (voice upload), queue it for background sync
          if (request.method === 'POST' || request.method === 'PUT') {
            console.log('[SW] Queueing failed API call for background sync');

            // Register background sync
            await registerBackgroundSync(request);

            // Return offline response
            return new Response(
              JSON.stringify({
                success: false,
                offline: true,
                message: 'Saved offline - will sync when connection restored',
                queued: true
              }),
              {
                status: 202, // Accepted
                headers: { 'Content-Type': 'application/json' }
              }
            );
          }

          // For GET requests, return offline error
          return new Response(
            JSON.stringify({
              success: false,
              offline: true,
              error: 'Backend offline - no cached data available'
            }),
            {
              status: 503, // Service Unavailable
              headers: { 'Content-Type': 'application/json' }
            }
          );
        })
    );
    return;
  }

  // Static assets: Cache-first with network fallback
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Cache successful responses
            if (response.ok && request.method === 'GET') {
              const responseClone = response.clone();
              caches.open(DYNAMIC_CACHE).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return response;
          })
          .catch(() => {
            // Return offline fallback page
            if (request.destination === 'document') {
              return caches.match('/index.html');
            }
          });
      })
  );
});

// Background Sync - retry failed uploads
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  if (event.tag === 'voice-upload-queue') {
    event.waitUntil(syncVoiceUploads());
  }
});

// Helper: Register background sync
async function registerBackgroundSync(request) {
  try {
    // Store request in IndexedDB queue (handled by queue-manager.js)
    const requestData = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: request.method !== 'GET' ? await request.blob() : null,
      timestamp: Date.now()
    };

    // Send message to client to queue the request
    const clients = await self.clients.matchAll();
    clients.forEach((client) => {
      client.postMessage({
        type: 'QUEUE_REQUEST',
        data: requestData
      });
    });

    // Register sync event
    await self.registration.sync.register('voice-upload-queue');
  } catch (error) {
    console.error('[SW] Failed to register background sync:', error);
  }
}

// Helper: Sync queued voice uploads
async function syncVoiceUploads() {
  console.log('[SW] Processing voice upload queue...');

  try {
    // Get all clients
    const clients = await self.clients.matchAll();

    // Tell queue manager to process queue
    clients.forEach((client) => {
      client.postMessage({
        type: 'PROCESS_QUEUE'
      });
    });

    console.log('[SW] Queue processing triggered');
  } catch (error) {
    console.error('[SW] Queue sync failed:', error);
    throw error; // Re-register sync for retry
  }
}

// Message handler - communication with main thread
self.addEventListener('message', (event) => {
  console.log('[SW] Received message:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((name) => caches.delete(name))
        );
      })
    );
  }
});

console.log('[SW] Service worker loaded');
