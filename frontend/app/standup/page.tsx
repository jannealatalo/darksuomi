import type { Metadata } from "next";
import Link from "next/link";
import meta from "../../data/meta.json";
import { getShows } from "../../lib/standup";
import ShowList from "./ShowList";

export const metadata: Metadata = {
  title: "Itse Keksityt Vitsit – stand up Helsingissä ja Espoossa",
  description: "Tulevat stand up -keikat ja komediaklubit Helsingissä ja Espoossa yhdellä sivulla.",
};

function scrapedAt(): string {
  return new Date(meta.lastScraped).toLocaleString("fi-FI", {
    timeZone: "Europe/Helsinki",
    day: "numeric",
    month: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Itse Keksityt Vitsit: stand-up shows in Helsinki and Espoo (in Finnish). */
export default function StandupPage() {
  const shows = getShows();
  return (
    <main lang="fi" className="min-h-screen bg-zinc-950 text-zinc-300">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
        <header className="mb-8 space-y-2">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-amber-300">
            Itse Keksityt Vitsit
          </h1>
          <p className="text-zinc-300">Stand up -keikat ja komediaklubit Helsingissä ja Espoossa.</p>
          <p className="text-xs text-zinc-500">
            {shows.length} tulevaa keikkaa · päivitetty {scrapedAt()}
          </p>
        </header>

        <ShowList shows={shows} />

        <footer className="mt-16 space-y-2 border-t border-zinc-800 pt-6 text-xs text-zinc-500">
          <p>
            Tiedot kerätään automaattisesti tapahtumapaikkojen sivuilta sekä Helsingin ja
            Espoon tapahtumarajapinnoista, joten niissä voi olla virheitä. Tarkista aina
            tiedot tapahtumapaikalta tai lipunmyyjältä.
          </p>
          <p>
            Samoilta tekijöiltä:{" "}
            <Link href="/" className="text-amber-400 hover:text-amber-300">
              Dark Suomi
            </Link>{" "}
            – synkät ja äänekkäät keikat ·{" "}
            <Link href="/privacy" className="text-amber-400 hover:text-amber-300">
              Tietosuoja (englanniksi)
            </Link>
          </p>
        </footer>
      </div>
    </main>
  );
}
