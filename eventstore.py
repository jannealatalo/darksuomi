"""
Shared helper for venue scrapers: merge scraped gigs into events.json.

A scraped gig matches an existing one by its event page URL, or else by
venue + day + title. Matches get their changing fields refreshed; new gigs
get the next free id. Gigs are never deleted here (past ones just stop
showing on the site).
"""

import json
from pathlib import Path

EVENTS_FILE = Path(__file__).resolve().parent / "frontend" / "data" / "events.json"

# Fields a venue scraper may refresh on an already-known gig.
REFRESHED_FIELDS = ("date", "ticketUrl", "eventUrl", "venue", "venueGenres",
                    "doors", "age", "schedule", "detailsFetched")


def load_events() -> list[dict]:
    with open(EVENTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_events(events: list[dict]) -> None:
    events.sort(key=lambda e: e["date"])
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
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
        existing = by_url.get(event.get("eventUrl")) or by_key.get(_key(event))
        if existing:
            for field in REFRESHED_FIELDS:
                if field in event:
                    existing[field] = event[field]
            continue
        event["id"] = next_id
        next_id += 1
        events.append(event)
        by_key[_key(event)] = event
        if event.get("eventUrl"):
            by_url[event["eventUrl"]] = event
        added += 1
    return added
