"""
Shared helper for venue scrapers: merge scraped gigs into events.json.

A scraped gig matches an existing one by its event page URL, or else by
venue + day + title. Matches get their changing fields refreshed; new gigs
get the next free id. Gigs are never deleted here (past ones just stop
showing on the site).

Helsinki gigs live in frontend/data/events.json; the experimental city sites
(darksuomi.fi/tampere, /oulu) keep theirs in frontend/data/<city>/events.json.
Pass `city=` to work on those.
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "frontend" / "data"
EVENTS_FILE = DATA_DIR / "events.json"
CITIES = ("tampere", "oulu")  # experimental sites, separate from Helsinki


def events_file(city: str | None = None) -> Path:
    """events.json of Helsinki (default) or of one of the CITIES."""
    if city in (None, "", "helsinki"):
        return EVENTS_FILE
    if city not in CITIES:
        raise ValueError(f"unknown city {city!r}")
    return DATA_DIR / city / "events.json"

# Fields a venue scraper may refresh on an already-known gig.
REFRESHED_FIELDS = ("date", "ticketUrl", "eventUrl", "venue", "venueGenres",
                    "venueDefault", "price",
                    "doors", "age", "schedule", "detailsFetched")


def load_events(city: str | None = None) -> list[dict]:
    path = events_file(city)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_events(events: list[dict], city: str | None = None) -> None:
    events.sort(key=lambda e: e["date"])
    path = events_file(city)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)


# Status words some venues put in the title: "Europe – … Tour (SOLD OUT!)",
# "PERUTTU: Disco Night". The site shows a status badge instead.
_SOLD_OUT = re.compile(r"\s*[(\[]?\s*\b(?:sold\s*out|loppuunmyyty)\b\s*!*\s*[)\]]?", re.I)
_CANCELLED = re.compile(
    r"^\s*(?:peruttu|cancell?ed)\s*[:!–—-]+\s*|\s*[(\[]\s*(?:peruttu|cancell?ed)\s*!*\s*[)\]]", re.I)


def status_from_title(event: dict) -> None:
    """Move a sold-out / cancelled note from the title to event["status"]."""
    title = event["artist"]
    if _CANCELLED.search(title):
        event["status"] = "cancelled"
        title = _CANCELLED.sub(" ", title)
    elif _SOLD_OUT.search(title):
        event["status"] = "sold out"
        title = _SOLD_OUT.sub(" ", title)
    else:
        return
    event["artist"] = " ".join(title.split()).strip(" -–—:")


def _key(e: dict) -> tuple:
    return (e["venue"], e["date"][:10], e["artist"].casefold().strip())


# The headliner: the title up to the first support act / list / subtitle,
# without a country code. "Kanonenfieber (GER) + support: Groza (GER)" and
# "Kanonenfieber (GER)" are both "kanonenfieber".
_HEADLINER_END = re.compile(r"\s+(?:\+|&|w/|with|feat\.?|support)\s+|\s*[,:/|–—]\s*|\s+-\s+", re.I)
_COUNTRY = re.compile(r"\s*\([A-Z]{2,3}\)", re.I)


def headliner(title: str) -> str:
    head = _HEADLINER_END.split(_COUNTRY.sub("", title), maxsplit=1)[0]
    return " ".join(head.split()).casefold()


def _slot_key(e: dict) -> tuple | None:
    """Venue + start time + headliner: the same gig renamed by the venue
    (support act added), which often also moves its page to a new URL."""
    if e["date"][11:16] in ("", "00:00"):
        return None  # no start time: too loose
    head = headliner(e["artist"])
    return (e["venue"], e["date"][:16], head) if len(head) >= 3 else None


def _contained(event: dict, events: list[dict]) -> dict | None:
    """A gig at the same venue and start time whose title is contained in
    the new one or the other way round: the venue added a name for the
    night ("TALVIPUUTARHA : Hulda Huima duo, Ingrid Yö, Unta") or dropped it."""
    if event["date"][11:16] in ("", "00:00"):
        return None
    new = " ".join(event["artist"].split()).casefold()
    for e in events:
        if e["venue"] != event["venue"] or e["date"][:16] != event["date"][:16]:
            continue
        old = " ".join(e["artist"].split()).casefold()
        if min(len(old), len(new)) >= 4 and (old in new or new in old):
            return e
    return None


def merge(scraped: list[dict], events: list[dict]) -> int:
    """Merge scraped gigs into `events` in place; returns how many were added."""
    by_key = {_key(e): e for e in events}
    by_url = {e["eventUrl"]: e for e in events if e.get("eventUrl")}
    by_slot = {k: e for e in events if (k := _slot_key(e))}
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    added = 0
    for event in scraped:
        status_from_title(event)
        same_page = by_url.get(event.get("eventUrl"))
        renamed = None if same_page else (by_slot.get(_slot_key(event) or ())
                                          or _contained(event, events))
        if renamed:
            # The venue retitled the gig: keep the newest title and page.
            same_page = renamed
        existing = same_page or by_key.get(_key(event))
        if existing:
            for field in REFRESHED_FIELDS:
                if field in event:
                    existing[field] = event[field]
            if same_page:
                # Same event page: the title may have been updated (line-up
                # completed, support act added), so keep it current.
                existing["artist"] = event["artist"]
            if event.get("status"):
                existing["status"] = event["status"]
            continue
        event["id"] = next_id
        next_id += 1
        events.append(event)
        by_key[_key(event)] = event
        if slot := _slot_key(event):
            by_slot[slot] = event
        if event.get("eventUrl"):
            by_url[event["eventUrl"]] = event
        added += 1
    return added
