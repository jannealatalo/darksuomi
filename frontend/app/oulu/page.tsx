import type { Metadata } from "next";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";

export const metadata: Metadata = {
  title: "Dark Suomi Oulu",
  description: "Alternative music events in Oulu (experimental)",
};

/** Experimental Oulu site: its own venues and data (data/oulu/events.json). */
export default function OuluPage() {
  return <GigCalendar events={getEvents("oulu")} city="oulu" />;
}
