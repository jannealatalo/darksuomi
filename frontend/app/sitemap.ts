import type { MetadataRoute } from "next";
import meta from "../data/meta.json";
import { SITE_URL } from "../lib/site";

/**
 * The site's pages for search engines. The gig pages change with every
 * nightly scrape (and deploy), so they carry the scrape time.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const scraped = new Date(meta.lastScraped);
  const page = (
    path: string,
    changeFrequency: "daily" | "weekly" | "monthly",
    priority: number
  ) => ({ url: `${SITE_URL}${path}`, lastModified: scraped, changeFrequency, priority });
  return [
    page("/", "daily", 1),
    page("/tampere", "daily", 0.9),
    page("/oulu", "daily", 0.9),
    page("/turku", "daily", 0.9),
    page("/bands", "weekly", 0.6),
    page("/releases", "daily", 0.5),
    page("/past", "daily", 0.5),
    page("/standup", "daily", 0.4),
    page("/updates", "monthly", 0.3),
    { url: `${SITE_URL}/weedian-in-spotify`, changeFrequency: "weekly" as const, priority: 0.3 },
    { url: `${SITE_URL}/privacy`, changeFrequency: "monthly" as const, priority: 0.1 },
  ];
}
