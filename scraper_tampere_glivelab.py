#!/usr/bin/env python3
"""
Scraper for G Livelab Tampere (https://glivelab.fi/tampere/).

The venue's front page lists all upcoming events as <li class="item"> cards:
title, date without year ("17.4."), weekday and start time. The year is
inferred: dates more than a week in the past belong to next year. The card
links to the event page on glivelab.fi, which also sells the tickets.

G Livelab is mostly a jazz / blues / singer-songwriter / indie club; every
gig is kept (genres.py sorts them out) except the few non-gig events
(drag / kiki balls, the "keikkaetkot" café series, stand-up, quizzes).

Usage:
  python scraper_tampere_glivelab.py
"""

import re
import sys
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://glivelab.fi/tampere/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
VENUE = "G Livelab Tampere"
CITY = "Tampere"

NOT_A_GIG = re.compile(r"\bball\b|keikkaetkot|stand[- ]?up|tietovisa|visailu|luento", re.I)


def infer_date(day: int, month: int, today: date) -> date | None:
    try:
        d = date(today.year, month, day)
    except ValueError:
        return None
    if d < today - timedelta(days=7):
        d = d.replace(year=today.year + 1)
    return d


def parse_cards(page_html: str, today: date, link_part: str = "/tampere/events/",
                venue: str = VENUE, city: str = CITY) -> list[dict]:
    """Event cards -> events (also used for G Livelab Helsinki: scraper_glivelab.py)."""
    soup = BeautifulSoup(page_html, "html.parser")
    events = []
    for item in soup.select("li.item"):
        link = item.select_one("a[href*='" + link_part + "']")
        h2 = item.select_one("h2.title")
        date_el = item.select_one(".datetime .date")
        if not (link and h2 and date_el):
            continue
        title = " ".join(h2.get_text(" ", strip=True).split())
        if NOT_A_GIG.search(title):
            continue
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.", date_el.get_text())
        if not m:
            continue
        day = infer_date(int(m.group(1)), int(m.group(2)), today)
        if not day:
            continue
        time_el = item.select_one(".datetime .time")
        t = re.search(r"(\d{1,2})[:.](\d{2})", time_el.get_text()) if time_el else None
        hh, mm = (int(t.group(1)), t.group(2)) if t else (0, "00")
        url = link["href"]
        event = {
            "artist": title,
            "venue": venue,
            "city": city,
            "date": f"{day.isoformat()}T{hh:02d}:{mm}:00",
            "ticketUrl": url,
            "eventUrl": url,
        }
        events.append(event)
    return events


def main() -> int:
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    today = date.today()
    scraped, seen = [], set()
    for e in parse_cards(resp.text, today):
        if e["date"][:10] >= today.isoformat() and e["eventUrl"] not in seen:
            seen.add(e["eventUrl"])
            scraped.append(e)
    print(f"✓ Found {len(scraped)} upcoming gigs at {VENUE}")
    if not scraped:
        return 1  # the page layout probably changed; fail loudly
    events = load_events(city="tampere")
    added = merge(scraped, events)
    save_events(events, city="tampere")
    print(f"✓ Added {added} new {VENUE} events ({len(events)} Tampere events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
