import { useEffect, useState } from "react";
import { scrapeDayIn } from "./events";

/** Today (YYYY-MM-DD) in a time zone by the visitor's clock; Finland by default. */
export function todayIn(timeZone = "Europe/Helsinki"): string {
  return new Date().toLocaleDateString("sv-SE", { timeZone });
}

/** Today in Finland (YYYY-MM-DD) by the visitor's clock. */
export function helsinkiToday(): string {
  return todayIn("Europe/Helsinki");
}

/**
 * "Today" for the gig lists: the scrape day while the page loads (so server
 * and browser render the same), then the real date in the browser. When the
 * nightly scrape is late (GitHub can start it hours late), yesterday's gigs
 * still disappear at midnight. `timeZone` is the city's (Seattle's gigs end
 * at Seattle's midnight, ten hours after Finland's).
 */
export function useToday(timeZone = "Europe/Helsinki"): string {
  const start = scrapeDayIn(timeZone);
  const [today, setToday] = useState(start);
  useEffect(() => {
    const now = todayIn(timeZone);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the clock is only known in the browser
    if (now > start) setToday(now);
  }, [timeZone, start]);
  return today;
}
