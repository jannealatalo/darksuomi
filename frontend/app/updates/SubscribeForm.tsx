import { BUTTONDOWN_USERNAME, SUBSCRIBE_URL } from "../../lib/newsletter";

/**
 * "Get these by email": a plain form posting to Buttondown, which opens in a
 * new tab to confirm (and asks the subscriber to confirm by email).
 */
export default function SubscribeForm() {
  if (!BUTTONDOWN_USERNAME) return null;
  return (
    <form
      action={SUBSCRIBE_URL}
      method="post"
      target="_blank"
      className="mt-4 max-w-md rounded border border-gray-800 bg-gray-950 p-4 space-y-2"
    >
      <label htmlFor="subscribe-email" className="block text-sm font-semibold text-gray-100">
        Get the new gigs by email
      </label>
      <p className="text-xs text-gray-400">
        One email on the mornings when new gigs are found. Unsubscribe from any email.
      </p>
      <div className="flex gap-2">
        <input
          id="subscribe-email"
          type="email"
          name="email"
          required
          autoComplete="email"
          placeholder="you@example.com"
          className="min-w-0 flex-1 rounded border border-gray-700 bg-black px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-purple-500 focus:outline-none"
        />
        <input type="hidden" name="embed" value="1" />
        <button
          type="submit"
          className="rounded bg-purple-700 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-600"
        >
          Subscribe
        </button>
      </div>
      <p className="text-xs text-gray-500">
        Sent with Buttondown; see <a href="/privacy" className="text-purple-400 hover:text-purple-300">Privacy</a>.
      </p>
    </form>
  );
}
