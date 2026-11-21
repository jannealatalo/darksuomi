import Link from "next/link";
import { getBands } from "../../lib/bands";
import { CITIES, type CityKey } from "../../lib/cities";
import SiteFooter from "../SiteFooter";
import BandDirectory from "./BandDirectory";

/** One city's band directory: /bands (Helsinki), /tampere/bands, /oulu/bands. */
export default function BandsPage({ city }: { city: CityKey }) {
  const bands = getBands(city);
  const gigsPath = CITIES.find((c) => c.key === city)?.path ?? "/";
  const cityName = city === "helsinki" ? "" : ` in ${CITIES.find((c) => c.key === city)?.name}`;
  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6">
          <Link href={gigsPath} className="text-purple-400 hover:text-purple-300">
            ← Back to gigs
          </Link>
        </p>
        <header className="mb-4 space-y-1">
          <h1 className="text-3xl font-bold text-gray-100">Bands{cityName}</h1>
          <p className="text-sm text-gray-400">
            {bands.length} bands with upcoming gigs{cityName}. Links come from MusicBrainz
            and Spotify; where none is known, a search link is shown instead.
          </p>
        </header>
        <BandDirectory bands={bands} gigsPath={gigsPath} />
        <SiteFooter />
      </div>
    </main>
  );
}
