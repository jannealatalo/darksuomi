#!/usr/bin/env python3
"""
Seattle: the Kremwerk complex (https://www.kremwerk.com/) and its three
rooms, Kremwerk, Timbre Room and Cherry: goth / industrial / darkwave nights,
techno and the odd live band.

The Squarespace events collection gives its upcoming events as JSON
(/upcoming?format=json -> {"upcoming": [{"title", "startDate": epoch ms,
"fullUrl", "location": {"addressTitle": "Timbre Room"}, "tags": [...]}]}).
Most are DJ nights, which genre tagging leaves among the hidden genres.

Usage:
  python scraper_seattle_kremwerk.py
"""

from datetime import datetime, timezone

import seattle as s

BASE = "https://www.kremwerk.com"
ROOMS = {"kremwerk": "Kremwerk", "kremwerk complex": "Kremwerk",
         "timbre room": "Timbre Room", "cherry": "Cherry"}


def main() -> int:
    data = s.get(f"{BASE}/upcoming", params={"format": "json"}).json()
    found = []
    for e in data.get("upcoming") or []:
        if not e.get("title") or not e.get("startDate"):
            continue
        start = s.local(datetime.fromtimestamp(e["startDate"] / 1000, timezone.utc))
        room = ((e.get("location") or {}).get("addressTitle") or "Kremwerk").strip()
        found.append(s.event(e["title"], ROOMS.get(room.casefold(), room), start.date(),
                             start.strftime("%H:%M"), BASE + e["fullUrl"]))
    return s.save("Kremwerk complex", found)


if __name__ == "__main__":
    s.main_guard(main)
