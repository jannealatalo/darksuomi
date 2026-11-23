import events from "../data/events.json";
import ouluEvents from "../data/oulu/events.json";
import tampereEvents from "../data/tampere/events.json";
import genreConfig from "../data/genre-config.json";
import meta from "../data/meta.json";
import type { Event } from "../types/events";
import type { CityKey } from "./cities";

/**
 * Stand-up shows (genre "stand-up") stay in the data, where standup.py
 * picks them up for /standup, but aren't gigs: they're left out of the gig
 * lists completely, also under "Show hidden genres".
 */
const isGig = (e: Event) => !(e.genres ?? []).includes("stand-up");

const EVENTS_BY_CITY: Record<CityKey, Event[]> = {
  helsinki: (events as Event[]).filter(isGig),
  tampere: (tampereEvents as Event[]).filter(isGig),
  oulu: (ouluEvents as Event[]).filter(isGig),
};

export const excludedGenres = new Set<string>(genreConfig.excludeGenres);

/** The header genres as filters, each matching a family of genre tags. */
export const GENRE_FILTERS: { name: string; patterns: RegExp[] }[] =
  genreConfig.genreFilters.map((g) => ({
    name: g.name,
    patterns: g.patterns.map((p) => new RegExp(p, "i")),
  }));

export const GENRE_FILTER_NAMES = GENRE_FILTERS.map((g) => g.name);

/** Does the gig have a tag in this header genre (e.g. "Doom": sludge, drone…)? */
export function matchesGenreFilter(event: Event, name: string): boolean {
  const filter = GENRE_FILTERS.find((g) => g.name === name);
  if (!filter) return false;
  return (event.genres ?? []).some((tag) => filter.patterns.some((re) => re.test(tag)));
}

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

const ALWAYS_SHOW_TOP_TAGS = 5;

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
export const scrapeDay = new Date(meta.lastScraped).toLocaleDateString("sv-SE", {
  timeZone: "Europe/Helsinki",
});

/** Upcoming events (from the scrape day on), sorted by date and time. */
export function getEvents(city: CityKey = "helsinki"): Event[] {
  return EVENTS_BY_CITY[city]
    .filter((e) => e.date.slice(0, 10) >= scrapeDay)
    .sort((a, b) => a.date.localeCompare(b.date));
}

/** Gigs of the last `days` days (before the scrape day), newest first. */
/**
 * Past gigs of every city site, newest first. Each gig carries `site`, since
 * ids are only unique within one city's list.
 */
export function getPastEvents(days = 90): Event[] {
  const shift = (n: number) => {
    const d = new Date(`${scrapeDay}T12:00:00Z`);
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  };
  const from = shift(-days);
  // A week past the scrape day too: when the nightly scrape is late or
  // missed, the browser (PastGigList, useToday) still moves yesterday's
  // gigs here at midnight.
  const until = shift(7);
  return (Object.entries(EVENTS_BY_CITY) as [CityKey, Event[]][])
    .flatMap(([site, list]) => list.map((e) => ({ ...e, site })))
    .filter((e) => e.date.slice(0, 10) < until && e.date.slice(0, 10) >= from)
    .sort((a, b) => b.date.localeCompare(a.date));
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
 * Shown by default (the Dark Suomi selection) when one of the strongest tags
 * is a core genre (alwaysShowGenres), or when it fits a main genre and its
 * strongest (first) tag isn't excluded (jazz, soul, pop…). Everything else
 * is behind "Show hidden genres".
 */
export function isExcludedByGenre(event: Event): boolean {
  // Only the strongest few tags count, so a stray tag at the end of the
  // list (e.g. from a mismatched support act) can't override everything.
  const top = (event.genres ?? []).slice(0, ALWAYS_SHOW_TOP_TAGS);
  if (top.some(isCoreGenre)) return false;
  if (top.length === 0 || excludedGenres.has(top[0])) return true;
  return !GENRE_FILTERS.some((g) => top.some((tag) => g.patterns.some((re) => re.test(tag))));
}

/** Artist names to match against Spotify follows, lowercased. */
export function eventArtistNames(event: Event): string[] {
  const names = event.artists?.length ? event.artists : [event.artist];
  return names.map((n) => n.toLowerCase());
}

/** Day key +n days ("2026-11-30" + 2 -> "2026-12-02"). */
function addDays(key: string, n: number): string {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + n)).toISOString().slice(0, 10);
}

export type GigGap = { from: string; to: string; days: number; label: string };

/**
 * Runs of days without any gig in `days` (already grouped, ascending),
 * from the scrape day up to the last listed day.
 */
export function gapsBefore(days: EventDay[], from: string = scrapeDay): Map<string, GigGap> {
  const gaps = new Map<string, GigGap>(); // keyed by the day the gap precedes
  let cursor = from;
  for (const day of days) {
    if (day.key > cursor) {
      const to = addDays(day.key, -1);
      let n = 0;
      for (let k = cursor; k <= to; k = addDays(k, 1)) n++;
      gaps.set(day.key, { from: cursor, to, days: n, label: gapLabel(cursor, to) });
    }
    cursor = addDays(day.key, 1);
  }
  return gaps;
}

function gapLabel(from: string, to: string): string {
  const [, fm, fd] = from.split("-").map(Number);
  const [, tm, td] = to.split("-").map(Number);
  if (from === to) {
    const [y] = from.split("-").map(Number);
    return `${WEEKDAYS[new Date(Date.UTC(y, fm - 1, fd)).getUTCDay()]} ${fd}.${fm}.`;
  }
  return fm === tm ? `${fd}.–${td}.${tm}.` : `${fd}.${fm}.–${td}.${tm}.`;
}
