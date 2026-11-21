import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Spotify only accepts 127.0.0.1 (not localhost) as a local redirect URI,
  // so the dev server must also accept requests from that host.
  allowedDevOrigins: ["127.0.0.1"],
  cacheComponents: true,
  // The service worker must never be cached, so app updates reach phones.
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
          { key: "Content-Type", value: "application/javascript; charset=utf-8" },
        ],
      },
    ];
  },
  // The city band directories were merged into the one /bands page.
  async redirects() {
    return [
      { source: "/tampere/bands", destination: "/bands", permanent: true },
      { source: "/oulu/bands", destination: "/bands", permanent: true },
    ];
  },
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
