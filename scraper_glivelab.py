#!/usr/bin/env python3
"""
Scraper for G Livelab Helsinki (https://glivelab.fi/), the club on
Yrjönkatu. The front page lists every upcoming gig as the same
<li class="item"> cards as G Livelab Tampere (scraper_tampere_glivelab.py
parses them): title, date without year and start time; the card links to
the event page, which also sells the tickets.

Most G Livelab gigs are jazz, folk, blues and singer-songwriters, so, as
for Dubrovnik, only gigs the site would show by default are kept: the
bands' genre tags are looked up right away (genres.py: Last.fm /
MusicBrainz, cached in artists.json) and checked with
genres.keep_when_scraping().

Usage:
  python scraper_glivelab.py
  python scraper_glivelab.py --all   # print every gig with its genres, save nothing
"""

import argparse
import re
import sys
from datetime import date

import requests

import genres as g
from eventstore import load_events, merge, save_events
from scraper_tampere_glivelab import HEADERS, parse_cards

LIST_URL = "https://glivelab.fi/"
VENUE = "G Livelab"
CITY = "Helsinki"
# "(levynjulkkarit)" = album release show; "(US)" etc. = the act's country.
TITLE_NOTES = re.compile(r"\s*\((?:levynjulkkarit|[A-Z]{2})\)", re.I)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every gig and whether it's kept; save nothing")
    args = parser.parse_args()

    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    today = date.today()
    gigs, seen = [], set()
    for e in parse_cards(resp.text, today, "glivelab.fi/events/", VENUE, CITY):
        if e["date"][:10] >= today.isoformat() and e["eventUrl"] not in seen and "gift-ticket" not in e["eventUrl"]:
            seen.add(e["eventUrl"])
            e["artist"] = TITLE_NOTES.sub("", e["artist"]).strip()
            gigs.append(e)
    print(f"✓ Found {len(gigs)} upcoming gigs at {VENUE}")
    if not gigs:
        return 1  # the page layout probably changed; fail loudly

    cache = g.load_json(g.CACHE_FILE, {})
    config = g.load_json(g.CONFIG_FILE, {})
    overrides = config.get("artistOverrides", {})
    kept = []
    for event in gigs:
        _artists, tags = g.gig_tags(event["artist"], cache, overrides)
        genres = g.pick_genres(event, tags)
        keep = g.keep_when_scraping(genres, config)
        if args.all or keep:
            print(f"  {'+' if keep else '-'} {event['date'][:10]} {event['artist']}  {genres[:4]}")
        if keep:
            kept.append(event)
    g.save_json(g.CACHE_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))
    if args.all:
        return 0

    events = load_events()
    added = merge(kept, events)
    save_events(events)
    print(f"✓ Kept {len(kept)} gigs that fit Dark Suomi; added {added} new "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
