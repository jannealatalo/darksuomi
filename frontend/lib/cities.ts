export type CityKey = "helsinki" | "tampere" | "oulu";

/** The calendars: Helsinki is the main site, the others are experimental. */
export const CITIES: { key: CityKey; name: string; path: string }[] = [
  { key: "helsinki", name: "Helsinki", path: "/" },
  { key: "tampere", name: "Tampere", path: "/tampere" },
  { key: "oulu", name: "Oulu", path: "/oulu" },
];
