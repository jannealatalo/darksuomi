import showData from "../data/standup/events.json";
import { scrapeDay } from "./events";
import { normalize } from "./search";

/** A stand-up show (standup.py -> data/standup/events.json). */
export type Show = {
  title: string;
  venue: string;
  city: string;
  /** Start time in Finnish local time, "2026-12-12T18:00:00". */
  date: string;
  ticketUrl: string;
  eventUrl: string;
  price?: string;
  age?: string;
  status?: string;
  room?: string;
  source: string;
};

/** Upcoming shows, in date order. */
export function getShows(): Show[] {
  return (showData as Show[])
    .filter((s) => s.date.slice(0, 10) >= scrapeDay)
    .sort((a, b) => a.date.localeCompare(b.date));
}

const WEEKDAYS = ["sunnuntai", "maanantai", "tiistai", "keskiviikko", "torstai", "perjantai", "lauantai"];
const MONTHS = [
  "tammikuu", "helmikuu", "maaliskuu", "huhtikuu", "toukokuu", "kesäkuu",
  "heinäkuu", "elokuu", "syyskuu", "lokakuu", "marraskuu", "joulukuu",
];

export type ShowDay = { key: string; label: string; monthLabel: string; shows: Show[] };

/** Shows by day: "lauantai 12.12." under "joulukuu 2026". */
export function groupShowsByDay(shows: Show[]): ShowDay[] {
  const days: ShowDay[] = [];
  for (const show of shows) {
    const key = show.date.slice(0, 10);
    let day = days[days.length - 1];
    if (!day || day.key !== key) {
      const [y, m, d] = key.split("-").map(Number);
      const weekday = WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()];
      day = { key, label: `${weekday} ${d}.${m}.`, monthLabel: `${MONTHS[m - 1]} ${y}`, shows: [] };
      days.push(day);
    }
    day.shows.push(show);
  }
  return days;
}

/** "18.00" (Finnish style), or null when no time is known. */
export function showTime(show: Show): string | null {
  const t = show.date.slice(11, 16);
  return t && t !== "00:00" ? t.replace(":", ".") : null;
}

/** Every word of the query must appear in the title, venue or city. */
export function matchesShow(show: Show, query: string): boolean {
  const text = normalize([show.title, show.venue, show.city].join(" | "));
  return normalize(query)
    .split(/\s+/)
    .filter(Boolean)
    .every((w) => text.includes(w));
}
