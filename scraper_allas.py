#!/usr/bin/env python3
"""
Scraper for Allas Live, Helsinki (https://www.allaslive.fi/), the summer
concert series (mid-May to mid-September) at Allas Sea Pool, Katajanokka.

The site is a Live Nation site; its gig list (/keikat) loads from a JSON
search API:
  /__api/search/events?VenueIds=1555379&PageSize=50&Page=1&culture=fi-FI
-> {"total": 5, "documents": [{"name": "Tehosekoitin", "eventDate":
"2027-09-11T00:00:00Z", "doorTime": "19:00", "lineup": [{"name": ...,
"type": "headline"}, ...], "url": "/all-events/...", "tickets": [{"ticketUrl":
..., "priceFrom": 0}], "agePolicy": "18+", ...}]}.

Every gig is kept, though most of Allas Live is Finnish pop: they're big
names people look for, and genres.py tags them so the pop ones are listed
under the genres hidden by default. New seasons are announced from the
autumn on.

Usage:
  python scraper_allas.py
"""

import html
import re
import sys
from datetime import date

import requests

from eventstore import load_events, merge, save_events

SITE = "https://www.allaslive.fi"
API_URL = f"{SITE}/__api/search/events"
VENUE_ID = "1555379"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Allas Live"
CITY = "Helsinki"
PAGE_SIZE = 50
CANCELLED = re.compile(r"\b(?:peruttu|perutaan|cancell?ed)\b", re.I)
POSTPONED = re.compile(r"\b(?:siirtyy|siirretty|postponed)\b", re.I)


def fetch_all() -> list[dict]:
    docs, page = [], 1
    while True:
        resp = requests.get(API_URL, headers=HEADERS, timeout=30, params={
            "VenueIds": VENUE_ID, "IncludePostponed": "true", "IncludeCancelled": "true",
            "PageSize": PAGE_SIZE, "Page": page, "culture": "fi-FI"})
        resp.raise_for_status()
        data = resp.json()
        docs += data.get("documents") or []
        if len(docs) >= (data.get("total") or 0) or not data.get("documents") or page >= 10:
            return docs
        page += 1


def to_event(doc: dict) -> dict | None:
    day = (doc.get("eventDate") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return None
    lineup = sorted(doc.get("lineup") or [], key=lambda a: a.get("rank") or 99)
    acts = [a["name"].strip() for a in lineup if a.get("type") == "headline" and a.get("name")]
    acts += [a["name"].strip() for a in lineup
             if a.get("type") != "headline" and a.get("name") and a["name"].strip() not in acts]
    name = (doc.get("name") or "").strip()
    title = name if not acts or len(acts) == 1 else ", ".join(acts)
    if not title:
        return None
    clock = doc.get("doorTime") or doc.get("showTime") or ""
    clock = clock if re.fullmatch(r"\d{1,2}:\d{2}", clock) else "00:00"
    hh, mm = clock.split(":")
    page = f"{SITE}{doc['url']}" if doc.get("url", "").startswith("/") else SITE + "/keikat"
    tickets = [t for t in doc.get("tickets") or [] if t.get("ticketUrl")]
    event = {
        "artist": title,
        "venue": VENUE,
        "city": CITY,
        "date": f"{day}T{int(hh):02d}:{mm}:00",
        "ticketUrl": tickets[0]["ticketUrl"] if tickets else page,
        "eventUrl": page,
    }
    if clock != "00:00":
        event["doors"] = f"{int(hh):02d}:{mm}"
    prices = [t["priceFrom"] for t in tickets if (t.get("priceFrom") or 0) > 0]
    if prices:
        event["price"] = f"alk. {min(prices):.2f}€".replace(".", ",").replace(",00€", "€")
    age = re.fullmatch(r"(\d{2})\+", doc.get("agePolicy") or "")
    if age:
        event["age"] = f"K-{age.group(1)}"
    notes = html.unescape(" ".join(str(doc.get(k) or "") for k in ("alertText", "listingsText")))
    if CANCELLED.search(notes) or CANCELLED.search(name):
        event["status"] = "cancelled"
    elif POSTPONED.search(notes):
        event["status"] = "postponed"
    return event


def main() -> int:
    try:
        docs = fetch_all()
    except (requests.RequestException, ValueError) as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    today = date.today().isoformat()
    found = [e for d in docs if not d.get("isDeleted") and (e := to_event(d))
             and e["date"][:10] >= today]
    # Between seasons the list can be empty: that's fine, not a broken page.
    print(f"✓ Found {len(found)} upcoming events at {VENUE}")
    for e in found:
        print(f"  {e['date'][:10]} {e['artist']}")

    events = load_events()
    added = merge(found, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
