#!/usr/bin/env python3
"""
Scraper for Veikkaus Arena, Helsinki (https://www.veikkausarena.fi/all-events).

The arena hosts ice hockey, galas, family shows and concerts. Its site loads
events from a JSON search API; every event has genre keys, and only events
with at least one music genre are kept (rock, metal, indie, pop, rap, R&B).
Sports, comedy-only, arts & culture and "other" events are skipped.

Each gig gets doors time, show time, age limit and a Ticketmaster link.
Several events share one page URL (e.g. two Pitbull nights), so the stored
eventUrl gets the date appended to keep gigs apart.

Usage:
  python scraper_veikkausarena.py
"""

import sys

import requests

from eventstore import load_events, merge, save_events

SITE = "https://www.veikkausarena.fi"
API = f"{SITE}/__api/search/events"
VENUE_ID = 4671
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)",
           "Accept": "application/json"}
VENUE = "Veikkaus Arena"
CITY = "Helsinki"
PAGE_SIZE = 100
MAX_PAGES = 10

# The arena's genre keys that mean music -> our genre names (used only when
# Last.fm and MusicBrainz know nothing about the artists).
MUSIC_GENRES = {
    "rock": "rock",
    "hard-rock-and-metal": "metal",
    "alternative-and-indie": "indie",
    "pop": "pop",
    "hip-hop-and-rap": "rap",
    "rnb-and-soul": "r&b",
}


def fetch_music_events() -> list[dict]:
    events, page, total = [], 1, None
    while page <= MAX_PAGES:
        resp = requests.get(API, headers=HEADERS, timeout=30, params={
            "VenueIds": VENUE_ID, "IncludePostponed": "false",
            "IncludeCancelled": "false", "Url": "/all-events",
            "PageSize": PAGE_SIZE, "Page": page, "culture": "fi-FI",
        })
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("documents", [])
        total = data.get("total", 0)
        for doc in docs:
            keys = [g.get("key") for g in doc.get("genres") or [] if isinstance(g, dict)]
            music = [MUSIC_GENRES[k] for k in keys if k in MUSIC_GENRES]
            if not music or doc.get("isDeleted"):
                continue

            day = doc["eventDate"][:10]
            doors = (doc.get("doorTime") or "").strip()
            show = (doc.get("showTime") or "").strip()
            tickets = [t.get("ticketUrl") for t in doc.get("tickets") or []
                       if t.get("isVisible", True) and t.get("ticketUrl")]
            page_url = SITE + doc["url"] if doc.get("url") else SITE + "/all-events"

            event = {
                "artist": " ".join(doc["name"].split()),
                "venue": VENUE,
                "city": CITY,
                "date": f"{day}T{doors or show or '00:00'}:00",
                "ticketUrl": tickets[0] if tickets else page_url,
                # Several nights can share one page; keep them apart.
                "eventUrl": f"{page_url}#{day}",
                "venueGenres": music,
            }
            if doors:
                event["doors"] = doors
            if show and show != doors:
                event["schedule"] = [{"time": show, "name": "Show starts"}]
            if doc.get("agePolicy"):
                event["age"] = doc["agePolicy"]
            events.append(event)
        if not docs or page * PAGE_SIZE >= total:
            break
        page += 1
    return events


def main() -> int:
    scraped = fetch_music_events()
    print(f"✓ Found {len(scraped)} upcoming music events at {VENUE}")
    if not scraped:
        return 1  # the API probably changed; fail loudly
    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
