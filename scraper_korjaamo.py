#!/usr/bin/env python3
"""
Scraper for Kulttuuritehdas Korjaamo, Helsinki (https://korjaamo.fi/tapahtumat/).

Each event card in the list carries its WordPress taxonomies as CSS classes,
e.g. "event_cat-musiikkitapahtumat-fi genres-metalli venue-vaunusali", so the
category, genres and room come straight from the list pages. Only music
events are kept (music category or a music genre); stand-up, poetry slams,
lectures, burlesque, cinema and the like are skipped.

The card's meta line gives the date, doors, price and age limit:
"21.11.2026 – Ovet 19:30 – Liput 22,60 € / 25 € – K18".

Usage:
  python scraper_korjaamo.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://korjaamo.fi/tapahtumat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Korjaamo"
CITY = "Helsinki"
MAX_PAGES = 10

MUSIC_CATS = re.compile(r"^event_cat-(musiikkitapahtumat|metallifestivaalit|rock-ja-pop-festivaalit|"
                        r"maailmanmusiikki|show-dinner-keikat|orkesterit)")
NOT_MUSIC_CATS = re.compile(r"^event_cat-(stand-up|komedia|runot|luennot|burles|elamanhallinta|"
                            r"sirkus|kabaree|tanssi)")


def page_url(n: int) -> str:
    return LIST_URL if n == 1 else f"{LIST_URL}sivu/{n}/"


COMEDY_CATS = re.compile(r"^event_cat-(stand-up|komedia)")


def parse_cards(html: str, kind: str = "music") -> list[dict]:
    """Event cards of one list page: music events, or with kind="comedy" the
    stand-up / comedy ones (for the stand-up site, standup.py)."""
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for li in soup.select("li.wp-block-post.event"):
        classes = li.get("class", [])
        genres = [c.removeprefix("genres-") for c in classes if c.startswith("genres-")]
        if kind == "comedy":
            if not any(COMEDY_CATS.match(c) for c in classes):
                continue
        else:
            is_music = any(MUSIC_CATS.match(c) for c in classes) or bool(genres)
            if not is_music or any(NOT_MUSIC_CATS.match(c) for c in classes):
                continue

        link = li.select_one(".event-card__title a")
        meta = li.select_one(".event-card__meta")
        if not (link and meta):
            continue
        text = " ".join(meta.get_text(" ", strip=True).split())
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
        if not m:
            continue
        d, mo, y = map(int, m.groups())
        doors = re.search(r"Ovet\s*(\d{1,2})[:.](\d{2})", text, re.I)
        price = re.search(r"Liput\s*(.+?)(?:\s+–|$)", text, re.I)
        age = re.search(r"\b(K-?\s?18|S/K-?18|S)\s*$", text)

        hh, mm = (int(doors.group(1)), doors.group(2)) if doors else (0, "00")
        ticket = next((a["href"] for a in li.select("a[href]")
                       if "osta" in a.get_text().lower()), link["href"])
        event = {
            "artist": " ".join(link.get_text(" ", strip=True).split()),
            "venue": VENUE,
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mm}:00",
            "ticketUrl": ticket,
            "eventUrl": link["href"],
            "venueGenres": genres,
        }
        if doors:
            event["doors"] = f"{hh:02d}:{mm}"
        if price:
            event["price"] = price.group(1).strip()
        if age:
            event["age"] = age.group(1).replace(" ", "").replace("K18", "K-18")
        room = li.select_one(".event-card__tag")
        if room:
            event["room"] = room.get_text(strip=True)
        events.append(event)
    return events


def fetch(kind: str = "music") -> list[dict]:
    """Every list page's events of this kind (see parse_cards)."""
    scraped, seen = [], set()
    for n in range(1, MAX_PAGES + 1):
        resp = requests.get(page_url(n), headers=HEADERS, timeout=30)
        if resp.status_code == 404:
            break
        resp.raise_for_status()
        found = [e for e in parse_cards(resp.text, kind) if e["eventUrl"] not in seen]
        if not found and n > 1 and "wp-block-post" not in resp.text:
            break
        seen.update(e["eventUrl"] for e in found)
        scraped += found
        if f"sivu/{n + 1}/" not in resp.text:
            break
    return scraped


def main() -> int:
    scraped = fetch()

    today = date.today().isoformat()
    scraped = [e for e in scraped if e["date"][:10] >= today]
    print(f"✓ Found {len(scraped)} upcoming music events at {VENUE}")
    if not scraped:
        return 1  # the page layout probably changed; fail loudly
    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
