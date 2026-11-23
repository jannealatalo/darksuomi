import type { MetadataRoute } from "next";
import { SITE_URL } from "../lib/site";

/** Everything may be crawled except the API routes; points to the sitemap. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: "/api/" },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
