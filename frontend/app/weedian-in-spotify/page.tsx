import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { getWeedianCompilations } from "../../lib/weedian";
import SiteFooter from "../SiteFooter";

export const metadata: Metadata = {
  title: "Weedian in Spotify – Dark Suomi",
  description:
    "Weedian's monthly stoner, doom and sludge compilations from Bandcamp as Spotify playlists.",
};

const linkClass = "text-purple-400 hover:text-purple-300";

export default async function WeedianPage() {
  const comps = await getWeedianCompilations();

  return (
    <main className="min-h-screen bg-black text-gray-300">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <p className="mb-6 text-sm">
          <Link href="/" className={linkClass}>
            ← Back to gigs
          </Link>
        </p>

        <header className="mb-8 space-y-3 leading-relaxed">
          <h1 className="text-3xl font-bold text-gray-100">Weedian in Spotify</h1>
          <p>
            <a
              href="https://weedian420.bandcamp.com/music"
              target="_blank"
              rel="noopener noreferrer"
              className={linkClass}
            >
              Weedian
            </a>{" "}
            puts together a compilation of the best new stoner, doom, sludge and
            psych releases every month on Bandcamp. Here they are as Spotify
            playlists, in the same order, updated weekly.
          </p>
          <p className="text-sm text-gray-400">
            Some bands are only on Bandcamp, so a few songs are always missing
            from the playlists. Found something you like? Buy it on Bandcamp.
          </p>
        </header>

        <ul className="grid gap-6 sm:grid-cols-2">
          {comps.map((c) => (
            <li
              key={c.bandcampUrl}
              className="flex gap-4 rounded-lg border border-gray-800 bg-gray-950 p-4"
            >
              {c.coverUrl && (
                <a href={c.playlistUrl ?? c.bandcampUrl} target="_blank" rel="noopener noreferrer">
                  <Image
                    src={c.coverUrl}
                    alt={`${c.title} cover`}
                    width={112}
                    height={112}
                    unoptimized
                    className="h-28 w-28 shrink-0 rounded object-cover"
                  />
                </a>
              )}
              <div className="min-w-0 space-y-2">
                <h2 className="font-semibold text-gray-100 leading-snug">{c.title}</h2>
                <p className="text-xs text-gray-500">
                  {c.found} of {c.total} songs on Spotify
                </p>
                <p className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
                  {c.playlistUrl && (
                    <a
                      href={c.playlistUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-400 hover:text-green-300"
                    >
                      Spotify playlist
                    </a>
                  )}
                  <a
                    href={c.bandcampUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={linkClass}
                  >
                    Bandcamp
                  </a>
                </p>
                {c.missing.length > 0 && (
                  <details className="text-xs text-gray-400">
                    <summary className="cursor-pointer text-gray-500 hover:text-gray-300">
                      Only on Bandcamp ({c.missing.length})
                    </summary>
                    <ul className="mt-1 space-y-0.5">
                      {c.missing.map((m) => (
                        <li key={m}>{m}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            </li>
          ))}
        </ul>

        <p className="mt-8 text-xs text-gray-500">
          The playlists are made automatically by matching artist and song names,
          so a wrong match can slip in now and then. Dark Suomi is not affiliated
          with Weedian.
        </p>

        <SiteFooter />
      </div>
    </main>
  );
}
