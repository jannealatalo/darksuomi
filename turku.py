"""
Shared helpers for the Turku scrapers (scraper_turku_*.py), the city site
darksuomi.fi/turku (frontend/data/turku/events.json).
"""

import html
import re
import sys
from datetime import date, timedelta

import requests

from eventstore import load_events, merge, save_events

CITY_KEY = "turku"
CITY = "Turku"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           "Accept-Encoding": "gzip, deflate"}

MONTHS_FI = {"tammikuuta": 1, "helmikuuta": 2, "maaliskuuta": 3, "huhtikuuta": 4,
             "toukokuuta": 5, "kesäkuuta": 6, "heinäkuuta": 7, "elokuuta": 8,
             "syyskuuta": 9, "lokakuuta": 10, "marraskuuta": 11, "joulukuuta": 12}


def clean(text: str) -> str:
    return " ".join(html.unescape(text or "").split())


def day_of(d: int, m: int, y: int | None = None) -> date | None:
    """Day and month; without a year, the next such day from about a
    month ago on (lists show "La 12.12." without the year)."""
    try:
        if y:
            return date(y, m, d)
        today = date.today()
        guess = date(today.year, m, d)
        return guess if guess >= today - timedelta(days=45) else date(today.year + 1, m, d)
    except ValueError:
        return None


def dm(text: str) -> date | None:
    """'27.11.2026', '12.12.' -> date."""
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})?", text or "")
    return day_of(int(m[1]), int(m[2]), int(m[3]) if m[3] else None) if m else None


def clock(text: str | None) -> str | None:
    m = re.search(r"\b(\d{1,2})[:.](\d{2})\b", text or "")
    return f"{int(m[1]):02d}:{m[2]}" if m and int(m[1]) < 24 else None


def event(title: str, venue: str, day: date, time: str | None, url: str,
          ticket_url: str | None = None, **extra) -> dict:
    e = {
        "artist": clean(title),
        "venue": venue,
        "city": CITY,
        "date": f"{day.isoformat()}T{time or '00:00'}:00",
        "ticketUrl": ticket_url or url,
        "eventUrl": url,
    }
    if time:
        e["doors"] = time
    e.update({k: v for k, v in extra.items() if v})
    return e


def get(url: str, **kw) -> requests.Response:
    r = requests.get(url, headers={**HEADERS, **kw.pop("headers", {})}, timeout=40, **kw)
    r.raise_for_status()
    return r


def save(name: str, scraped: list[dict], empty_ok: bool = False) -> int:
    """Merge upcoming gigs into Turku's events.json; exit code for main()."""
    today = date.today().isoformat()
    upcoming, seen = [], set()
    for e in scraped:
        key = (e["eventUrl"], e["date"][:16])
        if e["date"][:10] >= today and key not in seen:
            seen.add(key)
            upcoming.append(e)
    print(f"✓ {name}: {len(upcoming)} upcoming gigs")
    for e in upcoming:
        print(f"  {e['date'][:16]} {e['venue']}: {e['artist'][:70]}")
    if not upcoming:
        return 0 if empty_ok else 1  # the page layout probably changed; fail loudly
    events = load_events(CITY_KEY)
    added = merge(upcoming, events)
    save_events(events, CITY_KEY)
    print(f"✓ Added {added} new ({len(events)} Turku events in total)")
    return 0


def main_guard(fn) -> None:
    try:
        sys.exit(fn())
    except requests.RequestException as e:
        print(f"✗ {e}")
        sys.exit(1)
