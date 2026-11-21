import bandData from "../data/bands.json";
import ouluBandData from "../data/oulu/bands.json";
import tampereBandData from "../data/tampere/bands.json";
import type { CityKey } from "./cities";
import { CITIES } from "./cities";
import { getEvents } from "./events";
import type { Event, GigBand } from "../types/events";
import { LINK_LABELS, bandSlug, type LinkKind } from "./bandLinks";

export { LINK_LABELS, bandSlug, type LinkKind };

type BandEntry = {
  display?: string;
  genres?: string[];
  eventIds?: number[];
  links?: Partial<Record<LinkKind, string>>;
};

const BANDS_BY_CITY: Record<CityKey, Record<string, BandEntry>> = {
  helsinki: bandData as Record<string, BandEntry>,
  tampere: tampereBandData as Record<string, BandEntry>,
  oulu: ouluBandData as Record<string, BandEntry>,
};

/** The one band directory, for every city. */
export const BANDS_PATH = "/bands";

/** An upcoming gig in the directory, with its city's gig list. */
export type BandGig = Event & { gigsPath: string; cityName: string };

export type Band = {
  name: string;
  genres: string[];
  links: Partial<Record<LinkKind, string>>;
  gigs: BandGig[];
};

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

/**
 * Bands with upcoming gigs in any city, alphabetically, with their gigs
 * attached. A band in several cities' data is one entry (matched by
 * bandSlug, which also folds spelling variants like "KANONENFIEBER").
 */
export function getBands(): Band[] {
  const bands = new Map<string, Band>();
  for (const city of CITIES) {
    const upcoming = new Map(getEvents(city.key).map((e) => [e.id, e]));
    for (const [key, b] of Object.entries(BANDS_BY_CITY[city.key])) {
      const gigs = (b.eventIds ?? [])
        .map((id) => upcoming.get(id))
        .filter((e): e is Event => Boolean(e))
        .map((e) => ({ ...e, gigsPath: city.path, cityName: city.name }));
      if (gigs.length === 0) continue;
      const name = b.display || key;
      const slug = bandSlug(name);
      const known = bands.get(slug);
      if (!known) {
        bands.set(slug, { name, genres: b.genres ?? [], links: { ...b.links }, gigs });
        continue;
      }
      known.links = { ...b.links, ...known.links };
      if (known.genres.length === 0) known.genres = b.genres ?? [];
      const ids = new Set(known.gigs.map((g) => `${g.gigsPath}${g.id}`));
      known.gigs.push(...gigs.filter((g) => !ids.has(`${g.gigsPath}${g.id}`)));
    }
  }
  return [...bands.values()]
    .map((b) => ({ ...b, gigs: b.gigs.sort((a, c) => a.date.localeCompare(c.date)) }))
    .sort((a, b) => a.name.localeCompare(b.name, "fi", { sensitivity: "base" }));
}

/** Letter group for the A–Z index ("#" for digits and symbols). */
export function letterOf(name: string): string {
  const first = name.trim().charAt(0).toLocaleUpperCase("fi");
  return /[A-ZÅÄÖ]/.test(first) ? first : "#";
}

/**
 * The gig list's "Band info": each gig gets the directory entries of its
 * bands (name, anchor, links), in the order they appear in the title. Done
 * on the server so the browser gets only these, not all of bands.json.
 */
export function withBandInfo(events: Event[], city: CityKey = "helsinki"): Event[] {
  const byEvent = new Map<number, GigBand[]>();
  for (const [key, b] of Object.entries(BANDS_BY_CITY[city])) {
    const name = b.display || key;
    const links = b.links ?? {};
    for (const id of b.eventIds ?? []) {
      const list = byEvent.get(id) ?? [];
      list.push({ name, links, href: `${BANDS_PATH}#band-${bandSlug(name)}` });
      byEvent.set(id, list);
    }
  }
  return events.map((e) => {
    const bands = byEvent.get(e.id);
    if (!bands) return e;
    const title = e.artist.toLowerCase();
    const pos = (b: GigBand) => {
      const i = title.indexOf(b.name.toLowerCase());
      return i < 0 ? title.length : i;
    };
    return { ...e, bands: [...bands].sort((a, b) => pos(a) - pos(b)) };
  });
}
