import NextAuth from "next-auth";
import Spotify from "next-auth/providers/spotify";

export const { handlers, auth } = NextAuth({
  providers: [
    Spotify({
      clientId: process.env.SPOTIFY_CLIENT_ID,
      clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
      authorization: {
        params: {
          scope: "user-follow-read",
        },
      },
      allowDangerousEmailAccountLinking: true,
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET,
  callbacks: {
    jwt({ token, account }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    session({ session, token }) {
      (session as any).accessToken = token.accessToken as string;
      return session;
    },
  },
});

export const GET = handlers.GET;
export const POST = handlers.POST;