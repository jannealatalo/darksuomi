import type { Metadata } from "next";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";

export const metadata: Metadata = {
  title: "Dark Suomi Tampere",
  description: "Alternative music events in Tampere (experimental)",
};

/** Experimental Tampere site: its own venues and data (data/tampere/events.json). */
export default function TamperePage() {
  return <GigCalendar events={getEvents("tampere")} city="tampere" />;
}
