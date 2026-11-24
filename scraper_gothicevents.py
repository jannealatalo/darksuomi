#!/usr/bin/env python3
"""
Gigs from Gothic Events Finland (https://gothiceventsfinland.blogspot.com/),
a hand-kept calendar of goth, industrial, EBM and dark electro events in
Finland. It catches gigs at small places that have no gig list of their
own, like Varjobaari in Tampere (Miseria Ultima, Sortaja…).

The events page (/p/events.html) has one line per event:
  "08.01.2027 <a href=post>Miseria Ultima, Sortaja, Stuka, DJ Albiino</a>,
   Varjobaari, Tampere"
and each post has the time ("20:00-", "Doors: 20:00", "Ovet: 19:00"), the
price ("Liput: 10€") and sometimes a ticket link. The post also says
"Tapahtuma on peruttu!" when an event is cancelled. These are read from
the blog's JSON feed (the start of each post as plain text, 150 posts per
request): loading each post page from GitHub's runners gets HTTP 429.

Only events in Dark Suomi's cities are used (Helsinki, Espoo, Vantaa ->
the main site; Tampere; Oulu). An event is left out when a venue scraper
already has a gig in that city on that day at the same venue (the venue's
own data is better), except that the blog's cancellation is passed on to
it. DJ-only club nights (no "Live:" line-up, and a "Club …" title or DJs
in the text) are skipped. Gigs get venueDefault "goth" for genre tagging
when the bands are unknown.

Usage:
  python scraper_gothicevents.py            # updates the event files
  python scraper_gothicevents.py --dry-run  # only prints
"""

import argparse
import html
import re
import sys
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from eventstore import load_events, merge, save_events

LIST_URL = "https://gothiceventsfinland.blogspot.com/p/events.html"
FEED_URL = "https://gothiceventsfinland.blogspot.com/feeds/posts/default?alt=json&max-results=150"
FEED_PAGES = 3
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
SITE_OF_CITY = {"helsinki": "helsinki", "espoo": "helsinki", "vantaa": "helsinki",
                "tampere": "tampere", "oulu": "oulu"}
# The blog's venue names -> the names the venue scrapers use, where they differ.
VENUE_NAMES = {"varjobaari": "Varjobaari"}
# Closed venues whose old gigs may linger in the blog: (city, venue word).
# Olympia-kortteli, Tampere, closed on 30.9.2026; its gigs were cancelled
# or moved to other venues (which the venue scrapers find).
CLOSED_VENUES = {("tampere", "olymp")}

LINE_DATE = re.compile(r"^(\d{1,2})\.(?:-\d{1,2}\.)?(\d{1,2})\.(\d{4})(?!\d)")
TIME = re.compile(r"(?:ovet|doors|showtime|klo)?[:\s]*\b(\d{1,2})[:.](\d{2})\s*(?:-|–|$)", re.I)
PRICE = re.compile(r"(?:liput|tickets|pääsymaksu|hinta)(?:\s+alkaen)?\s*:\s*([^|]+)", re.I)
CANCELLED = re.compile(r"\b(?:peruttu|perutaan|cancell?ed)\b", re.I)
DJ_ONLY_TITLE = re.compile(r"^club\b|pre-club|\bclub night\b|\bdj\b", re.I)
DJ_PART = re.compile(r"^\s*dj\b", re.I)
STOP_WORDS = {"ravintola", "klubi", "club", "bar", "baari", "the", "live", "helsinki",
              "tampere", "oulu", "espoo", "kortteli", "konepaja", "level"}


def words(text: str) -> set[str]:
    """Distinctive words of a venue name, cut to 5 letters ("Tullikamarin" ~ "Tullikamari")."""
    return {w[:5] for w in re.findall(r"\w+", text.casefold()) if len(w) >= 4 and w not in STOP_WORDS}


