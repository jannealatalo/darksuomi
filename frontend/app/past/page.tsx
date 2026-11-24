import type { Metadata } from "next";
import Link from "next/link";
import { getPastEvents } from "../../lib/events";
import PastGigList from "./PastGigList";
import SiteFooter from "../SiteFooter";

export const metadata: Metadata = {
  title: "Past gigs – Dark Suomi",
  description:
    "Recent alternative gigs in Helsinki, Espoo, Tampere, Oulu and Turku with their actual setlists from setlist.fm, and one-click Spotify playlists of them.",
};

export default function PastGigsPage() {
  const events = getPastEvents(90);
  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6">
          <Link href="/" className="text-purple-400 hover:text-purple-300">
            ← Upcoming gigs
          </Link>
        </p>
        <header className="mb-6 space-y-2">
          <h1 className="text-3xl font-bold text-gray-100">Past gigs</h1>
          <p className="text-sm text-gray-400 max-w-2xl">
            Gigs of the last three months in Helsinki &amp; Espoo, Tampere, Oulu and Turku,
            newest first. When fans have added the
            night&apos;s setlist to{" "}
            <a
              href="https://www.setlist.fm"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              setlist.fm
            </a>
            , it is linked here, with a one-click Spotify playlist of it made by{" "}
            <a
              href="https://setlistfm.selbi.club/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-green-500 hover:text-green-400"
            >
              setlistfm.selbi.club
            </a>{" "}
            (an independent tool by Selbi). Setlists usually appear within a day or
            two; we check every night.
          </p>
        </header>

        <PastGigList events={events} />

        <SiteFooter />
      </div>
    </main>
  );
}
