#!/usr/bin/env python3
"""
Scraper for Dubrovnik, Helsinki (https://www.dubrovnik.fi/), the club in the
Konepaja area (Corona Baari's sister venue).

The front page lists every upcoming gig (WordPress, Divi theme):

  <article class="... category-keikat">
    <h2 class="entry-title"><a href="…/keikat/<slug>/">Maustetytöt LOPPUUNMYYTY</a></h2>
    <div class="post-content"><p>LA 21.11.2026</p></div>

Most Dubrovnik gigs are pop, jazz, iskelmä and Christmas shows, so this
scraper only keeps gigs the site would show by default: the bands' genre
tags are looked up right away (genres.py: Last.fm / MusicBrainz, cached in
artists.json) and checked with genres.shown_by_default(). Only the kept
gigs' own pages are loaded, for the ticket link and any time or price.

Usage:
  python scraper_dubrovnik.py
  python scraper_dubrovnik.py --all   # print every gig with its genres, save nothing
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

LIST_URL = "https://www.dubrovnik.fi/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Dubrovnik"
CITY = "Helsinki"
DELAY = 1.0  # seconds between gig page loads

DATE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
SOLD_OUT = re.compile(r"\s*\b(loppuunmyyty|sold out)\b\s*", re.I)
CANCELLED = re.compile(r"\s*\b(peruttu|cancelled)\b\s*", re.I)
TICKET_HOSTS = re.compile(r"tiketti\.fi|lippu\.fi|ticketmaster|eventbrite|holvi|lippupiste|tiketin")


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for art in soup.select("article.category-keikat"):
        link = art.select_one("h2.entry-title a")
        when = art.select_one(".post-content")
        m = DATE.search(when.get_text(" ", strip=True)) if when else None
        if not (link and m):
            continue
        d, mo, y = map(int, m.groups())
        title = " ".join(link.get_text(" ", strip=True).split())
        event = {"venue": VENUE, "city": CITY, "date": f"{y:04d}-{mo:02d}-{d:02d}T00:00:00",
                 "eventUrl": link["href"], "ticketUrl": link["href"]}
        if SOLD_OUT.search(title):
            event["status"] = "sold out"
            title = SOLD_OUT.sub(" ", title).strip()
        if CANCELLED.search(title):
            event["status"] = "cancelled"
            title = CANCELLED.sub(" ", title).strip()
        if re.search(r"\(S\)", title):
            event["age"] = "S"
        event["artist"] = title
        events.append(event)
    return events


def add_details(event: dict, html: str) -> None:
    """Ticket link, and doors time and price when the text gives them."""
    content = BeautifulSoup(html, "html.parser").select_one(".et_pb_post_content")
    if not content:
        return
    ticket = next((a["href"] for a in content.select("a[href]")
                   if TICKET_HOSTS.search(a["href"])), None)
    if ticket:
        event["ticketUrl"] = ticket
    text = " ".join(content.get_text(" ", strip=True).split())
    # Only "Ovet 19.00" counts: a bare "klo 16:00" is often the ticket sale start.
    t = re.search(r"\b(?:ovet|doors)\s*(?:klo\s*)?(\d{1,2})[.:](\d{2})", text, re.I)
    if t:
        hh, mm = int(t.group(1)), t.group(2)
        event["date"] = f"{event['date'][:10]}T{hh:02d}:{mm}:00"
        event["doors"] = f"{hh:02d}:{mm}"
    price = re.search(r"\bliput\s*(?:alk\.?\s*)?(\d+(?:[,.]\d+)?\s*€)", text, re.I)
    if price:
        event["price"] = " ".join(price.group(1).split())
    if re.search(r"\bK-?18\b", text):
        event["age"] = "K-18"


def tag(event: dict, cache: dict, overrides: dict) -> list[str]:
    """The gig's genres, the same way genres.py tags it every night."""
    tags = []
    for act in g.parse_title(event["artist"]):
        _name, artist_tags = g.resolve_artist(act, cache, overrides, refresh=False)
        tags += [t for t in artist_tags if t not in tags]
    return g.pick_genres(event, tags)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every gig and whether it's kept; save nothing")
    args = parser.parse_args()

    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    today = date.today().isoformat()
    gigs = [e for e in parse_list(resp.text) if e["date"][:10] >= today]
    print(f"✓ Found {len(gigs)} upcoming gigs at {VENUE}")
    if not gigs:
        return 1  # the page layout probably changed; fail loudly

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

    for i, event in enumerate(kept):
        if i:
            time.sleep(DELAY)
        try:
            page = requests.get(event["eventUrl"], headers=HEADERS, timeout=30)
            page.raise_for_status()
            add_details(event, page.text)
        except requests.RequestException as e:
            print(f"  ! {event['artist'][:50]}: {e}", file=sys.stderr)

    events = load_events()
    # merge() doesn't refresh "status", so update it here (sold out / cancelled / gone).
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
