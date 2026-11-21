import type { Metadata } from "next";
import { withBandInfo } from "../../lib/bands";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";

export const metadata: Metadata = {
  title: "Dark Suomi Tampere",
  description: "Alternative music events in Tampere",
};

/** Tampere site: its own venues and data (data/tampere/events.json). */
export default function TamperePage() {
  return <GigCalendar events={withBandInfo(getEvents("tampere"), "tampere")} city="tampere" />;
}
