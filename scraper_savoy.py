#!/usr/bin/env python3
"""
Scraper for Savoy-teatteri, Helsinki (https://www.savoyteatteri.fi/), from
the city's Linked Events API (scraper_tiivistamo.run). Savoy tags its gigs
"musiikki"; theatre, dance and stand-up are left out.

Savoy is mostly jazz, chanson and Christmas concerts with an occasional
rock gig (e.g. The 69 Eyes acoustic), so only metal, punk, goth and other
core-genre gigs are kept (genres.keep_fitting, core_only).

Usage:
  python scraper_savoy.py
  python scraper_savoy.py --all   # print every gig with its genres, save nothing
"""

import sys

from scraper_tiivistamo import run

if __name__ == "__main__":
    sys.exit(run(
        fit_genres=True,
        core_only=True,
        place="tprek:7258",
        venue="Savoy-teatteri",
        music_keywords=("musiikki",),
        skip_keywords=("teatteri", "tanssi"),
    ))
