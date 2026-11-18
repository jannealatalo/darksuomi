import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

export function useSpotifyFollowedArtists() {
  const { data: session } = useSession();
  const [followedArtists, setFollowedArtists] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!session?.accessToken) {
      setFollowedArtists(new Set());
      return;
    }

    const fetchFollowedArtists = async () => {
      setLoading(true);
      try {
        const artists = new Set<string>();
        let after = null;
        let hasMore = true;

        while (hasMore) {
          const url = new URL("https://api.spotify.com/v1/me/following");
          url.searchParams.append("type", "artist");
          url.searchParams.append("limit", "50");
          if (after) {
            url.searchParams.append("after", after);
          }

          const response = await fetch(url, {
            headers: {
              Authorization: `Bearer ${session.accessToken}`,
            },
          });

          if (!response.ok) {
            console.error("Failed to fetch Spotify artists");
            break;
          }

          const data = await response.json();

          if (data.artists?.items) {
            data.artists.items.forEach((artist: any) => {
              artists.add(artist.name.toLowerCase());
            });
          }

          after = data.artists?.cursors?.after;
          hasMore = !!after;
        }

        setFollowedArtists(artists);
      } catch (error) {
        console.error("Error fetching followed artists:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchFollowedArtists();
  }, [session?.accessToken]);

  return { followedArtists, loading };
}
