#!/usr/bin/env python3
"""
Scraper for Ääniwalli, Helsinki (https://aaniwalli.fi/), the club in Vallila.

The front page (an Astro site) lists every upcoming event:

  <div class="event-wrapper">
    <a class="event" href="/events/<slug>">
      <div class="pills"><span class="pill">perjantai 11.12.</span><span class="pill">ROOM 1</span></div>
      <h1 class="event-title">Mental Cruelty <span class="country-code">(DE)</span> + …</h1>
    </a>
    <a class="button buy-button" href="https://www.ticketmaster.fi/…">Osta liput</a>

The date has no year, so the weekday picks it (this year or next). The slug's
date is not reliable: postponed gigs keep their old slug.

Ääniwalli also hosts a lot of techno and other club nights, so like the
Dubrovnik scraper this keeps only gigs the site would show by default (genre
tags looked up right away, see genres.shown_by_default()). When no band is
found (festival-style titles like "Nordic Death Mass"), genre words in the
gig page's description decide. The kept gigs' own pages give the advance
price, door time and age limit.

Usage:
  python scraper_aaniwalli.py
  python scraper_aaniwalli.py --all   # print every gig with its genres, save nothing
"""

import argparse
import re
import sys
import time
from datetime import date, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import genres as g
from eventstore import load_events, merge, save_events

LIST_URL = "https://aaniwalli.fi/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Ääniwalli"
CITY = "Helsinki"
DELAY = 1.0  # seconds between gig page loads

WEEKDAYS = ["maanantai", "tiistai", "keskiviikko", "torstai", "perjantai", "lauantai", "sunnuntai"]
PILL_DATE = re.compile(r"([a-zä]+)\s+(\d{1,2})\.(\d{1,2})\.", re.I)


def gig_date(pill: str, today: date) -> date | None:
    """'perjantai 11.12.' -> the next such date (from yesterday on) on that weekday."""
    m = PILL_DATE.search(pill)
    if not m:
        return None
    weekday, d, mo = m.group(1).lower(), int(m.group(2)), int(m.group(3))
    candidates = []
    for y in (today.year - 1, today.year, today.year + 1, today.year + 2):
        try:
            candidates.append(date(y, mo, d))
        except ValueError:
            pass
    upcoming = [c for c in candidates if c >= today - timedelta(days=1)]
    matching = [c for c in upcoming if weekday in WEEKDAYS and c.weekday() == WEEKDAYS.index(weekday)]
    return (matching or upcoming or [None])[0]


def parse_list(html: str, today: date) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for wrapper in soup.select(".event-wrapper"):
        link = wrapper.select_one("a.event")
        title_el = wrapper.select_one(".event-title")
        pills = [p.get_text(" ", strip=True) for p in wrapper.select(".pill")]
        when = gig_date(pills[0], today) if pills else None
        if not (link and title_el and when):
            continue
        title = " ".join(title_el.get_text(" ", strip=True).split())
        title = re.sub(r"\(\s*([A-Z]{2,3})\s*\)", r"(\1)", title).replace(" ,", ",")
        # "ASCENSION presents: POPOF (FR)": the presenter is a promoter, not the
        # act, so put the acts first ("POPOF (FR) – ASCENSION presents").
        m = re.match(r"^(.+?)\s+presents\s*:\s*(.+)$", title, flags=re.I)
        if m:
            title = f"{m.group(2)} – {m.group(1)} presents"
        url = urljoin(LIST_URL, link["href"])
        buy = wrapper.select_one("a.buy-button[href]")
        event = {"artist": title, "venue": VENUE, "city": CITY,
                 "date": f"{when.isoformat()}T00:00:00",
                 "eventUrl": url, "ticketUrl": buy["href"] if buy else url}
        if len(pills) > 1:
            event["room"] = pills[1].title() if pills[1].isupper() else pills[1]
        events.append(event)
    return events


