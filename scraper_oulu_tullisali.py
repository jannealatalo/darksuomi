#!/usr/bin/env python3
"""
Scraper for Tapahtumakeskus Tullisali, Oulu (https://www.tullisali.fi/tapahtumat/).

The WordPress events page lists every upcoming event on one page as
".event-list-item" cards: a date block ("pe 4.12." + year, "Ovet klo 19:00",
sometimes "Showtime klo 20:00"), a category ("Musiikki", "Teatteri", ...),
the title, price ("alk. 35,00 €"), age limit ("Ikäraja: K18") and a
Ticketmaster link. Only the "Musiikki" category is kept; theatre, comedy,
fairs and private parties are skipped.

Titles like "Anvil | Support: Killer (BE), Gobra" are turned into
"Anvil + Killer (BE), Gobra" so that genres.py sees each act.

Usage:
  python scraper_oulu_tullisali.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://www.tullisali.fi/tapahtumat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Tullisali"
CITY = "Oulu"
MUSIC_CATEGORIES = {"musiikki", "konsertti", "konsertit", "keikka", "keikat"}


def clean_title(title: str) -> str:
    title = " ".join(title.split())
    title = re.sub(r"\s*\|\s*(?:support|special guests?|guests?|lisäksi)\s*:?\s*", " + ",
                   title, flags=re.I)
    title = re.sub(r"\s*\|\s*", " + ", title)
    return title.strip(" +")


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for card in soup.select(".event-list-item"):
        cats = {li.get_text(strip=True).lower() for li in card.select(".event-category li")}
        if not cats & MUSIC_CATEGORIES:
            continue
        link = card.select_one(".info h3 a[href]")
        date_box = card.select_one(".date-content")
        if not (link and date_box):
            continue
        date_text = " ".join(date_box.get_text(" ", strip=True).split())
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.\s*(\d{4})", date_text)
        if not m:
            continue
        d, mo, y = map(int, m.groups())
        doors = re.search(r"Ovet\s+klo\s+(\d{1,2})[:.](\d{2})", date_text, re.I)
        show = re.search(r"Showtime\s+klo\s+(\d{1,2})[:.](\d{2})", date_text, re.I)
        start = doors or show
        hh, mm = (int(start.group(1)), start.group(2)) if start else (0, "00")

        ticket = card.select_one("a.tickets[href]")
        event = {
            "artist": clean_title(link.get_text(" ", strip=True)),
            "venue": VENUE,
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mm}:00",
            "ticketUrl": ticket["href"] if ticket else link["href"],
            "eventUrl": link["href"],
        }
        if doors:
            event["doors"] = f"{hh:02d}:{mm}"
        price = card.select_one(".price")
        if price and price.get_text(strip=True):
            event["price"] = " ".join(price.get_text(" ", strip=True).split())
        age = card.select_one(".age")
        if age:
            a = re.search(r"(S\s*/\s*K-?\s?18|K-?\s?18|S)\b", age.get_text(" ", strip=True))
            if a:
                event["age"] = a.group(1).replace(" ", "").replace("K18", "K-18")
        events.append(event)
    return events


def main() -> int:
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"✗ Could not fetch {LIST_URL}: {exc}")
        return 1

    today = date.today().isoformat()
    scraped = [e for e in parse(resp.text) if e["date"][:10] >= today]
    print(f"✓ Found {len(scraped)} upcoming music events at {VENUE}")
    if not scraped:
        return 1  # the page layout probably changed; fail loudly
    events = load_events(city="oulu")
    added = merge(scraped, events)
    save_events(events, city="oulu")
    print(f"✓ Added {added} new {VENUE} events ({len(events)} Oulu events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
