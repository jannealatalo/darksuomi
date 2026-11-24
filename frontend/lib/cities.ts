export type CityKey = "helsinki" | "tampere" | "oulu" | "seattle";

export type City = {
  key: CityKey;
  name: string;
  path: string;
  /** The city's time zone: "today" and past gigs go by it. */
  timeZone: string;
  /** US formats: dates "11/24", times "7:00 PM". */
  us?: boolean;
};

/** The calendars: Helsinki is the main site, Tampere and Oulu have their own pages. */
export const CITIES: City[] = [
  { key: "helsinki", name: "Helsinki", path: "/", timeZone: "Europe/Helsinki" },
  { key: "tampere", name: "Tampere", path: "/tampere", timeZone: "Europe/Helsinki" },
  { key: "oulu", name: "Oulu", path: "/oulu", timeZone: "Europe/Helsinki" },
];

/**
 * Experiments with their own page but left out of the menus, the band
 * directory, past gigs, the updates page and the sitemap: only people with
 * the link find them (the page also asks search engines not to index it).
 */
export const HIDDEN_CITIES: City[] = [
  { key: "seattle", name: "Seattle", path: "/seattle", timeZone: "America/Los_Angeles", us: true },
];

export function cityInfo(key: CityKey): City {
  return [...CITIES, ...HIDDEN_CITIES].find((c) => c.key === key) ?? CITIES[0];
}
