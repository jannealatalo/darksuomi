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
import { recommendedArtists } from "../lib/recommended";
import { useLastfmArtists } from "../lib/useLastfmArtists";
import LastfmBox from "./LastfmBox";
import { useEffect, useState } from "react";
import { TAGLINES } from "../lib/jokes";
import { useToday } from "../lib/today";
import { InstallButton } from "./AppShell";
import { CITIES, type CityKey } from "../lib/cities";
import { matchesSearch } from "../lib/search";
import SearchBox from "./SearchBox";

/**
 * The gig calendar of one city: Helsinki on the front page, and the
 * Tampere and Oulu sites under /tampere and /oulu.
 */
// Header buttons, styled alike so they read as links.
const NAV_BUTTON =
  "inline-flex items-center rounded px-2.5 py-1 text-xs font-semibold text-purple-100 " +
  "bg-purple-900/60 border border-purple-700 hover:bg-purple-700 hover:text-white transition-colors";
const CITY_BUTTON =
  "inline-flex items-center rounded px-2 py-0.5 border border-gray-700 text-gray-300 " +
  "hover:border-purple-500 hover:text-white transition-colors";
const CITY_BUTTON_ACTIVE =
  "inline-flex items-center rounded px-2 py-0.5 border border-gray-500 bg-gray-800 text-white";

