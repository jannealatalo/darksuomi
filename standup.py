#!/usr/bin/env python3
"""
Stand-up shows in Helsinki and Espoo for "Itse Keksityt Vitsit"
(darksuomi.fi/standup). Writes frontend/data/standup/events.json.

Sources, first one wins when the same show is found twice:
  1. Dark Suomi's own venue scrapes (frontend/data/events.json): gigs whose
     title says stand-up / comedy (Kulttuuritalo, KULT, Semifinal's "Joka
     v*tun keskiviikko", Bar Loose's "Naurut"…). Run this after the scrapers.
  2. Korjaamo's stand-up / comedy category (scraper_korjaamo, kind="comedy").
  3. The City of Helsinki's and Espoo's Linked Events APIs: events with the
     "stand up -komiikka" / "koomikot" keyword, or found by a text search
     for stand up and saying so in their title or description (this skips
     plays that only mention stand-up somewhere).

The file is rebuilt every run with upcoming shows only. If a source fails,
its shows from the previous run are kept.

Usage:
  python standup.py
"""

import html
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import requests

import scraper_korjaamo
from scraper_tiivistamo import age_label, finnish_time

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "frontend" / "data"
OUT_FILE = DATA_DIR / "standup" / "events.json"
HEADERS = {"User-Agent": "event-calendar-bot/1.0"}
MAX_PAGES = 10

LINKED_EVENTS = [
    # (source name, API, the event's public page, default city)
    ("helsinki-api", "https://api.hel.fi/linkedevents/v1/event/",
     "https://tapahtumat.hel.fi/fi/events/{id}", "Helsinki"),
    ("espoo-api", "https://api.espoo.fi/events/v1/event/",
     "https://www.espoo.fi/fi/tapahtumat/{id}", "Espoo"),
]
STANDUP_KEYWORDS = "yso:p9244,yso:p15401"  # stand up -komiikka, koomikot
TEXT_SEARCHES = ("stand up", "standup", "stand-up", "koomikko", "komiikka")
CITY_NAME = re.compile(r"\b(helsin\w*|helsingfors|espoo\w*|esbo)\b", re.I)  # "Espoon kaupunki"
# "Club Act!One K-18", "Niko Kivelä (K16)": the age limit goes to its own field.
AGE_AT_END = re.compile(r"\s*[(\[]?\b(K-?\s?1[268]|S\s*/\s*K-?18|S)\b[)\]]?\s*$", re.I)

# A title that says it's a stand-up / comedy show.
COMEDY_TITLE = re.compile(
    r"stand.?up|standup|komedia|comedy|koomik|qoomik|naurut|nauru(?:korjaamo|klubi|ilta)|"
    r"roast|joka v\*tun keskiviikko|komiikka", re.I)
# ...but not these, even if the title has a comedy word.
NOT_COMEDY = re.compile(r"pubivisa|visailu|quiz|bingo|wrestling|painia|disko|disco", re.I)
# A description that clearly speaks of stand-up.
STANDUP_TEXT = re.compile(r"stand[\s-]?up|standup", re.I)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def show_key(show: dict) -> tuple:
    """Same day + same start of the title = the same show."""
    return show["date"][:10], norm(show["title"])[:18]


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def from_darksuomi() -> list[dict]:
    """Comedy shows already scraped from Dark Suomi's venues."""
    with open(DATA_DIR / "events.json", encoding="utf-8") as f:
        events = json.load(f)
    shows = []
    for e in events:
        if not COMEDY_TITLE.search(e["artist"]) or NOT_COMEDY.search(e["artist"]):
            continue
        shows.append(show_from_gig(e, "darksuomi"))
    return shows


def from_korjaamo() -> list[dict]:
    return [show_from_gig(e, "korjaamo") for e in scraper_korjaamo.fetch("comedy")]


def tidy(show: dict) -> dict:
    """Age limit out of the title, Finnish wording for Dark Suomi's prices."""
    m = AGE_AT_END.search(show["title"])
    if m and len(show["title"]) > len(m.group(0)) + 3:
        show["title"] = show["title"][:m.start()].strip(" -–")
        age = re.sub(r"\s", "", m.group(1)).upper().replace("K18", "K-18").replace("K16", "K-16").replace("K12", "K-12")
        show.setdefault("age", age)
    if show.get("price"):
        show["price"] = re.sub(r"\s*at the door$", " ovelta", show["price"])
        # "15 € + toimitusmaksu (nauramaan.com)" -> "15 €"
        show["price"] = re.sub(r"\s*\+\s*(toimitus|palvelu|lippukaupan)\S*.*$", "", show["price"], flags=re.I)
    return show


