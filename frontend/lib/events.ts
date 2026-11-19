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

export function getEvents(): Event[] {
  return [...(events as Event[])].sort(
    (a, b) =>
      new Date(a.date).getTime() - new Date(b.date).getTime()
  );
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
