#!/usr/bin/env python3
"""
Scraper for Helsingin Kulttuuritalo and its club stage KULT
(https://kulttuuritalo.fi/tapahtumat/).

Gigs come from the site's WordPress API (post type "tapahtuma"): title, date
(from the event URL), hall ("KULT" or the main "Kulttuuritalo" hall) and the
venue's genre category. For each upcoming gig, the event page is read once a
week for the doors time, start time, age limit, price and ticket link.

Both halls are stored as separate venues ("KULT", "Kulttuuritalo") so the
site's venue filter can tell them apart.

Usage:
  python scraper_kulttuuritalo.py
"""

import html
import re
import sys
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

API = "https://kulttuuritalo.fi/wp-json/wp/v2/tapahtuma"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
CITY = "Helsinki"
MAX_PAGES = 20
PAGE_DELAY = 1.0      # seconds between event page loads
RECHECK_DAYS = 7

# Hall taxonomy (tapahtumapaikka) slugs -> venue names on Dark Suomi.
HALLS = {"kult": "KULT", "kulttuuritalo": "Kulttuuritalo"}
DEFAULT_HALL = "Kulttuuritalo"

DATE_IN_URL = re.compile(r"/tapahtuma/(\d{4}-\d{2}-\d{2})/")
TICKET_HOSTS = re.compile(r"lippu\.fi/event|tiketti\.fi|ticketmaster|tiketit", re.I)


def api_get(path_params: dict) -> requests.Response:
    resp = requests.get(API, params=path_params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def taxonomy_slugs(taxonomy: str) -> dict[int, str]:
    url = API.replace("/tapahtuma", f"/{taxonomy}")
    resp = requests.get(url, params={"per_page": 100, "_fields": "id,slug"},
                        headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return {t["id"]: t["slug"] for t in resp.json()}


def fetch_upcoming() -> list[dict]:
    halls = taxonomy_slugs("tapahtumapaikka")
    genres = taxonomy_slugs("genre")
    today = date.today().isoformat()
    events = []
    for page in range(1, MAX_PAGES + 1):
        resp = api_get({"per_page": 100, "page": page,
                        "_fields": "link,title,genre,tapahtumapaikka"})
        items = resp.json()
        for item in items:
            m = DATE_IN_URL.search(item["link"])
            if not m or m.group(1) < today:
                continue
            title = html.unescape(item["title"]["rendered"]).strip()
            # The hall is already the venue: "KULT: Band" -> "Band".
            title = re.sub(r"^KULT\s*[:\-–]\s*", "", title, flags=re.I)
            hall_slugs = [halls.get(h) for h in item.get("tapahtumapaikka", [])]
            venue = next((HALLS[s] for s in hall_slugs if s in HALLS), DEFAULT_HALL)
            events.append({
                "artist": " ".join(title.split()),
                "venue": venue,
                "city": CITY,
                "date": f"{m.group(1)}T00:00:00",
                "ticketUrl": item["link"],
                "eventUrl": item["link"],
                "venueGenres": [genres[g] for g in item.get("genre", []) if g in genres],
            })
        if page >= int(resp.headers.get("X-WP-TotalPages", page)):
            break
    return events


def hhmm(text: str) -> str | None:
    m = re.search(r"(\d{1,2})[.:](\d{2})", text)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def page_details(url: str) -> dict:
    """Doors, start time, age limit and ticket link from an event page."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    details: dict = {}

    for strong in soup.select(".fl-callout-text strong"):
        label = strong.get_text(strip=True).rstrip(":").casefold()
        value = strong.parent.get_text(" ", strip=True)
        value = value[len(strong.get_text(strip=True)):].lstrip(" :")
        if label == "ovet":
            details["doors"] = hhmm(value)
        elif label == "tapahtuma alkaa":
            details["start"] = hhmm(value)
        elif label == "ikäraja" and value:
            details["age"] = value

    # "Liput alkaen 32,00 € + tilausmaksut ..." -> "alk. 32,00 €"
    m = re.search(r"Liput\s+alkaen\s+(\d[\d,.]*\s*€)", soup.get_text(" "), re.I)
    if m:
        details["price"] = f"alk. {' '.join(m.group(1).split())}"

    for a in soup.select("a.fl-button[href]"):
        if TICKET_HOSTS.search(a["href"]):
            details["ticketUrl"] = a["href"]
            break
    return {k: v for k, v in details.items() if v}


def main() -> int:
    scraped = fetch_upcoming()
    print(f"✓ Found {len(scraped)} upcoming events at Kulttuuritalo/KULT")
    if not scraped:
        return 1  # the API probably changed; fail loudly

    events = load_events()
    known = {e.get("eventUrl"): e for e in events if e.get("eventUrl")}
    stale = (date.today() - timedelta(days=RECHECK_DAYS)).isoformat()
    checked = 0
    for event in scraped:
        previous = known.get(event["eventUrl"])
        if previous and previous.get("detailsFetched", "") >= stale:
            # Fresh enough: keep the details we already have.
            for field in ("date", "doors", "age", "price", "ticketUrl", "detailsFetched"):
                if field in previous:
                    event[field] = previous[field]
            continue
        if checked:
            time.sleep(PAGE_DELAY)
        try:
            d = page_details(event["eventUrl"])
        except requests.RequestException as e:
            print(f"  ! {event['artist'][:50]}: {e}", file=sys.stderr)
            continue
        checked += 1
        doors = d.get("doors") or d.get("start")
        if doors:
            event["doors"] = doors
            event["date"] = f"{event['date'][:10]}T{doors}:00"
        if d.get("start") and d.get("start") != doors:
            event["schedule"] = [{"time": d["start"], "name": "Show starts"}]
        if d.get("age"):
            event["age"] = d["age"]
        if d.get("price"):
            event["price"] = d["price"]
        if d.get("ticketUrl"):
            event["ticketUrl"] = d["ticketUrl"]
        event["detailsFetched"] = date.today().isoformat()

    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Checked {checked} event pages, added {added} new events "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
