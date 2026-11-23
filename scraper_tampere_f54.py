#!/usr/bin/env python3
"""
Scraper for F54, Tampere (https://f54.fi/), the club in Finlayson's
building 54. The site uses The Events Calendar WordPress plugin, so events
come from its JSON API (/wp-json/tribe/events/v1/events).

F54 is mostly electronic club nights with an occasional metal gig, so only
gigs that fit Dark Suomi are kept (genres.keep_fitting). Private events and
"TBA" placeholders are skipped.

Usage:
  python scraper_tampere_f54.py
  python scraper_tampere_f54.py --all   # print every gig with its genres, save nothing
"""

import argparse
import html
import re
import sys
from datetime import date

import requests

import genres as g
from eventstore import load_events, merge, save_events

API = "https://f54.fi/wp-json/tribe/events/v1/events"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "F54"
CITY = "Tampere"
SITE = "tampere"
MAX_PAGES = 10
SKIP_TITLE = re.compile(r"^\s*(tba|tbc|yksityistilaisuus|private)\b", re.I)
TICKET_LINK = re.compile(
    r'href="(https?://[^"]*(?:tiketti\.fi|lippu\.fi|ticketmaster|holvi|eventbrite|kide\.app|tiketin)[^"]*)"',
    re.I)


def fetch_upcoming() -> list[dict]:
    url, params = API, {"per_page": 50, "start_date": date.today().isoformat()}
    events = []
    for _ in range(MAX_PAGES):
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("events", []):
            title = " ".join(html.unescape(item["title"]).split())
            if item.get("hide_from_listings") or SKIP_TITLE.search(title):
                continue
            d = item["start_date_details"]
            tickets = TICKET_LINK.findall(item.get("description") or "")
            event = {
                "artist": title,
                "venue": VENUE,
                "city": CITY,
                "date": f"{d['year']}-{d['month']}-{d['day']}T{d['hour']}:{d['minutes']}:00",
                "ticketUrl": html.unescape(tickets[0]) if tickets else (item.get("website") or item["url"]),
                "eventUrl": item["url"],
            }
            cost = html.unescape(item.get("cost") or "").strip()
            if cost:
                event["price"] = cost
            events.append(event)
        url, params = data.get("next_rest_url"), None
        if not url:
            break
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every gig and whether it's kept; save nothing")
    args = parser.parse_args()

    try:
        gigs = fetch_upcoming()
    except (requests.RequestException, ValueError) as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    print(f"✓ Found {len(gigs)} upcoming events at {VENUE}")
    kept = g.keep_fitting(gigs, args.all)
    if args.all:
        return 0
    events = load_events(SITE)
    added = merge(kept, events)
    save_events(events, SITE)
    print(f"✓ Kept {len(kept)} gigs that fit Dark Suomi; added {added} new "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
