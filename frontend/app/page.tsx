"use client";

import {
  eventArtistNames,
  excludedGenres,
  getEvents,
  isExcludedByGenre,
} from "../lib/events";
import type { Event } from "../types/events";
import { signIn, signOut, useSession } from "next-auth/react";
import { useSpotifyFollowedArtists } from "../lib/useSpotifyFollowedArtists";
import { useState } from "react";

const events = getEvents();
const hiddenByGenreCount = events.filter(isExcludedByGenre).length;

export default function Home() {
  const { data: session } = useSession();
  const { followedArtists } = useSpotifyFollowedArtists();
  const [showOnlyFollowed, setShowOnlyFollowed] = useState(false);
  const [showAllGenres, setShowAllGenres] = useState(false);

  const isFollowedEvent = (event: Event) =>
    eventArtistNames(event).some((name) => followedArtists.has(name));

  const filteredEvents = events.filter(
    (event) =>
      (showAllGenres || !isExcludedByGenre(event)) &&
      (!showOnlyFollowed || isFollowedEvent(event))
  );

  const hasFollowedArtists = followedArtists.size > 0;

  return (
    <main className="min-h-screen bg-black text-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-5xl font-bold mb-2">Dark Suomi</h1>
            <p className="text-gray-400">
              Doom • Stoner • Goth • Darkwave • Industrial • Punk • Metal
            </p>
          </div>

          <div>
            {session ? (
              <div className="text-right">
                <p className="text-sm text-gray-400 mb-2">
                  Logged in as {session.user?.name || session.user?.email}
                </p>
                <button
                  onClick={() => signOut()}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => signIn("spotify")}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z" />
                </svg>
                Login with Spotify
              </button>
            )}
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

        {hiddenByGenreCount > 0 && (
          <div className="mb-6 text-sm text-gray-400">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showAllGenres}
                onChange={(e) => setShowAllGenres(e.target.checked)}
                className="accent-purple-600"
              />
              Show all genres
            </label>
            {!showAllGenres && (
              <p className="text-xs text-gray-500 mt-1">
                {hiddenByGenreCount} events hidden (
                {[...excludedGenres].join(", ")})
              </p>
            )}
          </div>
        )}

        <hr className="border-gray-800 mb-8" />

        <h2 className="text-2xl font-semibold mb-6">
          Upcoming Events {showOnlyFollowed && "- Your Artists"}
        </h2>

        {filteredEvents.length === 0 ? (
          <p className="text-gray-400">
            {showOnlyFollowed
              ? "No upcoming events for artists you follow"
              : "No upcoming events"}
          </p>
        ) : (
          <div className="space-y-8">
            {filteredEvents.map((event) => {
              const isFollowed = isFollowedEvent(event);
              return (
                <div key={event.ticketUrl || `${event.artist}-${event.date}`}>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold">{event.artist}</h3>
                    {isFollowed && (
                      <svg
                        className="w-5 h-5 text-green-500"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        aria-label="You follow this artist on Spotify"
                      >
                        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z" />
                      </svg>
                    )}
                  </div>

                  <p className="text-gray-400">
                    {event.venue} · {event.city}
                  </p>

                  <p>
                    {new Date(event.date).toLocaleDateString("fi-FI")}
                  </p>

                  {event.genres && event.genres.length > 0 && (
                    <p className="text-xs text-gray-500">
                      {event.genres.slice(0, 4).join(" · ")}
                    </p>
                  )}

                  <a
                    href={event.ticketUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-400 hover:text-purple-300"
                  >
                    Tickets
                  </a>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}