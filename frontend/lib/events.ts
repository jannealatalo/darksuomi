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
 * An event is hidden by default when its strongest genre is excluded, or when
 * at least half of its genres are. A single stray tag (e.g. "pop" as the
 * sixth tag of a glam punk band) is not enough. Untagged events are shown.
 */
export function isExcludedByGenre(event: Event): boolean {
  const genres = event.genres ?? [];
  if (genres.length === 0) return false;
  const excludedCount = genres.filter((g) => excludedGenres.has(g)).length;
  return excludedGenres.has(genres[0]) || excludedCount * 2 >= genres.length;
}

/** Artist names to match against Spotify follows, lowercased. */
export function eventArtistNames(event: Event): string[] {
  const names = event.artists?.length ? event.artists : [event.artist];
  return names.map((n) => n.toLowerCase());
}
