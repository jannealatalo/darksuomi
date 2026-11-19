import { eventTime, groupByDay } from "../lib/events";
import { expectedSetlists, isSpecialShow, playlistUrl } from "../lib/setlists";
import type { Event } from "../types/events";
import ExpectedSetlists from "./ExpectedSetlist";

const SPOTIFY_ICON =
  "M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-12-1.5-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15.179 10.561 18.72 12.84c.361.21.599.659.359 1.2zm.12-3.36C15.312 8.322 8.654 8.034 5.409 9.425c-.589.25-1.238-.056-1.488-.646-.25-.59.056-1.24.646-1.488 4.326-1.822 11.461-1.471 15.174 1.971.406.325.344 1.025-.067 1.407-.413.347-1.113.291-1.519-.034z";

/** Upcoming gigs grouped by day, with a heading whenever the month changes. */
export default function EventList({
  events,
  isFollowed,
}: {
  events: Event[];
  isFollowed: (event: Event) => boolean;
}) {
  const days = groupByDay(events);

  return (
    <div>
      {days.map((day, i) => {
        const newMonth = i === 0 || days[i - 1].monthLabel !== day.monthLabel;
        return (
          <section key={day.key} aria-label={`${day.weekday} ${day.day}.${day.month}.`}>
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
                    key={event.id}
                    event={event}
                    followed={isFollowed(event)}
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

function EventItem({ event, followed }: { event: Event; followed: boolean }) {
  const time = eventTime(event);
  return (
    <li>
      <div className="flex items-start gap-2">
        <h3 className="text-lg font-semibold leading-snug text-gray-100">
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
        {event.venue} · {event.city}
        {time && <> · doors {time}</>}
        {event.age && <> · {event.age}</>}
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

      <div className="text-sm mt-1">
        <a
          href={event.ticketUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-purple-400 hover:text-purple-300"
        >
          Tickets
        </a>
        <ExpectedSetlists
          setlists={expectedSetlists(event)}
          special={isSpecialShow(event)}
          playlistUrl={playlistUrl(event)}
        />
      </div>
    </li>
  );
}
