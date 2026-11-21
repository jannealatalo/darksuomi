/** A band on the bill, from the band directory (see withBandInfo). */
export type GigBand = {
  name: string;
  /** Anchor in /bands: /bands#band-<slug> */
  slug: string;
  links: Partial<Record<string, string>>;
};

export type Event = {
  id: number;
  /** Event title as listed by the venue. */
  artist: string;
  venue: string;
  city: string;
  date: string;
  ticketUrl: string;
  /** The gig's own page where the scraper found it (usually the venue's site). */
  eventUrl?: string;
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
  /** Ticket sales, from the venue listing; absent while on sale. */
  status?: "sold out" | "cancelled";
  /** Directory entries of the bands on the bill (Helsinki front page only). */
  bands?: GigBand[];
};
