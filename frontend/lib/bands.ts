import bandData from "../data/bands.json";
import { getEvents } from "./events";
import type { Event } from "../types/events";

export type LinkKind =
  | "spotify" | "bandcamp" | "soundcloud" | "tidal" | "apple" | "deezer"
  | "youtube" | "discogs" | "metalArchives" | "wikipedia" | "homepage"
  | "instagram";

type BandEntry = {
  display?: string;
  genres?: string[];
  eventIds?: number[];
  links?: Partial<Record<LinkKind, string>>;
};

export type Band = {
  name: string;
  genres: string[];
  links: Partial<Record<LinkKind, string>>;
  gigs: Event[];
};

/** Labels in display order. */
export const LINK_LABELS: [LinkKind, string][] = [
  ["spotify", "Spotify"],
  ["bandcamp", "Bandcamp"],
  ["soundcloud", "SoundCloud"],
  ["tidal", "Tidal"],
  ["apple", "Apple Music"],
  ["deezer", "Deezer"],
  ["youtube", "YouTube"],
  ["discogs", "Discogs"],
  ["metalArchives", "Metal Archives"],
  ["wikipedia", "Wikipedia"],
  ["homepage", "Homepage"],
  ["instagram", "Instagram"],
];

/** Search pages for the main services, used when no profile link is known. */
export const SEARCH_LINKS: [LinkKind, string, (q: string) => string][] = [
  ["spotify", "Spotify", (q) => `https://open.spotify.com/search/${q}/artists`],
  ["bandcamp", "Bandcamp", (q) => `https://bandcamp.com/search?q=${q}&item_type=b`],
  ["soundcloud", "SoundCloud", (q) => `https://soundcloud.com/search/people?q=${q}`],
  ["tidal", "Tidal", (q) => `https://listen.tidal.com/search/artists?q=${q}`],
  ["discogs", "Discogs", (q) => `https://www.discogs.com/search/?q=${q}&type=artist`],
];

/** Metal Archives only lists metal bands, so its search is offered for those. */
export const METAL_ARCHIVES_SEARCH = (q: string) =>
  `https://www.metal-archives.com/search?searchString=${q}&type=band_name`;

export function isMetal(genres: string[]): boolean {
  return genres.some((g) => /metal|doom|grind|-core|core$|sludge/.test(g));
}

/** Bands with upcoming gigs, alphabetically, with their gigs attached. */
export function getBands(): Band[] {
  const upcoming = new Map(getEvents().map((e) => [e.id, e]));
  return Object.entries(bandData as Record<string, BandEntry>)
    .map(([name, b]) => ({
      name: b.display || name,
      genres: b.genres ?? [],
      links: b.links ?? {},
      gigs: (b.eventIds ?? [])
        .map((id) => upcoming.get(id))
        .filter((e): e is Event => Boolean(e))
        .sort((a, c) => a.date.localeCompare(c.date)),
    }))
    .filter((b) => b.gigs.length > 0)
    .sort((a, b) => a.name.localeCompare(b.name, "fi", { sensitivity: "base" }));
}

/** Letter group for the A–Z index ("#" for digits and symbols). */
export function letterOf(name: string): string {
  const first = name.trim().charAt(0).toLocaleUpperCase("fi");
  return /[A-ZÅÄÖ]/.test(first) ? first : "#";
}
