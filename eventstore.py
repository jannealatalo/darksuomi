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


def _key(e: dict) -> tuple:
    return (e["venue"], e["date"][:10], e["artist"].casefold().strip())


def merge(scraped: list[dict], events: list[dict]) -> int:
    """Merge scraped gigs into `events` in place; returns how many were added."""
    by_key = {_key(e): e for e in events}
    by_url = {e["eventUrl"]: e for e in events if e.get("eventUrl")}
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    added = 0
    for event in scraped:
        same_page = by_url.get(event.get("eventUrl"))
        existing = same_page or by_key.get(_key(event))
        if existing:
            for field in REFRESHED_FIELDS:
                if field in event:
                    existing[field] = event[field]
            if same_page:
                # Same event page: the title may have been updated (line-up
                # completed, support act added), so keep it current.
                existing["artist"] = event["artist"]
            continue
        event["id"] = next_id
        next_id += 1
        events.append(event)
        by_key[_key(event)] = event
        if event.get("eventUrl"):
            by_url[event["eventUrl"]] = event
        added += 1
    return added
