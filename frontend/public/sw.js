/*
 * Dark Suomi service worker: keeps the gig pages on the phone so the
 * installed app opens fast and works offline (on the metro, at a festival).
 *
 *  - Pages: network first (fresh gigs), the saved copy when offline.
 *  - Next.js build files (/_next/static, hashed names): saved once, reused.
 *  - Icons and images: the saved copy at once, refreshed in the background.
 *  - Login, API calls and other sites: never touched.
 *
 * Bump VERSION to drop everything saved by older versions.
 */
const VERSION = "v4";
const PAGES = `pages-${VERSION}`;
const STATIC = `static-${VERSION}`;
const IMAGES = `images-${VERSION}`;
const START_PAGES = ["/", "/tampere", "/oulu"];
const OFFLINE_PAGE = "/offline.html";
const NETWORK_TIMEOUT_MS = 4000;
const MAX_IMAGES = 150;

/**
 * Save the start pages and everything they load (styles, scripts, logo):
 * the first visit loads those before this worker is running, so they
 * wouldn't be saved otherwise and the offline page would have no styles.
 */
async function precache() {
  const pages = await caches.open(PAGES);
  await pages.add(OFFLINE_PAGE);
  const assets = new Set();
  for (const path of START_PAGES) {
    const response = await fetch(path);
    if (!response.ok) continue;
    await pages.put(path, response.clone());
    const html = await response.text();
    for (const m of html.matchAll(/["'(,\s](\/_next\/(?:static\/[^"'()\s]+|image\?[^"'()\s]+))/g)) {
      const url = m[1].replace(/&amp;/g, "&");
      // The logo is listed in many widths; phones use at most ~640 px.
      const width = Number(new URL(url, self.location.origin).searchParams.get("w") || 0);
      if (width <= 640) assets.add(url);
    }
  }
  const statics = await caches.open(STATIC);
  const images = await caches.open(IMAGES);
  await Promise.all(
    [...assets].map((url) =>
      (url.startsWith("/_next/static/") ? statics : images).add(url).catch(() => {})
    )
  );
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    precache()
      .catch(() => {}) // offline install: things get saved on the next visit
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  const keep = new Set([PAGES, STATIC, IMAGES]);
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function timeout(ms) {
  return new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms));
}

/** Fresh page when the network answers in time; the saved copy otherwise. */
async function networkFirst(request) {
  const cache = await caches.open(PAGES);
  try {
    const response = await Promise.race([fetch(request), timeout(NETWORK_TIMEOUT_MS)]);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    // A page never visited: the "you're offline" page, not some other page.
    const saved =
      (await cache.match(request, { ignoreSearch: true })) || (await cache.match(OFFLINE_PAGE));
    if (saved) return saved;
    throw err;
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(STATIC);
  const saved = await cache.match(request, { ignoreVary: true });
  if (saved) return saved;
  const response = await fetch(request);
  if (response.ok) cache.put(request, response.clone());
  return response;
}

async function trim(cacheName, max) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  await Promise.all(keys.slice(0, Math.max(0, keys.length - max)).map((k) => cache.delete(k)));
}

async function staleWhileRevalidate(request, event) {
  const cache = await caches.open(IMAGES);
  const saved = await cache.match(request, { ignoreVary: true });
  const update = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
        trim(IMAGES, MAX_IMAGES);
      }
      return response;
    })
    .catch(() => saved);
  if (saved) {
    event.waitUntil(update);
    return saved;
  }
  return update;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname === "/sw.js") return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
  } else if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(cacheFirst(request));
  } else if (
    url.pathname.startsWith("/icons/") ||
    url.pathname.startsWith("/_next/image") ||
    /\.(png|jpe?g|webp|svg|ico)$/.test(url.pathname)
  ) {
    event.respondWith(staleWhileRevalidate(request, event));
  }
  // Everything else (page data for in-app navigation, analytics) goes to
  // the network as usual; offline, Next.js falls back to a full page load,
  // which the saved pages answer.
});
