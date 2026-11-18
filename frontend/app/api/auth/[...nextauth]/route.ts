import { handlers } from "@/auth";
import type { NextRequest } from "next/server";

/**
 * Spotify only accepts http://127.0.0.1 (never localhost) as a local redirect
 * URI, but Next.js rewrites 127.0.0.1 to "localhost" in every NextRequest URL,
 * so Auth.js would send Spotify a localhost redirect_uri. In development,
 * hand Auth.js a plain Request carrying the host the browser actually used.
 * Production (Vercel) already gets the correct URL and is left untouched.
 */
function withBrowserHost(req: NextRequest): NextRequest {
  if (process.env.NODE_ENV !== "development") return req;

  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
  if (!host) return req;

  const url = new URL(req.url);
  url.host = host;
  if (url.href === req.url) return req;

  // Plain Request on purpose: wrapping it in NextRequest would undo the host.
  // Auth.js only needs the standard Request API here.
  return new Request(url, {
    method: req.method,
    headers: req.headers,
    body: req.body,
    // Required by Node when forwarding a streamed body.
    duplex: "half",
  } as RequestInit) as NextRequest;
}

export const GET = (req: NextRequest) => handlers.GET(withBrowserHost(req));
export const POST = (req: NextRequest) => handlers.POST(withBrowserHost(req));
