import type { Metadata } from "next";
import { withBandInfo } from "../../lib/bands";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";

export const metadata: Metadata = {
  title: "Dark Suomi Seattle (experiment)",
  description: "Dark and loud gigs in Seattle",
  // A hidden experiment: not linked anywhere, not in the sitemap, not indexed.
  robots: { index: false, follow: false },
};

/**
 * Seattle: a hidden experiment with its own venues and data
 * (data/seattle/events.json, scraper_seattle_*.py). No JSON-LD event
 * markup, band directory, past gigs or updates for it.
 */
export default function SeattlePage() {
  const events = getEvents("seattle");
  return <GigCalendar events={withBandInfo(events, "seattle")} city="seattle" />;
}
