/** Venue home pages, keyed by the venue name used in events.json. */
export const VENUE_LINKS: Record<string, string> = {
  "Tavastia Klubi": "https://tavastiaklubi.fi/",
  "On the Rocks": "https://www.rocks.fi/",
  Kulttuuritalo: "https://kulttuuritalo.fi/",
  KULT: "https://kulttuuritalo.fi/kult/",
};

export type SiteLink = { name: string; url: string };

/** Official ticket sellers. */
export const TICKET_SITES: SiteLink[] = [
  { name: "Tiketti", url: "https://www.tiketti.fi/" },
  { name: "Lippu.fi", url: "https://www.lippu.fi/" },
  { name: "Ticketmaster", url: "https://www.ticketmaster.fi/" },
  { name: "Live Nation", url: "https://www.livenation.fi/" },
];

/** Fan-to-fan ticket resale. */
export const RESALE_SITES: SiteLink[] = [
  { name: "Liputon", url: "https://www.liputon.fi/" },
  { name: "Liput vaihtoon", url: "https://liputvaihtoon.fi/liput" },
];
