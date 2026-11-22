import { useEffect, useState } from "react";
import { scrapeDay } from "./events";

/** Today in Finland (YYYY-MM-DD) by the visitor's clock. */
export function helsinkiToday(): string {
  return new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Helsinki" });
}

/**
 * "Today" for the gig lists: the scrape day while the page loads (so server
 * and browser render the same), then the real date in the browser. When the
 * nightly scrape is late (GitHub can start it hours late), yesterday's gigs
 * still disappear at midnight.
 */
export function useToday(): string {
  const [today, setToday] = useState(scrapeDay);
  useEffect(() => {
    const now = helsinkiToday();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the clock is only known in the browser
    if (now > scrapeDay) setToday(now);
  }, []);
  return today;
}
