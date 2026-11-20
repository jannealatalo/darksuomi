import { getEvents } from "../lib/events";
import GigCalendar from "./GigCalendar";

export default function Home() {
  return <GigCalendar events={getEvents("helsinki")} city="helsinki" />;
}
