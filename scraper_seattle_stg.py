#!/usr/bin/env python3
"""
Seattle: Seattle Theatre Group (https://www.stgpresents.org/), which runs
the Paramount, the Moore and the Neptune.

The events page loads its list with WordPress "Modern Events Calendar":
POST /wp-admin/admin-ajax.php action=mec_list_load_more returns up to 100
events as HTML with a schema.org Event (JSON-LD) each: name, startDate
("2026-11-25T19:00:00-08:00"), location and url; the answer's end_date and
offset continue the list. STG also runs classes, Broadway tours and
other halls, so only the three venues are kept and the events in the
"Broadway" and "Performing Arts Series" categories (from the WordPress
REST API) are dropped.

Usage:
  python scraper_seattle_stg.py
"""

import html
import json
import re
import time

import seattle as s

BASE = "https://www.stgpresents.org"
VENUES = {"Paramount Theatre", "Moore Theatre", "Neptune Theatre"}
NOT_GIGS = {"Broadway", "Performing Arts Series"}
MAX_CALLS = 8
# Broadway shows' extra performances aren't always in the Broadway category.
NOT_A_GIG = re.compile(r"\bmatinee\b|\bbroadway\b|\bthe musical\b", re.I)


def not_gig_pages() -> set[str]:
    """Event page URLs in the Broadway / Performing Arts Series categories."""
    cats = s.get(f"{BASE}/wp-json/wp/v2/mec_category",
                 params={"per_page": 100, "_fields": "id,name"}).json()
    ids = [str(c["id"]) for c in cats if c["name"] in NOT_GIGS]
    if not ids:
        return set()
    out, page = set(), 1
    while page <= 10:
        r = s.get(f"{BASE}/wp-json/wp/v2/mec-events",
                  params={"mec_category": ",".join(ids), "per_page": 100, "page": page,
                          "_fields": "link"})
        out |= {e["link"].rstrip("/") for e in r.json()}
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return out


def main() -> int:
    skip = not_gig_pages()
    start, offset, found = s.today().isoformat(), 0, []
    for _ in range(MAX_CALLS):
        r = s.requests.post(f"{BASE}/wp-admin/admin-ajax.php", headers=s.HEADERS, timeout=60, data={
            "action": "mec_list_load_more", "mec_start_date": start, "mec_offset": offset,
            "atts[sk-options][list][style]": "standard",
            "atts[sk-options][list][limit]": 100,
        })
        r.raise_for_status()
        data = r.json()
        for block in re.findall(r'application/ld\+json">(.*?)</script>', data.get("html", ""), re.S):
            try:
                ev = json.loads(block)
            except ValueError:
                continue
            venue = s.venue_name((ev.get("location") or {}).get("name", ""))
            url = (ev.get("url") or "").rstrip("/")
            when = ev.get("startDate") or ""
            title = html.unescape(ev.get("name", ""))
            if (venue not in VENUES or url in skip or len(when) < 10
                    or NOT_A_GIG.search(title)):
                continue
            status = None
            if re.search(r"\s*[–-]\s*(?:CANCEL+ED|POSTPONED)\s*$", title, re.I):
                status = "cancelled" if "CANCEL" in title.upper() else "postponed"
                title = re.sub(r"\s*[–-]\s*(?:CANCEL+ED|POSTPONED)\s*$", "", title, flags=re.I)
            found.append(s.event(title, venue, s.day_of(when[:10]), s.clock(when[11:16]),
                                 url + "/", status=status))
        if not data.get("has_more_event"):
            break
        start, offset = data.get("end_date") or start, data.get("offset") or offset + 100
        time.sleep(2)
    return s.save("STG (Paramount, Moore, Neptune)", found)


if __name__ == "__main__":
    s.main_guard(main)
