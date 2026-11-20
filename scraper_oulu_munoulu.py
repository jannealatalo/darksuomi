#!/usr/bin/env python3
"""
Scraper for the City of Oulu's event calendar, Mun Oulu
(https://tapahtumat.munoulu.fi/), for Oulu venues that have no usable
listing of their own:

  - Hevimesta (Isokatu 36)          - metal club, tickets on Lippu.fi
  - Kantakrouvi (Uusikatu 23)       - rock/metal club, tickets on Ticketmaster
  - Tukikohta (Sorvarintie 5)       - DIY band club (punk, metal, noise fests)
  - Oulun Energia Areena            - arena; music events only (not ice hockey)
  - Oulun Musiikkikeskus (Madetojan sali, Pohjankartanon sali) - concert hall;
    only gigs whose title/description mentions rock, metal, punk, goth ...

Mun Oulu runs on the LocalHub "Bubster" platform. Its public JSON search
(/api/collection/<site id>/content/general-search?start=...&end=...) returns
events from the city's own calendar plus Ticketmaster, Lippu.fi and Tiketti
imports. It returns at most 500 events per call and has no paging, so the
date range is split until each window fits. Event pages are
https://tapahtumat.munoulu.fi/fi-FI/page/<id>.

The same gig often appears several times (city calendar + Oulu2026 calendar +
ticket shop import); those are merged by venue, day and title. Stale ticket
imports (a gig listed at midnight at one venue while the same title has a
real time elsewhere that day, e.g. a gig moved to another venue) are dropped.

Venues with their own scraper (45 Special, Tullisali, Toppila Klubi) are
deliberately not taken from here.

Usage:
  python scraper_oulu_munoulu.py
"""

import html
import re
import sys
from datetime import date, timedelta

import requests

from eventstore import load_events, merge, save_events
from scraper_tiivistamo import finnish_time

SITE_ID = "5dc549a38925dd23b5949a4d"
API = f"https://tapahtumat.munoulu.fi/api/collection/{SITE_ID}/content/general-search"
PAGE = "https://tapahtumat.munoulu.fi/fi-FI/page/{id}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)",
           "Accept": "application/json"}
CITY = "Oulu"
DAYS_AHEAD = 365
FIRST_WINDOW = 45      # days per request; halved while a window hits the cap
RESULT_CAP = 500
MAX_REQUESTS = 15

ROCKISH = re.compile(r"\b(rock|metal|metalli|hevi|heavy|punk|goth|grunge|doom|thrash|"
                     r"hard ?core|industrial|darkwave|post-punk|stoner|sludge)", re.I)
# In a concert hall's description "rock" alone is too loose (Christmas shows
# with "rock arrangements", humour choirs ...), so ask for a harder genre.
ROCKISH_DESC = re.compile(r"\b(metal|metalli|hevi|heavy metal|hard ?rock|punk|goth|grunge|"
                          r"doom|thrash|industrial|darkwave|stoner|sludge)", re.I)
# (venue name, location regex, needs a rock/metal word in title or description)
VENUES = [
    ("Hevimesta", re.compile(r"hevimesta|isokatu 36\b", re.I), False),
    ("Kantakrouvi", re.compile(r"kantakrouvi|uusikatu 23\b", re.I), False),
    ("Tukikohta", re.compile(r"tukikoh|sorvarintie 5\b", re.I), False),
    ("Oulun Energia Areena", re.compile(r"energia areena|teuvo pakkalan katu 11", re.I), False),
    ("Oulun Musiikkikeskus", re.compile(r"madetojan sali|pohjankartanon sali|musiikkikeskus|"
                                       r"leevi madetojan katu", re.I), True),
]
MUSIC_CATEGORIES = {"Music", "Gigs", "Concerts", "Festivals"}
NOT_MUSIC_CATEGORIES = {"Spectator sports", "Sports"}
NOT_MUSIC_TITLE = re.compile(r"kirppis|kirpputori|stand ?-?up|lasten|nukketeatteri|"
                             r"luento|työpaja|bingo|visa\b|quiz|karaoke|tanssikurssi|"
                             r"perhepaket|\bvip\b|pysäköinti|parking|tiernapoja|"
                             r"joulukonsertti|kauneimmat joululaulut", re.I)
AGE = re.compile(r"\b(S\s*/\s*K-?\s?18|K-?\s?18)\b", re.I)


