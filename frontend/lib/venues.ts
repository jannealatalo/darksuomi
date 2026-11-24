/**
 * Street addresses of the venues, for the gigs' structured data (Google
 * shows an event only with its place's address). Keyed by the venue name
 * as the scrapers write it. A venue missing here still gets its city.
 *
 * Checked against OpenStreetMap in November 2026.
 */
export type VenueAddress = { street: string; postalCode: string; city: string };

const v = (street: string, postalCode: string, city: string): VenueAddress => ({
  street,
  postalCode,
  city,
});

export const VENUE_ADDRESSES: Record<string, VenueAddress> = {
  // Helsinki region
  "Tavastia Klubi": v("Urho Kekkosen katu 4-6", "00100", "Helsinki"),
  Semifinal: v("Urho Kekkosen katu 6", "00100", "Helsinki"),
  Kulttuuritalo: v("Sturenkatu 4", "00510", "Helsinki"),
  KULT: v("Sturenkatu 4", "00510", "Helsinki"),
  Korjaamo: v("Töölönkatu 51", "00250", "Helsinki"),
  "On the Rocks": v("Mikonkatu 15", "00100", "Helsinki"),
  Lepakkomies: v("Helsinginkatu 1", "00500", "Helsinki"),
  "Bar Loose": v("Annankatu 21", "00100", "Helsinki"),
  "Veikkaus Arena": v("Areenankuja 1", "00240", "Helsinki"),
  "G Livelab": v("Yrjönkatu 3", "00120", "Helsinki"),
  Tiivistämö: v("Kaasutehtaankatu 1", "00540", "Helsinki"),
  "Suvilahti (Tuska)": v("Kaasutehtaankatu 1", "00540", "Helsinki"),
  Ääniwalli: v("Pälkäneentie 13", "00510", "Helsinki"),
  "Helsingin Jäähalli": v("Nordenskiöldinkatu 11-13", "00250", "Helsinki"),
  Olympiastadion: v("Paavo Nurmen tie 1", "00250", "Helsinki"),
  Dubrovnik: v("Eerikinkatu 11", "00100", "Helsinki"),
  "Apollo Live Club": v("Mannerheimintie 16", "00100", "Helsinki"),
  "Allas Live": v("Katajanokanlaituri 2a", "00160", "Helsinki"),
  "Espoon kulttuurikeskus": v("Kulttuuriaukio 2", "02100", "Espoo"),
  Sellosali: v("Soittoniekanaukio 1 A", "02600", "Espoo"),
  Kannusali: v("Kannusillankatu 4", "02770", "Espoo"),
  "Krapin Paja": v("Rantatie 2", "04310", "Tuusula"),
  // Tampere
  "G Livelab Tampere": v("Puutarhakatu 1", "33100", "Tampere"),
  Pakkahuone: v("Tullikamarin aukio 2", "33100", "Tampere"),
  "Tullikamarin Klubi": v("Tullikamarin aukio 2", "33100", "Tampere"),
  "Tavara-asema": v("Ratapihankatu 33", "33100", "Tampere"),
  "Vastavirta-klubi": v("Pispalan valtatie 39", "33250", "Tampere"),
  Olympia: v("Hämeenkatu 26", "33200", "Tampere"),
  "Bar Kotelo": v("Sammonkatu 50", "33540", "Tampere"),
  "Nokia Arena": v("Kansikatu 3", "33100", "Tampere"),
  Varjobaari: v("Insinöörinkatu 38", "33720", "Tampere"),
  // Oulu
  "45 Special": v("Saaristonkatu 4", "90100", "Oulu"),
  Tarkastamo: v("Saaristonkatu 1c", "90100", "Oulu"),
  Tullisali: v("Tyrnäväntie 16", "90400", "Oulu"),
  "Oulun Musiikkikeskus": v("Leiritie 1", "90100", "Oulu"),
  "Toppila Klubi": v("Kapteenintie 24", "90520", "Oulu"),
  Tukikohta: v("Sorvarintie 5", "90530", "Oulu"),
  Hevimesta: v("Isokatu 36", "90100", "Oulu"),
  Kantakrouvi: v("Uusikatu 23", "90100", "Oulu"),
  "Oulun Energia Areena": v("Teuvo Pakkalan katu 11", "90130", "Oulu"),
  "Ouluhallin parkkialue (Rokki Raikaa)": v("Ouluhallintie 20", "90130", "Oulu"),
};
