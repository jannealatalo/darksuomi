#!/usr/bin/env python3
"""
Scraper for Olympia (Olympia-kortteli), Tampere (https://olympiakortteli.fi/keikat/).

The "Keikat" page lists only gigs (the club nights are elsewhere), one
<div class="grid-x keikka"> row each: weekday + date ("To 17.12.2026"),
the title with the age limit stuck on ("Combichrist (USA) - Electro
Combichristmas Tour 2026 K-18") and an "Osta lippu" link to Lippu.fi.
The page gives no doors time, so dates are "T00:00:00". The Lippu.fi link
(without its tracking query) is the event's stable URL.

Usage:
  python scraper_tampere_olympia.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://olympiakortteli.fi/keikat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
VENUE = "Olympia"
CITY = "Tampere"

# "K-18", "(K18)", "S", "-S- / K-18" (all ages + 18+ area) at the title's end.
AGE_SUFFIX = re.compile(r"\s+\(?(-?S-?\s*/\s*K-?\s?18|K-?\s?\d{1,2}|-?S-?)\)?\s*$", re.I)


def age_label(raw: str) -> str:
    raw = raw.upper().replace(" ", "")
    if "S" in raw and "18" in raw:
        return "S/K-18"
    if "S" in raw:
        return "S"
    return "K-" + re.sub(r"\D", "", raw)


def parse_rows(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    events = []
    for row in soup.select("div.keikka"):
        h2 = row.find("h2")
        pvm = row.select_one(".pvm")
        if not (h2 and pvm):
            continue
        m = re.search(r"(\d{1,2})\.(\d{1,2})\.\s*(\d{4})", pvm.get_text(" ", strip=True))
        if not m:
            continue
        d, mo, y = map(int, m.groups())
        title = " ".join(h2.get_text(" ", strip=True).split())
        age = AGE_SUFFIX.search(title)
        if age:
            title = title[:age.start()].strip()
        link = next((a["href"] for a in row.select("a[href]") if "lippu" in a.get_text().lower()
                     or "lippu.fi" in a["href"]), None)
        page = link.split("?")[0] if link else f"{LIST_URL}#{y:04d}-{mo:02d}-{d:02d}"
        event = {
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T00:00:00",
            "ticketUrl": page,
            "eventUrl": page,
        }
        if age:
            event["age"] = age_label(age.group(1))
        events.append(event)
    return events


def main() -> int:
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    today = date.today().isoformat()
    scraped, seen = [], set()
    for e in parse_rows(resp.text):
        if e["date"][:10] >= today and e["eventUrl"] not in seen:
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
