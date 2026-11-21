import { withBandInfo } from "../lib/bands";
import { getEvents } from "../lib/events";
import GigCalendar from "./GigCalendar";

export default function Home() {
  return <GigCalendar events={withBandInfo(getEvents("helsinki"), "helsinki")} city="helsinki" />;
}
