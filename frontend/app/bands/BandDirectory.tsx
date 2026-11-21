"use client";

import Link from "next/link";
import { useState } from "react";
import {
  LINK_LABELS,
  METAL_ARCHIVES_SEARCH,
  SEARCH_LINKS,
  bandSlug,
  isMetal,
  letterOf,
  type Band,
} from "../../lib/bands";

function shortDate(iso: string) {
  const [, m, d] = iso.slice(0, 10).split("-").map(Number);
  return `${d}.${m}.`;
}

/** Searchable A–Z list of bands with their links and upcoming gigs. */
export default function BandDirectory({
  bands,
  gigsPath = "/",
}: {
  bands: Band[];
  /** The city's gig list, for the gig date links: "/", "/tampere"… */
  gigsPath?: string;
}) {
  const [query, setQuery] = useState("");
  const q = query.trim().toLocaleLowerCase("fi");
  const shown = q
    ? bands.filter(
        (b) =>
          b.name.toLocaleLowerCase("fi").includes(q) ||
          b.genres.some((g) => g.includes(q))
      )
    : bands;

  const letters = [...new Set(bands.map((b) => letterOf(b.name)))];
  const groups = new Map<string, Band[]>();
  for (const band of shown) {
    const letter = letterOf(band.name);
    groups.set(letter, [...(groups.get(letter) ?? []), band]);
  }

  return (
    <div>
      <div className="sticky top-0 z-10 bg-black/95 py-3 space-y-2 border-b border-gray-800">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search bands or genres…"
          aria-label="Search bands or genres"
          className="w-full rounded bg-gray-900 border border-gray-700 px-3 py-2 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-purple-500"
        />
        {!q && (
          <nav aria-label="Jump to letter" className="flex flex-wrap gap-x-2 gap-y-1 text-sm">
            {letters.map((l) => (
              <a key={l} href={`#letter-${l}`} className="text-purple-400 hover:text-purple-300">
                {l}
              </a>
            ))}
          </nav>
        )}
      </div>

      {shown.length === 0 && <p className="text-gray-400 mt-6">No bands match.</p>}

      {[...groups.entries()].map(([letter, list]) => (
        <section key={letter} id={`letter-${letter}`} className="scroll-mt-28">
          <h2 className="text-xs uppercase tracking-[0.2em] text-purple-400 border-b border-gray-800 pb-2 mt-8 mb-2">
            {letter}
          </h2>
          <ul className="divide-y divide-gray-900">
            {list.map((band) => (
              <BandRow key={band.name} band={band} gigsPath={gigsPath} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function BandRow({ band, gigsPath }: { band: Band; gigsPath: string }) {
  const confirmed = LINK_LABELS.filter(([kind]) => band.links[kind]);
  const q = encodeURIComponent(band.name);
  const searches: [string, string, (q: string) => string][] = SEARCH_LINKS.filter(
    ([kind]) => !band.links[kind]
  );
  if (!band.links.metalArchives && isMetal(band.genres)) {
    searches.push(["metalArchives", "Metal Archives", METAL_ARCHIVES_SEARCH]);
  }

  return (
    <li id={`band-${bandSlug(band.name)}`} className="py-3 scroll-mt-32">
      <div className="flex flex-wrap items-baseline gap-x-3">
        <h3 className="text-lg font-semibold text-gray-100">{band.name}</h3>
        {band.genres.length > 0 && (
          <span className="text-xs text-gray-400">{band.genres.join(" · ")}</span>
        )}
      </div>

      <p className="text-sm text-gray-300">
        {band.gigs.map((gig, i) => (
          <span key={gig.id}>
            {i > 0 && <span className="text-gray-600"> · </span>}
            <Link href={`${gigsPath}#gig-${gig.id}`} className="hover:text-white">
              <span className="font-semibold text-gray-100">{shortDate(gig.date)}</span>{" "}
              {gig.venue}
            </Link>
          </span>
        ))}
      </p>

      <p className="text-sm mt-1">
        {confirmed.map(([kind, label], i) => (
          <span key={kind}>
            {i > 0 && <span className="text-gray-600"> · </span>}
            <a
              href={band.links[kind]}
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300"
            >
              {label}
            </a>
          </span>
        ))}
        {searches.length > 0 && (
          <span className="text-xs text-gray-500">
            {confirmed.length > 0 && <span className="text-gray-600"> · </span>}
            search:{" "}
            {searches.map(([kind, label, url], i) => (
              <span key={kind}>
                {i > 0 && ", "}
                <a
                  href={url(q)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-gray-200 underline decoration-gray-700"
                >
                  {label}
                </a>
              </span>
            ))}
          </span>
        )}
      </p>
    </li>
  );
}
