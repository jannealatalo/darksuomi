#!/usr/bin/env python3
"""
Scraper for Kannusali, Espoo (Kannusillankatu 4, Espoon keskus), from
Espoo's Linked Events server like Sellosali (scraper_tiivistamo.run).

Kannusali's programme is mostly pop, Christmas concerts, films and dance
afternoons with an occasional rock or metal gig, so only metal, punk,
goth and other core-genre gigs are kept (genres.keep_fitting, core_only).

Usage:
  python scraper_kannusali.py
  python scraper_kannusali.py --all   # print every gig with its genres, save nothing
"""

import sys

from scraper_tiivistamo import run

if __name__ == "__main__":
    sys.exit(run(
        fit_genres=True,
        core_only=True,
        api="https://api.espoo.fi/events/v1/event/",
        place="tprek:21430",
        venue="Kannusali",
        city="Espoo",
        music_keywords=("musiikki", "konsertit"),
        skip_keywords=("tanssi", "teatteritaide", "elokuvat"),
        skip_title=r"^lasten\b|^elokuva\b|muskari|päivätanssit|mummodisko|kabaree",
        event_page="https://www.espoo.fi/fi/tapahtumat/{id}",
    ))
