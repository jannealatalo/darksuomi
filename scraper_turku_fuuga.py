#!/usr/bin/env python3
"""
Scraper for Musiikkitalo Fuuga, Turku (https://www.musiikkitalofuuga.fi/), the
concert house (mostly classical, Turku Philharmonic). Only gigs that fit
Dark Suomi are kept.

The events page loads its list from the site's search API:
POST /wp-json/karhu-content-filtered-search/v1/get-content {"post_types":
"event", "posts_per_page": 300, ...} -> {"contentList": [{"data": {
"eventTitle", "eventDateDayNum": "9", "eventDateMonth": "joulukuuta",
"eventTime": "19:00", "eventVenue": ["Ateljee"], "eventGen": ["Rock"],
"buyLink", "url"}}]}. The year isn't given, so the next such date is used.

Kept: events the house tags Rock or Indie, and others whose acts' genre
tags fit (genres.keep_fitting: e.g. a symphonic metal night).

Usage:
  python scraper_turku_fuuga.py
"""

import genres as g
import turku as t

API = "https://www.musiikkitalofuuga.fi/wp-json/karhu-content-filtered-search/v1/get-content"
VENUE = "Musiikkitalo Fuuga"
OWN_GENRES = {"Rock", "Indie"}
NOT_GIGS = {"Klassinen", "Sinfoniakonsertti", "Kamarimusiikki", "Kuoromusiikki",
            "Lastenmusiikki", "Ooppera", "Komedia", "Talkshow", "Kierrokset", "Tanssi"}


def main() -> int:
    r = t.requests.post(API, headers=t.HEADERS, timeout=60, json={
        "page": 1, "search_key": "", "filters": {}, "post_types": "event",
        "show_only_terms": "", "dynamic_filters": "false",
        "filter_options": "event-gen,event-venue", "lang": "fi", "meta": {},
        "posts_per_page": 300})
    r.raise_for_status()
    tagged, others = [], []
    for item in r.json().get("contentList", []):
        e = item.get("data") or {}
        month = t.MONTHS_FI.get((e.get("eventDateMonth") or "").lower())
        if not month or not e.get("eventDateDayNum") or not e.get("url"):
            continue
        day = t.day_of(int(e["eventDateDayNum"]), month)
        gens = {t.clean(x) for x in e.get("eventGen") or []}
        room = ", ".join(e.get("eventVenue") or [])
        gig = t.event(e.get("eventTitle") or e.get("title", ""), VENUE, day,
                      t.clock(e.get("eventTime")), e["url"], e.get("buyLink") or None,
                      room=room or None)
        if gens & OWN_GENRES:
            tagged.append(gig)
        elif not gens & NOT_GIGS:
            others.append(gig)
    kept = tagged + g.keep_fitting(others)
    return t.save(VENUE, kept)


if __name__ == "__main__":
    t.main_guard(main)
