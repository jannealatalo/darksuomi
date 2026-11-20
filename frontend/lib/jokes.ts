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
  "No gigs today. A good day to check out [Veriteras' latest album](https://open.spotify.com/album/1DKpwS1MGQMDE46wennc0l).",
  "Nope. No gigs today. It's [Sorcia](https://open.spotify.com/artist/1Yy3XvKls9yjdnRQAhcrK5) day.",
  "No gigs today – but there's always [Zombie Eater](https://open.spotify.com/artist/1Gd0bnQiWDvWFnoMSJe2Ll).",
  "No gigs today, but no worries: play [Year of the Cobra](https://open.spotify.com/artist/1EVrYCCBDAobe64D8pUG0h) on 11.",
  "No gigs today – check out some old [Indica](https://open.spotify.com/artist/1Nc6H2qbH5SljekjNBTX7m) record instead.",
];

/** For several empty days in a row; "{n}" becomes the number of days. */
export const NO_GIG_RANGE_JOKES = [
  "{n} days without gigs. Your ears could use the rest anyway.",
  "Nothing for {n} days – a perfect time to finally alphabetise your vinyl.",
  "{n} quiet days. Practise your headbanging in front of the mirror.",
  "No gigs for {n} days. Your band T-shirts deserve a wash.",
  "{n} days without gigs. You might want to play [Hillbilly Fuckery](https://open.spotify.com/track/4nrlUlG4vX6CxTxX7Hsbuo) on repeat while waiting for the next gig.",
  "Nothing for {n} days. Your tinnitus will think you've retired.",
  "{n} gigless days. Grow your hair a few millimetres longer.",
  "{n} days of nothing. Even the merch table is lonely.",
  "Nothing for {n} days – go stare at a frozen lake, very black metal.",
  "{n} days without anything, but no worries, [Ajattara](https://open.spotify.com/artist/19WQljDiwhjoGNc8CMbQgn) has many good albums to check out.",
  "{n} very quiet days. This is not normal. Is the Simulation failing?",
  "There's nothing to see in {n} days. But [Rock Siltanen Group](https://open.spotify.com/artist/6ymNbj6lLTOuuqaMsIuFUr) might help with the anxiety.",
];

/** Second line of the header; a random one on every visit. */
export const TAGLINES = [
  "Life is short, winters are long. Go see a band.",
  "Sunlight is overrated anyway.",
  "Cheaper than therapy, louder too.",
  "It's dark outside anyway.",
  "Bring earplugs. Leave hope at the door.",
  "Seasonal affective disorder, now with a soundtrack.",
  "Black clothes are always in season here.",
  "Nobody smiles at a doom gig. Perfect.",
  "No small talk needed. The band is too loud anyway.",
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
