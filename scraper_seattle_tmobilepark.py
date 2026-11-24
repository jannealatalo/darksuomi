#!/usr/bin/env python3
"""
Seattle: concerts at T-Mobile Park, the Mariners' ballpark
(https://www.mlb.com/mariners/tickets/concerts). There are only a few a
year. The page lists each as a date line ("Tuesday, August 24, 2027")
followed by its heading ("Fall Out Boy at T-Mobile Park").

Usage:
  python scraper_seattle_tmobilepark.py
"""

import html
import re

import seattle as s

URL = "https://www.mlb.com/mariners/tickets/concerts"
VENUE = "T-Mobile Park"
DATE_LINE = re.compile(r"^(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s+([A-Z][a-z]+ \d{1,2}, \d{4})$")


def parse(page_html: str) -> list[dict]:
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", page_html, flags=re.S)
    lines = [" ".join(html.unescape(t).split()) for t in re.split(r"<[^>]+>", body)]
    lines = [t for t in lines if t]
    out = []
    for i, line in enumerate(lines[:-1]):
        m = DATE_LINE.match(line)
        if not m:
            continue
        title = re.sub(r"\s+at T-Mobile Park\s*$", "", lines[i + 1], flags=re.I)
        day = s.day_of(m.group(1))
        if day and title and len(title) < 120:
            out.append(s.event(title, VENUE, day, None, URL))
    return out


def main() -> int:
    found = parse(s.get(URL).text)
    if not found:  # no concerts announced is normal here
        print(f"✓ {VENUE}: no concerts listed")
        return 0
    return s.save(VENUE, found)


if __name__ == "__main__":
    s.main_guard(main)