export default function GigCalendar({
  events: allEvents,
  city,
}: {
  events: Event[];
  city: CityKey;
}) {
  // Gigs from today on by the visitor's clock (the list was built at the
  // last scrape, which may have been yesterday).
  const today = useToday();
  const events = allEvents.filter((e) => e.date.slice(0, 10) >= today);
  const hiddenByGenreCount = events.filter(isExcludedByGenre).length;
  const allVenues = [...new Set(events.map((e) => e.venue))].sort((a, b) =>
    a.localeCompare(b, "fi")
  );
  const isMain = city === "helsinki";
  const { lastfmUser, setLastfmUser, lastfmArtists, lastfmLoading, lastfmError } =
    useLastfmArtists();
  // The page is pre-rendered, so the random tagline is picked in the
  // browser after load (null until then, keeping server and client equal).
  const [tagline, setTagline] = useState<string | null>(null);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one random pick per visit
    setTagline(TAGLINES[Math.floor(Math.random() * TAGLINES.length)]);
  }, []);
  // "Filter what DarkSuomi recommends" and the Last.fm "show only these".
  const [onlyRecommended, setOnlyRecommended] = useState(false);
  const [onlyLastfm, setOnlyLastfm] = useState(false);
  const [showAllGenres, setShowAllGenres] = useState(false);
  const [hiddenVenues, setHiddenVenues] = useState<Set<string>>(new Set());
  // Main genres the visitor unticked; empty = every gig is shown.
  const [hiddenGenres, setHiddenGenres] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [showOtherGenreList, setShowOtherGenreList] = useState(false);

  const isRecommendedEvent = (event: Event) =>
    eventArtistNames(event).some((name) => recommendedArtists.has(name));
  const isListenedEvent = (event: Event) =>
    eventArtistNames(event).some((name) => lastfmArtists.has(name));
  // Counted among the gigs the genre filter shows, like the list itself.
  const listenedGigCount = events.filter(
    (e) => (showAllGenres || !isExcludedByGenre(e)) && isListenedEvent(e)
  ).length;
  // Removing the Last.fm user also turns its filter off.
  const lastfmOn = onlyLastfm && lastfmArtists.size > 0;
  const recommendedOn = onlyRecommended && recommendedArtists.size > 0;
  // With both on, a gig needs to match either one.
  const inBandFilters = (event: Event) =>
    (!recommendedOn && !lastfmOn) ||
    (recommendedOn && isRecommendedEvent(event)) ||
    (lastfmOn && isListenedEvent(event));

  // Genre and follow filters first; venue counts are based on this list.
  const genreFiltered = events.filter(
    (event) =>
      (showAllGenres || !isExcludedByGenre(event)) &&
      inBandFilters(event)
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
    setOnlyRecommended(false);
    setOnlyLastfm(false);
  };

  const shownGenres = GENRE_FILTER_NAMES.length - hiddenGenres.size;
  const shownVenues = allVenues.length - allVenues.filter((v) => hiddenVenues.has(v)).length;
  const others = showAllGenres ? " + others" : "";
  const filterSummary =
    hiddenGenres.size === 0 && shownVenues === allVenues.length
      ? `(all genres${others} and venues)`
      : `(${
          hiddenGenres.size === 0
            ? "all genres"
            : shownGenres === 1
              ? GENRE_FILTER_NAMES.find((g) => !hiddenGenres.has(g))
              : `${shownGenres} genres`
        }${others}, ${
          shownVenues === allVenues.length
            ? "all venues"
            : shownVenues === 1
              ? allVenues.find((v) => !hiddenVenues.has(v))
              : `${shownVenues} venues`
        })`;

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
    setFiltersOpen(true);
    document.getElementById("gig-filters")?.scrollIntoView({ behavior: "smooth" });
  };

  const toggleVenue = (venue: string) =>
    setHiddenVenues((prev) => {
      const next = new Set(prev);
      if (next.has(venue)) next.delete(venue);
      else next.add(venue);
      return next;
    });


  const siteLinks = (
    <nav
      aria-label="Venue and ticket sites"
      className="text-xs text-gray-500 space-y-0.5 md:text-right"
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
  );

  return (
    <main className="min-h-screen bg-black text-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-6 mb-8">
          {/* Phones: logo and intro side by side, the rest full width below.
              From sm up: everything in a column beside the logo. */}
          <div className="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-3 sm:gap-x-5 sm:gap-y-1">
            {/* shrink-0: long header text must not squeeze the square logo. */}
            <h1 className="shrink-0 sm:row-span-2">
              {/* On the city sites the logo leads back to the main (Helsinki) site. */}
              <Link href="/" aria-label={isMain ? undefined : "Dark Suomi Helsinki"}>
                <Image
                  src="/logo.webp"
                  alt={isMain ? "Dark Suomi" : `Dark Suomi ${CITIES.find((c) => c.key === city)?.name}`}
                  width={512}
                  height={512}
                  preload
                  sizes="(min-width: 640px) 144px, 96px"
                  className="w-24 h-24 sm:w-36 sm:h-36"
                />
              </Link>
            </h1>
            <p className="text-gray-400 text-sm sm:text-base leading-snug sm:leading-relaxed sm:self-end">
              {/* What the site is, in one breath. */}
              <span className="block text-gray-200">
                List of dark and loud gigs in{" "}
                {isMain ? "Helsinki-Espoo" : CITIES.find((c) => c.key === city)?.name} area from
                the main venues on one page.
              </span>
              {/* Fixed height, so the page doesn't jump when the line appears. */}
              <span
                className={`block mt-1 min-h-[1.5em] text-xs sm:text-sm text-gray-500 italic transition-opacity duration-500 ${
                  tagline ? "opacity-100" : "opacity-0"
                }`}
              >
                {tagline ?? " "}
              </span>
            </p>
            <div className="col-span-2 sm:col-span-1 sm:col-start-2 self-start text-gray-400 text-sm sm:text-base leading-relaxed">
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
              {/* Site pages and the other cities, as buttons. */}
              <span className="flex flex-wrap gap-2 mt-3">
                <Link href="/bands" className={NAV_BUTTON} title="Links to Spotify, Bandcamp, SoundCloud…">
                  Band Directory
                </Link>
                <Link href="/past" className={NAV_BUTTON}>
                  Past gigs & setlists
                </Link>
                <Link href="/updates" className={NAV_BUTTON}>
                  Subscribe to daily updates
                </Link>
                <InstallButton className={NAV_BUTTON} />
              </span>
              <span className="flex flex-wrap items-center gap-1.5 mt-2 text-xs">
                <span className="text-gray-500 mr-0.5">City:</span>
                {CITIES.map((c) =>
                  c.key === city ? (
                    <span key={c.key} aria-current="page" className={CITY_BUTTON_ACTIVE}>
                      {c.key === "helsinki" ? "Helsinki & Espoo" : c.name}
                    </span>
                  ) : (
                    <Link key={c.key} href={c.path} className={CITY_BUTTON}>
                      {c.key === "helsinki" ? "Helsinki & Espoo" : c.name}
                    </Link>
                  )
                )}
              </span>
            </div>
          </div>

          {/* Top right on wide screens; on phones at the end of the page. */}
          <div className="hidden md:block md:max-w-xs md:shrink-0">{siteLinks}</div>
        </div>

        <div className="mb-6 space-y-3">
        {recommendedArtists.size > 0 && (
          <button
            type="button"
            onClick={() => setOnlyRecommended(!onlyRecommended)}
            aria-pressed={recommendedOn}
            className={`px-4 py-2 rounded flex items-center gap-2 transition ${
              recommendedOn
                ? "bg-purple-700 hover:bg-purple-600 text-white"
                : "bg-gray-800 hover:bg-gray-700"
            }`}
          >
            <span aria-hidden="true">★</span>
            Filter what DarkSuomi recommends
          </button>
        )}
          <LastfmBox
            user={lastfmUser}
            onUserChange={setLastfmUser}
            loading={lastfmLoading}
            error={lastfmError}
            artistCount={lastfmArtists.size}
            gigCount={listenedGigCount}
            onlyThese={lastfmOn}
            onOnlyTheseChange={setOnlyLastfm}
          />
        </div>

        {/* Genre and venue checkboxes, collapsed by default to keep the
            top of the page short on phones. */}
        <details
          id="gig-filters"
          open={filtersOpen}
          onToggle={(e) => setFiltersOpen(e.currentTarget.open)}
          className="mb-4 scroll-mt-4"
        >
          <summary className="cursor-pointer select-none text-sm text-gray-300 hover:text-white mb-2">
            Filter by genre and venue
            <span className="ml-2 text-xs text-gray-500">
              {filterSummary}
            </span>
          </summary>
          <fieldset className="mb-4 text-sm text-gray-400">
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
            {/* Gigs outside the main genres (pop, rap, jazz...): one more
                genre checkbox, with the list behind "which?". */}
            {hiddenByGenreCount > 0 && (
              <div className="mt-2.5 pt-2 border-t border-gray-800">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showAllGenres}
                    onChange={(e) => setShowAllGenres(e.target.checked)}
                    className="accent-purple-600"
                  />
                  Other genres too
                  <span className="text-gray-600 tabular-nums">{hiddenByGenreCount}</span>
                </label>
                <button
                  type="button"
                  onClick={() => setShowOtherGenreList(!showOtherGenreList)}
                  aria-expanded={showOtherGenreList}
                  className="ml-3 text-xs text-purple-400 hover:text-purple-300"
                >
                  which?
                </button>
                {showOtherGenreList && (
                  <p className="text-xs text-gray-500 mt-1">
                    Gigs outside the main genres, or mainly {[...excludedGenres].join(", ")}
                  </p>
                )}
              </div>
            )}
          </fieldset>

          {allVenues.length > 1 && (
            <fieldset className="mb-2 text-sm text-gray-400">
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
        </details>


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

        {(recommendedOn || lastfmOn) && (
          <p className="text-sm text-purple-300 mb-4">
            Showing only gigs{" "}
            {recommendedOn && lastfmOn
              ? "DarkSuomi recommends or by bands you listen to"
              : recommendedOn
                ? "DarkSuomi recommends"
                : "by bands you listen to"}
          </p>
        )}

        {filteredEvents.length === 0 ? (
          <p className="text-gray-400">
            {searching
              ? "Nothing found. Maybe they broke up. Maybe they never existed."
              : recommendedOn || lastfmOn
                ? "No upcoming gigs match these filters"
                : "No upcoming events"}
          </p>
        ) : (
          <EventList
            events={filteredEvents}
            isRecommended={isRecommendedEvent}
            isListened={isListenedEvent}
            jokes={!searching}
            from={today}
          />
        )}

        <div className="mt-12 md:hidden">{siteLinks}</div>

        {/* Data credits: at the end, to keep the header short on phones. */}
        <div className="mt-12 flex flex-col items-end gap-2 text-right">
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

        </div>

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
