import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

/** The parts of Spotify's GET /v1/me/following response we use. */
type FollowedArtistsResponse = {
  artists?: {
    items?: { name: string }[];
    cursors?: { after?: string | null };
  };
};

const EMPTY = new Set<string>();

export function useSpotifyFollowedArtists() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;

  // Results are stored together with the token they were fetched for, so a
  // logout (or a different token) shows an empty list without resetting
  // state inside the effect.
  const [result, setResult] = useState<{
    token: string;
    artists: Set<string>;
  } | null>(null);

  useEffect(() => {
    if (!accessToken) return;

    let cancelled = false;

    const fetchFollowedArtists = async () => {
      const artists = new Set<string>();
      try {
        let after: string | null | undefined = null;

        do {
          const url = new URL("https://api.spotify.com/v1/me/following");
          url.searchParams.append("type", "artist");
          url.searchParams.append("limit", "50");
          if (after) url.searchParams.append("after", after);

          const response = await fetch(url, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });

          if (!response.ok) {
            console.error("Failed to fetch Spotify artists");
            break;
          }

          const data: FollowedArtistsResponse = await response.json();
          data.artists?.items?.forEach((artist) => {
            artists.add(artist.name.toLowerCase());
          });
          after = data.artists?.cursors?.after;
        } while (after);
      } catch (error) {
        console.error("Error fetching followed artists:", error);
      }

      if (!cancelled) setResult({ token: accessToken, artists });
    };

    fetchFollowedArtists();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const isCurrent = !!accessToken && result?.token === accessToken;
  return {
    followedArtists: isCurrent ? result.artists : EMPTY,
    loading: !!accessToken && !isCurrent,
  };
}
