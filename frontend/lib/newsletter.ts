/**
 * The daily updates newsletter on Buttondown (buttondown.com), which keeps
 * the subscriber list and sends confirmations and unsubscribe links. The
 * nightly job posts each day's email with the BUTTONDOWN_API_KEY secret.
 *
 * The newsletter's Buttondown username; the subscribe form is hidden while
 * this is empty.
 */
export const BUTTONDOWN_USERNAME = "turhapuro";

export const SUBSCRIBE_URL = `https://buttondown.com/api/emails/embed-subscribe/${BUTTONDOWN_USERNAME}`;
