export type Event = {
  id: number;
  /** Event title as listed by the venue. */
  artist: string;
  venue: string;
  city: string;
  date: string;
  ticketUrl: string;
  /** Artist names parsed from the title (added by genres.py). */
  artists?: string[];
  /** Genre tags, strongest first (added by genres.py). */
  genres?: string[];
  /** Band stage times, e.g. [{ time: "21:45", name: "Amorphis" }]. */
  schedule?: { time: string; name: string }[];
  /** Age limit as the venue writes it ("K-18", "Ikärajaton", ...). */
  age?: string;
  /** Ticket price as the venue writes it ("14€", "Vapaa pääsy!", ...). */
  price?: string;
};
