import { cacheLife } from "next/cache";
import type { NextRequest } from "next/server";

/**
 * GET /api/lastfm?user=<Last.fm username>
 *
 * The artists that user has listened to most (all time, up to 1000), as
 * lowercased names, so a visitor can filter gigs by their listening without
 * logging in. Runs on the server so the Last.fm API key stays private.
 */

// Last.fm usernames: 2-15 characters, starting with a letter.
const USERNAME = /^[A-Za-z][A-Za-z0-9_-]{1,14}$/;

type TopArtistsResponse = {
  error?: number;
  message?: string;
  topartists?: { artist?: { name: string }[] };
};

type Result = { artists: string[] } | { error: "not-found" | "unavailable" };

async function topArtists(user: string): Promise<Result> {
  "use cache";
  // Listening changes slowly; one Last.fm call per user per few hours is plenty.
  cacheLife("hours");

  const key = process.env.LASTFM_API_KEY;
  if (!key) return { error: "unavailable" };

  const url = new URL("https://ws.audioscrobbler.com/2.0/");
  url.search = new URLSearchParams({
    method: "user.gettopartists",
    user,
    period: "overall",
    limit: "1000",
    api_key: key,
    format: "json",
  }).toString();

  try {
    const response = await fetch(url, { headers: { "User-Agent": "DarkSuomi/1.0" } });
    const data: TopArtistsResponse = await response.json();
    // Error 6: no such user.
    if (data.error === 6) return { error: "not-found" };
    if (!response.ok || data.error) return { error: "unavailable" };
    const names = (data.topartists?.artist ?? []).map((a) => a.name.toLowerCase());
    return { artists: [...new Set(names)] };
  } catch {
    return { error: "unavailable" };
  }
}

export async function GET(request: NextRequest) {
  const user = request.nextUrl.searchParams.get("user")?.trim() ?? "";
  if (!USERNAME.test(user)) {
    return Response.json({ error: "not-found" }, { status: 404 });
  }
  // Last.fm usernames are case-insensitive: one cache entry per user.
  const result = await topArtists(user.toLowerCase());
  if ("error" in result) {
    return Response.json(result, { status: result.error === "not-found" ? 404 : 502 });
  }
  return Response.json(result, {
    headers: { "Cache-Control": "public, s-maxage=21600, stale-while-revalidate=86400" },
  });
}
