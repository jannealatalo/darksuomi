import type { Metadata } from "next";
import { withBandInfo } from "../../lib/bands";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";
import GigJsonLd from "../GigJsonLd";

export const metadata: Metadata = {
  title: "Dark Suomi Tampere",
  description: "Alternative music events in Tampere",
};

/** Tampere site: its own venues and data (data/tampere/events.json). */
export default function TamperePage() {
  const events = getEvents("tampere");
  return (
    <>
      <GigJsonLd events={events} city="tampere" />
      <GigCalendar events={withBandInfo(events, "tampere")} city="tampere" />
    </>
  );
}
