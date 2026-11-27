"use client";

import Link from "next/link";
import { releaseDate } from "../../lib/releaseDate";
import type { Release } from "../../lib/releases";

/** Coming soon + Out now. */
export default function ReleaseList({ upcoming, recent }: { upcoming: Release[]; recent: Release[] }) {
  return (
    <div>
      <Section title="Coming soon" releases={upcoming} empty="Nothing announced right now." />
      <Section title="Out now" releases={recent} empty="No new releases lately." />
    </div>
  );
}

function Section({ title, releases, empty }: { title: string; releases: Release[]; empty: string }) {
  return (
    <section>
      <h2 className="text-xs uppercase tracking-[0.2em] text-purple-400 border-b border-gray-800 pb-2 mt-8 mb-2">
        {title}
      </h2>
      {releases.length === 0 && <p className="text-gray-500 text-sm py-3">{empty}</p>}
      <ul className="divide-y divide-gray-900">
        {releases.map((r) => (
          <ReleaseRow key={r.id} release={r} />
        ))}
      </ul>
    </section>
  );
}

function ReleaseRow({ release: r }: { release: Release }) {
  return (
    <li className="py-3 flex gap-3">
      {r.cover ? (
        // eslint-disable-next-line @next/next/no-img-element -- Spotify's CDN, already sized
        <img src={r.cover} alt="" width={64} height={64} loading="lazy" className="w-16 h-16 rounded shrink-0 object-cover" />
      ) : (
        <div className="w-16 h-16 rounded shrink-0 bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-600 text-xl" aria-hidden="true">
          ♪
        </div>
      )}
      <div className="min-w-0">
        <p className="text-sm">
          <span className="font-semibold text-gray-100">{releaseDate(r.date)}</span>{" "}
          <span className="text-xs text-gray-500 uppercase tracking-wide">{r.type}</span>
        </p>
        <p className="text-gray-100">
          <Link href={r.bandHref} className="font-semibold hover:text-white hover:underline underline-offset-4">
            {r.band}
          </Link>
          <span className="text-gray-500"> – </span>
          <span className="italic">{r.title}</span>
        </p>
        {r.genres.length > 0 && <p className="text-xs text-gray-400">{r.genres.slice(0, 3).join(" · ")}</p>}
        <p className="text-sm mt-0.5">
          {r.links.map(([label, url], i) => (
            <span key={label}>
              {i > 0 && <span className="text-gray-600"> · </span>}
              <a href={url} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300">
                {label}
              </a>
            </span>
          ))}
          {r.links.length === 0 && r.musicbrainz && (
            <a href={r.musicbrainz} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-400 hover:text-gray-200 underline decoration-gray-700">
              Details on MusicBrainz
            </a>
          )}
        </p>
      </div>
    </li>
  );
}
