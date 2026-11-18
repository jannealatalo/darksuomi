import type { ExpectedSetlist } from "../lib/setlists";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("fi-FI", { timeZone: "Europe/Helsinki" });
}

/** Collapsible expected setlist(s) for one event. */
export default function ExpectedSetlists({
  setlists,
  special,
}: {
  setlists: ExpectedSetlist[];
  special: boolean;
}) {
  if (setlists.length === 0) return null;
  const showArtistNames = setlists.length > 1;

  return (
    <details className="mt-1 text-sm group">
      <summary className="cursor-pointer text-gray-400 hover:text-gray-200 select-none">
        Expected setlist
      </summary>

      <div className="mt-2 pl-4 border-l border-gray-800 space-y-4">
        {special && (
          <p className="text-xs text-amber-400">
            Special show: the setlist will likely differ from their usual set.
          </p>
        )}

        {setlists.map((s) => {
          const main = s.songs.filter((song) => !song.encore);
          const encore = s.songs.filter((song) => song.encore);
          return (
            <div key={s.artist}>
              {showArtistNames && (
                <p className="font-semibold text-gray-300 mb-1">{s.artist}</p>
              )}
              <ol className="list-decimal list-inside text-gray-300 space-y-0.5">
                {main.map((song) => (
                  <Song key={song.name} song={song} />
                ))}
              </ol>
              {encore.length > 0 && (
                <>
                  <p className="text-xs uppercase tracking-wide text-gray-500 mt-2 mb-0.5">
                    Encore
                  </p>
                  <ol
                    start={main.length + 1}
                    className="list-decimal list-inside text-gray-300 space-y-0.5"
                  >
                    {encore.map((song) => (
                      <Song key={song.name} song={song} />
                    ))}
                  </ol>
                </>
              )}
              <p className="text-xs text-gray-500 mt-2">
                Based on {s.basedOn} shows, {formatDate(s.from)}–{formatDate(s.to)}
                {s.url && (
                  <>
                    {" · "}
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300"
                    >
                      setlist.fm
                    </a>
                  </>
                )}
              </p>
            </div>
          );
        })}
      </div>
    </details>
  );
}

function Song({ song }: { song: ExpectedSetlist["songs"][number] }) {
  return (
    <li>
      {song.name}
      {song.cover && (
        <span className="text-gray-500"> ({song.cover} cover)</span>
      )}
      {song.playedPct < 50 && (
        <span className="text-gray-600 text-xs"> · sometimes</span>
      )}
    </li>
  );
}
