import type { Metadata } from "next";
import Link from "next/link";
import { getBands } from "../../lib/bands";
import { CITIES } from "../../lib/cities";
import SiteFooter from "../SiteFooter";
import BandDirectory from "./BandDirectory";

export const metadata: Metadata = {
  title: "Bands – Dark Suomi",
  description:
    "Bands with upcoming gigs in Helsinki, Espoo, Tampere, Oulu and Turku, with links to Spotify, Bandcamp, SoundCloud, Tidal, Discogs and more.",
};

/** One band directory for every city's gigs. */
export default function BandsPage() {
  const bands = getBands();
  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6 text-sm">
          <span className="text-gray-500">Back to gigs: </span>
          {CITIES.map((c, i) => (
            <span key={c.key}>
              {i > 0 && <span className="text-gray-600"> · </span>}
              <Link href={c.path} className="text-purple-400 hover:text-purple-300">
                {c.key === "helsinki" ? "Helsinki & Espoo" : c.name}
              </Link>
            </span>
          ))}
        </p>
        <header className="mb-4 space-y-1">
          <h1 className="text-3xl font-bold text-gray-100">Bands</h1>
          <p className="text-sm text-gray-400">
            {bands.length} bands with upcoming gigs in Helsinki, Espoo, Tampere, Oulu and Turku. Links
            come from MusicBrainz and Spotify; where none is known, a search link is shown
            instead.
          </p>
        </header>
        <BandDirectory bands={bands} />
        <SiteFooter />
      </div>
    </main>
  );
}
