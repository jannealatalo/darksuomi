"use client";

import { useEffect } from "react";

/**
 * The gig search field. The query lives in the address (?q=…) so a search
 * can be shared as a link; it is read once in the browser after load,
 * since the pages are pre-rendered without it.
 */
export default function SearchBox({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) onChange(q);
    // Only on first load; later changes come from typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = (next: string) => {
    onChange(next);
    const params = new URLSearchParams(window.location.search);
    if (next.trim()) params.set("q", next);
    else params.delete("q");
    const query = params.toString();
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`
    );
  };

  return (
    <div className="relative max-w-md">
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        type="search"
        value={value}
        onChange={(e) => update(e.target.value)}
        onKeyDown={(e) => e.key === "Escape" && update("")}
        placeholder="Search bands, venues, genres…"
        aria-label="Search gigs"
        className="w-full rounded border border-gray-700 bg-gray-950 py-2 pl-9 pr-9 text-sm text-gray-100 placeholder-gray-500 focus:border-purple-500 focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
      />
      {value && (
        <button
          type="button"
          onClick={() => update("")}
          aria-label="Clear search"
          className="absolute right-2 top-1/2 -translate-y-1/2 px-1.5 text-gray-400 hover:text-white"
        >
          ✕
        </button>
      )}
    </div>
  );
}
