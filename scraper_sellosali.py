#!/usr/bin/env python3
"""
Scraper for Sellosali, Espoo (https://www.espoo.fi/fi/sellosalin-tapahtumat).

Espoo runs its own Linked Events server (api.espoo.fi/events/v1/), so this
reuses scraper_tiivistamo.fetch_concerts. Espoo tags gigs with the keyword
"musiikki"; children's shows, dance afternoons, the afternoon disco and
music theatre are left out.

Usage:
  python scraper_sellosali.py
"""

import sys

from scraper_tiivistamo import run

if __name__ == "__main__":
    sys.exit(run(
        api="https://api.espoo.fi/events/v1/event/",
        place="tprek:26429",
        venue="Sellosali",
        city="Espoo",
        music_keywords=("musiikki", "konsertit"),
        skip_keywords=("tanssi", "teatteritaide", "elokuvat"),
        skip_title=r"^lasten\b|iltapäivädisko|päivätanssit|nukketeatteri|musiikkiteatteri",
        event_page="https://www.espoo.fi/fi/tapahtumat/{id}",
    ))
