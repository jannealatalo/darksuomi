#!/usr/bin/env python3
"""
Seattle: El Corazón and The Funhouse (https://www.elcorazonseattle.com/),
the metal / punk / hardcore clubs on Eastlake Ave, one site for both.

The front page lists every upcoming show (Webflow) as a <div class="event-div">:
the day ("Wed" "Nov 25", no year), the headliners, "Supporting Talent:" and
the acts, "Doors at 6:00 pm / Show at 7:00 pm", the age, the room ("AT El
Corazón") and the price. The show's own page (/shows/...) is the link.

Usage:
  python scraper_seattle_elcorazon.py
"""

import re

from bs4 import BeautifulSoup

import seattle as s

BASE = "https://www.elcorazonseattle.com"


def text(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def parse(page_html: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    out = []
    for item in soup.select("div.event-div"):
        link = next((a for a in item.select("a[href^='/shows/']")), None)
        # Festivals have no headliners, only the title ("RAIN CITY DOOM FEST").
        heads = text(item.select_one(".headliners")) or text(item.select_one(".event-title"))
        if not link or not heads:
            continue
        day_el = item.select_one(".day-date")
        day = s.day_of(text(day_el))
        if not day:
            continue
        times = text(item.select_one(".show-times"))
        doors = re.search(r"doors\s*at\s*([\d:]+\s*[ap]\.?m)", times, re.I)
        time = s.clock(doors.group(1) if doors else times)
        venue_parts = [t for t in item.select(".venue-location div")
                       if "w-condition-invisible" not in (t.get("class") or [])]
        venue = next((text(t) for t in venue_parts if text(t).upper() != "AT"), "El Corazón")
        url = BASE + link["href"]
        out.append(s.event(
            s.title_with_support(heads, text(item.select_one(".supports")) or None),
            venue, day, time, url,
            age=s.age_of(text(item.select_one(".age-restriction"))),
            price=s.price_of(text(item.select_one(".ticket-price")))))
    return out


def main() -> int:
    return s.save("El Corazón / The Funhouse", parse(s.get(BASE + "/").text))


if __name__ == "__main__":
    s.main_guard(main)
