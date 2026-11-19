import NextAuth from "next-auth";
import Spotify from "next-auth/providers/spotify";

// Only what the site uses: reading the followed artists (no email address).
const SPOTIFY_SCOPES = "user-follow-read";

// Spotify access tokens live for one hour; refresh them with the refresh token.
async function refreshSpotifyToken(refreshToken: string) {
  const basic = Buffer.from(
    `${process.env.SPOTIFY_CLIENT_ID}:${process.env.SPOTIFY_CLIENT_SECRET}`
  ).toString("base64");

  const response = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: {
      Authorization: `Basic ${basic}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
    }),
  });

  const data = await response.json();
  if (!response.ok) throw data;

  return {
    accessToken: data.access_token as string,
    expiresAt: Math.floor(Date.now() / 1000) + (data.expires_in as number),
    // Spotify may or may not rotate the refresh token.
    refreshToken: (data.refresh_token as string | undefined) ?? refreshToken,
  };
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Spotify({
      clientId: process.env.SPOTIFY_CLIENT_ID,
      clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
      // Must be the full URL: passing only `{ params }` replaces the
      // provider's default authorize URL and breaks sign-in ("Invalid URL").
      authorization: `https://accounts.spotify.com/authorize?scope=${encodeURIComponent(
        SPOTIFY_SCOPES
      )}`,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      // First sign-in: store the tokens from Spotify.
      if (account) {
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          expiresAt: account.expires_at,
          error: undefined,
        };
      }

      // Token still valid (with a 60 s margin).
      if (token.expiresAt && Date.now() / 1000 < token.expiresAt - 60) {
        return token;
      }

      if (!token.refreshToken) {
        return { ...token, error: "RefreshTokenError" as const };
      }

      try {
        const refreshed = await refreshSpotifyToken(token.refreshToken);
        return { ...token, ...refreshed, error: undefined };
      } catch (error) {
        console.error("Failed to refresh Spotify token", error);
        return { ...token, error: "RefreshTokenError" as const };
      }
    },
    session({ session, token }) {
      session.accessToken = token.accessToken;
      session.error = token.error;
      return session;
    },
  },
});
