import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Spotify only accepts 127.0.0.1 (not localhost) as a local redirect URI,
  // so the dev server must also accept requests from that host.
  allowedDevOrigins: ["127.0.0.1"],
  cacheComponents: true,
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
