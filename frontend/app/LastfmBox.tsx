"use client";

import { useState } from "react";

/**
 * "Your bands from Last.fm": a username field (no login), or the name in
 * use with a way to change or remove it.
 */
export default function LastfmBox({
  user,
  onUserChange,
  loading,
  error,
  artistCount,
  gigCount,
}: {
  user: string;
  onUserChange: (user: string) => void;
  loading: boolean;
  error: "not-found" | "unavailable" | null;
  artistCount: number;
  /** Upcoming gigs (in the shown city) by the user's artists. */
  gigCount: number;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  if (user && !editing) {
    return (
      <p className="text-xs text-gray-400">
        Last.fm:{" "}
        <a
          href={`https://www.last.fm/user/${encodeURIComponent(user)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-red-300 hover:text-red-200"
        >
          {user}
        </a>
        {" · "}
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
          className="text-purple-400 hover:text-purple-300"
        >
          change
        </button>
        {" · "}
        <button
          type="button"
          onClick={() => onUserChange("")}
          className="text-purple-400 hover:text-purple-300"
        >
          remove
        </button>
      </p>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onUserChange(draft);
        setEditing(false);
      }}
      className="flex flex-wrap items-center gap-2 text-xs text-gray-400"
    >
      <label htmlFor="lastfm-user">Find gigs by bands you listen to: your Last.fm username</label>
      <input
        id="lastfm-user"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        maxLength={15}
        autoComplete="off"
        spellCheck={false}
        placeholder="username"
        className="w-32 rounded border border-gray-700 bg-gray-900 px-2 py-1 text-gray-200 focus:border-red-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={!draft.trim()}
        className="rounded bg-red-800 px-2.5 py-1 font-semibold text-red-50 hover:bg-red-700 disabled:opacity-50"
      >
        Show
      </button>
      {editing && (
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="text-purple-400 hover:text-purple-300"
        >
          cancel
        </button>
      )}
    </form>
  );
}
