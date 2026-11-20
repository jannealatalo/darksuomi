#!/usr/bin/env python3
"""
Scraper for Bar Kotelo, Tampere (https://barkotelo.fi/keikat/), a small metal /
rock bar on Sammonkatu.

The gig page is built with a site builder: every gig is a text box of
centered lines, e.g.

    21.11.2026
    DISGRAVE
    PYRE OF HYPOCRISY
    LIPUT: 10€
    KEIKAT: KLO 22->

Lines between the date and the "liput"/"keikat" lines are the acts (a line
in parentheses belongs to the act above it, a line ending in ":" is the
night's name). Two-day events ("11.-12.12.2026") list each day's acts on a
"11.12.: ACT, ACT" line and become one gig per day. The "keikat klo" time
is when the bands start. There are no event pages, so eventUrl is the gig
page with the date as fragment (one gig per night).

Usage:
  python scraper_tampere_kotelo.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://barkotelo.fi/keikat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
VENUE = "Bar Kotelo"
CITY = "Tampere"

DATE_LINE = re.compile(r"^(\d{1,2})\.(?:\s*-\s*(\d{1,2})\.)?(\d{1,2})\.(\d{4})$")
DAY_ACTS = re.compile(r"^(\d{1,2})\.(\d{1,2})\.?\s*:\s*(.+)$")
INFO_LINE = re.compile(r"^(liput|keikat|ovet|vapaa pääsy|ilmainen|k-?18|ikäraja)", re.I)


def block_lines(box) -> list[str]:
    lines = []
    for el in box.find_all(["h1", "h2", "h3", "h4", "h5", "p"]):
        text = " ".join(el.get_text(" ", strip=True).replace("\xa0", " ").split())
        if text:
            lines.append(text)
    return lines


def parse_block(lines: list[str]) -> list[dict]:
    m = DATE_LINE.match(lines[0]) if lines else None
    if not m:
        return []
    d1, d2, mo, y = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
    name, acts, per_day, price, start, free = "", [], {}, None, None, False
    for line in lines[1:]:
        if INFO_LINE.match(line):
            low = line.lower()
            if low.startswith("liput"):
                price = line.split(":", 1)[-1].strip()
            elif low.startswith(("vapaa pääsy", "ilmainen")):
                free = True
            elif low.startswith("keikat") or low.startswith("ovet"):
                t = re.search(r"(\d{1,2})(?:[:.](\d{2}))?", line)
                if t:
                    start = f"{int(t.group(1)):02d}:{t.group(2) or '00'}"
            continue
        dm = DAY_ACTS.match(line)
        if dm:
            per_day[int(dm.group(1))] = dm.group(3).strip()
        elif line.startswith("(") and acts:
            acts[-1] += " " + line
        elif line.endswith(":") and not acts:
            name = line.rstrip(": ")
        else:
            acts.append(line)

    days = range(int(d1), int(d2) + 1) if d2 else [int(d1)]
    gigs = []
    for day in days:
        if per_day:
            label = " ".join(acts)  # the festival name
            title = f"{label}: {per_day[day]}" if label and day in per_day else per_day.get(day, label)
        else:
            title = ", ".join(acts)
            if name:
                title = f"{name}: {title}" if title else name
        if not title:
            continue
        iso = f"{y:04d}-{mo:02d}-{day:02d}"
        event = {
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{iso}T{start or '00:00'}:00",
            "ticketUrl": LIST_URL,
            "eventUrl": f"{LIST_URL}#{iso}",
            "venueDefault": "rock",
        }
        if start:
            event["doors"] = start
        if price:
            event["price"] = price
        elif free:
            event["price"] = "Vapaa pääsy"
        gigs.append(event)
    return gigs


def parse_page(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    events = []
    for box in soup.select("div.wb_text_element"):
        events += parse_block(block_lines(box))
    return events


def main() -> int:
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    resp.encoding = resp.encoding if resp.encoding and resp.encoding.lower() != "iso-8859-1" else "utf-8"
    today = date.today().isoformat()
    scraped, seen = [], set()
    for e in parse_page(resp.text):
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
