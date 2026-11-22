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
  "Suvilahti (Tuska)": "https://tuska.fi/",
  Korjaamo: "https://korjaamo.fi/tapahtumat/",
  Dubrovnik: "https://www.dubrovnik.fi/",
  Ääniwalli: "https://aaniwalli.fi/",
  "Apollo Live Club": "https://apolloliveclub.fi/tapahtumat/",
  Sellosali: "https://www.espoo.fi/fi/sellosalin-tapahtumat?topics=Musiikki",
  // Tuusula, at Hotel Krapi; the club gigs are listed in its web shop.
  "Krapin Paja": "https://kauppa.krapinpaja.fi/category/pajan-klubit",
  // Tampere
  "Tavara-asema": "https://tavara-asema.fi/",
  Pakkahuone: "https://tullikamari.fi/",
  "Tullikamarin Klubi": "https://tullikamari.fi/",
  Olympia: "https://olympiakortteli.fi/keikat/",
  "Vastavirta-klubi": "https://vastavirta.net/",
  "G Livelab Tampere": "https://glivelab.fi/tampere/",
  "Nokia Arena": "https://nokiaarena.fi/",
  "Bar Kotelo": "https://barkotelo.fi/",
  // Oulu
  "45 Special": "https://45special.com/",
  Tullisali: "https://www.tullisali.fi/",
  Tarkastamo: "https://tarkastamo-oulu.fi/tapahtumat/",
  "Toppila Klubi": "https://toppilaklubi.fi/",
  "Oulun Musiikkikeskus": "https://www.oulunmusiikkikeskus.fi/",
  "Ouluhallin parkkialue (Rokki Raikaa)": "https://rokkiraikaa.fi/oulu-2027/",
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

/** Ticket shops: a link there is "Tickets", not the venue's page. */
const TICKET_SHOPS =
  /(^|\.)(tiketti\.fi|lippu\.fi|ticketmaster\.\w+|livenation\.\w+|eventbrite\.[\w.]+|biletti\.fi|eventu\.al|weezevent\.com|cluby\.com|holvi\.com)$/;

function isTicketShop(url: string): boolean {
  try {
    return TICKET_SHOPS.test(new URL(url).hostname);
  } catch {
    return true; // not a usable URL
  }
}

/**
 * Where the venue name of a gig links: the gig's page at the venue (or the
 * listing it was found in) when there is one, else the venue's home page.
 */
export function venueUrl(event: {
  venue: string;
  eventUrl?: string;
  ticketUrl: string;
}): string | undefined {
  for (const url of [event.eventUrl, event.ticketUrl]) {
    if (url && !isTicketShop(url)) return url;
  }
  return VENUE_LINKS[event.venue];
}
