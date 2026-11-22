"use client";

import { useState } from "react";
import { matchesSearch } from "../../lib/search";
import { useToday } from "../../lib/today";
import type { Event } from "../../types/events";
import EventList from "../EventList";
import SearchBox from "../SearchBox";

/** Past gigs with the search field (the page itself is a server component). */
export default function PastGigList({ events }: { events: Event[] }) {
  const [search, setSearch] = useState("");
  const today = useToday();
  const searching = search.trim() !== "";
  const shown = events.filter(
    (e) => e.date.slice(0, 10) < today && matchesSearch(e, search),
  );

  return (
    <>
      <div className="mb-6">
        <SearchBox value={search} onChange={setSearch} />
        {searching && (
          <p className="mt-2 text-xs text-gray-500">
            {shown.length} {shown.length === 1 ? "gig" : "gigs"} found
          </p>
        )}
      </div>
      {shown.length === 0 ? (
        <p className="text-gray-400">
          {searching
            ? "Nothing found. Maybe they broke up. Maybe they never existed."
            : "No past gigs yet."}
        </p>
      ) : (
        <EventList events={shown} past />
      )}
    </>
  );
}
