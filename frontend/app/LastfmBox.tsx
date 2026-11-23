"use client";

import { useState } from "react";

// Same look as the other filter rows (genre/venue, DarkSuomi recommended):
// the label in text-sm, details in small grey text.
const ROW = "flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-gray-300";
const DETAIL = "text-xs text-gray-500";
const LINK = "text-purple-400 hover:text-purple-300";

/**
 * The Last.fm filter row: a username field (no login), or, once a name is
 * given, a "show only bands I listen to" checkbox with the name and a way
 * to change or remove it.
 */
export default function LastfmBox({
  user,
  onUserChange,
  loading,
  error,
  artistCount,
  gigCount,
  onlyThese,
  onOnlyTheseChange,
}: {
  user: string;
  onUserChange: (user: string) => void;
  loading: boolean;
  error: "not-found" | "unavailable" | null;
  artistCount: number;
  /** Upcoming gigs (in the shown city) by the user's artists. */
  gigCount: number;
  /** Showing only the gigs by the user's artists. */
  onlyThese: boolean;
  onOnlyTheseChange: (on: boolean) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  if (user && !editing) {
    const ready = !loading && !error;
    return (
      <div className={ROW}>
        <label
          className={`inline-flex items-center gap-2 ${
            ready && gigCount > 0 ? "cursor-pointer hover:text-white" : "text-gray-500"
          }`}
        >
          <input
            type="checkbox"
            checked={onlyThese}
            disabled={!ready || gigCount === 0}
            onChange={(e) => onOnlyTheseChange(e.target.checked)}
            className="accent-purple-600"
          />
          Show only bands I listen to on Last.fm
        </label>
        <span className={DETAIL}>
          (
          <a
            href={`https://www.last.fm/user/${encodeURIComponent(user)}`}
            target="_blank"
            rel="noopener noreferrer"
            className={LINK}
          >
            {user}
          </a>
          {": "}
          {loading ? (
            "loading your artists…"
          ) : error === "not-found" ? (
            <span role="alert" className="text-red-400">no such Last.fm user</span>
          ) : error ? (
            <span role="alert" className="text-red-400">Last.fm didn&apos;t answer, try again later</span>
          ) : (
            <>
              {gigCount} {gigCount === 1 ? "gig" : "gigs"} by your top {artistCount} artists
            </>
          )}
          {" · "}
          <button
            type="button"
            onClick={() => {
              setDraft(user);
              setEditing(true);
            }}
            className={LINK}
          >
            change
          </button>
          {" · "}
          <button type="button" onClick={() => onUserChange("")} className={LINK}>
            remove
          </button>
          )
        </span>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onUserChange(draft);
        setEditing(false);
      }}
      className={ROW}
    >
      <label htmlFor="lastfm-user">Show bands I listen to on Last.fm:</label>
      <input
        id="lastfm-user"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        maxLength={15}
        autoComplete="off"
        spellCheck={false}
        placeholder="Last.fm username"
        className="w-36 rounded border border-gray-700 bg-gray-900 px-2 py-0.5 text-xs text-gray-200 focus:border-purple-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={!draft.trim()}
        className="rounded border border-purple-700 bg-purple-900/60 px-2 py-0.5 text-xs font-semibold text-purple-100 hover:bg-purple-700 disabled:opacity-50"
      >
        Show
      </button>
      {editing && (
        <button type="button" onClick={() => setEditing(false)} className={`text-xs ${LINK}`}>
          cancel
        </button>
      )}
    </form>
  );
}