def show_from_gig(e: dict, source: str) -> dict:
    show = {
        "title": e["artist"],
        "venue": e["venue"],
        "city": e.get("city", "Helsinki"),
        "date": e["date"],
        "ticketUrl": e.get("ticketUrl") or e.get("eventUrl"),
        "eventUrl": e.get("eventUrl") or e.get("ticketUrl"),
        "source": source,
    }
    for field in ("price", "age", "status", "room"):
        if e.get(field):
            show[field] = e[field]
    return show


def text(value: dict | None) -> str:
    value = value or {}
    return value.get("fi") or value.get("en") or value.get("sv") or ""


def from_linked_events(source: str, api: str, page: str, default_city: str) -> list[dict]:
    """Stand-up shows on one Linked Events server (Helsinki or Espoo)."""
    queries = [{"keyword": STANDUP_KEYWORDS}] + [{"text": t} for t in TEXT_SEARCHES]
    items: dict[str, dict] = {}
    for query in queries:
        url, params = api, {**query, "start": "today", "sort": "start_time",
                            "page_size": 100, "include": "keywords,location"}
        for _ in range(MAX_PAGES):
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", []):
                items[item["id"]] = item
            url, params = (data.get("meta") or {}).get("next"), None
            if not url:
                break

    shows = []
    for item in items.values():
        if item.get("super_event_type"):  # umbrella events duplicate their days
            continue
        if item.get("event_status") in ("EventCancelled", "EventPostponed"):
            continue
        name = text(item.get("name")).strip()
        keywords = {k.get("id") for k in item.get("keywords", []) if isinstance(k, dict)}
        description = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(
            text(item.get(f)) for f in ("description", "short_description"))))
        is_standup = (keywords & set(STANDUP_KEYWORDS.split(","))
                      or COMEDY_TITLE.search(name) or STANDUP_TEXT.search(description))
        if not is_standup or NOT_COMEDY.search(name):
            continue

        location = item.get("location") or {}
        city = text(location.get("address_locality")) or default_city
        if not CITY_NAME.search(city):
            continue
        start = finnish_time(item["start_time"])
        offers = item.get("offers") or []
        ticket = text(item.get("info_url")) or next(
            (text(o.get("info_url")) for o in offers if text(o.get("info_url"))), "")
        event_page = page.format(id=item["id"])
        show = {
            "title": " ".join(name.split()),
            "venue": text(location.get("name")) or "?",
            "city": "Espoo" if re.search(r"espoo|esbo", city, re.I) else "Helsinki",
            "date": start.strftime("%Y-%m-%dT%H:%M:00"),
            "ticketUrl": ticket or event_page,
            "eventUrl": event_page,
            "source": source,
        }
        age = age_label(item.get("audience_min_age"), name)
        if age:
            show["age"] = age
        if any(o.get("is_free") for o in offers):
            show["price"] = "Vapaa pääsy"
        else:
            price = next((text(o.get("price")) for o in offers if text(o.get("price"))), "")
            if price and len(price) <= 40:
                show["price"] = " ".join(price.split())
        shows.append(show)
    return shows


# ---------------------------------------------------------------------------

def main() -> int:
    try:
        with open(OUT_FILE, encoding="utf-8") as f:
            previous = json.load(f)
    except FileNotFoundError:
        previous = []

    sources = [("darksuomi", from_darksuomi), ("korjaamo", from_korjaamo)]
    sources += [(name, lambda a=api, p=page, c=city, n=name: from_linked_events(n, a, p, c))
                for name, api, page, city in LINKED_EVENTS]

    today = date.today().isoformat()
    shows: dict[tuple, dict] = {}
    for name, fetch in sources:
        try:
            found = fetch()
            print(f"  {name}: {len(found)} shows")
        except (requests.RequestException, OSError, ValueError) as e:
            found = [s for s in previous if s.get("source") == name]
            print(f"  ! {name} failed ({e}); keeping its {len(found)} earlier shows",
                  file=sys.stderr)
        for show in found:
            if show["date"][:10] >= today:
                tidy(show)
                shows.setdefault(show_key(show), show)

    result = sorted(shows.values(), key=lambda s: (s["date"], s["title"]))
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ {len(result)} upcoming stand-up shows in Helsinki and Espoo")
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
