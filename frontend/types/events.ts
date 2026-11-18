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
};
