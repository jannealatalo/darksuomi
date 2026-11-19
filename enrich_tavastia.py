#!/usr/bin/env python3
"""
Adds doors time, band stage times, age limit and room to Tavastia gigs.

The Tavastia listing only gives dates, but each gig's own page has a
timetable ("Ovet 20.00 · Us 20.30 · The Flaming Sideburns 21.45"). This
visits the page of every upcoming Tavastia gig that hasn't been checked in
the last 7 days and stores, in frontend/data/events.json:

  date       -> gets the doors time, e.g. 2026-11-20T20:00:00
  doors      -> "20:00"
  schedule   -> [{"time": "20:30", "name": "Us"}, ...]
  age        -> "K-18" / "S" / ...
  room       -> "Tavastia-klubi" / "Semifinal" / ...
  detailsFetched -> date of the check

Usage:
  python enrich_tavastia.py
"""

import json
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
EVENTS_FILE = ROOT / "frontend" / "data" / "events.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
RECHECK_DAYS = 7
DELAY = 1.0  # seconds between page loads
TIME = re.compile(r"^(\d{1,2})[.:](\d{2})$")


def hhmm(text: str) -> str | None:
    m = TIME.match(text.strip())
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def parse_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    details: dict = {}

    timetable = soup.select_one(".timetable")
    if timetable:
        schedule = []
        for row in timetable.find_all("div", recursive=False):
            cells = [c.get_text(" ", strip=True) for c in row.find_all("div", recursive=False)]
            if len(cells) < 2:
                continue
            t = hhmm(cells[0])
            if not t:
                continue
            if "doors" in (row.find("div").get("class") or []) or cells[1].lower() == "ovet":
                details["doors"] = t
            elif cells[1].lower().startswith(("ovet", "doors")):
                continue  # e.g. "Ovet kiinni" (doors close), not a band
            else:
                schedule.append({"time": t, "name": cells[1]})
        if schedule:
            details["schedule"] = schedule

    for field, selector in (("age", ".age"), ("room", ".location")):
        el = soup.select_one(selector)
        if el and el.get_text(strip=True):
            details[field] = el.get_text(" ", strip=True)
    return details


def main() -> int:
    with open(EVENTS_FILE, encoding="utf-8") as f:
        events = json.load(f)

    today = date.today().isoformat()
    stale = (date.today() - timedelta(days=RECHECK_DAYS)).isoformat()
    todo = [e for e in events
            if e.get("venue") == "Tavastia Klubi"
            and e["date"][:10] >= today
            and "tavastiaklubi.fi/events/" in e.get("ticketUrl", "")
            and e.get("detailsFetched", "") < stale]
    print(f"  {len(todo)} Tavastia gigs to check")

    updated = 0
    for i, event in enumerate(todo):
        if i:
            time.sleep(DELAY)
        try:
            resp = requests.get(event["ticketUrl"], headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ! {event['artist'][:50]}: {e}", file=sys.stderr)
            continue
        details = parse_page(resp.text)
        for key in ("schedule", "age", "room", "doors"):
            if key in details:
                event[key] = details[key]
        if "doors" in details:
            event["date"] = f"{event['date'][:10]}T{details['doors']}:00"
        event["detailsFetched"] = today
        updated += 1

    events.sort(key=lambda e: e["date"])
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"✓ Checked {updated} Tavastia gig pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