def parse_list(page_html: str) -> list[dict]:
    """The events page -> [{date, title, url, venue, city}], one per line.

    A line is "DATE <a>TITLE</a>, VENUE, CITY"; a few have no link and
    are plain "DATE TITLE, VENUE, CITY" (the title then can't be told from
    the venue if it has commas, so the last two parts are venue and city).
    """
    soup = BeautifulSoup(page_html, "html.parser")
    body = soup.select_one(".post-body") or soup
    for br in body.find_all("br"):
        br.replace_with("\n")
    for a in body.find_all("a"):
        if "gothiceventsfinland.blogspot.com/20" in a.get("href", ""):
            a.replace_with(f"[[{a['href']}|{a.get_text(' ', strip=True)}]]")
    items = []
    # Split at line breaks and also before each date: the last line is
    # sometimes glued to the previous one ("…, Turku02.04.2027 …").
    for line in re.split(r"\n|(?<![\d.\-])(?=\d{1,2}\.(?:-\d{1,2}\.)?\d{1,2}\.\d{4}(?!\d))",
                         body.get_text()):
        line = " ".join(line.split())
        m = LINE_DATE.match(line)
        if not m:
            continue
        d, mo, y = map(int, m.groups())
        rest = line[m.end():].strip()
        link = re.match(r"\[\[(\S+)\|(.*?)\]\]\s*,?\s*(.*)", rest)
        if link:
            url, title, place = link.group(1), link.group(2), link.group(3)
            parts = [p.strip() for p in place.split(",") if p.strip()]
            if len(parts) < 2:  # "<a>Combichrist (US), Olympia-kortteli</a>, Tampere"
                t = [p.strip() for p in title.split(",")]
                if len(t) < 2 or not parts:
                    continue
                title, parts = ", ".join(t[:-1]), [t[-1], *parts]
        else:
            url = ""
            parts = [p.strip() for p in rest.split(",") if p.strip()]
            if len(parts) < 3:
                continue
            title, parts = ", ".join(parts[:-2]), parts[-2:]
        items.append({"date": date(y, mo, d), "title": " ".join(title.split()), "url": url,
                      "venue": ", ".join(parts[:-1]), "city": parts[-1]})
    return items


