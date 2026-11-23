"""
Rokki Raikaa (https://rokkiraikaa.fi/), the rock and metal events of
Rauhala Events, for each Dark Suomi site:

* The summer festivals: two days at one city's ice hall / sports hall area
  (pages /oulu-2027/, /tampere-2027/). The page shows the dates
  ("... rokkifestarit Tampereella 23.-24.7.2027") and a "Line up" section of
  h3 headings, one per act (unannounced slots read "12/16"). The line-up
  isn't split by day, so a festival becomes one gig on its first day,
  titled "Rokki Raikaa Tampere 2027 (23.–24.7.): Act, Act, ..." so
  genres.py can tag each act; the title follows new announcements.

* "Suurimmat rokit": one-night indoor shows touring cities
  (/rokki-raikaa-vantaan-suurimmat-rokit/): "Lauantai 28.11.2026", the
  acts as "Kotiteollisuus klo 20:00" headings and "Osoite Myyrmäkihalli ...".

The front page links every current page. Used by scraper_oulu_rokkiraikaa.py,
scraper_tampere_rokkiraikaa.py and scraper_rokkiraikaa.py (Vantaa, on the
Helsinki site).
"""

import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

HOME = "https://rokkiraikaa.fi/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; event-calendar-bot/1.0)"}
FEST_DATES = re.compile(r"(\d{1,2})\.?\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{4})")
DAY = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
ACT_TIME = re.compile(r"^(.+?)\s+klo\s+(\d{1,2})[:.](\d{2})$", re.I)

# Per site: festival page slug -> (city, venue); show page city word -> city.
SITES = {
    "oulu": {
        "festivals": {"oulu": ("Oulu", "Ouluhallin parkkialue (Rokki Raikaa)")},
        "shows": {"oulun": "Oulu"},
    },
    "tampere": {
        "festivals": {"tampere": ("Tampere", "Hakametsän jäähallin piha-alue (Rokki Raikaa)")},
        "shows": {"tampereen": "Tampere"},
    },
    "helsinki": {
        "festivals": {"helsinki": ("Helsinki", "Rokki Raikaa")},
        "shows": {"helsingin": "Helsinki", "espoon": "Espoo", "vantaan": "Vantaa"},
    },
}


def front_page_links() -> list[str]:
    resp = requests.get(HOME, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return sorted({a["href"].rstrip("/") + "/" for a in soup.select("a[href]")
                   if a["href"].startswith(HOME)})


def ticket_link(soup: BeautifulSoup, url: str) -> str:
    return next((a["href"] for a in soup.select("a[href]")
                 if "lippu.fi" in a["href"] or "osta liput" in a.get_text(" ").lower()), url)


def parse_festival(html: str, url: str, city: str, venue: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    m = FEST_DATES.search(text)
    if not m:
        return None
    d1, d2, mo, y = map(int, m.groups())

    heading = next((h for h in soup.find_all(["h2", "h3"])
                    if h.get_text(strip=True).lower() == "line up"), None)
    if not heading:
        return None
    section = heading.find_parent(class_="e-con-inner") or heading.find_parent(class_="e-con")
    acts = []
    for h in section.select("h3"):
        name = " ".join(h.get_text(" ", strip=True).split())
        if name and not re.fullmatch(r"\d+\s*/\s*\d+", name) and name not in acts:
            acts.append(name)
    if not acts:
        return None
    return {
        "artist": f"Rokki Raikaa {city} {y} ({d1}.–{d2}.{mo}.): {', '.join(acts)}",
        "venue": venue,
        "city": city,
        "date": f"{y:04d}-{mo:02d}-{d1:02d}T00:00:00",
        "ticketUrl": ticket_link(soup, url),
        "eventUrl": url,
        "age": "K-18",
    }


def parse_show(html: str, url: str, city: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    m = DAY.search(text)
    if not m:
        return None
    d, mo, y = map(int, m.groups())
    acts, schedule = [], []
    for h in soup.find_all(["h2", "h3", "h4"]):
        a = ACT_TIME.match(" ".join(h.get_text(" ", strip=True).split()))
        if a and a.group(1) not in acts:
            acts.append(a.group(1))
            schedule.append({"time": f"{int(a.group(2)):02d}:{a.group(3)}", "name": a.group(1)})
    if not acts:
        return None
    doors = re.search(r"sisäänkäynti\s+klo\s+(\d{1,2})[:.](\d{2})", text, re.I)
    start = f"{int(doors.group(1)):02d}:{doors.group(2)}" if doors else schedule[0]["time"]
    place = re.search(r"\bOsoite\s+(.+?)\s+\S+\s+\d", text)
    price = re.search(r"Peruslippu\s+(\d+(?:,\d+)?\s*€)", text)
    event = {
        "artist": f"Rokki Raikaa {city}: {', '.join(acts)}",
        "venue": place.group(1) if place else f"Rokki Raikaa {city}",
        "city": city,
        "date": f"{y:04d}-{mo:02d}-{d:02d}T{start}:00",
        "doors": start,
        "ticketUrl": ticket_link(soup, url),
        "eventUrl": url,
        "age": "K-18",
        "schedule": schedule,
    }
    if price:
        event["price"] = price.group(1)
    return event


def scrape(site: str) -> list[dict]:
    """This site's upcoming Rokki Raikaa events."""
    conf = SITES[site]
    found = []
    for url in front_page_links():
        slug = url[len(HOME):].strip("/")
        fest = re.fullmatch(r"([a-zäö]+)-(\d{4})", slug)
        show = re.fullmatch(r"rokki-raikaa-([a-zäö]+)-suurimmat-rokit", slug)
        if fest and fest.group(1) in conf["festivals"]:
            kind = ("festival", conf["festivals"][fest.group(1)])
        elif show and show.group(1) in conf["shows"]:
            kind = ("show", conf["shows"][show.group(1)])
        else:
            continue
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        if kind[0] == "festival":
            event = parse_festival(resp.text, url, *kind[1])
        else:
            event = parse_show(resp.text, url, kind[1])
        if not event:
            print(f"! No date or line-up found on {url}; the page layout may have changed")
        elif event["date"][:10] >= date.today().isoformat():
            found.append(event)
    return found


def run(site: str) -> int:
    try:
        scraped = scrape(site)
    except requests.RequestException as exc:
        print(f"✗ Could not fetch Rokki Raikaa: {exc}")
        return 1
    for e in scraped:
        print(f"✓ Rokki Raikaa {e['date'][:10]} {e['venue']}: {e['artist']}")
    store = None if site == "helsinki" else site
    events = load_events(store)
    added = merge(scraped, events)
    save_events(events, store)
    print(f"✓ Added {added} new Rokki Raikaa events ({len(events)} {site} events in total)")
    return 0
