// Shoot Tracker - Service Worker (PWA Install & Offline Cache)
const CACHE_NAME = "shoot-tracker-v3";
const STATIC_ASSETS = [
  "/mobile",
  "/static/mobile.css",
  "/static/mobile.js",
  "/static/app_icon.png",
  "/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  
  // APIs are always network-first
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ error: "Offline" }), {
          headers: { "Content-Type": "application/json" }
        })
      )
    );
    return;
  }

  // Network-First for HTML, JS, CSS to ensure instant updates
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok && (url.pathname.startsWith("/static/") || url.pathname === "/mobile" || url.pathname === "/app")) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

