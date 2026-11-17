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
          <div>
            <h3 className="text-xl font-bold">
              Oranssi Pazuzu
            </h3>

            <p className="text-gray-400">
              Ääniwalli · Helsinki
            </p>

            <p>
              13 February 2027
            </p>
          </div>

          <div>
            <h3 className="text-xl font-bold">
              Mokoma
            </h3>

            <p className="text-gray-400">
              Tavastia · Helsinki
            </p>

            <p>
              20 February 2027
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}