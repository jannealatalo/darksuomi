"use client";

import Image from "next/image";
import Link from "next/link";
import {
  eventArtistNames,
  excludedGenres,
  GENRE_FILTER_NAMES,
  isExcludedByGenre,
  matchesGenreFilter,
  lastScraped,
} from "../lib/events";
import EventList from "./EventList";
import SiteFooter from "./SiteFooter";
import {
  MEDIA_SITES,
  MERCH_SITES,
  RESALE_SITES,
  TICKET_SITES,
  VENUE_LINKS,
  type SiteLink,
} from "../lib/links";
import type { Event } from "../types/events";
import { signIn, signOut, useSession } from "next-auth/react";
import { useSpotifyFollowedArtists } from "../lib/useSpotifyFollowedArtists";
import { useEffect, useState } from "react";
import { TAGLINES } from "../lib/jokes";
import { CITIES, type CityKey } from "../lib/cities";
import { matchesSearch } from "../lib/search";
import SearchBox from "./SearchBox";

/**
 * The gig calendar of one city: Helsinki on the front page, and the
 * Tampere and Oulu sites under /tampere and /oulu.
 */
export default function GigCalendar({ events, city }: { events: Event[]; city: CityKey }) {
  const hiddenByGenreCount = events.filter(isExcludedByGenre).length;
  const allVenues = [...new Set(events.map((e) => e.venue))].sort((a, b) =>
    a.localeCompare(b, "fi")
  );
  const isMain = city === "helsinki";
  const { data: session } = useSession();
  const { followedArtists, error: spotifyError } = useSpotifyFollowedArtists();
  const spotifyProblem =
    session?.error === "RefreshTokenError"
      ? "Your Spotify login has expired. Please log in again."
      : spotifyError
        ? "Couldn't load your Spotify artists. Try logging in again."
        : null;
  // The page is pre-rendered, so the random tagline is picked in the
  // browser after load (null until then, keeping server and client equal).
  const [tagline, setTagline] = useState<string | null>(null);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one random pick per visit
    setTagline(TAGLINES[Math.floor(Math.random() * TAGLINES.length)]);
  }, []);
  const [showOnlyFollowed, setShowOnlyFollowed] = useState(false);
  const [showAllGenres, setShowAllGenres] = useState(false);
  const [hiddenVenues, setHiddenVenues] = useState<Set<string>>(new Set());
  // Main genres the visitor unticked; empty = every gig is shown.
  const [hiddenGenres, setHiddenGenres] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");

  const isFollowedEvent = (event: Event) =>
    eventArtistNames(event).some((name) => followedArtists.has(name));

  // Genre and follow filters first; venue counts are based on this list.
  const genreFiltered = events.filter(
    (event) =>
      (showAllGenres || !isExcludedByGenre(event)) &&
      (!showOnlyFollowed || isFollowedEvent(event))
  );
  // All ticked shows everything; otherwise a gig needs a ticked genre.
  const inPickedGenres = (e: Event) =>
    hiddenGenres.size === 0 ||
    GENRE_FILTER_NAMES.some((g) => !hiddenGenres.has(g) && matchesGenreFilter(e, g));
  const inShownVenues = (e: Event) => !hiddenVenues.has(e.venue);

  // Each filter's counts reflect the other filter's current choice.
  const venueCounts = new Map<string, number>();
  for (const e of genreFiltered.filter(inPickedGenres)) {
    venueCounts.set(e.venue, (venueCounts.get(e.venue) ?? 0) + 1);
  }
  const genreCounts = new Map<string, number>();
  for (const e of genreFiltered.filter(inShownVenues)) {
    for (const g of GENRE_FILTER_NAMES) {
      if (matchesGenreFilter(e, g)) genreCounts.set(g, (genreCounts.get(g) ?? 0) + 1);
    }
  }
  const filteredEvents = genreFiltered.filter(
    (e) => inShownVenues(e) && inPickedGenres(e) && matchesSearch(e, search)
  );
  const searching = search.trim() !== "";
  // Matches the filters hide, so a search for a hidden band isn't a dead end.
  const hiddenMatches = searching
    ? events.filter((e) => matchesSearch(e, search)).length - filteredEvents.length
    : 0;
  const clearFilters = () => {
    setHiddenGenres(new Set());
    setHiddenVenues(new Set());
    setShowAllGenres(true);
    setShowOnlyFollowed(false);
  };

  const toggleGenre = (genre: string) =>
    setHiddenGenres((prev) => {
      const next = new Set(prev);
      if (next.has(genre)) next.delete(genre);
      else next.add(genre);
      return next;
    });

  // Header genre names: show only that genre and jump to the list.
  const showOnlyGenre = (genre: string) => {
    setHiddenGenres(new Set(GENRE_FILTER_NAMES.filter((g) => g !== genre)));
    document.getElementById("gig-filters")?.scrollIntoView({ behavior: "smooth" });
  };

  const toggleVenue = (venue: string) =>
    setHiddenVenues((prev) => {
      const next = new Set(prev);
      if (next.has(venue)) next.delete(venue);
      else next.add(venue);
      return next;
    });

  const hasFollowedArtists = followedArtists.size > 0;

  return (
    <main className="min-h-screen bg-black text-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-6 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-5">
            {/* shrink-0: long header text must not squeeze the square logo. */}
            <h1 className="shrink-0">
              {/* On the city sites the logo leads back to the main (Helsinki) site. */}
              <Link href="/" aria-label={isMain ? undefined : "Dark Suomi Helsinki"}>
                <Image
                  src="/logo.webp"
                  alt={isMain ? "Dark Suomi" : `Dark Suomi ${CITIES.find((c) => c.key === city)?.name}`}
                  width={512}
                  height={512}
                  preload
                  sizes="(min-width: 640px) 144px, 112px"
                  className="w-28 h-28 sm:w-36 sm:h-36"
                />
              </Link>
            </h1>
            <p className="text-gray-400 text-sm sm:text-base leading-relaxed">
              {/* What the site is, in one breath. */}
              <span className="block text-gray-200">
                List of dark and loud gigs in{" "}
                {isMain ? "Helsinki-Espoo" : CITIES.find((c) => c.key === city)?.name} area from
                the main venues on one page.
              </span>
              {/* Fixed height, so the page doesn't jump when the line appears. */}
              <span
                className={`block mb-2 min-h-[1.5em] text-xs sm:text-sm text-gray-500 italic transition-opacity duration-500 ${
                  tagline ? "opacity-100" : "opacity-0"
                }`}
              >
                {tagline ?? " "}
              </span>
              {[GENRE_FILTER_NAMES.slice(0, 6), GENRE_FILTER_NAMES.slice(6)].map((row) => (
                <span key={row[0]} className="block">
                  {row.map((genre, i) => (
                    <span key={genre}>
                      {i > 0 && " • "}
                      <button
                        type="button"
                        onClick={() => showOnlyGenre(genre)}
                        title={`Show only ${genre} gigs`}
                        className={`hover:text-white hover:underline underline-offset-4 ${
                          hiddenGenres.size > 0 && !hiddenGenres.has(genre) ? "text-white" : ""
                        }`}
                      >
                        {genre}
                      </button>
                    </span>
                  ))}
                </span>
              ))}
              {isMain ? (
                <>
                  <span className="flex flex-wrap gap-x-4 mt-2">
                    <Link href="/bands" className="text-purple-400 hover:text-purple-300">
                      Bands A–Z: Spotify, Bandcamp, SoundCloud… →
                    </Link>
                    <Link href="/past" className="text-purple-400 hover:text-purple-300">
                      Past gigs & setlists →
                    </Link>
                  </span>
                  <span className="block mt-1 text-xs text-gray-500">
                    Helsinki & Espoo · also:{" "}
                    {CITIES.filter((c) => c.key !== "helsinki").map((c, i) => (
                      <span key={c.key}>
                        {i > 0 && " · "}
                        <Link href={c.path} className="text-purple-400 hover:text-purple-300">
                          {c.name} →
                        </Link>
                      </span>
                    ))}
                  </span>
                </>
              ) : (
                <span className="block mt-2">
                  <span className="text-gray-200 font-semibold">
                    {CITIES.find((c) => c.key === city)?.name}
                  </span>{" "}
                  <span className="text-xs text-gray-500">·</span>{" "}
                  {CITIES.filter((c) => c.key !== city).map((c, i) => (
                    <span key={c.key} className="text-xs">
                      {i > 0 && " · "}
                      <Link href={c.path} className="text-purple-400 hover:text-purple-300">
                        {c.name}
                      </Link>
                    </span>
                  ))}
                  <span className="block mt-2">
                    <Link
                      href={`${CITIES.find((c) => c.key === city)?.path}/bands`}
                      className="text-purple-400 hover:text-purple-300"
                    >
                      Bands A–Z: Spotify, Bandcamp, SoundCloud… →
                    </Link>
                  </span>
                </span>
              )}
            </p>
          </div>

          <div className="flex flex-col items-end gap-2 text-right self-end md:self-auto md:max-w-xs md:shrink-0">
            {session ? (
              <div>
                <p className="text-sm text-gray-400 mb-2">
                  Logged in as {session.user?.name || session.user?.email}
                </p>
                <button
                  onClick={() => signOut()}
                  className="px-2.5 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-end gap-1">
              <button
                onClick={() => signIn("spotify")}
                className="px-2.5 py-1 bg-green-700 hover:bg-green-600 rounded flex items-center gap-1.5 text-xs"
              >
                <svg
                  className="w-3.5 h-3.5"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z" />
                </svg>
                Login with Spotify
              </button>
              <p className="text-xs text-gray-500">(by invite only)</p>
              </div>
            )}

            {session && spotifyProblem && (
              <p role="alert" className="text-xs text-red-400 max-w-56">
                {spotifyProblem}
              </p>
            )}

            <div className="text-xs text-gray-500 space-y-0.5">
              <p>
                Genres from{" "}
                <a
                  href="https://www.last.fm"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300"
                >
                  Last.fm
                </a>{" "}
                &amp;{" "}
                <a
                  href="https://musicbrainz.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300"
                >
                  MusicBrainz
                </a>
              </p>
              <p>
                Setlists from{" "}
                <a
                  href="https://www.setlist.fm"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300"
                >
                  setlist.fm
                </a>
              </p>
              <p>Last scraped {lastScraped}</p>
            </div>

            <nav
              aria-label="Venue and ticket sites"
              className="text-xs text-gray-500 space-y-0.5 border-t border-gray-800 pt-2"
            >
              <LinkRow
                label="Venues"
                links={allVenues
                  .filter((v) => VENUE_LINKS[v])
                  .map((v) => ({ name: v, url: VENUE_LINKS[v] }))}
              />
              <LinkRow label="Tickets" links={TICKET_SITES} />
              <LinkRow label="Resale" links={RESALE_SITES} />
              <LinkRow label="Merch" links={MERCH_SITES} />
              <LinkRow label="Media" links={MEDIA_SITES} />
            </nav>
          </div>
        </div>

        {session && hasFollowedArtists && (
          <div className="mb-6">
            <button
              onClick={() => setShowOnlyFollowed(!showOnlyFollowed)}
              className={`px-4 py-2 rounded flex items-center gap-2 transition ${
                showOnlyFollowed
                  ? "bg-green-600 hover:bg-green-700"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
            >
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z" />
              </svg>
              {showOnlyFollowed
                ? "Showing only followed artists"
                : "Show only artists I follow"}
            </button>
            <p className="text-xs text-gray-500 mt-2">
              {followedArtists.size} artists followed
            </p>
          </div>
        )}

        <fieldset id="gig-filters" className="mb-4 text-sm text-gray-400 scroll-mt-4">
          <legend className="mb-1.5 flex items-baseline gap-3">
            <span>Dark Suomi main genres</span>
            <button
              type="button"
              onClick={() => setHiddenGenres(new Set())}
              className="text-xs text-purple-400 hover:text-purple-300"
            >
              all
            </button>
            <button
              type="button"
              onClick={() => setHiddenGenres(new Set(GENRE_FILTER_NAMES))}
              className="text-xs text-purple-400 hover:text-purple-300"
            >
              none
            </button>
          </legend>
          <div className="flex flex-wrap gap-x-5 gap-y-1.5">
            {GENRE_FILTER_NAMES.map((genre) => (
              <label key={genre} className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!hiddenGenres.has(genre)}
                  onChange={() => toggleGenre(genre)}
                  className="accent-purple-600"
                />
                {genre}
                <span className="text-gray-600 tabular-nums">
                  {genreCounts.get(genre) ?? 0}
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        {hiddenByGenreCount > 0 && (
          <div className="mb-4 text-sm text-gray-400">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showAllGenres}
                onChange={(e) => setShowAllGenres(e.target.checked)}
                className="accent-purple-600"
              />
              Show hidden genres
            </label>
            {!showAllGenres && (
              <p className="text-xs text-gray-500 mt-1">
                {hiddenByGenreCount} events hidden: outside the main genres, or mainly{" "}
                {[...excludedGenres].join(", ")}
              </p>
            )}
          </div>
        )}

        {allVenues.length > 1 && (
          <fieldset className="mb-6 text-sm text-gray-400">
            <legend className="mb-1.5 flex items-baseline gap-3">
              <span>Venues</span>
              <button
                type="button"
                onClick={() => setHiddenVenues(new Set())}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                all
              </button>
              <button
                type="button"
                onClick={() => setHiddenVenues(new Set(allVenues))}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                none
              </button>
            </legend>
            <div className="flex flex-wrap gap-x-5 gap-y-1.5">
              {allVenues.map((venue) => (
                <label key={venue} className="inline-flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!hiddenVenues.has(venue)}
                    onChange={() => toggleVenue(venue)}
                    className="accent-purple-600"
                  />
                  {venue}
                  <span className="text-gray-600 tabular-nums">
                    {venueCounts.get(venue) ?? 0}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
        )}

        <hr className="border-gray-800 mb-6" />

        <div className="mb-6">
          <SearchBox value={search} onChange={setSearch} />
          {searching && (
            <p className="mt-2 text-xs text-gray-500">
              {filteredEvents.length} {filteredEvents.length === 1 ? "gig" : "gigs"} found
              {hiddenMatches > 0 && (
                <>
                  {" · "}
                  {hiddenMatches} more hidden by your filters{" "}
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="text-purple-400 hover:text-purple-300"
                  >
                    show them
                  </button>
                </>
              )}
            </p>
          )}
        </div>

        {showOnlyFollowed && (
          <p className="text-sm text-green-500 mb-4">Showing only artists you follow</p>
        )}

        {filteredEvents.length === 0 ? (
          <p className="text-gray-400">
            {searching
              ? "Nothing found. Maybe they broke up. Maybe they never existed."
              : showOnlyFollowed
                ? "No upcoming events for artists you follow"
                : "No upcoming events"}
          </p>
        ) : (
          <EventList events={filteredEvents} isFollowed={isFollowedEvent} jokes={!searching} />
        )}

        <SiteFooter />
      </div>
    </main>
  );
}

function LinkRow({ label, links }: { label: string; links: SiteLink[] }) {
  if (links.length === 0) return null;
  return (
    <p>
      {label}:{" "}
      {links.map((link, i) => (
        <span key={link.url}>
          {i > 0 && " · "}
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-purple-400 hover:text-purple-300"
          >
            {link.name}
          </a>
        </span>
      ))}
    </p>
  );
}
