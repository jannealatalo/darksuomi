import releaseData from "../data/releases.json";
import { bandSlug } from "./bandLinks";
import { isExcludedByGenre, scrapeDayIn } from "./events";
import type { Event } from "../types/events";

export { releaseDate } from "./releaseDate";

/** Streaming links of a release, in display order. */
export const RELEASE_LINKS: [string, string][] = [
  ["spotify", "Spotify"],
  ["apple", "Apple Music"],
  ["tidal", "Tidal"],
  ["deezer", "Deezer"],
  ["youtubeMusic", "YouTube Music"],
  ["bandcamp", "Bandcamp"],
  ["amazon", "Amazon Music"],
];

type RawRelease = {
  id: string;
  title: string;
  type: string;
  date: string; // YYYY, YYYY-MM or YYYY-MM-DD
  band: string;
  genres?: string[];
  spotify?: string;
  cover?: string | null;
  musicbrainz?: string;
  links?: Record<string, string>;
};

export type Release = {
  id: string;
  title: string;
  type: string;
  date: string;
  band: string;
  bandHref: string;
  genres: string[];
  cover?: string;
  links: [string, string][]; // [label, url]
  musicbrainz?: string;
};

/** Days back that "Out now" covers. */
export const OUT_NOW_DAYS = 150;

/** Only the Dark Suomi genres (the gig list's default filter); releases.py
 * already skips the other bands, this also covers genre config changes. */
function releasesInGenre(): RawRelease[] {
  return (releaseData.releases as RawRelease[]).filter(
    (r) => !isExcludedByGenre({ genres: r.genres ?? [] } as Event)
  );
}

function toRelease(r: RawRelease): Release {
  const urls: Record<string, string | undefined> = { spotify: r.spotify, ...r.links };
  const genres = r.genres ?? [];
  return {
    id: r.id,
    title: r.title,
    type: r.type,
    date: r.date,
    band: r.band,
    bandHref: `/bands#band-${bandSlug(r.band)}`,
    genres,
    cover: r.cover ?? undefined,
    links: RELEASE_LINKS.filter(([k]) => urls[k]).map(([k, label]) => [label, urls[k]!]),
    musicbrainz: r.musicbrainz,
  };
}

/** A release dated only "2027" or "2027-03" is upcoming until that year/month is over. */
export function isUpcomingDate(d: string, today = scrapeDayIn("Europe/Helsinki")): boolean {
  return d > today.slice(0, d.length);
}

/** Upcoming (soonest first) and recent (newest first) albums and EPs. */
export function getReleases(): { upcoming: Release[]; recent: Release[] } {
  const today = scrapeDayIn("Europe/Helsinki");
  const from = new Date(Date.parse(today) - OUT_NOW_DAYS * 86400000).toISOString().slice(0, 10);
  const all = releasesInGenre().map(toRelease);
  const isUpcoming = (d: string) => isUpcomingDate(d, today);
  const upcoming = all.filter((r) => isUpcoming(r.date)).sort((a, b) => a.date.localeCompare(b.date));
  const recent = all
    .filter((r) => !isUpcoming(r.date) && r.date.length === 10 && r.date >= from)
    .sort((a, b) => b.date.localeCompare(a.date) || a.band.localeCompare(b.band));
  return { upcoming, recent };
}

/** The newest release of each band (by band slug), for the band directory. */
export function latestReleaseByBand(): Map<string, Release> {
  const today = scrapeDayIn("Europe/Helsinki");
  const map = new Map<string, Release>();
  for (const r of releasesInGenre().map(toRelease)) {
    if (r.date.length < 10 && r.date <= today.slice(0, r.date.length)) continue;
    const slug = bandSlug(r.band);
    const known = map.get(slug);
    if (!known || r.date > known.date) map.set(slug, r);
  }
  return map;
}
