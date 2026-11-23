import { withBandInfo } from "../lib/bands";
import { getEvents } from "../lib/events";
import GigCalendar from "./GigCalendar";
import GigJsonLd from "./GigJsonLd";

export default function Home() {
  const events = getEvents("helsinki");
  return (
    <>
      <GigJsonLd events={events} city="helsinki" />
      <GigCalendar events={withBandInfo(events, "helsinki")} city="helsinki" />
    </>
  );
}
