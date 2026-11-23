/**
 * POST /api/visits  body: {"count": true | false}
 *
 * The site's visit counter, kept in an Upstash Redis database (created in
 * Vercel: Storage -> Upstash). {"count": true} adds one visit, false only
 * reads; both answer {"visits": n}. POST, so nothing caches it.
 *
 * Stores one number and nothing about the visitor.
 */

const KEY = "darksuomi:visits";

// Vercel's Upstash integration names them KV_REST_API_*; Upstash's own
// console uses UPSTASH_REDIS_REST_*.
const URL_ = process.env.KV_REST_API_URL ?? process.env.UPSTASH_REDIS_REST_URL;
const TOKEN = process.env.KV_REST_API_TOKEN ?? process.env.UPSTASH_REDIS_REST_TOKEN;

export async function POST(request: Request) {
  if (!URL_ || !TOKEN) {
    return Response.json({ error: "not configured" }, { status: 503 });
  }
  let count = false;
  try {
    count = (await request.json())?.count === true;
  } catch {
    // No body: just read.
  }

  try {
    // Upstash's REST API: one Redis command as a JSON array.
    const response = await fetch(URL_, {
      method: "POST",
      headers: { Authorization: `Bearer ${TOKEN}` },
      body: JSON.stringify(count ? ["INCR", KEY] : ["GET", KEY]),
      cache: "no-store",
    });
    const data: { result?: number | string | null; error?: string } = await response.json();
    if (!response.ok || data.error) throw new Error(data.error ?? `HTTP ${response.status}`);
    return Response.json({ visits: Number(data.result ?? 0) });
  } catch (error) {
    console.error("Visit counter failed:", error);
    return Response.json({ error: "unavailable" }, { status: 502 });
  }
}
