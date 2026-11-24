#!/usr/bin/env python3
"""
Seattle: the AEG / AXS venue sites, which share one platform:
  - Showbox Presents (https://www.showboxpresents.com/): the Showbox, Showbox
    SoDo and AEG's shows at other venues (Paramount, Moore, Neptune…);
    each entry names its venue ("@ Showbox SoDo").
  - Neumos (https://www.neumos.com/) and Barboza (https://www.thebarboza.com/),
    downstairs from Neumos.

/events lists the first page; /events/events_ajax/<offset> returns the
next ones as a JSON string of the same HTML. Entries: the headliner in
<h3>, the support acts in <h4> ("with Silent Planet, … and Save Us"), the
date ("Tue, Nov 24, 2026" or aria-label "November 24 2026"), "Show 7:00 PM"
or "Doors: 7:00 PM", the age and the AXS ticket link.

Usage:
  python scraper_seattle_aeg.py
"""

import json
import re
import time

from bs4 import BeautifulSoup

import seattle as s

SITES = [
    ("https://www.showboxpresents.com", None),
    ("https://www.neumos.com", "Neumos"),
    ("https://www.thebarboza.com", "Barboza"),
]
PAGE = 20  # the sites ignore a bigger per_page
PAUSE = 10  # seconds between pages
MAX_PAGES = 15


def parse(page_html: str, site_venue: str | None) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    out = []
    for item in soup.select("div.entry"):
        link = item.select_one("h3 a[href]")
        if not link:
            continue
        support = item.select_one("h4")
        date_el = item.select_one(".date")
        when = (date_el.get("aria-label") or date_el.get_text(" ", strip=True)) if date_el else ""
        day = s.day_of(when)
        if not day:
            continue
        time_el = item.select_one(".time")
        time = s.clock(time_el.get_text(" ", strip=True) if time_el else "")
        venue = site_venue
        venue_el = item.select_one(".venue")
        if venue_el:
            venue = venue_el.get_text(" ", strip=True).lstrip("@ ").strip()
        # Showbox Presents also books Portland, Spokane, Boise…: Seattle only.
        if not venue or s.venue_name(venue) not in s.SEATTLE_VENUES:
            continue
        ticket = item.select_one("a.tickets[href], a.btn-tickets[href]")
        age = item.select_one(".age")
        title = s.title_with_support(link.get_text(" ", strip=True),
                                     support.get_text(" ", strip=True) if support else None)
        status = None
        if ticket is not None and ticket.get("data-canceled") == "true":
            status = "cancelled"
        elif ticket is not None and re.search(r"sold\s*out", ticket.get_text(" "), re.I):
            status = "sold out"
        out.append(s.event(title, venue, day, time, link["href"],
                           ticket["href"] if ticket else None,
                           age=s.age_of(age.get_text(" ", strip=True) if age else None),
                           status=status))
    return out


def scrape_site(base: str, venue: str | None) -> list[dict]:
    events = parse(s.get(f"{base}/events").text, venue)
    offset = len(events)
    for _ in range(MAX_PAGES):
        # The sites refuse quick successive pages ("406 Not Acceptable"), so
        # go slowly and stop at the first refusal, keeping what we have: gigs
        # are never deleted, so the later pages fill in over the nights.
        time.sleep(PAUSE)
        r = s.requests.get(f"{base}/events/events_ajax/{offset}", timeout=40,
                           params={"category": 0, "venue": 0, "team": 0, "exclude": "",
                                   "per_page": PAGE, "came_from_page": "event-list-page"},
                           headers={**s.HEADERS, "X-Requested-With": "XMLHttpRequest"})
        if r.status_code != 200:
            print(f"  ! {base}: page at {offset} refused (HTTP {r.status_code}); stopping here")
            break
        try:
            chunk = parse(json.loads(r.text), venue)
        except ValueError:
            break
        known = {e["eventUrl"] for e in events}
        new = [e for e in chunk if e["eventUrl"] not in known]
        if not new:  # past the end (some sites then repeat the last page)
            break
        events += new
        offset += PAGE
    return events


def main() -> int:
    scraped = []
    for base, venue in SITES:
        try:
            found = scrape_site(base, venue)
            print(f"  {base}: {len(found)}")
            scraped += found
        except Exception as e:  # one broken site shouldn't stop the others
            print(f"  ! {base}: {e}")
    return s.save("AEG venues (Showbox, Neumos, Barboza)", scraped)


if __name__ == "__main__":
    s.main_guard(main)
