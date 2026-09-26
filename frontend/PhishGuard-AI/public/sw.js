/*
 * PhishGuard-AI service worker (registered in production only, src/main.ts).
 *
 * - Pages: network first, falling back to the cached app shell when offline, so
 *   the app opens without a connection (messages typed offline are queued and
 *   analysed when the network is back - see stores/analysis.ts).
 * - Built assets (/assets/*, hashed names) and icons: cache first.
 * - API calls (/api/*) are never cached: results and personal data stay on the server.
 */
const VERSION = 'pg-v1'
const SHELL = ['/', '/check', '/learn', '/privacy', '/manifest.webmanifest', '/favicon-192.png']

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== VERSION).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone()
          caches.open(VERSION).then((cache) => cache.put(url.pathname, copy))
          return response
        })
        .catch(() => caches.match(url.pathname).then((hit) => hit || caches.match('/'))),
    )
    return
  }

  if (url.pathname.startsWith('/assets/') || /\.(png|svg|ico|woff2?|webmanifest)$/.test(url.pathname)) {
    event.respondWith(
      caches.match(request).then((hit) => hit || fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone()
          caches.open(VERSION).then((cache) => cache.put(request, copy))
        }
        return response
      })),
    )
  }
})
