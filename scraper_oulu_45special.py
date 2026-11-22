#!/usr/bin/env python3
"""
Scraper for 45 Special, Oulu (https://45special.com/).

The club's programme lives in its gapp.fi web shop (https://45special.gapp.fi/),
a JavaScript app that reads a public JSON API on Heroku:
  https://production45special.herokuapp.com/api/v1/companies/45special/events
Each event has its title ("names"), a short price line ("descriptions",
e.g. "20 / 23€ + PM"), a long description and two UTC times: startDate
(doors) and gigStartDate (show). The event page is
https://45special.gapp.fi/event/<id>.

45 Special is mostly a rock club but also books rap and pop, so no
venueDefault is set. Stand-up / open mic nights and DJ club nights are
skipped (a long description that keeps saying "DJ" is a club night).

Usage:
  python scraper_oulu_45special.py
"""

import re
import sys
from datetime import date

import requests

from eventstore import load_events, merge, save_events
from scraper_tiivistamo import finnish_time

API = "https://production45special.herokuapp.com/api/v1/companies/45special/events"
EVENT_PAGE = "https://45special.gapp.fi/event/{id}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)",
           "Accept": "application/json"}
VENUE = "45 Special"
CITY = "Oulu"

NOT_MUSIC = re.compile(r"stand ?-?up|open mic|karaoke|pubivisa|quiz|bingo|"
                       r"\bdj\b|\bdjs\b|club night|klubi-?ilta", re.I)
AGE_IN_TITLE = re.compile(r"\s*\(\s*(S\s*/\s*K-?\s?18|K-?\s?18|S)\s*\)\s*", re.I)
SOLD_OUT = re.compile(r"\s*\(?\b(loppuunmyyty|sold out)\b\)?!?\s*", re.I)
AGE_IN_TEXT = re.compile(r"\b(S\s*/\s*K-?\s?18|K-?\s?18)\b", re.I)


def text(values: list[dict]) -> str:
    """First Finnish (or any) value of a gapp multilingual field."""
    values = values or []
    for v in values:
        if v.get("language") == "fi" and v.get("value"):
            return v["value"]
    return next((v.get("value") or "" for v in values), "")


def norm_age(raw: str) -> str:
    raw = raw.upper().replace(" ", "")
    return raw.replace("K18", "K-18")


def parse(items: list[dict]) -> list[dict]:
    events = []
    today = date.today().isoformat()
    for item in items:
        if item.get("isDeleted") or not item.get("isVisible", True):
            continue
        name = " ".join(text(item.get("names")).split())
        long_desc = text(item.get("longDescriptions"))
        if not name or NOT_MUSIC.search(name):
            continue
        if len(re.findall(r"\bDJ", long_desc)) >= 3:  # DJ club night
            continue

        age = None
        m = AGE_IN_TITLE.search(name)
        if m:
            age = norm_age(m.group(1))
            name = AGE_IN_TITLE.sub(" ", name)
        sold_out = bool(SOLD_OUT.search(name))
        name = " ".join(SOLD_OUT.sub(" ", name).split()).strip(" -–")
        if not age:
            m = AGE_IN_TEXT.search(long_desc)
            if m:
                age = norm_age(m.group(1))

        doors = finnish_time(item["startDate"])
        if doors.date().isoformat() < today:
            continue
        page = EVENT_PAGE.format(id=item["_id"])
        event = {
            "artist": name,
            "venue": VENUE,
            "city": CITY,
            "date": doors.strftime("%Y-%m-%dT%H:%M:00"),
            "doors": doors.strftime("%H:%M"),
            "ticketUrl": page,
            "eventUrl": page,
        }
        if sold_out:
            event["status"] = "sold out"
        price = " ".join(text(item.get("descriptions")).split())
        if price and re.search(r"\d", price) and len(price) <= 40:
            event["price"] = price
        if age:
            event["age"] = age
        events.append(event)
    return events


def main() -> int:
    try:
        resp = requests.get(API, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data["data"]["context"]
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        print(f"✗ Could not fetch {VENUE} events: {exc}")
        return 1

    scraped = parse(items)
    print(f"✓ Found {len(scraped)} upcoming music events at {VENUE} ({len(items)} listed)")
    if not scraped:
        return 1  # the API probably changed; fail loudly
    events = load_events(city="oulu")
    added = merge(scraped, events)
    save_events(events, city="oulu")
    print(f"✓ Added {added} new {VENUE} events ({len(events)} Oulu events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
