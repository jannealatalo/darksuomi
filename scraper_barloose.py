#!/usr/bin/env python3
"""
Scraper for Bar Loose, Helsinki (https://barloose.com/live).

The site uses The Events Calendar WordPress plugin, so gigs come from its
JSON API (/wp-json/tribe/events/v1/events): title, start time, price and
the description (for a Tiketti/Lippu.fi ticket link).

A few events are entered with morning times ("07:30") although the bar is
an evening venue; times before noon are read as evening (07:30 -> 19:30).

Usage:
  python scraper_barloose.py
"""

import html
import re
import sys
from datetime import date

import requests

from eventstore import load_events, merge, save_events

API = "https://barloose.com/wp-json/tribe/events/v1/events"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Bar Loose"
CITY = "Helsinki"
MAX_PAGES = 10
TICKET_LINK = re.compile(
    r'href="(https?://[^"]*(?:tiketti\.fi|lippu\.fi|ticketmaster|holvi|eventbrite|kide\.app)[^"]*)"',
    re.I)


def fetch_upcoming() -> list[dict]:
    url = API
    params = {"per_page": 50, "start_date": date.today().isoformat()}
    events = []
    for _ in range(MAX_PAGES):
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("events", []):
            if item.get("hide_from_listings"):
                continue
            details = item["start_date_details"]
            hour, minute = int(details["hour"]), int(details["minutes"])
            if item.get("all_day"):
                hour = minute = 0
            elif hour < 12:
                hour += 12  # "07:30" at a bar is 19:30
            tickets = TICKET_LINK.findall(item.get("description", ""))
            cost = html.unescape(item.get("cost") or "").strip()
            event = {
                "artist": " ".join(html.unescape(item["title"]).split()),
                "venue": VENUE,
                "city": CITY,
                "date": f"{details['year']}-{details['month']}-{details['day']}"
                        f"T{hour:02d}:{minute:02d}:00",
                "ticketUrl": html.unescape(tickets[0]) if tickets else item["url"],
                "eventUrl": item["url"],
                # A rock bar: untagged gigs default to rock (genres.py
                # recognises DJ and comedy nights from the title first).
                "venueDefault": "rock",
            }
            if cost:
                event["price"] = cost
            events.append(event)
        url, params = data.get("next_rest_url"), None
        if not url:
            break
    return events


def main() -> int:
    scraped = fetch_upcoming()
    print(f"✓ Found {len(scraped)} upcoming events at {VENUE}")
    if not scraped:
        return 1  # the API probably changed; fail loudly
    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