def post_details(url: str) -> dict:
    """Time, price, ticket link, line-up flags and cancellation from a post."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    body = BeautifulSoup(resp.text, "html.parser").select_one(".post-body")
    lines = [" ".join(t.split()) for t in body.get_text("\n", strip=True).split("\n")] if body else []
    text = " | ".join(lines)
    out = {"live": any(re.match(r"^live\s*:?$", ln, re.I) for ln in lines),
           "dj": bool(re.search(r"\bdj\b", text, re.I)),
           "cancelled": any(CANCELLED.search(ln) for ln in lines[:3])}
    for ln in lines[:12]:
        m = TIME.match(ln)
        if m and int(m.group(1)) < 24:
            out["time"] = f"{int(m.group(1)):02d}:{m.group(2)}"
            if re.match(r"(ovet|doors)", ln, re.I):
                out["doors"] = out["time"]
            break
    m = PRICE.search(text)
    if m:
        out["price"] = m.group(1).strip()[:60]
    elif re.search(r"ei pääsymaksua|vapaa pääsy|free entry", text, re.I):
        out["price"] = "free"
    links = [a.get("href", "") for a in body.find_all("a")] if body else []
    tickets = [h for h in links if h.startswith("http") and "blogger" not in h and "blogspot" not in h]
    if tickets:
        out["ticketUrl"] = tickets[0]
    return out


def feed_summaries() -> dict[str, str]:
    """
    Post URL -> the start of the post as plain text, for the newest
    FEED_PAGES * 150 posts (Blogger's JSON feed gives 150 per request; about
    a year of posts). Loading each post page from GitHub's runners gets
    HTTP 429 from Google.
    """
    entries = []
    for page in range(FEED_PAGES):
        try:
            resp = requests.get(FEED_URL, params={"start-index": 1 + 150 * page},
                                headers=HEADERS, timeout=60)
            resp.raise_for_status()
            got = resp.json()["feed"].get("entry", [])
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"  ! feed: {e}", file=sys.stderr)
            break
        entries += got
        if len(got) < 150:
            break
    out = {}
    for e in entries:
        url = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), None)
        text = html.unescape((e.get("summary") or e.get("content") or {}).get("$t", ""))
        if url and text:
            out[url.replace("http://", "https://")] = " ".join(text.split())
    return out


def summary_details(text: str) -> dict:
    """post_details() from a feed summary, whose lines are glued together:
    "08.01.2027Live:Miseria UltimaSortajaDJ:AlbiinoVarjobaari, Tampere 20:00-Liput: 10€…"."""
    out = {"live": bool(re.search(r"live\s*:", text, re.I)),
           "dj": bool(re.search(r"\bdj\b|dj\s*:", text, re.I)),  # "StukaDJ:Albiino"
           "cancelled": bool(CANCELLED.search(text[:80]))}
    # "Doors: 20.00", "Ovet klo 20:00", else the first "20:00" (the date is "08.01.2027").
    m = (re.search(r"(ovet|doors)(?:\s*klo)?\s*:?\s*(\d{1,2})[:.](\d{2})", text, re.I)
         or re.search(r"()\b(\d{1,2}):(\d{2})", text))
    if m and int(m.group(2)) < 24:
        out["time"] = f"{int(m.group(2)):02d}:{m.group(3)}"
        if m.group(1):
            out["doors"] = out["time"]
    m = re.search(r"(?:liput|tickets|pääsymaksu|hinta)(?:\s+alkaen)?\s*:\s*"
                  r"(\d[\d,.]*\s*€(?:\s*/\s*[^€:]{0,25}?\d[\d,.]*\s*€)*)", text, re.I)
    if m:
        out["price"] = m.group(1).strip()
    elif re.search(r"ei pääsymaksua|vapaa pääsy|free entry", text, re.I):
        out["price"] = "free"
    tickets = [u.rstrip(".,)") for u in re.findall(r"https?://[^\s*]+", text)
               if "blogger" not in u and "blogspot" not in u]
    if tickets:
        out["ticketUrl"] = tickets[0]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="only print, don't save")
    args = parser.parse_args()

    resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    today = date.today()
    items = [i for i in parse_list(resp.text)
             if i["date"] >= today and i["city"].casefold() in SITE_OF_CITY
             and not any(city == i["city"].casefold() and w in words(i["venue"])
                         for city, w in CLOSED_VENUES)]
    print(f"Gothic Events Finland: {len(items)} upcoming events in Dark Suomi's cities")
    summaries = feed_summaries() if items else {}

    stores = {}
    scraped = {}
    for item in items:
        site = SITE_OF_CITY[item["city"].casefold()]
        if site not in stores:
            stores[site] = load_events(site)
        same_day = [e for e in stores[site] if e["date"][:10] == item["date"].isoformat()
                    and words(e["venue"]) & words(item["venue"])]
        if not item["url"]:  # a line without its own post
            item["url"] = f"{LIST_URL}#{item['date'].isoformat()}-{re.sub(r'\W+', '-', item['title'].casefold())[:40]}"
            details = {"live": True, "dj": False, "cancelled": False}
        elif item["url"].replace("http://", "https://") in summaries:
            details = summary_details(summaries[item["url"].replace("http://", "https://")])
        else:
            # Not in the feed (an old post): load the post itself. Google
            # sometimes rate-limits Blogger for GitHub's runners (HTTP 429):
            # skip that event tonight instead of failing the whole run.
            time.sleep(1)
            try:
                details = post_details(item["url"])
            except requests.RequestException as e:
                print(f"  ! skipped {item['date']} {item['title']}: {e}", file=sys.stderr)
                continue
        if same_day:
            if details["cancelled"]:
                for e in same_day:
                    if e.get("status") != "cancelled":
                        e["status"] = "cancelled"
                        scraped.setdefault(site, [])  # mark the file for saving
                        print(f"  ✓ cancelled: {e['date'][:10]} {e['artist']} ({e['venue']})")
            continue
        if not details["live"] and (DJ_ONLY_TITLE.search(item["title"]) or details["dj"]):
            print(f"  - skip club night: {item['date']} {item['title']}")
            continue
        acts = [a.strip() for a in item["title"].split(",") if a.strip() and not DJ_PART.match(a)]
        title = ", ".join(acts) or item["title"]
        hhmm = details.get("time", "00:00")
        event = {
            "artist": title,
            "venue": VENUE_NAMES.get(item["venue"].casefold(), item["venue"]),
            "city": item["city"],
            "date": f"{item['date'].isoformat()}T{hhmm}:00",
            "eventUrl": item["url"],
            "ticketUrl": details.get("ticketUrl", item["url"]),
            "venueDefault": "goth",
        }
        for k in ("doors", "price"):
            if details.get(k):
                event[k] = details[k]
        if details["cancelled"]:
            event["status"] = "cancelled"
        scraped.setdefault(site, []).append(event)
        print(f"  + {site}: {event['date'][:16]} {title} @ {event['venue']}")

    for site, events in scraped.items():
        added = merge(events, stores[site])
        if not args.dry_run:
            save_events(stores[site], site)
        print(f"✓ {site}: {added} new gigs from Gothic Events Finland")
    if args.dry_run:
        print("Dry run: nothing saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
