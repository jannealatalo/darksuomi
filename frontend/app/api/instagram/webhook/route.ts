/**
 * Webhook address for the "DarkSuomi Poster" Meta app (Instagram API).
 *
 * Meta requires a webhook before it hands out the posting token, but the
 * site doesn't use the notifications (comments, messages). So:
 * - GET: Meta's check. It sends hub.mode=subscribe, hub.verify_token and
 *   hub.challenge; we answer the challenge when the token matches.
 * - POST: notifications are acknowledged and thrown away.
 *
 * The verify token only proves to Meta that this address belongs to the
 * app; nothing can be read or changed with it, so it can live in the code.
 */

const VERIFY_TOKEN = "pbcwPqIxDN8oEVPz9BHGCxSm";

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const challenge = params.get("hub.challenge");
  if (
    params.get("hub.mode") === "subscribe" &&
    params.get("hub.verify_token") === VERIFY_TOKEN &&
    challenge
  ) {
    return new Response(challenge, { headers: { "Content-Type": "text/plain" } });
  }
  return new Response("Forbidden", { status: 403 });
}

export async function POST() {
  return new Response(null, { status: 200 });
}
