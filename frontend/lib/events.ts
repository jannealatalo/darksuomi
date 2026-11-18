import events from "../data/events.json";
import type { Event } from "../types/events";

export function getEvents(): Event[] {
  return [...(events as Event[])].sort(
    (a, b) =>
      new Date(a.date).getTime() - new Date(b.date).getTime()
  );
}