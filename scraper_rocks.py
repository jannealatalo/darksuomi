#!/usr/bin/env python3
"""
Scraper for On the Rocks, Helsinki (https://www.rocks.fi/tapahtumat/).

Reads every page of the venue's event listing and adds new gigs to
frontend/data/events.json. Each gig keeps the venue's own genre class
(`venueGenres`, e.g. "industrial", "metal", "dj"); genres.py uses it when
Last.fm and MusicBrainz know nothing about the artists.

Postponed or cancelled shows ("KEIKKA SIIRTYY", "PERUTTU", ...) are skipped.

Usage:
  python scraper_rocks.py
"""

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
EVENTS_FILE = ROOT / "frontend" / "data" / "events.json"

LIST_URL = "https://www.rocks.fi/tapahtumat/"
MAX_PAGES = 15
VENUE = "On the Rocks"
CITY = "Helsinki"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}

CANCELLED = re.compile(r"siirtyy|peruttu|peruu|postponed|cancel", re.I)
TICKET_HOSTS = re.compile(r"tiketti|lippu|ticketmaster|holvi|eventbrite|tikettiapp", re.I)
DATE_TIME = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4}).*?klo\s*(\d{1,2})[:.](\d{2})")
DATE_ONLY = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")


def fetch_page(page: int, list_url: str = LIST_URL) -> str | None:
    # The listing uses the Search & Filter plugin's ?sf_paged=N; the /page/N/
    # links in the HTML just return the first page again.
    url = list_url if page == 1 else f"{list_url}?sf_paged={page}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.text


def parse_events(html: str, venue: str = VENUE) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for article in soup.select("article.tapahtuma.loop-item"):
        link = article.select_one("h1 a")
        date_info = article.select_one(".date-info")
        if not link or not date_info:
            continue

        title = " ".join((link.get("title") or link.get_text()).split())
        if CANCELLED.search(title):
            print(f"  skipping (postponed/cancelled): {title[:70]}")
            continue

        text = date_info.get_text(" ", strip=True)
        m = DATE_TIME.search(text)
        if m:
            day, month, year, hour, minute = map(int, m.groups())
        else:
            m = DATE_ONLY.search(text)
            if not m:
                continue
            day, month, year = map(int, m.groups())
            hour = minute = 0

        tickets = [a["href"] for a in article.select("a[href]")
                   if TICKET_HOSTS.search(a["href"])]
        genres = [c.removeprefix("tapahtumaluokka-") for c in article.get("class", [])
                  if c.startswith("tapahtumaluokka-")]

        sold_out = article.select_one(".lippujen-lisatieto.loppuunmyyty")
        events.append({
            **({"status": "sold out"} if sold_out else {}),
            "artist": title,
            "venue": venue,
            "city": CITY,
            "date": f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00",
            "ticketUrl": tickets[0] if tickets else link["href"],
            "eventUrl": link["href"],
            "venueGenres": genres,
        })
    return events


def main(list_url: str = LIST_URL, venue: str = VENUE) -> int:
    """Scrape a Mediaani-built venue site (On the Rocks, Lepakkomies)."""
    scraped: list[dict] = []
    seen_urls: set[str] = set()
    for page in range(1, MAX_PAGES + 1):
        html = fetch_page(page, list_url)
        if html is None:
            break
        found = [e for e in parse_events(html, venue) if e["eventUrl"] not in seen_urls]
        if not found:  # empty page, or the same page served again
            break
        seen_urls.update(e["eventUrl"] for e in found)
        scraped += found
    print(f"✓ Found {len(scraped)} events at {venue}")
    if not scraped:
        return 1  # the site layout probably changed; fail loudly

    with open(EVENTS_FILE, encoding="utf-8") as f:
        events = json.load(f)

    def key(e: dict) -> tuple:
        return (e["venue"], e["date"][:10], e["artist"].casefold().strip())

    by_key = {key(e): e for e in events}
    by_url = {e["eventUrl"]: e for e in events if e.get("eventUrl")}

    # A renamed gig ("Killer (BE)" -> "Killer (BEL)") gets a new page address
    # too, but keeps its ticket link; match on that so it isn't added twice.
    def ticket_key(e: dict) -> tuple | None:
        if not e.get("ticketUrl") or e["ticketUrl"] == e.get("eventUrl"):
            return None
        return (e["venue"], e["date"][:10], e["ticketUrl"])

    by_ticket = {ticket_key(e): e for e in events if ticket_key(e)}
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    added = 0
    for event in scraped:
        existing = by_url.get(event["eventUrl"]) or by_key.get(key(event))
        renamed = None if existing else by_ticket.get(ticket_key(event))
        if renamed:
            renamed["artist"] = event["artist"]
            existing = renamed
        if existing:
            # Keep details current (time, ticket link, venue genres).
            for field in ("date", "ticketUrl", "eventUrl", "venueGenres"):
                existing[field] = event[field]
            if event.get("status"):
                existing["status"] = event["status"]
            else:
                existing.pop("status", None)
            continue
        event["id"] = next_id
        next_id += 1
        events.append(event)
        by_key[key(event)] = event
        added += 1

    events.sort(key=lambda e: e["date"])
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"✓ Added {added} new {venue} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
