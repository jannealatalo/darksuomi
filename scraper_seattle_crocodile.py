#!/usr/bin/env python3
"""
Seattle: The Crocodile's calendar (https://calendar.thecrocodile.com/), which
covers its rooms (The Crocodile, Madame Lou's, Here-After, The Rabbit Box,
Hotel Crocodile) and some shows it books at the Sunset Tavern.

Every upcoming show is a Webflow list item: a link (TicketWeb or the show
page), the title in <h3>, then "Nov 28, 2026 6:00 PM" (or "December 2,
2026" without a time) and the room.

Usage:
  python scraper_seattle_crocodile.py
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

import seattle as s

URL = "https://calendar.thecrocodile.com/"


def parse(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    out = []
    for item in soup.select("[role=listitem].w-dyn-item"):
        link = next((a for a in item.select("a[href]")
                     if "w-condition-invisible" not in (a.get("class") or [])), None)
        title = item.select_one("h3")
        lines = [" ".join(d.get_text(" ", strip=True).split())
                 for d in item.select(".cal-start-date")]
        if not (link and title and len(lines) >= 2):
            continue
        day = s.day_of(lines[0])
        if not day:
            continue
        url = urljoin(URL, link["href"])
        # Each item has the date twice, with and without the time (one hidden).
        time = next((t for t in map(s.clock, lines) if t), None)
        out.append(s.event(title.get_text(" ", strip=True), lines[1], day, time, url))
    return out


def main() -> int:
    return s.save("The Crocodile (and its rooms)", parse(s.get(URL).text))


if __name__ == "__main__":
    s.main_guard(main)
