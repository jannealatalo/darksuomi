#!/usr/bin/env python3
"""
Scraper for Nokia Arena, Tampere (https://nokiaarena.fi/tapahtumat/), music only.

The arena hosts ice hockey (Tappara, Ilves), other sports, galas and shows
besides concerts. Its WordPress REST API tags each event with "eventcat"
terms; only events in the "konsertit" category (id 15) are kept. Steps:
  1. /tapahtumat/ lists the upcoming events with date and year,
  2. /wp-json/wp/v2/event?eventcat=15 tells which of them are concerts,
  3. each concert's own page (a handful) gives "Ovet klo 17.00", the price
     ("Liput alk. 59 EUR") and the Lippu.fi ticket link.
Season-long entries with a date range (hockey seasons) are skipped. No age
limit is stored: arena pages mix "S" halls with K-18 bar stands and parties.

Usage:
  python scraper_tampere_nokiaarena.py
"""

import html
import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

SITE = "https://nokiaarena.fi"
LIST_URL = f"{SITE}/tapahtumat/"
API = f"{SITE}/wp-json/wp/v2/event"
CONCERT_CAT = 15  # "konsertit"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
VENUE = "Nokia Arena"
CITY = "Tampere"
MAX_DETAIL_PAGES = 10


def concert_urls() -> set[str]:
    urls = set()
    for page in range(1, 4):
        resp = requests.get(API, headers=HEADERS, timeout=30,
                            params={"eventcat": CONCERT_CAT, "per_page": 100, "page": page,
                                    "_fields": "link"})
        if resp.status_code == 400:
            break
        resp.raise_for_status()
        items = resp.json()
        urls.update(i["link"].rstrip("/") for i in items)
        if len(items) < 100:
            break
    return urls


def parse_list(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    events = []
    for card in soup.select("div.events__event"):
        link = card.select_one("a.events__titlelink[href]") or card.select_one("a.events__imagecontainer[href]")
        day = card.select_one(".events__date")
        year = card.select_one(".events__year")
        title = card.select_one(".events__title")
        if not (link and day and year and title):
            continue
        y = year.get_text(" ", strip=True)
        m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.", day.get_text(" ", strip=True))
        if not m or not re.fullmatch(r"\d{4}", y):  # "2026-2027" = a season
            continue
        events.append({
            "artist": " ".join(html.unescape(title.get_text(" ", strip=True)).split()),
            "date": f"{int(y):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}",
            "url": link["href"],
        })
    return events


def parse_detail(page_html: str) -> dict:
    soup = BeautifulSoup(page_html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    info = {}
    doors = re.search(r"Ovet\s+(?:klo\s+)?(\d{1,2})[.:](\d{2})", text, re.I)
    if doors:
        info["doors"] = f"{int(doors.group(1)):02d}:{doors.group(2)}"
    price = re.search(r"Liput\s+(alk\.\s*[\d,.]+\s*(?:EUR|€))", text, re.I)
    if price:
        info["price"] = price.group(1).replace("EUR", "€")
    ticket = next((a["href"] for a in soup.select("a[href*='lippu.fi/event/']")), None)
    if ticket:
        info["ticketUrl"] = html.unescape(ticket)
    return info


def main() -> int:
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        concerts = concert_urls()
    except requests.RequestException as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    today = date.today().isoformat()
    listed = [e for e in parse_list(resp.text)
              if e["date"] >= today and e["url"].rstrip("/") in concerts]

    scraped = []
    for item in listed[:MAX_DETAIL_PAGES]:
        info = {}
        try:
            page = requests.get(item["url"], headers=HEADERS, timeout=30)
            page.raise_for_status()
            info = parse_detail(page.text)
        except requests.RequestException as e:
            print(f"  (no details for {item['artist']}: {e})")
        doors = info.get("doors")
        event = {
            "artist": item["artist"],
            "venue": VENUE,
            "city": CITY,
            "date": f"{item['date']}T{doors or '00:00'}:00",
            "ticketUrl": info.get("ticketUrl", item["url"]),
            "eventUrl": item["url"],
        }
        for field in ("doors", "price"):
            if info.get(field):
                event[field] = info[field]
        scraped.append(event)

    print(f"✓ Found {len(scraped)} upcoming concerts at {VENUE}")
    if not scraped:
        return 1  # the page layout probably changed; fail loudly
    events = load_events(city="tampere")
    added = merge(scraped, events)
    save_events(events, city="tampere")
    print(f"✓ Added {added} new {VENUE} events ({len(events)} Tampere events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
