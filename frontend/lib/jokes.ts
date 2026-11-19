/**
 * Dry humour for days without gigs (in the currently shown list, so they
 * follow the genre/venue filters). Add more freely.
 */
export const NO_GIG_JOKES = [
  "There's simply nothing for today – your next best option is to watch Friends on Netflix.",
  "Your music today comes from playing GTA VI.",
  "Nothing today, go see your mom.",
  "Nothing today – how can that be?",
  "It's a no-music day, do some kalsarikänni at home.",
  "No gigs today, check if Wolt can bring you some.",
];

/** For several empty days in a row; "{n}" becomes the number of days. */
export const NO_GIG_RANGE_JOKES = [
  "{n} days without gigs. Your ears could use the rest anyway.",
  "Nothing for {n} days – a perfect time to finally alphabetise your vinyl.",
  "{n} quiet days. Practise your headbanging in front of the mirror.",
  "No gigs for {n} days. Your band T-shirts deserve a wash.",
];

/** The same date always gets the same joke (stable across page loads). */
function pick(list: string[], key: string): string {
  let hash = 0;
  for (const ch of key) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return list[hash % list.length];
}

export function noGigJoke(dayKey: string, days: number): string {
  return days > 1
    ? pick(NO_GIG_RANGE_JOKES, dayKey).replace("{n}", String(days))
    : pick(NO_GIG_JOKES, dayKey);
}
