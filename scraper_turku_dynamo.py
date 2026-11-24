#!/usr/bin/env python3
"""
Scraper for Dynamo Klubi, Turku (https://www.dynamoklubi.com/), the
two-floor club on Linnankatu (live gigs downstairs, DJs on both floors).

The front page lists the coming nights as WordPress posts: a date box
("Lauantai 28.11.", no year) and free text. A night with a gig says "Live
klo 21:30" / "Live 21:30", or has a ticket link (Eventim Light, sold as
Lippu.fi) and "Ovet klo 18:30". The acts are the bold text right before
"Liput:" ("<strong>Stepa<br>Tohtori Getto</strong>"), or else the first
bold line. DJ-only nights, quizzes and "we are closed" days are skipped.

Usage:
  python scraper_turku_dynamo.py
"""

import re

from bs4 import BeautifulSoup

import turku as t

BASE = "https://www.dynamoklubi.com/"
VENUE = "Dynamo"
LIVE = re.compile(r"\blive\s+(?:klo\s*)?(\d{1,2}(?:[:.]\d{2})?)\b", re.I)
DOORS = re.compile(r"\bovet\s+klo\s*(\d{1,2}(?:[:.]\d{2})?)\b", re.I)


def hhmm(text: str) -> str:
    """'20' / '20:30' / '20.30' -> '20:00' / '20:30'."""
    h, _, m = text.replace(".", ":").partition(":")
    return f"{int(h):02d}:{m or '00'}"


def acts(excerpt_html: str) -> str | None:
    """The gig's acts: the last bold block before "Liput:", else the first one."""
    cut = re.search(r"Liput\s*:", excerpt_html)
    before = excerpt_html[:cut.start()] if cut else excerpt_html
    blocks = re.findall(r"<strong>(.*?)</strong>", before, re.S)
    if not blocks:
        return None
    block = blocks[-1] if cut else blocks[0]
    names = [t.clean(re.sub(r"<[^>]+>", "", p)) for p in re.split(r"<br\s*/?>", block)]
    names = [n for n in names if n and not re.match(r"(?:dj\b|kuva|liput|ovet|vapaa)", n, re.I)]
    return ", ".join(names) or None


def main() -> int:
    soup = BeautifulSoup(t.get(BASE).text, "html.parser")
    found = []
    for item in soup.select(".content_item_article_link"):
        day_el = item.select_one(".day-number")
        excerpt = item.select_one(".content_item_excerpt") or item.find_next_sibling(
            class_="content_item_excerpt")
        if not day_el or not excerpt:
            continue
        text = t.clean(excerpt.get_text(" ", strip=True))
        live = LIVE.search(text)
        doors = DOORS.search(text)
        ticket = next((a["href"] for a in excerpt.select("a[href]")
                       if "eventim" in a["href"] or "lippu.fi" in a["href"]), None)
        if not live and not (ticket and doors):
            continue  # DJ nights, karaoke, closed days
        title = acts(str(excerpt))
        day = t.dm(day_el.get_text(strip=True))
        if not title or not day:
            continue
        page = re.search(r"page_id=(\d+)", item.get("onclick", ""))
        url = f"{BASE}?page_id={page[1]}" if page else BASE
        price = re.search(r"à\s*(\d+(?:,\d+)?\s*€)", text)
        age = re.search(r"\bK-?(18|20)\b", text)
        found.append(t.event(title, VENUE, day, hhmm((doors or live)[1]), url, ticket,
                             price=price[1].replace(" ", "") if price else None,
                             age=f"K-{age[1]}" if age else None))
    return t.save(VENUE, found)


if __name__ == "__main__":
    t.main_guard(main)
