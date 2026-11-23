import data from "../data/recommended.json";

/**
 * DarkSuomi's recommended bands: the artists the Dark Suomi Spotify account
 * follows (lowercased; written nightly by recommended.py).
 */
export const recommendedArtists = new Set<string>(data.artists);
