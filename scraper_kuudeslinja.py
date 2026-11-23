#!/usr/bin/env python3
"""
Scraper for Kuudes Linja, Helsinki (https://www.kuudeslinja.com/), the
club in Hakaniemi. The front page lists every upcoming event:

  <article class="event">
    <div class="pvm">Perjantai 4.12.</div>      (a year only after New Year)
    <div class="title">ALKUILLAN KONSERTTI: VACUOUS (UK) + DOME RUNNER</div>
    <div class="info"><p>LIVE: Vacuous<br>LIVE: Dome Runner</p>
                      <p>Ennakot Tiketistä 20 €, liput ovelta 25 € ... Ovet klo 18</p></div>
    <a class="event-button" href="…tiketti…">Liput</a> <a … facebook …>FB</a>

The "LIVE:" lines name the bands; events without any (DJ club nights) are
skipped. Kuudes Linja books punk and metal but also indie, rap and pop, so,
as for G Livelab, only gigs that fit Dark Suomi are kept
(genres.keep_fitting).

Usage:
  python scraper_kuudeslinja.py
  python scraper_kuudeslinja.py --all   # print every gig with its genres, save nothing
"""

import argparse
import re
import string
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

import genres as g
from eventstore import load_events, merge, save_events

LIST_URL = "https://www.kuudeslinja.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
VENUE = "Kuudes Linja"
CITY = "Helsinki"

DAY = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})?")
CONCERT_PREFIX = re.compile(r"^\s*alku\s*i?llan\s+konsertti\s*:\s*", re.I)
NOTES = re.compile(r"\s*\((?:[^)]*julkkarit[^)]*|[A-Z]{2,3})\)", re.I)
DOORS = re.compile(r"ovet\s+klo\s+(\d{1,2})(?:[:.](\d{2}))?", re.I)
EUROS = re.compile(r"(\d+(?:,\d+)?)\s*€")


def event_date(text: str, today: date) -> date | None:
    m = DAY.search(text)
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
    year = int(y) if y else today.year + (1 if mo < today.month - 1 else 0)
    try:
        return date(year, mo, d)
    except ValueError:
        return None


def gig_title(title: str, acts: list[str]) -> str:
    """The bands as "A + B"; a named event as "Name: A, B"."""
    name = NOTES.sub("", CONCERT_PREFIX.sub("", title)).strip()
    if not acts:
        return string.capwords(name)
    first = acts[0].casefold()
    if name.casefold().startswith(first[:12]):
        return " + ".join(acts)
    return f"{string.capwords(name)}: {', '.join(acts)}"


def price_text(info: str) -> str | None:
    # Leave out the security fee line: it's on top of every ticket.
    text = re.split(r"\+\s*security fee", info, flags=re.I)[0]
    amounts = sorted({float(a.replace(",", ".")) for a in EUROS.findall(text)})
    if not amounts:
        return "Vapaa pääsy" if re.search(r"vapaa pääsy", text, re.I) else None
    fmt = lambda a: f"{a:g}".replace(".", ",")
    low, high = amounts[0], amounts[-1]
    return f"{fmt(low)} €" if low == high else f"{fmt(low)}–{fmt(high)} €"


def parse(page_html: str, today: date) -> list[dict]:
    gigs = []
    for art in BeautifulSoup(page_html, "html.parser").select("article.event"):
        pvm = art.select_one(".pvm")
        title_el = art.select_one(".title")
        info_el = art.select_one(".info")
        if not (pvm and title_el and info_el):
            continue
        day = event_date(pvm.get_text(), today)
        if not day or day < today:
            continue
        lines = [" ".join(t.split()) for t in info_el.get_text("\n").split("\n") if t.strip()]
        acts = [re.sub(r"^live\s*:\s*", "", l, flags=re.I).strip()
                for l in lines if re.match(r"live\s*:", l, re.I)]
        if not acts:
            continue  # a DJ club night
        info = "\n".join(lines)
        doors = DOORS.search(info)
        hour, minute = (int(doors.group(1)), int(doors.group(2) or 0)) if doors else (0, 0)
        title = " ".join(title_el.get_text().split())
        links = {a.get_text(strip=True).lower(): a.get("href") for a in art.select("a.event-button")}
        ticket = links.get("liput") or ""
        page = links.get("fb") or ticket or f"{LIST_URL}#{day.isoformat()}-{acts[0]}"
        event = {
            "artist": gig_title(title, acts),
            "venue": VENUE,
            "city": CITY,
            "date": f"{day.isoformat()}T{hour:02d}:{minute:02d}:00",
            "ticketUrl": ticket or LIST_URL,
            "eventUrl": page,
        }
        if doors:
            event["doors"] = f"{hour:02d}:{minute:02d}"
        price = price_text(info)
        if price:
            event["price"] = price
        if re.search(r"loppuunmyyty|sold out", title, re.I):
            event["status"] = "sold out"
        if re.search(r"\bperuttu\b|cancell?ed", title, re.I):
            event["status"] = "cancelled"
        gigs.append(event)
    return gigs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true",
                        help="print every gig and whether it's kept; save nothing")
    args = parser.parse_args()

    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Could not fetch {VENUE}: {e}")
        return 1
    gigs = parse(resp.text, date.today())
    print(f"✓ Found {len(gigs)} upcoming gigs at {VENUE}")
    if not gigs:
        return 1  # the page layout probably changed; fail loudly

    kept = g.keep_fitting(gigs, args.all)
    if args.all:
        return 0
    events = load_events()
    added = merge(kept, events)
    save_events(events)
    print(f"✓ Kept {len(kept)} gigs that fit Dark Suomi; added {added} new "
          f"({len(events)} events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
