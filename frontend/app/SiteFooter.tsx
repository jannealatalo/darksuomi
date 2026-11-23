import Link from "next/link";
import meta from "../data/meta.json";
import VisitCounter from "./VisitCounter";

export const CONTACT_EMAIL = "jamesturhapuro@gmail.com";

// The year of the last nightly scrape: stable during prerendering (unlike
// new Date()) and current, since the site is rebuilt every night.
const YEAR = meta.lastScraped.slice(0, 4);

/** Owner, contact, privacy link and a short disclaimer. */
export default function SiteFooter() {
  return (
    <footer className="mt-16 pt-6 border-t border-gray-800 text-xs text-gray-400 space-y-2">
      <p>
        © {YEAR} Dark Suomi
        {" · "}
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="text-purple-400 hover:text-purple-300"
        >
          {CONTACT_EMAIL}
        </a>
        {" · "}
        <Link href="/privacy" className="text-purple-400 hover:text-purple-300">
          Privacy
        </Link>
        <VisitCounter />
      </p>
      <p className="text-gray-300">
        Like Dark Suomi? Support the scene: go to gigs, buy tickets and merch
        straight from the bands and venues.
      </p>
      <p className="text-gray-500">
        Gig information is collected automatically from venue websites and may
        contain errors — always check the details from the venue or ticket seller.
        Dark Suomi is not affiliated with the venues, ticket sellers, Spotify,
        Last.fm, MusicBrainz or setlist.fm.
      </p>
    </footer>
  );
}
