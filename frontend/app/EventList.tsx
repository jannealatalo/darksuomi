import { eventTime, gapsBefore, groupByDay, type GigGap } from "../lib/events";
import { jokeParts, noGigJoke } from "../lib/jokes";
import { venueUrl } from "../lib/links";
import {
  actualSetlists,
  expectedSetlists,
  isSpecialShow,
  latestShows,
  playlistUrl,
  selbiUrl,
  type ShowLink,
} from "../lib/setlists";
import type { Event } from "../types/events";
import ExpectedSetlists from "./ExpectedSetlist";

const SPOTIFY_ICON =
  "M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z";

/** The venue name, linked to the gig's page at the venue when known. */
function VenueName({ event }: { event: Event }) {
  const url = venueUrl(event);
  if (!url) return <>{event.venue}</>;
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      title={`${event.venue}: this gig on the venue's site`}
      className="underline decoration-gray-600 underline-offset-2 hover:text-purple-300 hover:decoration-purple-400"
    >
      {event.venue}
    </a>
  );
}

/**
 * Gigs grouped by day, with a heading whenever the month changes. With
 * `past`, gigs show their actual setlists instead of tickets.
 */
export default function EventList({
  events,
  isFollowed,
  past = false,
  jokes = true,
}: {
  events: Event[];
  isFollowed?: (event: Event) => boolean;
  past?: boolean;
  /** Off while searching: jokes between search results would be noise. */
  jokes?: boolean;
}) {
  const days = groupByDay(events);
  // Empty days in the shown (filtered) list get a joke; not for past gigs.
  const gaps = past || !jokes ? new Map<string, GigGap>() : gapsBefore(days);

  return (
    <div>
      {days.map((day, i) => {
        const newMonth = i === 0 || days[i - 1].monthLabel !== day.monthLabel;
        const gap = gaps.get(day.key);
        return (
          <section key={day.key} aria-label={`${day.weekday} ${day.day}.${day.month}.`}>
            {gap && <GapRow gap={gap} />}
            {newMonth && (
              <h2 className="text-xs uppercase tracking-[0.2em] text-purple-400 border-b border-gray-800 pb-2 mb-2 mt-10 first:mt-0">
                {day.monthLabel}
              </h2>
            )}

            <div className="sm:grid sm:grid-cols-[4.5rem_1fr] sm:gap-6 border-b border-gray-900 py-4">
              {/* Date: a header line on phones, a column on wider screens. */}
              <div className="mb-2 sm:mb-0 sm:sticky sm:top-4 sm:self-start flex sm:flex-col items-baseline sm:items-start gap-2 sm:gap-0">
                <span className="text-sm font-semibold uppercase tracking-wider text-gray-300">
                  {day.weekday}
                </span>
                <span className="text-2xl sm:text-3xl font-bold leading-none text-gray-100">
                  {day.day}.{day.month}.
                </span>
              </div>

              <ul className="space-y-4">
                {day.events.map((event) => (
                  <EventItem
                    key={`${event.site ?? ""}${event.id}`}
                    event={event}
                    followed={isFollowed?.(event) ?? false}
                    past={past}
                  />
                ))}
              </ul>
            </div>
          </section>
        );
      })}
    </div>
  );
}

const SOLD_OUT_PRICE = /^\s*(loppuunmyyty|sold out)\s*$/i;

/** "sold out" / "cancelled": from the venue listing, or a price that says so. */
function saleStatus(event: Event): Event["status"] {
  if (event.status) return event.status;
  return event.price && SOLD_OUT_PRICE.test(event.price) ? "sold out" : undefined;
}

