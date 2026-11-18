import events from "../data/events.json";
import genreConfig from "../data/genre-config.json";
import meta from "../data/meta.json";
import type { Event } from "../types/events";

export const excludedGenres = new Set<string>(genreConfig.excludeGenres);

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
 * An event is hidden by default when it has no genre at all, or when its
 * strongest (first) genre is excluded. Weaker tags never decide.
 */
export function isExcludedByGenre(event: Event): boolean {
  const genres = event.genres ?? [];
  return genres.length === 0 || excludedGenres.has(genres[0]);
}

/** Artist names to match against Spotify follows, lowercased. */
export function eventArtistNames(event: Event): string[] {
  const names = event.artists?.length ? event.artists : [event.artist];
  return names.map((n) => n.toLowerCase());
}
