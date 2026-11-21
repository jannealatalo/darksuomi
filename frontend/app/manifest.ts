import type { MetadataRoute } from "next";

/** The installable app ("Add to Home Screen"): name, icons, colours. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Dark Suomi",
    short_name: "Dark Suomi",
    description: "Dark and loud gigs in Helsinki-Espoo, Tampere and Oulu on one page.",
    id: "/",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#000000",
    theme_color: "#000000",
    categories: ["music", "entertainment"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Tampere", url: "/tampere" },
      { name: "Oulu", url: "/oulu" },
      { name: "Band Directory", url: "/bands" },
    ],
  };
}
