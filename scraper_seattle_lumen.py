#!/usr/bin/env python3
"""
Seattle: Lumen Field and the WaMu Theater next to it, concerts only, from
the stadium's calendar (https://www.lumenfield.com/events-tickets/event-calendar).

Each Webflow list item carries hidden filter fields (the date
"2026-11-28", the category "Concerts", the venue "WAMU Theater"), the
start time "8:00 PM", the name (.card-title-h3) and the event page. Football,
soccer, Supercross and trade shows are left out. A multi-day event's days
each have their own item (Tape B night 1, night 2), and the multi-day
summary item is skipped.

Usage:
  python scraper_seattle_lumen.py
"""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

import seattle as s

URL = "https://www.lumenfield.com/events-tickets/event-calendar"


def parse(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    out = []
    for item in soup.select("[role=listitem].w-dyn-item"):
        hidden = [" ".join(e.get_text(" ", strip=True).split())
                  for e in item.select(".filter-item-hidden")]
        title = item.select_one(".card-title-h3")
        link = item.select_one("a[href]")
        if len(hidden) < 4 or not title or not link or hidden[1] != "Concerts":
            continue
        if "/multi-day-events/" in link["href"]:
            continue
        day = s.day_of(hidden[0])
        time_el = item.select_one(".ft-card-time")
        name = " ".join(title.get_text(" ", strip=True).split())
        if not day or name.casefold() == "venue change":
            continue
        out.append(s.event(name, hidden[3], day,
                           s.clock(time_el.get_text(" ", strip=True) if time_el else None),
                           urljoin(URL, link["href"])))
    return out


def main() -> int:
    return s.save("Lumen Field / WaMu Theater", parse(s.get(URL).text))


if __name__ == "__main__":
    s.main_guard(main)
