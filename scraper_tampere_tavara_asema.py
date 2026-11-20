#!/usr/bin/env python3
"""
Scraper for Tavara-asema, Tampere (https://tavara-asema.fi/ohjelma/).

Tavara-asema and Tullikamari (Pakkahuone + Klubi) are run by the same company
and share one WordPress theme, so this module also holds the parser that
scraper_tampere_tullikamari.py reuses.

Two requests per site:
  1. The program page (/ohjelma/) lists every upcoming event as an
     <article class="event-feed-item event_category-..."> card with the date,
     doors ("Ovet 19:00"), age limit and prices ("alk. 28€", "Ovelta 32€").
     Tullikamari's cards also say the room (data-venue="Klubi"/"Pakkahuone").
  2. The WordPress REST API (/wp-json/wp/v2/event) gives each event's title as
     the venue writes it ("Blues Pills (SWE), Graveyard (SWE)"); the card only
     lists the acts one by one. Matched to the cards by event page URL.

Only the "konsertti-keikka" category is kept: DJ club nights ("yokerho") and
other public events ("muu-julkinen-tapahtuma": dance shows, comedy) are
skipped, as are afternoon dances ("Päivähypyt") and DJ-only nights. The
year comes from the event URL slug ("...-04-12-2026/").
Tickets are sold on Tiketti; the link is only on the event page, so the
event page doubles as ticket link.

Usage:
  python scraper_tampere_tavara_asema.py
"""

import html
import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
CITY = "Tampere"
MUSIC_CATEGORY = "event_category-konsertti-keikka"
SLUG_DATE = re.compile(r"-(\d{2})-(\d{2})-(\d{4})(?:-\d+)?/?$")
# Afternoon dances ("Päivähypyt") and some DJ nights are filed as concerts
# but aren't gigs.
NOT_A_GIG = re.compile(r"^(päivähypyt|dj\b|dj[:'’]s\b|dj:t\b)|päivätanss", re.I)


def fetch_titles(site: str) -> dict[str, str]:
    """Event page URL -> title, from the WordPress REST API (Finnish posts)."""
    titles = {}
    for page in range(1, 4):
        resp = requests.get(f"{site}/wp-json/wp/v2/event", headers=HEADERS, timeout=30,
                            params={"per_page": 100, "page": page, "lang": "fi",
                                    "_fields": "link,title"})
        if resp.status_code == 400:  # past the last page
            break
        resp.raise_for_status()
        items = resp.json()
        for item in items:
            title = html.unescape(item["title"]["rendered"])
            titles[item["link"].rstrip("/")] = " ".join(title.split())
        if len(items) < 100:
            break
    return titles


def age_label(text: str) -> str | None:
    t = text.upper().replace(" ", "")
    if t in ("K18", "K-18"):
        return "K-18"
    if t in ("S/K18", "S/K-18"):
        return "S/K-18"
    if t == "S":
        return "S"
    m = re.fullmatch(r"K-?(\d{1,2})", t)
    return f"K-{m.group(1)}" if m else None


def parse_cards(page_html: str, titles: dict[str, str], venue_for) -> list[dict]:
    """Concert cards of the program page; venue_for(room) gives the venue name."""
    soup = BeautifulSoup(page_html, "html.parser")
    events = []
    for card in soup.select("article.event-feed-item"):
        if MUSIC_CATEGORY not in card.get("class", []):
            continue
        link = card.select_one("a.event-link[href]") or card.select_one("a[href]")
        if not link:
            continue
        url = link["href"]
        m = SLUG_DATE.search(url)
        if not m:
            continue
        d, mo, y = map(int, m.groups())

        acts = []
        for h2 in card.select("h2.event-artist"):
            span = h2.find("span")
            if span:
                span.extract()
            acts.append(" ".join(h2.get_text(" ", strip=True).split()))
        title = titles.get(url.rstrip("/")) or ", ".join(a for a in acts if a)
        title = re.sub(r"^\+\s*", "", title).strip()
        if not title or NOT_A_GIG.search(title):
            continue

        info = [" ".join(li.get_text(" ", strip=True).split())
                for li in card.select("ul.event-feed-item__info li")]
        room = card.get("data-venue") or ""
        doors = next((re.search(r"(\d{1,2})[:.](\d{2})", i) for i in info
                      if i.lower().startswith("ovet")), None)
        hh, mm = (int(doors.group(1)), doors.group(2)) if doors else (0, "00")
        event = {
            "artist": title,
            "venue": venue_for(room),
            "city": CITY,
            "date": f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mm}:00",
            "ticketUrl": url,
            "eventUrl": url,
        }
        if doors:
            event["doors"] = f"{hh:02d}:{mm}"
        prices = []
        for i in info:
            pm = re.match(r"(alk\.|ovelta)\s*(.+)", i, re.I)
            if pm:
                prices.append(f"{pm.group(1).lower()} {pm.group(2)}")
            elif i.lower() == "loppuunmyyty":
                prices.append("loppuunmyyty")
        if prices:
            event["price"] = ", ".join(prices)
        age = next((age_label(i) for i in info if age_label(i)), None)
        if age:
            event["age"] = age
        if room:
            event["room"] = room
        events.append(event)
    return events


def scrape(site: str, venue_for, label: str) -> int:
    """Scrape one site of this theme and merge it into Tampere's events.json."""
    try:
        resp = requests.get(f"{site}/ohjelma/", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        titles = fetch_titles(site)
    except requests.RequestException as e:
        print(f"✗ Could not fetch {label}: {e}")
        return 1
    scraped = parse_cards(resp.text, titles, venue_for)
    today = date.today().isoformat()
    seen, unique = set(), []
    for e in scraped:
        if e["date"][:10] >= today and e["eventUrl"] not in seen:
            seen.add(e["eventUrl"])
            unique.append(e)
    print(f"✓ Found {len(unique)} upcoming concerts at {label}")
    if not unique:
        return 1  # the page layout probably changed; fail loudly
    events = load_events(city="tampere")
    added = merge(unique, events)
    save_events(events, city="tampere")
    print(f"✓ Added {added} new {label} events ({len(events)} Tampere events in total)")
    return 0


if __name__ == "__main__":
    sys.exit(scrape("https://tavara-asema.fi", lambda room: "Tavara-asema", "Tavara-asema"))
