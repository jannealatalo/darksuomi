/** Venue home pages, keyed by the venue name used in events.json. */
export const VENUE_LINKS: Record<string, string> = {
  "Tavastia Klubi": "https://tavastiaklubi.fi/",
  "On the Rocks": "https://www.rocks.fi/",
  Kulttuuritalo: "https://kulttuuritalo.fi/",
  KULT: "https://kulttuuritalo.fi/kult/",
  "Bar Loose": "https://barloose.com/",
  "Veikkaus Arena": "https://www.veikkausarena.fi/all-events",
  Semifinal: "https://tavastiaklubi.fi/semifinal/",
  Lepakkomies: "https://www.lepis.fi/",
  // Former Kulttuuriareena Gloria; run by the City of Helsinki youth services.
  Tiivistämö: "https://nuorten.hel.fi/en/youth-centers/tiivistamo/",
  "Helsingin Jäähalli": "https://helsinginjaahalli.fi/tapahtumat",
  Olympiastadion: "https://www.stadion.fi/en/events/events",
};

export type SiteLink = { name: string; url: string };

/** Official ticket sellers. */
export const TICKET_SITES: SiteLink[] = [
  { name: "Tiketti", url: "https://www.tiketti.fi/" },
  { name: "Lippu.fi", url: "https://www.lippu.fi/" },
  { name: "Ticketmaster", url: "https://www.ticketmaster.fi/" },
  { name: "Live Nation", url: "https://www.livenation.fi/" },
];

/** Fan-to-fan ticket resale. */
export const RESALE_SITES: SiteLink[] = [
  { name: "Liputon", url: "https://www.liputon.fi/" },
  { name: "Liput vaihtoon", url: "https://liputvaihtoon.fi/liput" },
];

/** Records and band merch; Bandcamp first since it pays bands directly. */
export const MERCH_SITES: SiteLink[] = [
  { name: "Bandcamp", url: "https://bandcamp.com/" },
  { name: "Levykauppa Äx", url: "https://www.levykauppax.fi/" },
  { name: "Svart Records", url: "https://www.svartrecords.com/" },
  { name: "Swamp Music", url: "https://www.swampmusic.com/" },
  { name: "Backstage Rock Shop", url: "https://www.backstagerockshop.com/" },
  { name: "Stupido Records", url: "https://www.stupido.fi/" },
  { name: "Inverse", url: "https://inverse.fi/" },
];

/** Finnish music media: news, reviews, interviews. */
export const MEDIA_SITES: SiteLink[] = [
  { name: "Desibeli.net", url: "https://desibeli.net/" },
  { name: "Kaaoszine", url: "https://kaaoszine.fi/" },
  { name: "Inferno", url: "https://www.inferno.fi/" },
  { name: "Soundi", url: "https://www.soundi.fi/" },
  { name: "Rumba", url: "https://www.rumba.fi/" },
  { name: "Noise.fi", url: "https://www.noise.fi/" },
  { name: "IMPE", url: "https://impe.fi/" },
  { name: "Metalliluola", url: "https://www.metalliluola.fi/" },
  { name: "Tuonela Magazine", url: "https://www.tuonelamagazine.com/" },
];
