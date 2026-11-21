#!/usr/bin/env python3
"""
Scraper for Krapin Paja, Tuusula (https://krapinpaja.fi/), the club stage at
Hotel Krapi by Lake Tuusula, about 30 km north of Helsinki.

The venue's web shop lists every club night in one category, 30-60 per page:

  <div class="product product-1095">
    <div class="ribbon ...">LOPPUUNMYYTY!</div>          (when sold out)
    <h3 class="product-title"><a href="/product/<slug>?cid=37">
        Kotiteollisuus, to 3.12. klo 20.00</a></h3>
    <div class="product_short_desc">Konsertti alkaa klo 20.00. Ovet aukeavat klo 18.30.</div>
    <div class="price-color">€ 36,50</div>

The titles have no year, so it comes from the weekday. The programme is
mostly pop, tribute bands, Christmas shows and stand-up, so (as with
Dubrovnik) only gigs the site would show by default are kept: the acts'
genre tags are looked up while scraping (genres.py, cached in artists.json)
and checked with genres.shown_by_default().

Usage:
  python scraper_krapinpaja.py
  python scraper_krapinpaja.py --all   # print every show with its genres, save nothing
"""

import argparse
import re
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

import genres as g
from eventstore import load_events, merge, save_events

SHOP = "https://kauppa.krapinpaja.fi"
LIST_URL = SHOP + "/category/pajan-klubit?limit=60&category_products%5Bpage%5D={page}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Krapin Paja"
CITY = "Tuusula"
MAX_PAGES = 5
DELAY = 1.0  # seconds between page loads

WEEKDAYS = {"ma": 0, "ti": 1, "ke": 2, "to": 3, "pe": 4, "la": 5, "su": 6}
# "Kotiteollisuus, to 3.12. klo 20.00" -> title, weekday, day, month, time
TITLE_DATE = re.compile(
    r"^(?P<title>.+?),?\s+(?P<wd>ma|ti|ke|to|pe|la|su)\s+(?P<d>\d{1,2})\.(?P<m>\d{1,2})\.?"
    r"(?:\s*klo\s*(?P<hh>\d{1,2})[.:](?P<mm>\d{2}))?\s*$", re.I)
DOORS = re.compile(r"\bovet\b[^.]*?\bklo\s*(\d{1,2})[.:](\d{2})", re.I)
PRICE = re.compile(r"€\s*(\d+(?:,\d+)?)")
SOLD_OUT = re.compile(r"loppuunmyyty|sold out", re.I)
CANCELLED = re.compile(r"peruttu|cancelled", re.I)


def year_for(weekday: int, day: int, month: int, today: date) -> int | None:
    """The year (this or the next two) in which day.month. falls on weekday."""
    for year in (today.year, today.year + 1, today.year + 2):
        try:
            d = date(year, month, day)
        except ValueError:
            continue
        if d.weekday() == weekday and d >= today:
            return year
    return None


def parse_list(html: str, today: date) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for card in soup.select("div.product"):
        link = card.select_one(".product-title a[href]")
        if not link:
            continue
        m = TITLE_DATE.match(" ".join(link.get_text(" ", strip=True).split()))
        if not m:
            continue
        day, month = int(m["d"]), int(m["m"])
        year = year_for(WEEKDAYS[m["wd"].lower()], day, month, today)
        if year is None:
            continue
        url = SHOP + link["href"].split("?")[0]
        start = f"{int(m['hh']):02d}:{m['mm']}" if m["hh"] else None
        desc = card.select_one(".product_short_desc")
        desc_text = " ".join(desc.get_text(" ", strip=True).split()) if desc else ""
        doors = DOORS.search(desc_text)
        doors = f"{int(doors.group(1)):02d}:{doors.group(2)}" if doors else None
        time_ = doors or start or "00:00"
        title = m["title"].strip(" -–,")
        # "Mieletön skaala -klubi - Death Hawks": the act first, so its
        # genres are looked up (the club's name is the suffix).
        club = re.match(r"^(.+?-klubi)\s+[-–]\s+(.+)$", title, re.I)
        if club:
            title = f"{club.group(2)} – {club.group(1)}"
        event = {
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{year:04d}-{month:02d}-{day:02d}T{time_}:00",
            "ticketUrl": url,
            "eventUrl": url,
        }
        if doors:
            event["doors"] = doors
        price = card.select_one(".price-color")
        p = PRICE.search(price.get_text(" ", strip=True)) if price else None
        if p:
            event["price"] = f"{p.group(1)} €"
        ribbon = " ".join(r.get_text(" ", strip=True) for r in card.select(".ribbon"))
        if CANCELLED.search(ribbon):
            event["status"] = "cancelled"
        elif SOLD_OUT.search(ribbon):
            event["status"] = "sold out"
        events.append(event)
    return events


def fetch_all(today: date) -> list[dict]:
    gigs, seen = [], set()
    for page in range(1, MAX_PAGES + 1):
        if page > 1:
            time.sleep(DELAY)
        resp = requests.get(LIST_URL.format(page=page), headers=HEADERS, timeout=30)
        resp.raise_for_status()
        found = [e for e in parse_list(resp.text, today) if e["eventUrl"] not in seen]
        if not found:
            break
        seen.update(e["eventUrl"] for e in found)
        gigs += found
    return gigs


def tag(event: dict, cache: dict, overrides: dict) -> list[str]:
    """The gig's genres, the same way genres.py tags it every night."""
    _artists, tags = g.gig_tags(event["artist"], cache, overrides)
    return g.pick_genres(event, tags)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every show and whether it's kept; save nothing")
    args = parser.parse_args()

    today = date.today()
    gigs = [e for e in fetch_all(today) if e["date"][:10] >= today.isoformat()]
    print(f"✓ Found {len(gigs)} upcoming shows at {VENUE}")
    if not gigs:
        return 1  # the shop layout probably changed; fail loudly

    cache = g.load_json(g.CACHE_FILE, {})
    config = g.load_json(g.CONFIG_FILE, {})
    overrides = config.get("artistOverrides", {})
    kept = []
    for event in gigs:
        tags = tag(event, cache, overrides)
        keep = g.shown_by_default(tags, config)
        if args.all or keep:
            print(f"  {'+' if keep else '-'} {event['date'][:10]} {event['artist']}  {tags[:4]}")
        if keep:
            kept.append(event)
    g.save_json(g.CACHE_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))
    if args.all:
        return 0

    events = load_events()
    # merge() doesn't refresh "status", so update it here (sold out / cancelled).
    by_url = {e.get("eventUrl"): e for e in events}
    for event in kept:
        existing = by_url.get(event["eventUrl"])
        if existing is not None:
            if "status" in event:
                existing["status"] = event["status"]
            else:
                existing.pop("status", None)
    added = merge(kept, events)
    save_events(events)
    print(f"✓ Kept {len(kept)} gigs that fit Dark Suomi; added {added} new "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
