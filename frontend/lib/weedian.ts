import { cacheLife } from "next/cache";

/**
 * Weedian's Bandcamp compilations and their Spotify playlists, from the
 * separate weedian-spotify project (github.com/jannealatalo/weedian-spotify).
 * Its weekly GitHub workflow updates data/*.json there; this site reads them
 * straight from GitHub, so new playlists show up without a darksuomi deploy.
 */

const DATA_URL =
  "https://raw.githubusercontent.com/jannealatalo/weedian-spotify/main/data";

type RawComp = {
  title: string;
  art_id?: number;
  released?: string;
  tracks: { artist: string; title: string }[];
  found?: number;
  playlist?: { url: string } | null;
};

type RawTracks = Record<string, { uri: string | null }>;

export type Compilation = {
  title: string;
  bandcampUrl: string;
  coverUrl: string | null;
  released: string | null; // ISO date
  total: number;
  found: number;
  playlistUrl: string | null;
  missing: string[]; // "Artist - Title" of songs not on Spotify
};

async function getJson<T>(file: string): Promise<T> {
  const response = await fetch(`${DATA_URL}/${file}`);
  if (!response.ok) throw new Error(`${file}: HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

/** Compilations that have a playlist, newest first. */
export async function getWeedianCompilations(): Promise<Compilation[]> {
  "use cache";
  // The playlists change weekly at most.
  cacheLife("hours");

  const [comps, tracks] = await Promise.all([
    getJson<Record<string, RawComp>>("compilations.json"),
    getJson<RawTracks>("tracks.json"),
  ]);

  return Object.entries(comps)
    .filter(([, c]) => c.playlist?.url && c.tracks?.length)
    .map(([bandcampUrl, c]) => {
      const released = c.released ? new Date(c.released) : null;
      const missing = c.tracks
        .filter((t) => !tracks[`${t.artist}|||${t.title}`]?.uri)
        .map((t) => (t.artist ? `${t.artist} - ${t.title}` : t.title));
      return {
        title: c.title,
        bandcampUrl,
        coverUrl: c.art_id ? `https://f4.bcbits.com/img/a${c.art_id}_16.jpg` : null,
        released:
          released && !isNaN(released.getTime()) ? released.toISOString().slice(0, 10) : null,
        total: c.tracks.length,
        found: c.found ?? c.tracks.length - missing.length,
        playlistUrl: c.playlist!.url,
        missing,
      };
    })
    .sort((a, b) => (b.released ?? "").localeCompare(a.released ?? ""));
}
