#!/usr/bin/env python3
"""
Scraper for the Helsinki Olympic Stadium (https://www.stadion.fi/en/events/events).

Reads the "Upcoming events" list (the Drupal view "event-listing--list"; the
page also shows past events in another view, which is ignored). Sport events
(City Run, relay games, national football team) are skipped. "Club Stadion"
gigs, the stadium's small club series, are named after the act, e.g.
"CLUB STADION - HERRA YLPPÖ" -> "Herra Ylppö (Club Stadion)".

Usage:
  python scraper_stadion.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

SITE = "https://www.stadion.fi"
LIST_URL = f"{SITE}/en/events/events"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Olympiastadion"
CITY = "Helsinki"

SPORT = re.compile(r"\brun\b|karneval|huuhkajat|\bsuomi\b.*\b-\b|jalkapallo|football|"
                   r"ski weeks|kouluviesti|stafett|marathon|gaala|tour of", re.I)
# "Sat 12.6.2027", "18.6-19.6.2027", "28.5-29.8.2026"
DATE = re.compile(r"(\d{1,2})\.(\d{1,2})\.?(\d{4})?(?:\s*-\s*\d{1,2}\.\d{1,2}\.(\d{4}))?")
CLUB = re.compile(r"^club\s+stadion\s*[-–]\s*", re.I)


def nice_name(name: str) -> str:
    """'HERRA YLPPÖ' -> 'Herra Ylppö' (only for all-caps names)."""
    return name.title() if name.isupper() else name


def main() -> int:
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    view = soup.select_one(".views-view--event-listing--list")
    if not view:
        print("✗ Upcoming events list not found (page layout changed?)", file=sys.stderr)
        return 1

    today = date.today().isoformat()
    scraped = []
    for card in view.select("article.node--type-event"):
        title_el, date_el = card.select_one("h2"), card.select_one(".event-date")
        if not (title_el and date_el):
            continue
        title = " ".join(title_el.get_text(" ", strip=True).split())
        if SPORT.search(title):
            continue
        m = DATE.search(date_el.get_text(" ", strip=True))
        if not m:
            continue
        d, mo = int(m.group(1)), int(m.group(2))
        year = int(m.group(3) or m.group(4))
        day = f"{year:04d}-{mo:02d}-{d:02d}"
        if day < today:
            continue

        if CLUB.match(title):
            title = f"{nice_name(CLUB.sub('', title))} (Club Stadion)"

        own_site = next((a["href"] for a in card.select("a[href]")
                         if "own website" in a.get_text().lower()), None)
        node = card.get("about") or ""
        page = SITE + node if node.startswith("/") else LIST_URL
        scraped.append({
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{day}T00:00:00",
            "ticketUrl": own_site or page,
            "eventUrl": f"{page}#{day}",
        })

    print(f"✓ Found {len(scraped)} upcoming music events at {VENUE}")
    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
