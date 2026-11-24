#!/usr/bin/env python3
"""
Scraper for Taiteen talo, Turku (https://taiteentalo.fi/tapahtumat/), the
arts centre in the old Tobacco factory (Läntinen Rantakatu) with gig nights,
experimental music and club events besides exhibitions and cinema. Music
only: the "Musiikki" category (id 24) of its WordPress REST API.

/wp-json/wp/v2/events?events-category=24 -> [{"title", "link", "acf": {
"event_dates_repeater": [{"event_date_start": "2026-12-04 19:00:00",
"event_tixly_flow": ticket link, ...}], "event_location": "Sigyn-sali"}}].
An event with several dates gives one gig per date. Genre tagging decides
which are shown by default (jazz and classical nights are hidden).

Usage:
  python scraper_turku_taiteentalo.py
"""

import time

import turku as t

API = "https://taiteentalo.fi/wp-json/wp/v2/events"
VENUE = "Taiteen talo"
MUSIC = 24


def main() -> int:
    found, page = [], 1
    while page <= 10:
        r = t.get(API, params={"events-category": MUSIC, "per_page": 100, "page": page,
                               "_fields": "title,link,acf"})
        for e in r.json():
            acf = e.get("acf") or {}
            room = t.clean(acf.get("event_location") or "") or None
            for d in acf.get("event_dates_repeater") or []:
                start = d.get("event_date_start") or ""
                if len(start) < 16:
                    continue
                day = t.dm(".".join(reversed(start[:10].split("-"))))
                title = d.get("event_title") or e["title"]["rendered"]
                found.append(t.event(title, VENUE, day,
                                     start[11:16] if start[11:16] != "00:00" else None,
                                     e["link"], d.get("event_tixly_flow") or None, room=room))
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
        time.sleep(1)
    return t.save(f"{VENUE} (music)", found, empty_ok=True)


if __name__ == "__main__":
    t.main_guard(main)
