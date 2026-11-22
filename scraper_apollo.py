#!/usr/bin/env python3
"""
Scraper for Apollo Live Club, Helsinki (https://apolloliveclub.fi/), the
club at Mannerheimintie 16 (Forum).

The events page lists every upcoming event (WordPress, "The Post Grid"):

  <div class="rt-grid-item ...">
    <h3 class="entry-title"><a href="https://apolloliveclub.fi/morcheeba/">MORCHEEBA</a></h3>
    <div class="tpg-excerpt-inner">21.4.2027 - 19:00 - 37,90€ - K-18</div>

Most of Apollo's programme is club nights, pop, hip hop and comedy, so (as
with Dubrovnik) only gigs the site would show by default are kept: the acts'
genre tags are looked up while scraping (genres.py, cached in artists.json)
and checked with genres.shown_by_default(). The weekly club nights ("FRIDAY
20.11.") and parties are skipped by title. The kept gigs' own pages are
loaded for the ticket link, and their description has the last word: a
namesake band's tags don't count when the text says it's a drum & bass
night ("Kanine") or a comedian ("Paul Smith – HAPPY").

Usage:
  python scraper_apollo.py
  python scraper_apollo.py --all   # print every event with its genres, save nothing
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

LIST_URL = "https://apolloliveclub.fi/tapahtumat/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Apollo Live Club"
CITY = "Helsinki"
DELAY = 1.0  # seconds between gig page loads

# "21.4.2027 - 19:00 - 37,90€ - K-18"; the time may be "--:--", the price "€".
INFO = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*-\s*(\d{1,2}:\d{2}|--:--)?\s*-?\s*([^-]*)-?\s*(.*)$")
NOT_A_GIG = re.compile(
    r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|maanantai|tiistai|"
    r"keskiviikko|torstai|perjantai|lauantai|sunnuntai)\b|pikkujoulu|after ?party|"
    r"\brave\b|juldagens|karaoke|\bfest\b|\bfestival\b|stand ?-?up|bingo", re.I)
# The description says it's not a band gig (unless it also says rock/metal).
NOT_BAND_TEXT = re.compile(r"drum\s*(?:&|and|n)\s*bass|\bdnb\b|neurofunk|\btechno\b|\bhouse\b|"
                           r"\bdj[- ]set|stand ?-?up|komiik|koomikk|comedian|comedy", re.I)
ROCKISH_TEXT = re.compile(r"\brock|metal|punk|\bgoth|grunge|hardcore(?!\s*techno)|\bindie", re.I)
TICKET_HOSTS = re.compile(r"tiketti\.fi|lippu\.fi|ticketmaster|livenation|eventbrite|"
                          r"lippupiste|holvi|tix\.fi|ticketswap|fienta")


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events, seen = [], set()
    for item in soup.select(".rt-grid-item"):
        link = item.select_one("h3.entry-title a[href]")
        info = item.select_one(".tpg-excerpt-inner")
        if not (link and info):
            continue
        m = INFO.search(" ".join(info.get_text(" ", strip=True).split()))
        if not m or link["href"] in seen:
            continue
        seen.add(link["href"])
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
        clock = m[4] if m[4] and m[4] != "--:--" else "00:00"
        hh, mm = clock.split(":")
        title = " ".join(link.get_text(" ", strip=True).split())
        event = {
            "artist": title,
            "venue": VENUE,
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T{int(hh):02d}:{mm}:00",
            "ticketUrl": link["href"],
            "eventUrl": link["href"],
        }
        price = m[5].strip()
        if re.search(r"\d", price):
            event["price"] = price.replace(" ", " ").strip()
        age = re.search(r"\b(K-?\d{2}(?:/K-?\d{2})?|S)\b", m[6] or "")
        if age:
            event["age"] = age.group(1)
        events.append(event)
    return events


def add_details(event: dict, html: str) -> bool:
    """Ticket link from the gig page; False when the text says it's not a band gig."""
    soup = BeautifulSoup(html, "html.parser")
    ticket = next((a["href"] for a in soup.select("a[href]") if TICKET_HOSTS.search(a["href"])), None)
    if ticket:
        event["ticketUrl"] = ticket
    main = soup.select_one(".entry-content") or soup.select_one("main") or soup
    text = " ".join(main.get_text(" ", strip=True).split())
    return not (NOT_BAND_TEXT.search(text) and not ROCKISH_TEXT.search(text))


def tag(event: dict, cache: dict, overrides: dict) -> list[str]:
    """The gig's genres, the same way genres.py tags it every night."""
    _artists, tags = g.gig_tags(event["artist"], cache, overrides)
    return g.pick_genres(event, tags)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every event and whether it's kept; save nothing")
    args = parser.parse_args()

    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    today = date.today().isoformat()
    events_found = [e for e in parse_list(resp.text) if e["date"][:10] >= today]
    print(f"✓ Found {len(events_found)} upcoming events at {VENUE}")
    if not events_found:
        return 1  # the page layout probably changed; fail loudly

    cache = g.load_json(g.CACHE_FILE, {})
    config = g.load_json(g.CONFIG_FILE, {})
    overrides = config.get("artistOverrides", {})
    kept = []
    for event in events_found:
        if NOT_A_GIG.search(event["artist"]):
            if args.all:
                print(f"  - {event['date'][:10]} {event['artist']}  (club night / party)")
            continue
        tags = tag(event, cache, overrides)
        keep = g.keep_when_scraping(tags, config)
        if args.all or keep:
            print(f"  {'+' if keep else '-'} {event['date'][:10]} {event['artist']}  {tags[:4]}")
        if keep:
            kept.append(event)
    g.save_json(g.CACHE_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))
    if args.all:
        return 0

    checked = []
    for i, event in enumerate(kept):
        if i:
            time.sleep(DELAY)
        try:
            page = requests.get(event["eventUrl"], headers=HEADERS, timeout=30)
            page.raise_for_status()
            if not add_details(event, page.text):
                print(f"  - {event['date'][:10]} {event['artist']}  (not a band gig, by its description)")
                continue
        except requests.RequestException as e:
            print(f"  ! {event['artist'][:50]}: {e}", file=sys.stderr)
        checked.append(event)
    kept = checked

    events = load_events()
    added = merge(kept, events)
    save_events(events)
    print(f"✓ Kept {len(kept)} gigs that fit Dark Suomi; added {added} new "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
