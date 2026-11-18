import events from "../data/events.json";
import genreConfig from "../data/genre-config.json";
import type { Event } from "../types/events";

export const excludedGenres = new Set<string>(genreConfig.excludeGenres);

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
