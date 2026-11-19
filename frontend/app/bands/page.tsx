import type { Metadata } from "next";
import Link from "next/link";
import { getBands } from "../../lib/bands";
import SiteFooter from "../SiteFooter";
import BandDirectory from "./BandDirectory";

export const metadata: Metadata = {
  title: "Bands – Dark Suomi",
  description:
    "Bands with upcoming gigs in Finland, with links to Spotify, Bandcamp, SoundCloud, Tidal, Discogs and more.",
};

export default function BandsPage() {
  const bands = getBands();
  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6">
          <Link href="/" className="text-purple-400 hover:text-purple-300">
            ← Back to gigs
          </Link>
        </p>
        <header className="mb-4 space-y-1">
          <h1 className="text-3xl font-bold text-gray-100">Bands</h1>
          <p className="text-sm text-gray-400">
            {bands.length} bands with upcoming gigs. Links come from MusicBrainz and
            Spotify; where none is known, a search link is shown instead.
          </p>
        </header>
        <BandDirectory bands={bands} />
        <SiteFooter />
      </div>
    </main>
  );
}
