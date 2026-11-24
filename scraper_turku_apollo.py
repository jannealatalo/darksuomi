#!/usr/bin/env python3
"""
Scraper for Apollo Live Club Turku (https://apolloturku.fi/keikat), the
nightclub on Humalistonkatu whose early-evening club gigs (Stam1na,
Uniklubi…) are listed on /keikat.

Each gig is a <div class="bandevents__event">: the day ("LA 12.12.", no
year), the name, the gig page (keikat/157/stam1na) and the Tiketti link.
Gigs are K-18 unless the ticket shop says otherwise; no times are given.

Usage:
  python scraper_turku_apollo.py
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

import turku as t

URL = "https://apolloturku.fi/keikat"
VENUE = "Apollo Turku"


def main() -> int:
    soup = BeautifulSoup(t.get(URL).text, "html.parser")
    found = []
    for item in soup.select(".bandevents__event"):
        title = item.select_one(".bandevents__event--title")
        day = t.dm(item.select_one(".bandevents__event--date").get_text(" ", strip=True)
                   if item.select_one(".bandevents__event--date") else "")
        info = item.select_one("a.info[href]")
        buy = item.select_one("a.buy[href]")
        if not (title and day and info):
            continue
        found.append(t.event(title.get_text(" ", strip=True), VENUE, day, None,
                             urljoin("https://apolloturku.fi/", info["href"]),
                             buy["href"] if buy else None, age="K-18"))
    return t.save(VENUE, found)


if __name__ == "__main__":
    t.main_guard(main)
