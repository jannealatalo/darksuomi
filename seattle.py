"""
Shared helpers for the Seattle scrapers (scraper_seattle_*.py), the hidden
experiment at darksuomi.fi/seattle (frontend/data/seattle/events.json).

US sites write "Tue, Nov 24, 2026", "Doors: 7:00 PM", "21 & Over" and
"$31.24"; these turn them into the same event fields the Finnish
scrapers use (date "2026-11-24T19:00:00", doors "19:00", age "21+").
Dates are Seattle's local time, like the Finnish ones are Helsinki's.
"""

import html
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

from eventstore import load_events, merge, save_events

CITY_KEY = "seattle"
CITY = "Seattle"
# Pacific time without tzdata (missing on Windows): UTC-8, and UTC-7 from
# the second Sunday of March to the first Sunday of November (2 am local).
TZ = timezone(timedelta(hours=-8))


def local(utc: datetime) -> datetime:
    """A UTC (aware) time in Seattle's local time."""
    y = utc.year
    march = datetime(y, 3, 8, 10, tzinfo=timezone.utc)   # 2 am PST = 10 UTC
    nov = datetime(y, 11, 1, 9, tzinfo=timezone.utc)     # 2 am PDT = 9 UTC
    start = march + timedelta(days=(6 - march.weekday()) % 7)
    end = nov + timedelta(days=(6 - nov.weekday()) % 7)
    hours = -7 if start <= utc < end else -8
    return utc.astimezone(timezone(timedelta(hours=hours)))
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           # Some sites answer 406 to the default, which offers zstd/brotli.
           "Accept-Encoding": "gzip, deflate"}

# One name per venue, whichever site lists it.
VENUE_NAMES = {
    "paramount theatre seattle": "Paramount Theatre", "the paramount theatre": "Paramount Theatre",
    "paramount theatre": "Paramount Theatre",
    "the moore theatre": "Moore Theatre", "moore theatre": "Moore Theatre",
    "the neptune theatre": "Neptune Theatre", "neptune theatre": "Neptune Theatre",
    "the showbox": "Showbox", "showbox": "Showbox", "showbox at the market": "Showbox",
    "showbox sodo": "Showbox SoDo",
    "wamu theater": "WaMu Theater", "wamu theatre": "WaMu Theater",
    "el corazón": "El Corazón", "el corazon": "El Corazón",
    "the funhouse": "The Funhouse", "funhouse": "The Funhouse",
    "the crocodile": "The Crocodile", "madame lou's": "Madame Lou's",
    "here-after": "Here-After", "the rabbit box": "The Rabbit Box",
    "hotel crocodile": "Hotel Crocodile",
    "sunset tavern": "Sunset Tavern", "the sunset tavern": "Sunset Tavern",
    "neumos": "Neumos", "barboza": "Barboza", "the barboza": "Barboza",
    "substation seattle": "Substation", "substation": "Substation",
    "chop suey": "Chop Suey", "clock-out lounge": "Clock-Out Lounge",
    "climate pledge arena": "Climate Pledge Arena", "lumen field": "Lumen Field",
    "t-mobile park": "T-Mobile Park", "kremwerk": "Kremwerk",
}

SEATTLE_VENUES = set(VENUE_NAMES.values())

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def venue_name(raw: str) -> str:
    raw = " ".join(html.unescape(raw).split())
    return VENUE_NAMES.get(raw.casefold(), raw)


def today() -> date:
    """Today in Seattle."""
    return local(datetime.now(timezone.utc)).date()


def clock(text: str | None) -> str | None:
    """'7:00 PM' / '7pm' / '19:30' -> '19:00'; None if there's no time."""
    if not text:
        return None
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\b", text, re.I)
    if m:
        h = int(m[1]) % 12 + (12 if m[3].lower() == "p" else 0)
        return f"{h:02d}:{int(m[2] or 0):02d}"
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    return f"{int(m[1]):02d}:{m[2]}" if m else None


def day_of(text: str, year: int | None = None) -> date | None:
    """'Tue, Nov 24, 2026', 'November 24 2026', 'Nov 25' (year guessed:
    the next such day from about a month ago on), '2026-11-24'."""
    text = html.unescape(text)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))
    m = re.search(r"\b([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?(?:\s+(\d{4}))?", text)
    if not m or m[1].lower() not in MONTHS:
        return None
    month, d = MONTHS[m[1].lower()], int(m[2])
    y = int(m[3]) if m[3] else year
    if y is None:
        now = today()
        y = now.year
        if date(y, month, min(d, 28)) < now - timedelta(days=45):
            y += 1
    try:
        return date(y, month, d)
    except ValueError:
        return None


