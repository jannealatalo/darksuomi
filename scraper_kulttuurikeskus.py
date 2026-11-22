#!/usr/bin/env python3
"""
Scraper for Espoon kulttuurikeskus, Tapiola
(https://www.espoo.fi/fi/espoon-kulttuurikeskus/espoon-kulttuurikeskuksen-tapahtumat).

Like Sellosali, the events come from Espoo's own Linked Events server
(api.espoo.fi/events/v1/) through scraper_tiivistamo.fetch_concerts. Every
concert is kept (the site hides pop, jazz and classical by genre); dance
afternoons, theatre, stand-up, children's concerts and the music institute's
(EMO) student concerts are left out, and so is Kummeli's sketch evening
(standup.py lists it on /standup). Christmas concerts are dropped by
genres.py, like at every venue.

Usage:
  python scraper_kulttuurikeskus.py
"""

import sys

from scraper_tiivistamo import run

if __name__ == "__main__":
    sys.exit(run(
        api="https://api.espoo.fi/events/v1/event/",
        place="tprek:20402",
        venue="Espoon kulttuurikeskus",
        city="Espoo",
        music_keywords=("musiikki", "konsertit"),
        skip_keywords=("tanssi", "teatteritaide", "elokuvat"),
        skip_title=r"^lasten|jazz for kids|nukketeatteri|retrodisco|tanssit\b|"
                   r"^emo\b|^emon\b|ti-ti nalle|uppo-nalle|koulusarjakiertue|kummeli",
        event_page="https://www.espoo.fi/fi/tapahtumat/{id}",
    ))
