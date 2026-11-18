import type { Event } from "../types/events";
import { getEvents } from "../lib/events";
const events = getEvents();
export default function Home() {
  return (
    <main className="min-h-screen bg-black text-gray-200">
      <div className="space-y-8">
  {events.map((event) => (
  <div key={event.id}>
    <h3 className="text-xl font-bold">
      {event.artist}
    </h3>

    <p className="text-gray-400">
      {event.venue} · {event.city}
    </p>

    <p>{event.date}</p>

    <p className="text-sm text-gray-500">
      {event.genre}
    </p>
    <a
  href={event.ticketUrl}
  target="_blank"
  rel="noopener noreferrer"
  className="text-purple-400 hover:text-purple-300"
>
  Tickets
</a>
  </div>
))}
</div>
    </main>
  );
}