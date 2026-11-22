/* MANTIS service worker — makes the app installable and the shell load offline.
   Strategy: cache-first for the static shell (HTML/CSS/JS/icons), always-network
   for /api/* and the live screen mirrors (never cache live state). */
const CACHE = "mantis-v1";
const SHELL = [
  "/", "/console.css", "/console.js", "/remote",
  "/icons/icon-192.png", "/icons/icon-512.png", "/icons/apple-touch-icon.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  // live data + screen mirrors: network only, never cached
  if (url.pathname.startsWith("/api/") ||
      url.pathname.endsWith(".png") && (url.pathname.includes("epaper") || url.pathname.includes("color"))) {
    return; // let the browser do its normal network fetch
  }
  // shell: cache-first, fall back to network and warm the cache
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => hit))
  );
});
