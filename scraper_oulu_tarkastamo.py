#!/usr/bin/env python3
"""
Scraper for Tarkastamo, Oulu (https://tarkastamo-oulu.fi/tapahtumat/).

Tarkastamo is the ~1,200-capacity event hall of the market-square hotel
(opened 2026). Its WordPress events page lists every upcoming event as
".events-featured__item" cards: weekday + day ("LA 12.12.", no year), the
title, a short description and prices. The site's REST API has no event
dates, so each event page is read for the details: the stage schedule
("19:00 Ovet", "20:00 The Ghoulstars", "21:00 Turmion Kätilöt") and the
age limit. Tickets are sold through an embedded widget, so the event page
doubles as the ticket link.

No year is shown anywhere: a day earlier in the year than today is taken to
be next year (the list only has upcoming events). Magic and dinner shows
are skipped; everything else is music and goes through the genre filter.

Usage:
  python scraper_oulu_tarkastamo.py
"""

import re
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://tarkastamo-oulu.fi/tapahtumat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Tarkastamo"
CITY = "Oulu"
SKIP = re.compile(r"magic show|stand ?up|standup|komiikk|illallis|dinner", re.I)
AGE_MARK = re.compile(r"\s*\((?:S\s*/\s*K-?18|K-?18|-?S-?|K-?\d{1,2})\)\s*$", re.I)
DOORS = {"ovet", "doors", "ovet aukeavat"}
INTERVAL = re.compile(r"väliaika|tauko|intermission|break|dj\b", re.I)


def text(el) -> str:
    # The site hyphenates titles with soft hyphens (Tur\xadmion).
    return " ".join(el.get_text(" ", strip=True).replace("\xad", "").split())


def guess_year(day: int, month: int, today: date) -> int:
    return today.year + 1 if (month, day) < (today.month, today.day) else today.year


def clean_title(title: str) -> str:
    title = AGE_MARK.sub("", title).strip()
    return re.sub(r"\s*\|\s*", " + ", title).strip(" +")


def lineup_title(title: str, schedule: list[dict]) -> str:
    """
    Name every act of a multi-act night, headliner (last on stage) first, so
    genres.py sees them all: "Turmion Kätilöt" -> "Turmion Kätilöt + The
    Ghoulstars"; a show name stays as a "Show: act, act" prefix ("ANKARA -
    Graham Bonnet + ..." -> "ANKARA: Stam1na, Zero Nine, Mustasch, ...").
    """
    acts = []
    for row in schedule:
        name = row["name"]
        if name.casefold() not in {a.casefold() for a in acts} and not INTERVAL.match(name):
            acts.append(name)
    if len(acts) < 2:
        return title
    acts.reverse()
    main = re.split(r"\s+[-–]\s+|:\s", title, maxsplit=1)[0].strip()
    if main.casefold() in {a.casefold() for a in acts}:
        return " + ".join(acts)
    return f"{main}: {', '.join(acts)}"


def parse_list(html: str, today: date) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events, seen = [], set()
    for card in soup.select(".events-featured__item"):
        link = card.select_one(".events-featured__title a[href]")
        day = card.select_one(".events-featured__day")
        if not (link and day) or link["href"] in seen:
            continue
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.", day.get_text())
        if not m:
            continue
        title = text(link)
        if SKIP.search(title):
            continue
        seen.add(link["href"])
        d, mo = int(m.group(1)), int(m.group(2))
        y = guess_year(d, mo, today)
        event = {
            "artist": clean_title(title),
            "venue": VENUE,
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T00:00:00",
            "ticketUrl": link["href"],
            "eventUrl": link["href"],
        }
        price = card.select_one(".events-featured__prices p")
        if price and text(price):
            event["price"] = text(price)
        events.append(event)
    return events


def add_details(event: dict) -> None:
    """Doors, stage times and age limit from the event page."""
    resp = requests.get(event["eventUrl"], headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    schedule = []
    for row in soup.select(".single-event__schedule-row"):
        t = row.select_one(".single-event__schedule-time")
        name = row.select_one(".single-event__schedule-artist")
        if not (t and name):
            continue
        tm = re.match(r"(\d{1,2})[:.](\d{2})", text(t))
        if not tm:
            continue
        hhmm = f"{int(tm.group(1)):02d}:{tm.group(2)}"
        if text(name).lower() in DOORS:
            event["doors"] = hhmm
        else:
            schedule.append({"time": hhmm, "name": text(name)})
    if schedule:
        event["schedule"] = schedule
        event["artist"] = lineup_title(event["artist"], schedule)
    start = event.get("doors") or (schedule[0]["time"] if schedule else None)
    if start:
        event["date"] = event["date"][:11] + start + ":00"
    age = soup.select_one(".single-event__age-limit-badge")
    if age and text(age):
        event["age"] = text(age)
    event["detailsFetched"] = True


def main() -> int:
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    scraped = parse_list(resp.text, date.today())
    print(f"✓ Found {len(scraped)} upcoming music events at {VENUE}")
    if not scraped:
        return 1  # the page layout probably changed; fail loudly
    for event in scraped:
        try:
            add_details(event)
        except requests.RequestException as e:
            print(f"  ! no details for {event['artist']}: {e}")
        time.sleep(0.5)
    events = load_events(CITY.lower())
    added = merge(scraped, events)
    save_events(events, CITY.lower())
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
