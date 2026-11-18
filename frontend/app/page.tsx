import type { Event } from "../types/event";
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
  </div>
))}
</div>
    </main>
  );
}