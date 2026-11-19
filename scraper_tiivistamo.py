#!/usr/bin/env python3
"""
Scraper for Tiivistämö, Helsinki (the former Kulttuuriareena Gloria; Gloria's
activity moved here in 2019). Note: gloria.fi is an unrelated magazine.

Tiivistämö is run by the City of Helsinki, so its events come from the city's
open Linked Events API (https://api.hel.fi/linkedevents/). Only concerts are
kept: events with the "konsertit" keyword (no breakdance contests, salsa or
poetry nights). Cancelled and postponed events are skipped.

Festival days (e.g. Hellsinki Industrial Festival) are separate events that
share one description listing every day's line-up; that day's acts are put
into the title ("Festival: Act (CC), Act, ...") so genres.py can tag them.

Usage:
  python scraper_tiivistamo.py
"""

import html
import re
import sys
from datetime import date, datetime, timedelta, timezone

import requests

from eventstore import load_events, merge, save_events

API = "https://api.hel.fi/linkedevents/v1/event/"
PLACE_ID = "tprek:8099"  # Tiivistämö
VENUE = "Tiivistämö"
CITY = "Helsinki"
HEADERS = {"User-Agent": "event-calendar-bot/1.0"}
MAX_PAGES = 10

AGE_IN_TITLE = re.compile(r"\s*\((S|K-?18|S\s*/\s*K-?18)\)\s*|\s+(S\s*/\s*K-?18)\s*$", re.I)
DAY_HEADER = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
NOT_AN_ACT = re.compile(
    r"\d{1,2}[.:]\d{2}|€|klo|ovet|ikäraja|liput|lippu|www\.|http|tiivistämö|festival|club|"
    r"nightrave|sisäänpääsy|päivän|^(ma|ti|ke|to|pe|la|su)\b", re.I)


def finnish_time(utc_iso: str) -> datetime:
    """UTC timestamp -> Finnish local time (EET/EEST, EU summer time rules)."""
    t = datetime.fromisoformat(utc_iso.replace("Z", "+00:00")).astimezone(timezone.utc)

    def last_sunday(year: int, month: int) -> datetime:
        d = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
        return d - timedelta(days=(d.weekday() + 1) % 7)

    summer_start = last_sunday(t.year, 3).replace(hour=1)   # 01:00 UTC
    summer_end = last_sunday(t.year, 10).replace(hour=1)
    offset = 3 if summer_start <= t < summer_end else 2
    return (t + timedelta(hours=offset)).replace(tzinfo=None)


def text_lines(description_html: str) -> list[str]:
    text = re.sub(r"<\s*(br|/p|/div|/li|/h\d)\s*/?>", "\n", description_html, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return [" ".join(line.split()) for line in text.split("\n") if line.strip()]


def festival_lineup(description_html: str, day: date) -> list[str]:
    """Acts listed under this day's date header in a festival description."""
    lines = text_lines(description_html)
    acts, in_day = [], False
    for line in lines:
        m = DAY_HEADER.search(line)
        if m:
            d, mo, y = map(int, m.groups())
            in_day = (y, mo, d) == (day.year, day.month, day.day)
            continue
        if in_day and len(line) <= 40 and not NOT_AN_ACT.search(line):
            acts.append(line)
    return acts


def age_label(min_age: int | None, title: str) -> str | None:
    m = AGE_IN_TITLE.search(title)
    if m:
        raw = (m.group(1) or m.group(2) or "").upper().replace(" ", "")
        return raw.replace("K18", "K-18")
    return "K-18" if min_age == 18 else None


def fetch_concerts() -> list[dict]:
    events = []
    url, params = API, {"location": PLACE_ID, "start": "today", "sort": "start_time",
                        "page_size": 100, "include": "keywords"}
    for _ in range(MAX_PAGES):
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            keywords = {((k.get("name") or {}).get("fi") or "").lower()
                        for k in item.get("keywords", []) if isinstance(k, dict)}
            if "konsertit" not in keywords:
                continue
            if item.get("event_status") not in (None, "EventScheduled"):
                continue
            if item.get("super_event_type"):  # umbrella events duplicate their days
                continue

            name = ((item.get("name") or {}).get("fi") or (item.get("name") or {}).get("en") or "").strip()
            start = finnish_time(item["start_time"])
            title = " ".join(AGE_IN_TITLE.sub(" ", name).split())

            if re.search(r"festival|fest\b", title, re.I):
                desc = (item.get("description") or {}).get("fi") or ""
                acts = festival_lineup(desc, start.date())
                if acts:
                    title = f"{title}: {', '.join(acts)}"

            info = (item.get("info_url") or {}).get("fi") or ""
            offers = item.get("offers") or []
            ticket = info or next(((o.get("info_url") or {}).get("fi") for o in offers
                                   if (o.get("info_url") or {}).get("fi")), "")
            event = {
                "artist": title,
                "venue": VENUE,
                "city": CITY,
                "date": start.strftime("%Y-%m-%dT%H:%M:00"),
                "doors": start.strftime("%H:%M"),
                "ticketUrl": ticket or f"https://tapahtumat.hel.fi/fi/events/{item['id']}",
                "eventUrl": f"https://tapahtumat.hel.fi/fi/events/{item['id']}",
            }
            age = age_label(item.get("audience_min_age"), name)
            if age:
                event["age"] = age
            if any(o.get("is_free") for o in offers):
                event["price"] = "Vapaa pääsy"
            events.append(event)
        url, params = (data.get("meta") or {}).get("next"), None
        if not url:
            break
    return events


def main() -> int:
    scraped = fetch_concerts()
    print(f"✓ Found {len(scraped)} upcoming concerts at {VENUE}")
    events = load_events()
    added = merge(scraped, events)
    save_events(events)
    print(f"✓ Added {added} new {VENUE} events ({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
