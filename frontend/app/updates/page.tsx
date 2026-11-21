import type { Metadata } from "next";
import Link from "next/link";
import { CITIES } from "../../lib/cities";
import { scrapeDay } from "../../lib/events";
import { getUpdates, type NewGig } from "../../lib/updates";
import SiteFooter from "../SiteFooter";
import SubscribeForm from "./SubscribeForm";

export const metadata: Metadata = {
  title: "Daily updates – Dark Suomi",
  description: "New gigs found by Dark Suomi's nightly scrape, day by day.",
};

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function dayLabel(iso: string, withYear = false) {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  const weekday = WEEKDAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()];
  return `${weekday} ${d}.${m}.${withYear ? y : ""}`;
}

/** Daily updates log: which new gigs each nightly scrape found. */
export default function UpdatesPage() {
  const days = getUpdates();
  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6">
          <Link href="/" className="text-purple-400 hover:text-purple-300">
            ← Upcoming gigs
          </Link>
        </p>
        <header className="mb-6 space-y-2">
          <h1 className="text-3xl font-bold text-gray-100">Daily updates</h1>
          <p className="text-sm text-gray-400 max-w-2xl">
            New gigs found by the nightly scrape, newest day first. Only gigs shown
            with the default genres are listed; the rest are counted. The last four
            months are kept.
          </p>
          <SubscribeForm />
        </header>

        {days.length === 0 && <p className="text-gray-400">No new gigs logged yet.</p>}

        {days.map((day) => {
          const hidden = Object.values(day.hidden).reduce((a, n) => a + (n ?? 0), 0);
          return (
            <section key={day.day} className="mt-8">
              <h2 className="text-xs uppercase tracking-[0.2em] text-purple-400 border-b border-gray-800 pb-2 mb-3">
                {dayLabel(day.day, true)} · {day.gigs.length} new
              </h2>
              {CITIES.map((city) => {
                const gigs = day.gigs.filter((g) => g.city === city.key);
                if (gigs.length === 0) return null;
                return (
                  <div key={city.key} className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-400 mb-1">
                      {city.key === "helsinki" ? "Helsinki & Espoo" : city.name}
                    </h3>
                    <ul className="space-y-1.5">
                      {gigs.map((gig) => (
                        <GigRow key={gig.id} gig={gig} path={city.path} />
                      ))}
                    </ul>
                  </div>
                );
              })}
              {hidden > 0 && (
                <p className="text-xs text-gray-500">
                  + {hidden} more not shown by the default genre filter
                </p>
              )}
            </section>
          );
        })}

        <SiteFooter />
      </div>
    </main>
  );
}

function GigRow({ gig, path }: { gig: NewGig; path: string }) {
  const upcoming = gig.date.slice(0, 10) >= scrapeDay;
  const where = gig.place && gig.place !== "Helsinki" ? `${gig.venue}, ${gig.place}` : gig.venue;
  const title = <span className="font-semibold text-gray-100">{gig.artist}</span>;
  return (
    <li className={`text-sm ${upcoming ? "" : "opacity-50"}`}>
      <span className="text-gray-400 tabular-nums">{dayLabel(gig.date)}</span>{" "}
      {upcoming ? (
        <Link href={`${path}#gig-${gig.id}`} className="hover:text-white">
          {title}
        </Link>
      ) : (
        title
      )}
      <span className="text-gray-400"> · {where}</span>
      {gig.status && (
        <span className="ml-2 text-xs font-semibold uppercase text-red-400">{gig.status}</span>
      )}
      {gig.genres.length > 0 && (
        <span className="block text-xs text-gray-500 sm:inline sm:ml-2">
          {gig.genres.join(" · ")}
        </span>
      )}
    </li>
  );
}
