#!/usr/bin/env python3
"""
Scraper for Oulu rock clubs that sell tickets through ParhaatBileet.fi:
Toppila Klubi (https://toppilaklubi.fi/), Hevimesta and Kantakrouvi.

ParhaatBileet.fi is a WordPress ticket shop running The Events Calendar, so
its public REST API (/lippukauppa/wp-json/tribe/events/v1/events) lists
upcoming events per category; each venue has its own category under
"keikat". Times are local (Europe/Helsinki). Titles end with the venue and
date ("SARA Toppila Klubi 12.2.2027"), which is stripped. Toppila Klubi's
Christmas parties, karaoke and bingo nights are skipped.

Hevimesta and Kantakrouvi currently sell most tickets elsewhere (Lippu.fi /
Ticketmaster; see scraper_oulu_munoulu.py), so their categories here are
often empty; they are still checked so new gigs show up.

Usage:
  python scraper_oulu_parhaatbileet.py
"""

import html
import re
import sys
from datetime import date

import requests

from eventstore import load_events, merge, save_events

API = "https://www.parhaatbileet.fi/lippukauppa/wp-json/tribe/events/v1/events"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)",
           "Accept": "application/json"}
CITY = "Oulu"
MAX_PAGES = 5
# Event category id -> venue name (category "keikat" > venue).
VENUES = {
    135: "Toppila Klubi",
    1582: "Hevimesta",
    1580: "Kantakrouvi",
}
NOT_MUSIC = re.compile(r"pikkujoul|karaoke|bingo|visa\b|quiz|stand ?-?up|tanssikurssi|"
                       r"\bdisko\b|\bdj\b", re.I)


def clean_title(title: str, venue: str) -> str:
    title = " ".join(html.unescape(title).split())
    # "Uniklubi Toppila Klubi 13.2.2027" -> "Uniklubi"
    title = re.sub(r"\s*[-–@,]?\s*" + re.escape(venue) + r"\b.*$", "", title, flags=re.I)
    title = re.sub(r"\s+\d{1,2}\.\d{1,2}\.\d{2,4}\s*$", "", title)
    return title.strip(" -–")


def price_text(cost: str) -> str | None:
    cost = html.unescape(cost or "").strip()
    if not cost:
        return None
    cost = re.sub(r"(\d+)\.00\b", r"\1", cost)
    cost = re.sub(r"(\d+)\.(\d{2})\b", r"\1,\2", cost)
    return cost.replace("€", " €").replace("  ", " ").strip()


def fetch_venue(cat_id: int, venue: str) -> list[dict]:
    events = []
    params = {"categories": cat_id, "per_page": 50, "start_date": date.today().isoformat()}
    url = API
    for _ in range(MAX_PAGES):
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if resp.status_code == 404:  # Tribe answers 404 when nothing matches
            break
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("events", []):
            title = clean_title(item.get("title", ""), venue)
            if not title or NOT_MUSIC.search(title):
                continue
            start = item.get("start_date", "")  # "2026-11-21 20:00:00", local time
            if not re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", start):
                continue
            hhmm = start[11:16]
            event = {
                "artist": title,
                "venue": venue,
                "city": CITY,
                "date": f"{start[:10]}T{hhmm}:00",
                "ticketUrl": item["url"],
                "eventUrl": item["url"],
            }
            if hhmm != "00:00":
                event["doors"] = hhmm
            price = price_text(item.get("cost", ""))
            if price:
                event["price"] = price
            events.append(event)
        url, params = data.get("next_rest_url"), None
        if not url:
            break
    return events


def main() -> int:
    scraped = []
    try:
        for cat_id, venue in VENUES.items():
            found = fetch_venue(cat_id, venue)
            print(f"  {venue}: {len(found)} upcoming gigs")
            scraped += found
    except (requests.RequestException, ValueError) as exc:
        print(f"✗ Could not fetch ParhaatBileet.fi events: {exc}")
        return 1

    today = date.today().isoformat()
    scraped = [e for e in scraped if e["date"][:10] >= today]
    print(f"✓ Found {len(scraped)} upcoming music events on ParhaatBileet.fi")
    if not scraped:
        return 1  # Toppila Klubi always has gigs listed; the API probably changed
    events = load_events(city="oulu")
    added = merge(scraped, events)
    save_events(events, city="oulu")
    print(f"✓ Added {added} new events ({len(events)} Oulu events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