def fetch_window(start: date, end: date) -> list[dict]:
    params = {"lang": "fi", "country": "FI", "sort": "startDate",
              "start": start.isoformat(), "end": end.isoformat()}
    resp = requests.get(API, params=params, headers=HEADERS, timeout=90)
    resp.raise_for_status()
    return resp.json().get("pages") or []


def fetch_all() -> list[dict]:
    """All calendar entries from today on, splitting windows that hit the cap."""
    today = date.today()
    todo = []
    d = today
    while d < today + timedelta(days=DAYS_AHEAD):
        todo.append((d, min(d + timedelta(days=FIRST_WINDOW - 1), today + timedelta(days=DAYS_AHEAD))))
        d += timedelta(days=FIRST_WINDOW)
    pages, requests_made = {}, 0
    while todo and requests_made < MAX_REQUESTS:
        start, end = todo.pop(0)
        found = fetch_window(start, end)
        requests_made += 1
        if len(found) >= RESULT_CAP and end > start:
            mid = start + (end - start) // 2
            todo[:0] = [(start, mid), (mid + timedelta(days=1), end)]
            continue
        for p in found:
            pages[p["_id"]] = p
    if todo:
        print(f"  (stopped after {MAX_REQUESTS} requests; {len(todo)} windows left)")
    return list(pages.values())


def plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return " ".join(html.unescape(text).split())


def location_text(page: dict) -> str:
    return " ".join((loc.get("address") or "") for loc in page.get("locations") or [])


def clean_title(name: str) -> str:
    name = " ".join(str(name).split())
    name = re.sub(r"\s*\((?:Madetojan sali|Pohjankartanon sali|Tulindbergin sali)\)\s*$", "", name, flags=re.I)
    name = re.sub(r"\s*\(?\b(?:S\s*/\s*)?K-?\s?18\)?\s*$", "", name, flags=re.I)
    return name.strip(" -–|")