def age_of(text: str | None) -> str | None:
    if not text:
        return None
    if re.search(r"all\s*ages", text, re.I):
        return "All ages"
    m = re.search(r"\b(21|18|16)\s*(?:\+|&\s*over|and\s*over|plus)", text, re.I)
    return f"{m[1]}+" if m else None


def price_of(text: str | None) -> str | None:
    if not text:
        return None
    if re.search(r"\bfree\b", text, re.I):
        return "Free"
    amounts = re.findall(r"\$\s?(\d+(?:\.\d{2})?)", text)
    if not amounts:
        return None
    values = sorted({float(a) for a in amounts})
    if values[-1] == 0:
        return "Free"
    fmt = lambda v: f"${v:.2f}".replace(".00", "")
    return fmt(values[0]) if len(values) == 1 else f"{fmt(values[0])}–{fmt(values[-1])}"


def title_with_support(headliner: str, support: str | None) -> str:
    """'SAOSIN' + 'with Silent Planet, Like Moths to Flames, and Save Us'
    -> 'SAOSIN, Silent Planet, Like Moths to Flames, Save Us'."""
    head = " ".join(html.unescape(headliner).split()).strip(" -–")
    if not support:
        return head
    sup = " ".join(html.unescape(support).split())
    sup = re.sub(r"^(?:with|w/|w\.|feat\.?|featuring|special guests?:?|plus)\s+", "", sup, flags=re.I)
    sup = re.sub(r",?\s+(?:and|&)\s+(?=[^,]+$)", ", ", sup).strip(" ,")
    return f"{head}, {sup}" if sup and sup.casefold() not in head.casefold() else head


# "Clock-Out Lounge Presents: Imprecation w/ …" -> "Imprecation w/ …"
PRESENTS = re.compile(r"^[^:]{2,60}?\bpresents?\s*[:–—-]\s*", re.I)
# Listings that aren't events at all.
NOT_EVENTS = re.compile(r"^closed\s*(?:$|[-:!(]|today|tonight)|\bclosed for\b|\b(?:we|we'll|we're)\b.{0,15}\bclosed\b|"
                        r"\bclosure\b|private event|private party|buyout", re.I)


def event(title: str, venue: str, day: date, time: str | None, url: str,
          ticket_url: str | None = None, **extra) -> dict:
    e = {
        "artist": PRESENTS.sub("", " ".join(html.unescape(title).split())),
        "venue": venue_name(venue),
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
    """GET, retried after a pause on a temporary refusal (406, 429, 5xx)."""
    headers = {**HEADERS, **kw.pop("headers", {})}
    for wait in (5, 30, None):
        r = requests.get(url, headers=headers, timeout=40, **kw)
        if r.status_code in (406, 429) or r.status_code >= 500:
            if wait:
                time.sleep(wait)
                continue
        r.raise_for_status()
        return r
    raise AssertionError("unreachable")


def save(name: str, scraped: list[dict]) -> int:
    """Merge upcoming gigs into Seattle's events.json; exit code for main()."""
    now = today().isoformat()
    upcoming, seen = [], set()
    for e in scraped:
        key = (e["eventUrl"], e["date"][:10])
        if e["date"][:10] >= now and key not in seen and not NOT_EVENTS.search(e["artist"]):
            seen.add(key)
            upcoming.append(e)
    print(f"✓ {name}: {len(upcoming)} upcoming events")
    for e in upcoming:
        print(f"  {e['date'][:16]} {e['venue']}: {e['artist'][:70]}")
    if not upcoming:
        return 1  # the page layout probably changed; fail loudly
    events = load_events(CITY_KEY)
    added = merge(upcoming, events)
    save_events(events, CITY_KEY)
    print(f"✓ Added {added} new ({len(events)} Seattle events in total)")
    return 0


def main_guard(fn) -> None:
    try:
        sys.exit(fn())
    except requests.RequestException as e:
        print(f"✗ {e}")
        sys.exit(1)
