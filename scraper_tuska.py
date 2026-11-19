#!/usr/bin/env python3
"""
Tuska Festival (https://tuska.fi/), the metal festival at Suvilahti, Helsinki.

The site's performer list comes from a custom WordPress endpoint
(/wp-json/v1/getartists) that returns HTML grouped under day headings
("perjantai 2.7.2027"). Each festival day becomes one gig titled
"Tuska 2027: Band, Band, ..." so genres.py, setlists.py and bands.py work per
band. As Tuska announces more bands, the nightly run updates the titles.

Usage:
  python scraper_tuska.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

API = "https://tuska.fi/wp-json/v1/getartists"
TICKETS = "https://tuska.fi/liput/"
LINEUP_PAGE = "https://tuska.fi/ohjelma/esiintyjat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Suvilahti (Tuska)"
CITY = "Helsinki"
DAY = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


def nice_name(name: str) -> str:
    """'CHILDREN OF BODOM' -> 'Children Of Bodom'; mixed-case names kept."""
    name = " ".join(name.split())
    return name.title() if name.isupper() and len(name) > 3 else name


def main() -> int:
    resp = requests.get(API, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.json(), "html.parser")  # the endpoint returns an HTML string

    lineup: dict[str, list[str]] = {}
    day = None
    for el in soup.find_all(["h2", "div"]):
        if el.name == "h2":
            m = DAY.search(el.get_text())
            if m:
                d, mo, y = map(int, m.groups())
                day = f"{y:04d}-{mo:02d}-{d:02d}"
                lineup.setdefault(day, [])
        elif day and "card-artist" in (el.get("class") or []):
            title = el.select_one(".card-title, h3, h4, .title")
            name = nice_name(title.get_text(" ", strip=True)) if title else ""
            if name and name not in lineup[day]:
                lineup[day].append(name)

    today = date.today().isoformat()
    scraped = []
    for day, acts in sorted(lineup.items()):
        if day < today or not acts:
            continue
        scraped.append({
            "artist": f"Tuska {day[:4]}: {', '.join(acts)}",
            "venue": VENUE,
            "city": CITY,
            "date": f"{day}T00:00:00",
            "ticketUrl": TICKETS,
            "eventUrl": f"{LINEUP_PAGE}#{day}",
            "venueDefault": "metal",
        })

    print(f"✓ Found {len(scraped)} Tuska festival days "
          f"({sum(len(a) for a in lineup.values())} bands announced)")
    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new festival days ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
