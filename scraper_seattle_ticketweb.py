#!/usr/bin/env python3
"""
Seattle: clubs whose sites use TicketWeb's WordPress plugin:
  - Chop Suey (https://chopsuey.com/), Capitol Hill
  - Clock-Out Lounge (https://clockoutlounge.com/), Beacon Hill

The front page lists the shows 20 at a time (/page/2/, /page/3/…), each a
<div class="tw-section">: the name and its page, "with <span>…</span>" for
the support acts, the date ("11.24" or "November 24, 2026"), "Doors: 7:00 PM
/ Show: 7:30 PM", the price and the TicketWeb link.

Usage:
  python scraper_seattle_ticketweb.py
"""

import re
import time
from datetime import date

from bs4 import BeautifulSoup

import seattle as s

SITES = [("https://chopsuey.com", "Chop Suey"), ("https://clockoutlounge.com", "Clock-Out Lounge")]
MAX_PAGES = 10


def text(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def day_of(raw: str) -> date | None:
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", raw)  # "11.24"
    if m:
        months = "jan feb mar apr may jun jul aug sep oct nov dec".split()
        return s.day_of(f"{months[int(m[1]) - 1]} {int(m[2])}")
    return s.day_of(raw)


def parse(page_html: str, venue: str) -> list[dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    out = []
    for sec in soup.select("div.tw-section"):
        link = sec.select_one(".tw-name a[href]")
        day = day_of(text(sec.select_one(".tw-event-date")))
        if not link or not day:
            continue
        support = sec.select_one(".tw-attractions")
        doors = text(sec.select_one(".tw-event-door-time"))
        show = text(sec.select_one(".tw-event-time"))
        ticket = next((a["href"] for a in sec.select("a[href]") if "ticketweb.com" in a["href"]), None)
        out.append(s.event(
            s.title_with_support(text(link), text(support) or None), venue, day,
            s.clock(doors) or s.clock(show), link["href"], ticket,
            price=s.price_of(text(sec.select_one(".tw-price"))),
            age=s.age_of(text(sec.select_one(".tw-age-restriction")))))
    return out


def main() -> int:
    scraped = []
    for base, venue in SITES:
        try:
            found = []
            for n in range(1, MAX_PAGES + 1):
                page = parse(s.get(base + ("/" if n == 1 else f"/page/{n}/")).text, venue)
                new = [e for e in page if e["eventUrl"] not in {f["eventUrl"] for f in found}]
                if not new:
                    break
                found += new
                time.sleep(1)
            print(f"  {venue}: {len(found)}")
            scraped += found
        except s.requests.RequestException as e:
            if "404" not in str(e):  # /page/N/ past the end
                print(f"  ! {venue}: {e}")
            scraped += found
    return s.save("Chop Suey, Clock-Out Lounge", scraped)


if __name__ == "__main__":
    s.main_guard(main)
