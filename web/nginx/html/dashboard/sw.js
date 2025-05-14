const CACHE_NAME = 'nginx-dashboard-v1';
const METRICS_CACHE_NAME = 'nginx-metrics-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/images/icon.svg',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// Utility functions
const logError = (error, context) => {
    console.error(`[Service Worker] ${context}:`, error);
};

const cacheStaticAssets = async () => {
    try {
        const cache = await caches.open(CACHE_NAME);
        await cache.addAll(STATIC_ASSETS);
    } catch (error) {
        logError(error, 'Static asset caching failed');
    }
};

const cacheMetrics = async (request, response) => {
    try {
        const cache = await caches.open(METRICS_CACHE_NAME);
        const clonedResponse = response.clone();
        await cache.put(request, clonedResponse);
    } catch (error) {
        logError(error, 'Metrics caching failed');
    }
};

const clearOldCaches = async () => {
    try {
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames
                .filter(name => ![CACHE_NAME, METRICS_CACHE_NAME].includes(name))
                .map(name => caches.delete(name))
        );
    } catch (error) {
        logError(error, 'Cache cleanup failed');
    }
};

// Install event handler
self.addEventListener('install', event => {
    event.waitUntil(
        Promise.all([
            cacheStaticAssets(),
            self.skipWaiting()
        ])
    );
});

// Activate event handler
self.addEventListener('activate', event => {
    event.waitUntil(
        Promise.all([
            clearOldCaches(),
            self.clients.claim()
        ])
    );
});

// Fetch event handler with improved caching strategy
self.addEventListener('fetch', event => {
    const isMetricsRequest = (url) => {
        return url.includes('/metrics/') || 
               url.includes('/health') || 
               url.includes('/ssl-status.json');
    };

    const handleMetricsRequest = async (request) => {
        try {
            const response = await fetch(request);
            if (response.ok) {
                await cacheMetrics(request, response);
                return response;
            }
            throw new Error('Network response was not ok');
        } catch (error) {
            const cachedResponse = await caches.match(request);
            if (cachedResponse) {
                return cachedResponse;
            }
            throw error;
        }
    };

    const handleStaticRequest = async (request) => {
        const cachedResponse = await caches.match(request);
        return cachedResponse || fetch(request);
    };

    event.respondWith(
        (async () => {
            try {
                return isMetricsRequest(event.request.url)
                    ? await handleMetricsRequest(event.request)
                    : await handleStaticRequest(event.request);
            } catch (error) {
                logError(error, `Request failed: ${event.request.url}`);
                throw error;
            }
        })()
    );
});

// Background sync handler
self.addEventListener('sync', event => {
    if (event.tag === 'sync-metrics') {
        event.waitUntil(
            (async () => {
                try {
                    const clients = await self.clients.matchAll();
                    clients.forEach(client => {
                        client.postMessage({
                            type: 'SYNC_METRICS',
                            timestamp: new Date().toISOString()
                        });
                    });
                } catch (error) {
                    logError(error, 'Background sync failed');
                }
            })()
        );
    }
});

// Push notification handler
self.addEventListener('push', event => {
    const options = {
        body: event.data.text(),
        icon: '/images/icon.svg',
        badge: '/images/icon.svg',
        tag: 'nginx-alert',
        data: {
            timestamp: new Date().toISOString()
        },
        actions: [
            {
                action: 'view',
                title: 'View Dashboard'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };

    event.waitUntil(
        (async () => {
            try {
                await self.registration.showNotification('Nginx Monitor Alert', options);
            } catch (error) {
                logError(error, 'Push notification failed');
            }
        })()
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/dashboard/')
        );
    }
});

