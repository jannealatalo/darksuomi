/**
 * Dry humour for days without gigs (in the currently shown list, so they
 * follow the genre/venue filters). Add more freely.
 *
 * Links: write [link text](https://address) inside a joke.
 */
export const NO_GIG_JOKES = [
  "There's simply nothing for today – your next best option is to watch [Friends on Netflix](https://www.netflix.com/title/70153404).",
  "Your music today comes from playing GTA VI.",
  "Nothing today, go see your mom.",
  "Nothing today – how can that be?",
  "It's a no-music day, do some kalsarikänni at home.",
  "No gigs today, check if Wolt can bring you some.",
  "Nothing to see today. Listen to [Kuuntelija](https://www.youtube.com/@Kuuntelijapodcast).",
  "A day to clean up your earplugs.",
  "Go visit [Levykauppa Äx](https://www.levykauppax.fi/), it's open until 19:00.",
  "Systeemi ei toimi. James was here.",
  "A day to visit [Bodom Bar & Sauna](https://www.bodombar.com/) in Espoo.",
  "No gigs today. Your neighbours say thank you.",
  "Nothing on. Put on Sunn O))) at full volume and pretend it's a gig.",
  "A quiet day. Tune your guitar. Then tune it again.",
  "No gigs today – re-read the liner notes of your favourite album.",
  "Nothing tonight. Finally time to argue online about the best Children of Bodom album.",
  "Nothing today, a nice day for a funeral.",
  "Nothing today, a good day to listen to the [latest Sunn O))) album](https://open.spotify.com/album/1grbT4stwprQnmPMxshbbI). 10 times.",
];

/** For several empty days in a row; "{n}" becomes the number of days. */
export const NO_GIG_RANGE_JOKES = [
  "{n} days without gigs. Your ears could use the rest anyway.",
  "Nothing for {n} days – a perfect time to finally alphabetise your vinyl.",
  "{n} quiet days. Practise your headbanging in front of the mirror.",
  "No gigs for {n} days. Your band T-shirts deserve a wash.",
  "{n} days without gigs. Time to finally finish that 40-minute doom song.",
  "Nothing for {n} days. Your tinnitus will think you've retired.",
  "{n} gigless days. Grow your hair a few millimetres longer.",
  "{n} days of nothing. Even the merch table is lonely.",
  "Nothing for {n} days – go stare at a frozen lake, very black metal.",
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

export type JokePart = { text: string; url?: string };

/** Split "Listen to [Kuuntelija](https://…)." into text and link parts. */
export function jokeParts(joke: string): JokePart[] {
  const parts: JokePart[] = [];
  const re = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;
  let last = 0;
  for (let m = re.exec(joke); m; m = re.exec(joke)) {
    if (m.index > last) parts.push({ text: joke.slice(last, m.index) });
    parts.push({ text: m[1], url: m[2] });
    last = m.index + m[0].length;
  }
  if (last < joke.length) parts.push({ text: joke.slice(last) });
  return parts;
}
