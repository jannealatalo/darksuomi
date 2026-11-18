import NextAuth from "next-auth";
import Spotify from "next-auth/providers/spotify";

const handler = NextAuth({
  providers: [
    Spotify({
      clientId: process.env.SPOTIFY_CLIENT_ID || "",
      clientSecret: process.env.SPOTIFY_CLIENT_SECRET || "",
      authorization: {
        params: {
          scope: "user-follow-read",
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      (session as any).accessToken = token.accessToken as string;
      return session;
    },
  },
});

export { handler as GET, handler as POST };