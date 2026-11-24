#!/usr/bin/env python3
"""
Scraper for Fuusio Turku (https://fuusioturku.fi/ohjelma/), the culture house
on Humalistonkatu with the Livesali hall, the Nirvana rock bar, Level2 and
the UG club.

The program page (WordPress, Sugar Calendar) lists the next 20 events,
about a month ahead; later ones appear here as the weeks go by (gigs are
never deleted). Each item: the title with the room after a slash
("Battlelore, Noumena, Numento /Live", "… /NIRVANA", "… /UG"), a
<time datetime="2026-11-27T00:00:00+0200"> and the event page, where the
tickets are sold on Biletti. UG nights and other DJ-club nights
("UG 27/11/26", "Student Rave …") are skipped: Fuusio's live gigs are in
Livesali and Nirvana.

Usage:
  python scraper_turku_fuusio.py
"""

import re

from bs4 import BeautifulSoup

import turku as t

URL = "https://fuusioturku.fi/ohjelma/"
VENUE = "Fuusio"
ROOMS = {"live": "Livesali", "livesali": "Livesali", "nirvana": "Nirvana",
         "level2": "Level2", "ug": "UG"}
ROOM_SUFFIX = re.compile(r"\s*/\s*(live|livesali|nirvana|level\s?2|ug)\s*$", re.I)
ROOM_PREFIX = re.compile(r"^(livesali|nirvana)\s*:\s*", re.I)
NOT_A_GIG = re.compile(r"\brave\b|\bdj\b|\bklubi\b|^ug\b|karaoke|stand ?-?up|bingo|"
                       r"\bvisa\b|tietovisa", re.I)


def main() -> int:
    soup = BeautifulSoup(t.get(URL).text, "html.parser")
    found = []
    for item in soup.select(".sugar-calendar-event-list-block__gridview__event, "
                            ".sugar-calendar-event-list-block__listview__event"):
        link = item.select_one("a[href*='/events/']")
        title_el = item.select_one(".sugar-calendar-event-list-block__event__title")
        when = item.select_one("time[datetime]")
        if not (link and title_el and when):
            continue
        title = t.clean(title_el.get_text(" ", strip=True))
        room = None
        m = ROOM_SUFFIX.search(title)
        if m:
            room = ROOMS.get(m[1].lower().replace(" ", ""))
            title = title[:m.start()].strip(" -–")
        m = ROOM_PREFIX.match(title)
        if m:
            room = room or ROOMS.get(m[1].lower())
            title = title[m.end():]
        if room == "UG" or NOT_A_GIG.search(title):
            continue
        day = t.dm(".".join(reversed(when["datetime"][:10].split("-"))) + "")
        found.append(t.event(title, VENUE, day, None, link["href"], room=room))
    return t.save("Fuusio (Livesali, Nirvana)", found)


if __name__ == "__main__":
    t.main_guard(main)
