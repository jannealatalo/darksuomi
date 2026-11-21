"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { LINK_LABELS } from "../lib/bandLinks";
import type { ExpectedSetlist } from "../lib/setlists";
import type { GigBand } from "../types/events";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("fi-FI", { timeZone: "Europe/Helsinki" });
}

/**
 * "Setlist stuff" and "Band info" for one event, both collapsed by default:
 * the expected setlist(s) and the links to each act's latest show
 * (`latestShows`); and each band's links from the band directory (`bands`).
 */
export default function ExpectedSetlists({
  setlists,
  special,
  playlistUrl,
  latestShows,
  bands = [],
}: {
  setlists: ExpectedSetlist[];
  special: boolean;
  playlistUrl: string | null;
  latestShows?: ReactNode;
  bands?: GigBand[];
}) {
  const [open, setOpen] = useState(false);
  const [bandsOpen, setBandsOpen] = useState(false);
  if (setlists.length === 0 && !latestShows && !playlistUrl && bands.length === 0) return null;
  const hasContent = setlists.length > 0 || !!latestShows;
  const showArtistNames = setlists.length > 1;

  return (
    <div className="mt-1 text-sm">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {hasContent && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            aria-expanded={open}
            className="inline-flex items-center gap-1.5 text-gray-300 hover:text-white"
          >
            <span aria-hidden="true" className={`text-xs transition-transform ${open ? "rotate-90" : ""}`}>
              ▶
            </span>
            Setlist stuff
          </button>
        )}

        {bands.length > 0 && (
          <button
            type="button"
            onClick={() => setBandsOpen(!bandsOpen)}
            aria-expanded={bandsOpen}
            className="inline-flex items-center gap-1.5 text-gray-300 hover:text-white"
          >
            <span aria-hidden="true" className={`text-xs transition-transform ${bandsOpen ? "rotate-90" : ""}`}>
              ▶
            </span>
            Band info
          </button>
        )}

        {playlistUrl && (
          <a
            href={playlistUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-green-500 hover:text-green-400"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z" />
            </svg>
            Listen on Spotify
          </a>
        )}
      </div>

      {bandsOpen && <BandInfo bands={bands} />}

      {open && (
      <div className="mt-2 pl-4 border-l border-gray-800 space-y-4">
        {setlists.length > 0 && (
          // Heading and special-show note in one block, closer to the songs
          // (mb-2 overrides space-y-4's gap). A negative margin on the heading
          // used to pull the note up over it.
          <div className="space-y-1 mb-2">
            <p className="text-xs uppercase tracking-wide text-gray-500">Expected setlist</p>
            {special && (
              <p className="text-xs text-amber-400">
                Special show: the setlist will likely differ from their usual set.
              </p>
            )}
          </div>
        )}

        {setlists.map((s) => {
          const main = s.songs.filter((song) => !song.encore);
          const encore = s.songs.filter((song) => song.encore);
          return (
            <div key={s.artist}>
              {showArtistNames && (
                <p className="font-semibold text-gray-300 mb-1">{s.artist}</p>
              )}
              <ol className="list-decimal list-inside text-gray-300 space-y-0.5">
                {main.map((song) => (
                  <Song key={song.name} song={song} />
                ))}
              </ol>
              {encore.length > 0 && (
                <>
                  <p className="text-xs uppercase tracking-wide text-gray-500 mt-2 mb-0.5">
                    Encore
                  </p>
                  <ol
                    start={main.length + 1}
                    className="list-decimal list-inside text-gray-300 space-y-0.5"
                  >
                    {encore.map((song) => (
                      <Song key={song.name} song={song} />
                    ))}
                  </ol>
                </>
              )}
              <p className="text-xs text-gray-500 mt-2">
                Based on {s.basedOn} shows, {formatDate(s.from)}–{formatDate(s.to)}
                {s.url && (
                  <>
                    {" · "}
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300"
                    >
                      setlist.fm
                    </a>
                  </>
                )}
              </p>
            </div>
          );
        })}

        {latestShows && (
          <div>
            {setlists.length > 0 && (
              <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Latest shows</p>
            )}
            {latestShows}
          </div>
        )}
      </div>
      )}
    </div>
  );
}

function Song({ song }: { song: ExpectedSetlist["songs"][number] }) {
  return (
    <li>
      {song.name}
      {song.cover && (
        <span className="text-gray-500"> ({song.cover} cover)</span>
      )}
      {song.playedPct < 50 && (
        <span className="text-gray-600 text-xs"> · sometimes</span>
      )}
    </li>
  );
}

/** Each band's links (Spotify, Bandcamp, homepage…) and its directory entry. */
function BandInfo({ bands }: { bands: GigBand[] }) {
  return (
    <ul className="mt-2 pl-4 border-l border-gray-800 space-y-2">
      {bands.map((band) => {
        const links = LINK_LABELS.filter(([kind]) => band.links[kind]);
        return (
          <li key={band.slug}>
            <span className="font-semibold text-gray-200">{band.name}</span>
            <span className="text-gray-600"> · </span>
            {links.length === 0 && <span className="text-gray-500">no links found · </span>}
            {links.map(([kind, label]) => (
              <span key={kind}>
                <a
                  href={band.links[kind]}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300"
                >
                  {label}
                </a>
                <span className="text-gray-600"> · </span>
              </span>
            ))}
            <Link
              href={`/bands#band-${band.slug}`}
              className="text-gray-400 hover:text-gray-200 whitespace-nowrap"
            >
              in directory →
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
