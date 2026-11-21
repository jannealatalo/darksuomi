/**
 * Band link kinds and labels, without the band data itself, so client
 * components (the gig list's "Band info") can use them without shipping
 * bands.json to the browser.
 */
export type LinkKind =
  | "spotify" | "bandcamp" | "soundcloud" | "tidal" | "apple" | "deezer"
  | "youtube" | "discogs" | "metalArchives" | "wikipedia" | "homepage"
  | "instagram";

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

/** "Ghosts on TV" -> "ghosts-on-tv": the band's anchor in /bands (#band-…). */
export function bandSlug(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/\p{M}/gu, "") // accents split off by NFKD
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
