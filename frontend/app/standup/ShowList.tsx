"use client";

import { useState } from "react";
import { groupShowsByDay, matchesShow, showTime, type Show } from "../../lib/standup";
import SearchBox from "../SearchBox";

/** The searchable list of shows, grouped by day under month headings. */
export default function ShowList({ shows }: { shows: Show[] }) {
  const [search, setSearch] = useState("");
  const shown = search.trim() ? shows.filter((s) => matchesShow(s, search)) : shows;
  const days = groupShowsByDay(shown);

  return (
    <div>
      <SearchBox
        value={search}
        onChange={setSearch}
        placeholder="Hae koomikkoa, klubia tai paikkaa…"
        label="Hae keikkoja"
        clearLabel="Tyhjennä haku"
      />
      {search.trim() && (
        <p className="mt-2 text-xs text-zinc-500">
          {shown.length === 1 ? "1 keikka löytyi" : `${shown.length} keikkaa löytyi`}
        </p>
      )}
      {shown.length === 0 && (
        <p className="mt-6 text-zinc-400">Ei löytynyt mitään. Ehkä sitä vitsiä ei ole vielä keksitty.</p>
      )}

      {days.map((day, i) => (
        <section key={day.key}>
          {(i === 0 || days[i - 1].monthLabel !== day.monthLabel) && (
            <h2 className="mt-10 mb-2 border-b border-zinc-800 pb-2 text-xs uppercase tracking-[0.2em] text-amber-400">
              {day.monthLabel}
            </h2>
          )}
          <h3 className="mt-6 text-lg font-semibold text-zinc-100 first-letter:uppercase">
            {day.label}
          </h3>
          <ul className="mt-2 space-y-4">
            {day.shows.map((show) => (
              <ShowItem key={`${show.date}${show.title}${show.venue}`} show={show} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

const STATUS_LABELS: Record<string, string> = {
  "sold out": "loppuunmyyty",
  cancelled: "peruttu",
};

function ShowItem({ show }: { show: Show }) {
  const time = showTime(show);
  return (
    <li>
      <p className="text-base font-bold leading-snug text-zinc-50 sm:text-lg">{show.title}</p>
      <p className="text-sm text-zinc-300">
        <a
          href={show.eventUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="underline decoration-zinc-600 underline-offset-2 hover:text-amber-300"
        >
          {show.venue}
        </a>
        {show.city !== "Helsinki" && <> · {show.city}</>}
        {time && <> · klo {time}</>}
        {show.age && <> · {show.age}</>}
        {show.price && <> · {show.price}</>}
        {show.status && (
          <span className="ml-2 rounded bg-red-900/60 px-1.5 py-0.5 text-xs font-semibold uppercase text-red-300">
            {STATUS_LABELS[show.status] ?? show.status}
          </span>
        )}
      </p>
      <p className="mt-0.5 text-sm">
        <a
          href={show.ticketUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-amber-400 hover:text-amber-300"
        >
          Liput
        </a>
      </p>
    </li>
  );
}
