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
};

const entries = setlistData as Record<string, Entry>;

/** Expected setlists for every act on the bill that has one, headliner first. */
export function expectedSetlists(event: Event): ExpectedSetlist[] {
  const result: ExpectedSetlist[] = [];
  const add = (artist: string) => {
    const entry = entries[artist];
    if (!entry) return;
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
