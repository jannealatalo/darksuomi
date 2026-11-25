import { CITIES, type CityKey } from "../lib/cities";
import { isExcludedByGenre } from "../lib/events";
import { SITE_URL } from "../lib/site";
import { VENUE_ADDRESSES } from "../lib/venues";
import type { Event } from "../types/events";

/**
 * The city page's gigs as schema.org MusicEvents (JSON-LD), so search
 * engines can show them, e.g. in Google's event listings. Covers the gigs
 * shown by default (not the hidden genres), with the venue's address,
 * the bands, the ticket link and price when known. The end is the end
 * of the gig's day (no end times are known) and the venue stands as organizer.
 */
export default function GigJsonLd({ events, city }: { events: Event[]; city: CityKey }) {
  const path = CITIES.find((c) => c.key === city)?.path ?? "/";
  const pageUrl = `${SITE_URL}${path === "/" ? "/" : path}`;
  const data = events
    .filter((e) => !isExcludedByGenre(e))
    .map((e) => musicEvent(e, pageUrl));
  if (data.length === 0) return null;
  return (
    <script
      type="application/ld+json"
      // "<" escaped so a title can't close the script tag (Next's advice).
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({ "@context": "https://schema.org", "@graph": data }).replace(
          /</g,
          "\\u003c"
        ),
      }}
    />
  );
}

function musicEvent(e: Event, pageUrl: string) {
  const address = VENUE_ADDRESSES[e.venue];
  const names = e.artists?.length ? e.artists : [e.artist];
  const price = parsePrice(e.price);
  const time = e.date.slice(11, 16);
  const day = e.date.slice(0, 10);
  const timed = time !== "" && time !== "00:00";
  return {
    "@type": "MusicEvent",
    name: e.artist,
    // Without a time, the day alone (Google accepts a date).
    startDate: timed ? `${day}T${time}:00${helsinkiOffset(day)}` : day,
    // No end times are known: the end of the gig's day (a bare date could
    // read as midnight, before the start).
    endDate: timed ? `${day}T23:59:00${helsinkiOffset(day)}` : day,
    eventStatus:
      e.status === "cancelled" ? "https://schema.org/EventCancelled" : "https://schema.org/EventScheduled",
    eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
    url: `${pageUrl}#gig-${e.id}`,
    image: [`${SITE_URL}/logo.webp`],
    description: `${names.join(", ")} at ${e.venue}, ${address?.city ?? e.city}${
      e.genres?.length ? ` (${e.genres.slice(0, 3).join(", ")})` : ""
    }`,
    location: {
      "@type": "Place",
      name: e.venue,
      address: {
        "@type": "PostalAddress",
        ...(address && { streetAddress: address.street, postalCode: address.postalCode }),
        addressLocality: address?.city ?? e.city,
        addressCountry: "FI",
      },
    },
    // The venue by name only: gig pages are often on Facebook, ticket
    // shops or city calendars, so they don't give the venue's own site.
    organizer: { "@type": "Organization", name: e.venue },
    performer: names.map((name) => ({ "@type": "MusicGroup", name })),
    ...(e.ticketUrl && {
      offers: {
        "@type": "Offer",
        url: e.ticketUrl,
        availability:
          e.status === "sold out" ? "https://schema.org/SoldOut" : "https://schema.org/InStock",
        ...(price && { price: price.amount, priceCurrency: "EUR" }),
      },
    }),
    ...(price?.amount === "0" && { isAccessibleForFree: true }),
  };
}

/** The first euro amount ("alk. 39,50€, ovelta 45€" -> 39.50, "20 / 23e" -> 20); free entry -> 0. */
function parsePrice(text?: string): { amount: string } | null {
  if (!text) return null;
  if (/vapaa|free|ilmai/i.test(text)) return { amount: "0" };
  // Euros said with € or "e"/"eur" after a number; the first amount wins.
  if (!/€|\de\b|\deur\b|\d eur\b/i.test(text)) return null;
  const m = text.match(/(\d+)(?:[.,](\d{1,2}))?/);
  if (!m) return null;
  return { amount: m[2] ? `${m[1]}.${m[2].padEnd(2, "0")}` : m[1] };
}

/** "+02:00" in winter, "+03:00" in summer, for a Finnish date. */
function helsinkiOffset(day: string): string {
  const name = new Intl.DateTimeFormat("en-US", {
    timeZone: "Europe/Helsinki",
    timeZoneName: "shortOffset",
  })
    .formatToParts(new Date(`${day}T12:00:00Z`))
    .find((p) => p.type === "timeZoneName")?.value; // "GMT+2"
  const hours = Number(name?.replace("GMT", "") || 2);
  return `+${String(hours).padStart(2, "0")}:00`;
}
