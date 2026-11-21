import type { Metadata } from "next";
import BandsPage from "../../bands/BandsPage";

export const metadata: Metadata = {
  title: "Bands in Oulu – Dark Suomi",
  description: "Bands with upcoming gigs in Oulu, with links to Spotify, Bandcamp, SoundCloud and more.",
};

export default function OuluBandsPage() {
  return <BandsPage city="oulu" />;
}