def add_details(event: dict, html: str) -> None:
    """Advance or door price, timetable and age limit from the gig page."""
    content = BeautifulSoup(html, "html.parser").select_one(".content")
    if not content:
        return
    text = " ".join(content.get_text(" ", strip=True).split())
    price = (re.search(r"\bEnnakko(?:on)?\s*:?\s*(\d+(?:[,.]\d+)?\s*€)", text, re.I)
             or re.search(r"\bLiput\s*:?\s*(\d+(?:[,.]\d+)?\s*€)", text, re.I))
    door = re.search(r"\bOvelta\s*:?\s*(\d+(?:[,.]\d+)?\s*€)", text, re.I)
    if price:
        event["price"] = " ".join(price.group(1).split())
    elif door:
        event["price"] = f"{' '.join(door.group(1).split())} at the door"
    # "AIKATAULU: 16:00 OVET 17:05 ANALEPSY 17:50 THE ZENIT PASSAGE … LIPUT …"
    doors, schedule = None, []
    table = re.search(r"\b(?:AIKATAULU|TIMETABLE)\s*:?\s*(.+?)(?=\bLIPUT\b|\bTICKETS\b|$)", text, re.I)
    if table:
        for hh, mm, name in re.findall(r"(\d{1,2})[:.](\d{2})\s+(.+?)(?=\s+\d{1,2}[:.]\d{2}\s|$)",
                                       table.group(1)):
            t = f"{int(hh):02d}:{mm}"
            if re.fullmatch(r"ovet|doors", name.strip(), re.I):
                doors = t
            elif not re.match(r"ovet|doors", name.strip(), re.I):
                schedule.append({"time": t, "name": name.strip()})
    if not doors:
        m = re.search(r"\b(?:ovet|doors)\s*(?:klo\s*|at\s*)?(\d{1,2})[.:](\d{2})", text, re.I)
        doors = f"{int(m.group(1)):02d}:{m.group(2)}" if m else None
    if doors:
        event["date"] = f"{event['date'][:10]}T{doors}:00"
        event["doors"] = doors
    if schedule:
        event["schedule"] = schedule
    if re.search(r"\bK-?18\b", text):
        event["age"] = "K-18"
    elif re.search(r"\bikärajaton\b|\bS\b-?\s*ikäraja|\(S\)", text, re.I):
        event["age"] = "S"


# For gigs whose bands aren't found (festival-style titles like "Nordic Death
# Mass"): genre words in the gig page's description -> venueGenres keys
# (see genres.VENUE_GENRES).
DESCRIPTION_GENRES = [
    ("metal", re.compile(r"metal|deathcore|grindcore", re.I)),
    ("doom", re.compile(r"\bdoom", re.I)),
    ("punk", re.compile(r"punk", re.I)),
    ("hc", re.compile(r"\bhardcore\b(?!\s*techno)", re.I)),
    ("gothic", re.compile(r"\bgoth|deathrock", re.I)),
    ("rock", re.compile(r"\brock\b|rock-?yhtye|rockbändi|\brokki", re.I)),
]


def description_genres(html: str) -> list[str]:
    content = BeautifulSoup(html, "html.parser").select_one(".content")
    text = content.get_text(" ", strip=True) if content else ""
    return [key for key, pattern in DESCRIPTION_GENRES if pattern.search(text)]


def tag(event: dict, cache: dict, overrides: dict) -> list[str]:
    """The gig's genres, the same way genres.py tags it every night."""
    _artists, tags = g.gig_tags(event["artist"], cache, overrides)
    return g.pick_genres(event, tags)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every gig and whether it's kept; save nothing")
    args = parser.parse_args()

    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    today = date.today()
    gigs = [e for e in parse_list(resp.text, today) if e["date"][:10] >= today.isoformat()]
    print(f"✓ Found {len(gigs)} upcoming events at {VENUE}")
    if not gigs:
        return 1  # the page layout probably changed; fail loudly

    cache = g.load_json(g.CACHE_FILE, {})
    config = g.load_json(g.CONFIG_FILE, {})
    overrides = config.get("artistOverrides", {})
    pages: dict[str, str] = {}

    def page(event: dict) -> str:
        if event["eventUrl"] not in pages:
            if pages:
                time.sleep(DELAY)
            try:
                resp = requests.get(event["eventUrl"], headers=HEADERS, timeout=30)
                resp.raise_for_status()
                pages[event["eventUrl"]] = resp.text
            except requests.RequestException as e:
                print(f"  ! {event['artist'][:50]}: {e}", file=sys.stderr)
                pages[event["eventUrl"]] = ""
        return pages[event["eventUrl"]]

    kept = []
    for event in gigs:
        tags = tag(event, cache, overrides)
        if not tags:
            # No band found: fall back to the genres the gig page mentions.
            event["venueGenres"] = description_genres(page(event))
            tags = tag(event, cache, overrides)
        keep = g.keep_when_scraping(tags, config)
        if args.all or keep:
            print(f"  {'+' if keep else '-'} {event['date'][:10]} {event['artist']}  {tags[:4]}")
        if keep:
            kept.append(event)
    g.save_json(g.CACHE_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))
    if args.all:
        return 0

    for event in kept:
        add_details(event, page(event))

    events = load_events()
    added = merge(kept, events)
    save_events(events)
    print(f"✓ Kept {len(kept)} gigs that fit Dark Suomi; added {added} new "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
