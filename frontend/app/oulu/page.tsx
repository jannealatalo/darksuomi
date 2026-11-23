import type { Metadata } from "next";
import { withBandInfo } from "../../lib/bands";
import { getEvents } from "../../lib/events";
import GigCalendar from "../GigCalendar";
import GigJsonLd from "../GigJsonLd";

export const metadata: Metadata = {
  title: "Dark Suomi Oulu",
  description: "Alternative music events in Oulu",
};

/** Oulu site: its own venues and data (data/oulu/events.json). */
export default function OuluPage() {
  const events = getEvents("oulu");
  return (
    <>
      <GigJsonLd events={events} city="oulu" />
      <GigCalendar events={withBandInfo(events, "oulu")} city="oulu" />
    </>
  );
}
