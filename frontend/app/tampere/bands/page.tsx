import type { Metadata } from "next";
import BandsPage from "../../bands/BandsPage";

export const metadata: Metadata = {
  title: "Bands in Tampere – Dark Suomi",
  description: "Bands with upcoming gigs in Tampere, with links to Spotify, Bandcamp, SoundCloud and more.",
};

export default function TampereBandsPage() {
  return <BandsPage city="tampere" />;
}
