#!/usr/bin/env python3
"""
Rokki Raikaa Oulu (https://rokkiraikaa.fi/oulu-<year>/), the two-day rock and
metal festival at the Ouluhalli parking area every July.

The festival's WordPress/Elementor page shows the dates
("Mahtavat koko kansan rokkifestarit oulussa 2.-3.7.2027") and a "Line up"
section of h3 headings, one per act (unannounced slots read "12/16").
The site does not split the line-up by day, so the festival becomes one gig
on its first day, titled "Rokki Raikaa Oulu 2027 (2.–3.7.): Act, Act, ..."
so genres.py can tag each act. As more acts are announced, the run updates
the title. Rokki Raikaa also tours other cities; only Oulu is taken.

Usage:
  python scraper_oulu_rokkiraikaa.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

HOME = "https://rokkiraikaa.fi/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Ouluhallin parkkialue (Rokki Raikaa)"
CITY = "Oulu"
DATES = re.compile(r"(\d{1,2})\.?\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{4})")


def festival_page() -> str | None:
    """URL of the current Oulu festival page, linked from the front page."""
    resp = requests.get(HOME, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = sorted({a["href"] for a in soup.select("a[href]")
                    if re.search(r"rokkiraikaa\.fi/oulu-\d{4}/?$", a["href"])})
    return links[-1] if links else None


def parse(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    m = DATES.search(text)
    if not m:
        return None
    d1, d2, mo, y = map(int, m.groups())

    heading = next((h for h in soup.find_all(["h2", "h3"])
                    if h.get_text(strip=True).lower() == "line up"), None)
    if not heading:
        return None
    section = heading.find_parent(class_="e-con-inner") or heading.find_parent(class_="e-con")
    acts = []
    for h in section.select("h3"):
        name = " ".join(h.get_text(" ", strip=True).split())
        if name and not re.fullmatch(r"\d+\s*/\s*\d+", name) and name not in acts:
            acts.append(name)
    if not acts:
        return None

    ticket = next((a["href"] for a in soup.select("a[href]")
                   if "lippu.fi" in a["href"] or "osta liput" in a.get_text(" ").lower()), url)
    return {
        "artist": f"Rokki Raikaa Oulu {y} ({d1}.–{d2}.{mo}.): {', '.join(acts)}",
        "venue": VENUE,
        "city": CITY,
        "date": f"{y:04d}-{mo:02d}-{d1:02d}T00:00:00",
        "ticketUrl": ticket,
        "eventUrl": url,
        "age": "K-18",
    }


def main() -> int:
    try:
        url = festival_page()
        if not url:
            print("✗ No Rokki Raikaa Oulu page linked from the front page")
            return 1
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"✗ Could not fetch Rokki Raikaa: {exc}")
        return 1

    event = parse(resp.text, url)
    if not event:
        print(f"✗ No dates or line-up found on {url}; the page layout probably changed")
        return 1
    if event["date"][:10] < date.today().isoformat():
        print(f"✓ Rokki Raikaa Oulu ({event['date'][:10]}) is already over; nothing to add")
        return 0
    print(f"✓ Found Rokki Raikaa Oulu {event['date'][:10]}: {event['artist']}")
    events = load_events(city="oulu")
    added = merge([event], events)
    save_events(events, city="oulu")
    print(f"✓ Added {added} new events ({len(events)} Oulu events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
