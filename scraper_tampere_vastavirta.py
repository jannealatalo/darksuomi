#!/usr/bin/env python3
"""
Scraper for Vastavirta-klubi, Tampere (https://vastavirta.net/), the punk /
metal / rock club in Pispala.

The front page lists every upcoming event as a <div class="vv-custom-events">
block: a heading "27.11.2026 20:00 - Garbagemen (23.00), God's Lonely Men
(22.00), Wolfmen (21.00)", the room ("Tapahtumapaikka: Vastavirta-Klubi
(alakerta)" downstairs or "Terassi Pub Yläkerta" upstairs), the price, and
links to Cluby (advance tickets) and Facebook. Set times are dropped from the
title; the heading's time is used as the start.

There are no event pages, so eventUrl is the Facebook event or Cluby link,
or else the front page with the date and time as fragment. Quizzes, DJ
nights, sing-alongs, Christmas parties and radio-station nights are skipped.
Downstairs gigs get venueDefault "rock"; the upstairs pub also hosts folk
and singer-songwriters, so those get no default.

Usage:
  python scraper_tampere_vastavirta.py
"""

import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://vastavirta.net/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
VENUE = "Vastavirta-klubi"
CITY = "Tampere"

HEADING = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2})[:.](\d{2})\s*-\s*(.+)")
SET_TIME = re.compile(r"\s*\(\d{1,2}[.,:]\d{1,2}\)")
NOT_A_GIG = re.compile(r"tietovisa|visa\b|\bdj\b|dj[- ]ilta|pikkujoulu|pikkuäcidjoulu|joulut\b|"
                       r"laula|karaoke|open mic$|goes vastavirta|kirpputori|elokuva|luento|"
                       r"stand[- ]?up", re.I)


def parse_blocks(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    events = []
    for block in soup.select("div.vv-custom-events"):
        h3 = block.find("h3")
        if not h3:
            continue
        m = HEADING.match(" ".join(h3.get_text(" ", strip=True).split()))
        if not m:
            continue
        d, mo, y, hh, mm = map(int, m.groups()[:5])
        title = m.group(6)
        if NOT_A_GIG.search(title):
            continue
        title = " ".join(SET_TIME.sub("", title).split()).strip(" ,")
        texts = [" ".join(p.get_text(" ", strip=True).split()) for p in block.find_all("p")]
        room = next((t.split(":", 1)[1].strip() for t in texts
                     if t.lower().startswith("tapahtumapaikka")), "")
        price = next((t.split(":", 1)[1].strip() for t in texts
                      if t.lower().startswith("liput:") and re.search(r"\d", t)), None)
        free = any("ilmainen" in t.lower() or "vapaa pääsy" in t.lower() for t in texts)
        links = [a["href"] for a in block.select("a[href]")]
        cluby = next((u for u in links if "cluby.com" in u), None)
        facebook = next((u for u in links if "facebook.com" in u), None)
        hhmm = f"{hh:02d}:{mm:02d}"
        if hhmm == "23:59":  # placeholder for "late"
            hhmm = "00:00"
        day = f"{y:04d}-{mo:02d}-{d:02d}"
        page = facebook or cluby or f"{LIST_URL}#{day}-{hh:02d}{mm:02d}"
        event = {
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{day}T{hhmm}:00",
            "ticketUrl": cluby or facebook or LIST_URL,
            "eventUrl": page,
        }
        if hhmm != "00:00":
            event["doors"] = hhmm
        if price:
            event["price"] = price
        elif free:
            event["price"] = "Vapaa pääsy"
        if room:
            event["room"] = room
        if "alakerta" in room.lower():
            event["venueDefault"] = "rock"
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
    for e in parse_blocks(resp.text):
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
