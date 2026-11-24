#!/usr/bin/env python3
"""
Scraper for Gatorade Center, Turku (https://gatoradecenter.fi/tapahtumat/),
the arena (TPS ice hockey), concerts only.

The events page loads its lists from the site's own JSON endpoint
(/?controller=ajax&events=1&categoryId=8...): [{"name", "activityStartTime":
"2026-12-05 18:30:00", "link" (tickets), "invitationLink" (event page)}].
Category 8 is "Tapahtumat" (concerts and shows); hockey games are in other
categories, and championship tournaments in this one are skipped by name.

Usage:
  python scraper_turku_gatorade.py
"""

import re

import turku as t

API = "https://gatoradecenter.fi/"
VENUE = "Gatorade Center"
NOT_A_GIG = re.compile(r"mm-kisat|\bkisat\b|ottelu|salibandy|jääkiekko|\bvs\.?\b|"
                       r"messut|gaala|disney on ice|\bshow\b.*\bice\b", re.I)


def main() -> int:
    data = t.get(API, params={
        "controller": "ajax", "events": 1, "limit": 0, "eventStarts": 0, "categoryId": 8,
        "categoryValues[0][name]": "eventCategory", "categoryValues[0][value]": 8}).json()
    found = []
    for e in data if isinstance(data, list) else []:
        when = e.get("activityStartTime") or ""
        name = e.get("name") or ""
        if len(when) < 16 or not name or NOT_A_GIG.search(name):
            continue
        day = t.dm(".".join(reversed(when[:10].split("-"))))
        page = e.get("invitationLink") or "https://gatoradecenter.fi/tapahtumat/"
        found.append(t.event(name, VENUE, day, when[11:16] if when[11:16] != "00:00" else None,
                             page, e.get("link") or None))
    return t.save(VENUE, found, empty_ok=True)


if __name__ == "__main__":
    t.main_guard(main)
