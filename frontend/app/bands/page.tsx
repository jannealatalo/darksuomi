import type { Metadata } from "next";
import BandsPage from "./BandsPage";

export const metadata: Metadata = {
  title: "Bands – Dark Suomi",
  description:
    "Bands with upcoming gigs in Finland, with links to Spotify, Bandcamp, SoundCloud, Tidal, Discogs and more.",
};

export default function HelsinkiBandsPage() {
  return <BandsPage city="helsinki" />;
}
