#!/usr/bin/env python3
"""
Seattle: Climate Pledge Arena (https://climatepledgearena.com/), concerts only.

The site's WordPress "The Events Calendar" REST API lists every event:
/wp-json/tribe/events/v1/events?per_page=50&start_date=... -> {"events": [{
"title", "start_date": "2026-11-29 19:30:00", "url", "website" (tickets),
"categories": [{"name": "Concerts"}, ...]}], "next_rest_url": ...}.
Hockey (Kraken, Torrent), basketball and family shows are left out: only
events in the "Concerts" or "Music" category are kept.

Usage:
  python scraper_seattle_climatepledge.py
"""

import re
import time

import seattle as s

API = "https://climatepledgearena.com/wp-json/tribe/events/v1/events"
VENUE = "Climate Pledge Arena"
MUSIC = {"concerts", "music"}


def main() -> int:
    url, params, found = API, {"per_page": 50, "start_date": s.today().isoformat()}, []
    for _ in range(10):
        data = s.get(url, params=params).json()
        for e in data.get("events", []):
            cats = {c.get("name", "").casefold() for c in e.get("categories") or []}
            when = e.get("start_date") or ""
            if not cats & MUSIC or len(when) < 16:
                continue
            title = e.get("title", "")
            status = "cancelled" if re.search(r"\bcancel+ed\b", title, re.I) else None
            found.append(s.event(title, VENUE, s.day_of(when[:10]), when[11:16], e["url"],
                                 e.get("website") or None, status=status))
        url, params = data.get("next_rest_url"), None
        if not url:
            break
        time.sleep(1)
    return s.save(VENUE, found)


if __name__ == "__main__":
    s.main_guard(main)
