#!/usr/bin/env python3
"""
Scraper for Logomo, Turku (https://logomo.fi/tapahtumakalenteri), music only.

The events calendar loads its list with the "Ajax Load More" WordPress
plugin (admin-ajax.php?action=alm_get_posts&post_type=logomo_event...),
which answers {"html": "<div class='logomo-event-teaser'>…", "meta":
{"totalposts": 69}}. The category filter (Musiikki = 1) is read from the
calendar page the request comes from, so the request sends that page as
its Referer. Each teaser has the title, "La 28.11.2026 | Logomo-sali" (or a
date range "Ti 24.11.2026 — 25.11.2026") and links to the event page and
the Livex ticket shop. Fairs and dinner shows are in other categories.

Usage:
  python scraper_turku_logomo.py
"""

import re

from bs4 import BeautifulSoup

import turku as t

AJAX = "https://logomo.fi/wp-admin/admin-ajax.php"
CALENDAR = "https://logomo.fi/tapahtumakalenteri"
MUSIC = 1
NOT_A_GIG = re.compile(r"pikkujoulu|messut|expo\b|stand ?-?up|\bkomiikk", re.I)


def main() -> int:
    r = t.get(AJAX, params={
        "action": "alm_get_posts", "query_type": "standard", "id": "logomo_salient_events_list",
        "post_id": 9173, "slug": "tapahtumakalenteri", "canonical_url": CALENDAR,
        "posts_per_page": 200, "page": 0, "offset": 0, "original_offset": 0,
        "post_type": "logomo_event", "repeater": "default", "seo_start_page": 1, "lang": "fi",
        "order": "ASC", "orderby": "_event_timestamp", "post_status": "publish", "currentPage": 1,
    }, headers={"Referer": f"{CALENDAR}?date_range=all&month=&date=&category={MUSIC}&events_s=",
                "X-Requested-With": "XMLHttpRequest"})
    soup = BeautifulSoup(r.json().get("html", ""), "html.parser")
    found = []
    for item in soup.select(".logomo-event-teaser"):
        title = item.select_one(".logomo-event-teaser__title")
        meta = t.clean(item.select_one(".logomo-event-teaser__meta").get_text(" ", strip=True)
                       if item.select_one(".logomo-event-teaser__meta") else "")
        links = [a["href"] for a in item.select("a[href]")]
        if not title or not links or "—" in meta.split("|")[0]:  # multi-day fairs
            continue
        name = t.clean(title.get_text(" ", strip=True))
        day = t.dm(meta)
        if not day or NOT_A_GIG.search(name):
            continue
        room = meta.split("|", 1)[1].strip() if "|" in meta else ""
        ticket = next((u for u in links if "livex" in u or "lippu" in u or "tiketti" in u), None)
        found.append(t.event(name, "Logomo", day, None, links[0], ticket, room=room or None))
    return t.save("Logomo (music)", found)


if __name__ == "__main__":
    t.main_guard(main)
