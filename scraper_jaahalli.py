#!/usr/bin/env python3
"""
Scraper for Helsingin Jäähalli (https://helsinginjaahalli.fi/tapahtumat).

The ice hall mostly hosts HIFK hockey, plus big rock/metal concerts. Sport
events carry the CSS class "urheilu" in the list and are skipped, as are a
few non-concert titles (school dances, galas, stunt shows).

For each remaining gig, the event page is read for support acts ("+ Support:
Dark Divine", "Very Special Guests: Pendulum"), which are added to the title,
and for the ticket price.

Usage:
  python scraper_jaahalli.py
"""

import re
import sys
import time

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://helsinginjaahalli.fi/tapahtumat"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Helsingin Jäähalli"
CITY = "Helsinki"
PAGE_DELAY = 1.0

NOT_A_CONCERT = re.compile(r"vanhojen|jatkot|gaala|trophy|stunt|messut|seminaari", re.I)
DATETIME = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})")
SUPPORT_LINE = re.compile(
    r"^\+?\s*(?:very\s+)?(?:special\s+guests?|support(?:\s+acts?)?|vieraina?|lämppär\w*)"
    r"\s*:\s*(.+)$", re.I)
PRICE = re.compile(r"Liput\s+alk\.?\s*([\d,.]+)\s*(?:EUR|€)", re.I)


def gig_details(url: str) -> dict:
    """Support acts and ticket price from a gig's own page."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    lines = [" ".join(l.split()) for l in soup.get_text("\n").split("\n") if l.strip()]
    details: dict = {"support": []}
    for line in lines:
        m = SUPPORT_LINE.match(line)
        if m:
            details["support"] += [a.strip() for a in re.split(r",|\s+&\s+|\s+ja\s+", m.group(1))
                                   if a.strip() and not re.search(r"tba|julkaistaan", a, re.I)]
        if "price" not in details:
            p = PRICE.search(line)
            if p:
                details["price"] = f"alk. {p.group(1)} €"
    return details


def main() -> int:
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    scraped, seen = [], set()
    for card in soup.select("div.custom-tapahtuma"):
        if "urheilu" in card.get("class", []):
            continue
        link, when, h3 = card.select_one('a[href*="/events/"]'), card.select_one("time"), card.select_one("h3")
        if not (link and when and h3) or link["href"] in seen:
            continue
        seen.add(link["href"])
        title = " ".join(h3.get_text(" ", strip=True).split())
        if NOT_A_CONCERT.search(title):
            continue
        m = DATETIME.search(when.get("datetime", ""))
        if not m:
            continue
        d, mo, y, hh, mm = map(int, m.groups())
        scraped.append({
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mm:02d}:00",
            "ticketUrl": link["href"],
            "eventUrl": link["href"],
        })

    print(f"✓ Found {len(scraped)} concerts at {VENUE}")
    if not scraped:
        return 1  # the page layout probably changed; fail loudly

    for i, event in enumerate(scraped):
        if i:
            time.sleep(PAGE_DELAY)
        try:
            extra = gig_details(event["eventUrl"])
        except requests.RequestException as e:
            print(f"  ! {event['artist'][:40]}: {e}", file=sys.stderr)
            continue
        if extra["support"]:
            event["artist"] = f"{event['artist']}, {', '.join(extra['support'])}"
        if extra.get("price"):
            event["price"] = extra["price"]

    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
