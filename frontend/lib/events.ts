import events from "../data/events.json";
import genreConfig from "../data/genre-config.json";
import meta from "../data/meta.json";
import type { Event } from "../types/events";

export const excludedGenres = new Set<string>(genreConfig.excludeGenres);

/**
 * Genres the site is about. A "*" matches any text, so "*metal*" covers
 * "black metal" and "metalcore"; entries without "*" must match exactly.
 */
const alwaysShowPatterns = genreConfig.alwaysShowGenres.map(
  (pattern) =>
    new RegExp(
      "^" +
        pattern
          .split("*")
          .map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&"))
          .join(".*") +
        "$"
    )
);

function isCoreGenre(genre: string): boolean {
  return alwaysShowPatterns.some((re) => re.test(genre));
}

/** When the scraper last saved events, formatted in Finnish time. */
export const lastScraped = new Date(meta.lastScraped).toLocaleString("fi-FI", {
  timeZone: "Europe/Helsinki",
  day: "numeric",
  month: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

/**
 * "Today" in Finland on the day of the last scrape (YYYY-MM-DD). Using the
 * scrape date instead of the clock keeps server and browser renders identical;
 * the nightly job refreshes it.
 */
const scrapeDay = new Date(meta.lastScraped).toLocaleDateString("sv-SE", {
  timeZone: "Europe/Helsinki",
});

/** Upcoming events (from the scrape day on), sorted by date and time. */
export function getEvents(): Event[] {
  return (events as Event[])
    .filter((e) => e.date.slice(0, 10) >= scrapeDay)
    .sort((a, b) => a.date.localeCompare(b.date));
}

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export type EventDay = {
  key: string; // YYYY-MM-DD
  weekday: string; // "Thu"
  day: number;
  month: number; // 1-12
  monthLabel: string; // "November 2026"
  events: Event[];
};

/** Group (already sorted) events by calendar day. */
export function groupByDay(list: Event[]): EventDay[] {
  const days: EventDay[] = [];
  for (const event of list) {
    const key = event.date.slice(0, 10);
    let day = days[days.length - 1];
    if (!day || day.key !== key) {
      const [y, m, d] = key.split("-").map(Number);
      day = {
        key,
        weekday: WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()],
        day: d,
        month: m,
        monthLabel: `${MONTHS[m - 1]} ${y}`,
        events: [],
      };
      days.push(day);
    }
    day.events.push(event);
  }
  return days;
}

/** Doors / start time as "19:00", or null when the venue gives none. */
export function eventTime(event: Event): string | null {
  const time = event.date.slice(11, 16);
  return time && time !== "00:00" ? time : null;
}

/**
 * An event is always shown when any of its genres is one the site is about
 * (alwaysShowGenres). Otherwise it is hidden by default when it has no genre
 * at all, or when its strongest (first) genre is excluded.
 */
export function isExcludedByGenre(event: Event): boolean {
  const genres = event.genres ?? [];
  if (genres.some(isCoreGenre)) return false;
  return genres.length === 0 || excludedGenres.has(genres[0]);
}

/** Artist names to match against Spotify follows, lowercased. */
export function eventArtistNames(event: Event): string[] {
  const names = event.artists?.length ? event.artists : [event.artist];
  return names.map((n) => n.toLowerCase());
}
