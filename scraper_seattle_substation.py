#!/usr/bin/env python3
"""
Seattle: Substation (https://substationseattle.com/), Ballard, punk / metal /
noise gigs and DJ nights, tickets on Eventbrite.

The front page (Astro) embeds its event list as the "props" of the
EventFeed island: JSON in Astro's serialisation, where every value is a
[type, value] pair (0 = plain, 1 = array): {"events": [1, [[0, {"title":
[0, "..."], "startsAt": [0, "2026-11-25T21:00:00"], "ticketUrl": [0, ...],
"venueName": [0, "Substation Seattle"], ...}], ...]]}.

Usage:
  python scraper_seattle_substation.py
"""

import html
import json
import re

import seattle as s

URL = "https://substationseattle.com/"


def plain(v):
    """Astro's [type, value] pairs -> plain Python values."""
    if isinstance(v, list) and len(v) == 2 and v[0] in (0, 1):
        return [plain(x) for x in v[1]] if v[0] == 1 else plain(v[1])
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    return v


def parse(page_html: str) -> list[dict]:
    out = []
    for props in re.findall(r'<astro-island[^>]*component-url="[^"]*EventFeed[^"]*"[^>]*props="([^"]*)"',
                            page_html):
        data = plain(json.loads(html.unescape(props)))
        for e in data.get("events") or []:
            when = e.get("startsAt") or ""
            day = s.day_of(when[:10])
            if not day or not e.get("title"):
                continue
            url = e.get("ticketUrl") or URL
            out.append(s.event(e["title"], "Substation", day, s.clock(when[11:16]), url))
    return out


def main() -> int:
    return s.save("Substation", parse(s.get(URL).text))


if __name__ == "__main__":
    s.main_guard(main)
