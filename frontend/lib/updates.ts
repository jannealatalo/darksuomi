import updates from "../data/updates.json";
import type { CityKey } from "./cities";

/** A gig first found by one night's scrape (changelog.py -> data/updates.json). */
export type NewGig = {
  id: number;
  city: CityKey;
  artist: string;
  venue: string;
  /** The gig's town, e.g. "Espoo", "Tuusula". */
  place: string;
  date: string;
  genres: string[];
  status?: string;
};

export type UpdateDay = {
  /** The scrape's day, "2026-11-21". */
  day: string;
  gigs: NewGig[];
  /** New gigs per city that the default genre filter hides. */
  hidden: Partial<Record<CityKey, number>>;
};

/** Days with new gigs, newest first. */
export function getUpdates(): UpdateDay[] {
  return updates as UpdateDay[];
}
