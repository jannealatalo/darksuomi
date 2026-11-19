import pastSetlistData from "../data/past-setlists.json";
import playlistData from "../data/playlists.json";
import setlistData from "../data/setlists.json";
import type { Event } from "../types/events";

export type SetlistSong = {
  name: string;
  encore: boolean;
  cover: string | null;
  playedPct: number;
};

export type ExpectedSetlist = {
  artist: string;
  url: string | null;
  basedOn: number;
  from: string;
  to: string;
  songs: SetlistSong[];
};

type Entry = {
  status: string;
  url?: string | null;
  basedOn?: number;
  from?: string;
  to?: string;
  songs?: SetlistSong[];
  parts?: string[];
  latest?: { url: string; date: string; venue?: string; city?: string; songs?: number };
};

const entries = setlistData as Record<string, Entry>;

/** Expected setlists for every act on the bill that has one, headliner first. */
export function expectedSetlists(event: Event): ExpectedSetlist[] {
  const result: ExpectedSetlist[] = [];
  const seen = new Set<string>();
  const add = (artist: string) => {
    const entry = entries[artist];
    if (!entry || seen.has(artist)) return; // a bill can name an act twice
    seen.add(artist);
    if (entry.status === "split") {
      entry.parts?.forEach(add);
    } else if (entry.status === "ok" && entry.songs?.length) {
      result.push({
        artist,
        url: entry.url ?? null,
        basedOn: entry.basedOn ?? 0,
        from: entry.from ?? "",
        to: entry.to ?? "",
        songs: entry.songs,
      });
    }
  };
  (event.artists ?? []).forEach(add);
  return result;
}

const playlists = playlistData as Record<string, { url: string }>;

/** Spotify playlist of the expected setlist, in the Dark Suomi account. */
export function playlistUrl(event: Event): string | null {
  return playlists[event.ticketUrl]?.url ?? null;
}

/**
 * Tribute, anniversary and farewell shows rarely follow the usual set,
 * so their expected setlist gets a warning.
 */
const SPECIAL_SHOW =
  /\bplays\b|anniversary|rarities|päätöskeikka|juhlakeikka|juhlakonsertti|\d+\s*v\b|\d+\s*vuotta|x-mas|christmas|joulu|tribute/i;

export function isSpecialShow(event: Event): boolean {
  return SPECIAL_SHOW.test(event.artist);
}

/** Selbi's setlist.fm -> Spotify converter, opened with this setlist. */
export function selbiUrl(setlistUrl: string): string {
  return `https://setlistfm.selbi.club/?auto=${encodeURIComponent(setlistUrl)}`;
}

export type ShowLink = { artist: string; url: string; date?: string; place?: string };

/** Each act's most recent show anywhere (headliner first), if known. */
export function latestShows(event: Event): ShowLink[] {
  const shows: ShowLink[] = [];
  const seen = new Set<string>();
  const add = (artist: string) => {
    const entry = entries[artist];
    if (!entry || seen.has(artist)) return;
    seen.add(artist);
    if (entry.status === "split") return entry.parts?.forEach(add);
    if (entry.latest?.url) {
      shows.push({
        artist,
        url: entry.latest.url,
        date: entry.latest.date,
        place: entry.latest.city || entry.latest.venue,
      });
    }
  };
  (event.artists ?? []).forEach(add);
  return shows;
}

const pastSetlists = pastSetlistData as Record<
  string,
  { setlists?: Record<string, { url: string; songs?: number }> }
>;

/** The actual setlists of a past gig, as found on setlist.fm. */
export function actualSetlists(event: Event): ShowLink[] {
  const found = pastSetlists[String(event.id)]?.setlists ?? {};
  return Object.entries(found).map(([artist, s]) => ({ artist, url: s.url }));
}
