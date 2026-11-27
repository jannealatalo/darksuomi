import type { Metadata } from "next";
import Link from "next/link";
import { OUT_NOW_DAYS, getReleases } from "../../lib/releases";
import SiteFooter from "../SiteFooter";
import ReleaseList from "./ReleaseList";

export const metadata: Metadata = {
  title: "Release Radar – Dark Suomi",
  description:
    "New and upcoming albums and EPs by the bands playing in Helsinki, Espoo, Tampere, Oulu and Turku, with links to Spotify, Apple Music, Tidal, Deezer, YouTube Music and Bandcamp.",
};

export default function ReleasesPage() {
  const { upcoming, recent } = getReleases();
  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6 text-sm">
          <Link href="/" className="text-purple-400 hover:text-purple-300">
            ← Upcoming gigs
          </Link>
          <span className="text-gray-600"> · </span>
          <Link href="/bands" className="text-purple-400 hover:text-purple-300">
            Band Directory
          </Link>
        </p>
        <header className="mb-6 space-y-2">
          <h1 className="text-3xl font-bold text-gray-100">Release Radar</h1>
          <p className="text-sm text-gray-400 max-w-2xl">
            Albums and EPs by bands that have played or will play a Dark Suomi gig: announced
            ones and those out in the last {OUT_NOW_DAYS} days. Release info comes from{" "}
            <a
              href="https://musicbrainz.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              MusicBrainz
            </a>
            . The streaming links come from MusicBrainz and Deezer, and{" "}
            <a
              href="https://song.link"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              song.link
            </a>{" "}
            finds the same album on Spotify, Apple Music, Tidal and the others. Updated every few
            days.
          </p>
        </header>
        <ReleaseList upcoming={upcoming} recent={recent} />
        <SiteFooter />
      </div>
    </main>
  );
}
