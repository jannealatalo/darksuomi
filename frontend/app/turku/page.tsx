import type { Metadata } from "next";
import { withBandInfo } from "../../lib/bands";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";
import GigJsonLd from "../GigJsonLd";

export const metadata: Metadata = {
  title: "Dark Suomi Turku",
  description: "Alternative music events in Turku",
};

/** Turku site: its own venues and data (data/turku/events.json). */
export default function TurkuPage() {
  const events = getEvents("turku");
  return (
    <>
      <GigJsonLd events={events} city="turku" />
      <GigCalendar events={withBandInfo(events, "turku")} city="turku" />
    </>
  );
}
