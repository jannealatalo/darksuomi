import type { Event } from "../types/events";

/** Lower case without accents: "Motörhead" -> "motorhead", "Ø" -> "o". */
export function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/ø/gi, "o")
    .replace(/æ/gi, "ae")
    .replace(/ß/g, "ss")
    .toLowerCase();
}

/** Everything a visitor might type to find this gig, normalized. */
function searchText(event: Event): string {
  return normalize(
    [
      event.artist,
      ...(event.artists ?? []),
      ...(event.schedule ?? []).map((s) => s.name),
      event.venue,
      event.city,
      ...(event.genres ?? []),
    ].join(" | ")
  );
}

/** Every word of the query must appear somewhere in the gig's text. */
export function matchesSearch(event: Event, query: string): boolean {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  if (words.length === 0) return true;
  const text = searchText(event);
  return words.every((w) => text.includes(w));
}