function EventItem({
  event,
  followed,
  past,
}: {
  event: Event;
  followed: boolean;
  past: boolean;
}) {
  const time = eventTime(event);
  const status = past ? undefined : saleStatus(event);
  // A price of just "loppuunmyyty" is shown as the sold-out mark instead.
  const price = event.price && !SOLD_OUT_PRICE.test(event.price) ? event.price : null;
  return (
    <li
      id={event.site && event.site !== "helsinki" ? `gig-${event.site}-${event.id}` : `gig-${event.id}`}
      className="scroll-mt-6"
    >
      <div className="flex items-start gap-2">
        <h3
          className={`text-lg font-semibold leading-snug ${
            status === "cancelled" ? "text-gray-500 line-through" : "text-gray-100"
          }`}
        >
          {event.artist}
        </h3>
        {followed && (
          <svg
            className="w-4 h-4 mt-1 shrink-0 text-green-500"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-label="You follow this artist on Spotify"
          >
            <path d={SPOTIFY_ICON} />
          </svg>
        )}
      </div>

      <p className="text-sm text-gray-300">
        <VenueName event={event} /> · {event.city}
        {time && <> · doors {time}</>}
        {event.age && <> · {event.age}</>}
        {price && <> · {price}</>}
        {status && (
          <>
            {" "}
            <span
              className={`ml-1 rounded px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${
                status === "cancelled"
                  ? "bg-gray-800 text-gray-300"
                  : "bg-red-900/60 text-red-300"
              }`}
            >
              {status}
            </span>
          </>
        )}
      </p>

      {event.schedule && event.schedule.length > 0 && (
        <p className="text-sm text-gray-300">
          {event.schedule.map((s, i) => (
            <span key={s.time + s.name}>
              {i > 0 && <span className="text-gray-500"> · </span>}
              <span className="text-gray-100 font-semibold tabular-nums">{s.time}</span> {s.name}
            </span>
          ))}
        </p>
      )}

      {event.genres && event.genres.length > 0 && (
        <p className="text-xs text-gray-400">{event.genres.slice(0, 4).join(" · ")}</p>
      )}

      {past ? (
        <PastSetlists shows={actualSetlists(event)} />
      ) : (
        <div className="text-sm mt-1">
          <a
            href={event.ticketUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-purple-400 hover:text-purple-300"
          >
            Tickets
          </a>
          {/* Expected setlist and latest shows fold under one "Setlist stuff"
              toggle, and band links under "Band info", so a festival bill
              doesn't fill the screen with links. */}
          <ExpectedSetlists
            setlists={expectedSetlists(event)}
            special={isSpecialShow(event)}
            playlistUrl={playlistUrl(event)}
            latestShows={latestShows(event).length > 0 ? <LatestShows shows={latestShows(event)} /> : null}
            bands={event.bands}
          />
        </div>
      )}
    </li>
  );
}

/** "21.11.2025": with the year, since a band's latest show can be old. */
function fullDate(iso?: string) {
  if (!iso) return "";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return `${d}.${m}.${y}`;
}

/** "Setlist · → Spotify playlist" links for one show. */
function ShowLinks({ show }: { show: ShowLink }) {
  return (
    <>
      <a
        href={show.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-purple-400 hover:text-purple-300"
      >
        setlist
      </a>
      <span className="text-gray-600"> · </span>
      <a
        href={selbiUrl(show.url)}
        target="_blank"
        rel="noopener noreferrer"
        title="Creates a Spotify playlist of this setlist with setlistfm.selbi.club"
        className="text-green-500 hover:text-green-400"
      >
        make a Spotify playlist ↗
      </a>
    </>
  );
}

/** Upcoming gigs: what each act played at their most recent show anywhere. */
function LatestShows({ shows }: { shows: ShowLink[] }) {
  if (shows.length === 0) return null;
  const many = shows.length > 1;
  return (
    <div className="space-y-0.5 text-sm text-gray-400">
      {shows.map((show) => (
        <p key={show.artist}>
          Latest show{many && <> of {show.artist}</>}: {show.place}{" "}
          {fullDate(show.date)} — <ShowLinks show={show} />
        </p>
      ))}
    </div>
  );
}

/** Past gigs: the actual setlist of that night, once someone has added it. */
function PastSetlists({ shows }: { shows: ShowLink[] }) {
  if (shows.length === 0) {
    return <p className="text-sm text-gray-500 mt-1">No setlist on setlist.fm yet.</p>;
  }
  const many = shows.length > 1;
  return (
    <div className="mt-1 space-y-0.5 text-sm text-gray-300">
      {shows.map((show) => (
        <p key={show.artist}>
          {many ? <>{show.artist}: </> : <>Setlist of the night: </>}
          <ShowLinks show={show} />
        </p>
      ))}
    </div>
  );
}

/** A day (or run of days) with nothing in the shown list: a dry joke. */
function GapRow({ gap }: { gap: GigGap }) {
  return (
    <div className="sm:grid sm:grid-cols-[4.5rem_1fr] sm:gap-6 border-b border-gray-900 py-3">
      <div className="mb-1 sm:mb-0 text-sm font-semibold text-gray-500">{gap.label}</div>
      <p className="text-sm italic text-gray-400">
        {jokeParts(noGigJoke(gap.from, gap.days)).map((part, i) =>
          part.url ? (
            <a
              key={i}
              href={part.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300 not-italic"
            >
              {part.text}
            </a>
          ) : (
            <span key={i}>{part.text}</span>
          )
        )}
      </p>
    </div>
  );
}