def text_lines(description_html: str) -> list[str]:
    text = re.sub(r"<\s*(br|/p|/div|/li|/h\d)\s*/?>", "\n", description_html or "", flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return [" ".join(line.split()) for line in text.split("\n") if line.strip()]


DAY_LINE = re.compile(r"^(ma|ti|ke|to|pe|la|su)\w*\s+(\d{1,2})\.(\d{1,2})\.", re.I)
LINEUP_START = re.compile(r"esiinty|line-?up|stageilla|lavalla|mekkaloi|soittavat", re.I)
NOT_AN_ACT = re.compile(r"€|\bklo\b|\d{1,2}[.:]\d{2}|liput|lippu|ovet|ikäraja|https?:|www\.|"
                        r"fest|tapahtum|järjest|[!?:]$", re.I)


def festival_acts(description_html: str, day: date) -> list[str]:
    """
    Acts of one festival day from a free-text description: the lines under
    this day's header ("Perjantai 20.11. 17-00"), or else the lines after
    "Esiintymässä ovat:" / bold names. "Band - Oulu (punk)" -> "Band".
    """
    lines = text_lines(description_html)
    has_days = any(DAY_LINE.match(line) for line in lines)
    bold = {html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
            for s in re.findall(r"<strong>(.*?)</strong>", description_html or "", flags=re.S)}
    acts, active = [], False
    for line in lines:
        m = DAY_LINE.match(line)
        if m:
            active = (int(m.group(2)), int(m.group(3))) == (day.day, day.month)
            continue
        if not has_days and LINEUP_START.search(line) and len(line) < 80:
            active = True
            continue
        if not (active or any(b and line.startswith(b) for b in bold)):
            continue
        name = re.split(r"\s+[-–]\s+|\s*\(", line)[0].strip()
        if (1 < len(name) <= 40 and len(name.split()) <= 6 and ", " not in name
                and not NOT_AN_ACT.search(name) and name not in acts):
            acts.append(name)
    return acts


def to_events(page: dict) -> list[dict]:
    loc = location_text(page)
    venue = next(((v, gated) for v, rx, gated in VENUES if rx.search(loc)), None)
    if not venue:
        return []
    venue, gated = venue
    cats = set(page.get("globalContentCategories") or [])
    if not cats & MUSIC_CATEGORIES or cats & NOT_MUSIC_CATEGORIES:
        return []
    name = str(page.get("name") or "")
    title = clean_title(name)
    if not title or NOT_MUSIC_TITLE.search(title):
        return []
    desc = plain(page.get("descriptionLong") or page.get("descriptionShort") or "")
    if gated and not (ROCKISH.search(title) or ROCKISH_DESC.search(desc)):
        return []
    ev = page.get("event") or {}
    if ev.get("isCancelled") or ev.get("isSuperEvent"):
        return []

    dates = [d for d in ev.get("dates") or [] if d.get("start") and not d.get("isCancelled")]
    if not dates and ev.get("start"):
        dates = [{"start": ev["start"]}]
    base_url = PAGE.format(id=page["_id"])
    events = []
    for d in dates:
        start = finnish_time(d["start"])
        artist = title
        if re.search(r"fest", title, re.I):
            acts = festival_acts(page.get("descriptionLong") or "", start.date())
            if acts:
                artist = f"{title.rstrip('.')}: {', '.join(acts)}"
        url = base_url if len(dates) == 1 else f"{base_url}#{start:%Y-%m-%d}"
        ticket = d.get("urlPurchaseTicket") or ev.get("urlPurchaseTicket") or url
        event = {
            "artist": artist,
            "venue": venue,
            "city": CITY,
            "date": start.strftime("%Y-%m-%dT%H:%M:00"),
            "ticketUrl": ticket,
            "eventUrl": url,
            "_source": page.get("sourceName") or "",
            "_title": title,  # without the line-up, for de-duplication
        }
        if start.strftime("%H:%M") != "00:00" and not ev.get("startTimeMissing"):
            event["doors"] = start.strftime("%H:%M")
        else:
            event["date"] = start.strftime("%Y-%m-%dT00:00:00")
        price = page.get("price") or {}
        if price.get("min") is not None:
            lo, hi = price["min"], price.get("max")
            fmt = lambda x: f"{x:g}".replace(".", ",")
            event["price"] = f"{fmt(lo)} €" if hi in (None, lo) else f"{fmt(lo)}–{fmt(hi)} €"
        age = AGE.search(name) or AGE.search(desc)
        if age:
            event["age"] = age.group(1).upper().replace(" ", "").replace("K18", "K-18")
        events.append(event)
    return events


def dedupe(events: list[dict], all_pages: list[dict]) -> list[dict]:
    # A gig listed at midnight while the same title has a real time at another
    # venue that day is a stale import (e.g. moved venue): drop it.
    timed_elsewhere = set()
    for p in all_pages:
        ev = p.get("event") or {}
        if not ev.get("start"):
            continue
        t = finnish_time(ev["start"])
        if t.strftime("%H:%M") != "00:00":
            timed_elsewhere.add((clean_title(p.get("name") or "").casefold(), t.date().isoformat(),
                                 location_text(p).split(",")[0].casefold()))
    kept = []
    for e in events:
        key_title, day = e["_title"].casefold(), e["date"][:10]
        if e["date"].endswith("T00:00:00") and any(
                t == key_title and d == day and e["venue"].casefold() not in loc
                for t, d, loc in timed_elsewhere):
            continue
        kept.append(e)

    # Same venue, day and title from several sources: keep one, preferring
    # the city's own calendar entry, then one with a known time.
    best = {}
    for e in kept:
        key = (e["venue"], e["date"][:10], e["_title"].casefold())
        rank = (e["_source"].startswith("Mun Oulu"), "doors" in e, "price" in e)
        if key not in best or rank > best[key][0]:
            best[key] = (rank, e)
    result = []
    for _, e in best.values():
        e.pop("_source", None)
        e.pop("_title", None)
        result.append(e)
    return sorted(result, key=lambda e: e["date"])


def main() -> int:
    try:
        pages = fetch_all()
    except (requests.RequestException, ValueError) as exc:
        print(f"✗ Could not fetch the Mun Oulu event calendar: {exc}")
        return 1
    if not pages:
        print("✗ Mun Oulu returned no events; the API probably changed")
        return 1

    today = date.today().isoformat()
    scraped = [e for p in pages for e in to_events(p) if e["date"][:10] >= today]
    scraped = dedupe(scraped, pages)
    by_venue = {}
    for e in scraped:
        by_venue[e["venue"]] = by_venue.get(e["venue"], 0) + 1
    for venue, _, _ in VENUES:
        print(f"  {venue}: {by_venue.get(venue, 0)} upcoming gigs")
    print(f"✓ Found {len(scraped)} upcoming gigs in Mun Oulu ({len(pages)} calendar entries checked)")
    events = load_events(city="oulu")
    added = merge(scraped, events)
    save_events(events, city="oulu")
    print(f"✓ Added {added} new events ({len(events)} Oulu events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
