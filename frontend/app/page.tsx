import { getEvents } from "../lib/events";

const events = getEvents();

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <h1 className="text-5xl font-bold mb-2">
          Dark Suomi
        </h1>

        <p className="text-gray-400 mb-8">
          Doom • Stoner • Goth • Darkwave • Industrial • Punk • Metal
        </p>

        <hr className="border-gray-800 mb-8" />

        <h2 className="text-2xl font-semibold mb-6">
          Upcoming Events
        </h2>

        <div className="space-y-8">
          {events.map((event) => (
            <div key={event.id}>
              <h3 className="text-xl font-bold">
                {event.artist}
              </h3>

              <p className="text-gray-400">
                {event.venue} · {event.city}
              </p>

              <p>
                {new Date(event.date).toLocaleDateString("fi-FI")}
              </p>

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
      </div>
    </main>
  );
}