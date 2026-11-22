#!/usr/bin/env python3
"""
Genre tagger for Dark Suomi events.

Reads frontend/data/events.json, works out the artists in each event title,
looks up genre tags for each artist and writes them back into events.json as
`artists` and `genres` fields.

Tag sources, in order:
  1. frontend/data/genre-config.json -> "artistOverrides" (manual, always wins)
  2. Last.fm artist.getTopTags        (only if LASTFM_API_KEY is set)
  3. MusicBrainz artist search tags   (no key needed, max 1 request/second)

Lookups are cached in frontend/data/artists.json so each artist is only
fetched once. Delete an entry there (or run with --refresh) to re-fetch it.

Usage:
  python genres.py            # tag events, fetch only uncached artists
  python genres.py --refresh  # re-fetch every artist
  python genres.py --report   # print every genre seen, with event counts
  python genres.py --city tampere  # the Tampere site's events (shared artist cache)
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "frontend" / "data"
EVENTS_FILE = DATA_DIR / "events.json"
CACHE_FILE = DATA_DIR / "artists.json"
CONFIG_FILE = DATA_DIR / "genre-config.json"

USER_AGENT = os.environ.get(
    "MUSICBRAINZ_USER_AGENT", "event-genre-tagger/0.1 ( https://github.com/ )"
)
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY")

# Tags that describe something other than the music itself.
JUNK_TAGS = {
    "seen live", "finnish", "finland", "suomi", "swedish", "sweden", "uk",
    "british", "american", "usa", "german", "danish", "norwegian", "estonian",
    "australian", "canadian", "japanese", "italian", "french", "ukrainian",
    "spanish", "female vocalists", "male vocalists", "female vocalist",
    "male vocalist", "favorites", "favourite", "love", "awesome", "beautiful",
    "under 2000 listeners", "albums i own", "my music", "check out",
    "ukraine", "australia", "england", "english", "singer", "finnish singer",
    "eurovision", "all", "norway", "norwegian", "belgian", "belgium", "greek",
    "dutch", "polish", "czech", "swiss", "austrian", "icelandic",
    "croatian", "faroese", "need to rate", "check", "brazil", "brazilian",
    "serbian", "christmas", "oon kayny kattomassa", "netherlands", "slovak",
    "dr congo", "albania", "albanian", "latvian", "latvia", "lithuanian",
    "russian", "polish", "hungarian", "italian", "spain",
    "my top songs", "somalia", "somali",
    "korean", "japanese", "south korea", "태민",
    "karelian", "nordic", "runous", "cmx", "violin", "trumpet",
}
# Event / contest tags such as "eurovision 2023 artists" or "umk 2025".
JUNK_TAG_PATTERN = re.compile(r"eurovision|^umk\b|^\d{4}$|^seen live")

# Map spelling variants onto one name so the genre list stays readable.
TAG_ALIASES = {
    "hip-hop": "hip hop",
    "hiphop": "hip hop",
    "suomirap": "rap",
    "finnish rap": "rap",
    "finnish hip hop": "hip hop",
    "suomi-rap": "rap",
    "schlager": "iskelmä",
    "iskelma": "iskelmä",
    "finnish schlager": "iskelmä",
    "suomi-iskelmä": "iskelmä",
    "suomi iskelmä": "iskelmä",
    "post punk": "post-punk",
    "post metal": "post-metal",
    "doom": "doom metal",
    "black": "black metal",
    "synth-pop": "synthpop",
    "synth pop": "synthpop",
    "rock and roll": "rock & roll",
    "suomipop": "finnish pop",
    "suomi pop": "finnish pop",
    "goth": "gothic rock",
    "gothic": "gothic rock",
    "goth rock": "gothic rock",
    "melodic/death-metal": "melodic death metal",
    "hip hop rnb and dance hall": "hip hop",
    "alternative/indie rock": "indie rock",
    "humor": "stand-up",
    "rnb": "r&b",
    "rhythm and blues": "r&b",
    "humour": "stand-up",
    "comedy": "stand-up",
    "stand-up comedy": "stand-up",
    "drag queen": "stand-up",
    "drag": "stand-up",
    "rock 'n' roll": "rock & roll",
}

# Country codes used in Tavastia titles, e.g. "Crashdiet (SWE)".
COUNTRY_CODES = {
    "SWE": "SE", "UK": "GB", "USA": "US", "US": "US", "ITA": "IT",
    "DK": "DK", "UA": "UA", "EST": "EE", "JPN": "JP", "CAN": "CA", "AU": "AU",
    "AUS": "AU", "ES": "ES", "FRA": "FR", "FR": "FR", "NOR": "NO", "GER": "DE",
    "BE": "BE", "NZ": "NZ", "MX": "MX", "CL": "CL", "NL": "NL", "PL": "PL",
}

# Venue event categories -> our genre names, used only when no artist on the
# bill has tags. "dj" and "stand-up" are excluded by default in the site config.
VENUE_GENRES = {
    "industrial": "industrial", "metal": "metal", "punk": "punk",
    "rock": "rock", "pop": "pop", "rap": "rap", "soul-rnb": "r&b",
    "iskelma": "iskelmä", "folk": "folk", "dj": "dj night",
    "stand-up": "stand-up", "other": None,
    # Lepakkomies categories (same site builder as On the Rocks)
    "gothic": "gothic rock", "hc": "hardcore", "stoner": "stoner rock",
    # Ääniwalli: genre words found in a gig's description
    "doom": "doom metal",
    # MunOulu (Oulu): genre words found in a gig's description
    "melodic death metal": "melodic death metal", "death metal": "death metal",
    "black metal": "black metal", "thrash metal": "thrash metal",
    "heavy metal": "heavy metal", "progressive metal": "progressive metal",
    "hard rock": "hard rock",
    # Kulttuuritalo / KULT categories
    "rock-ja-metalli": "rock", "punk-ja-indie": "indie", "pop-ja-rap": "pop",
    "stand-up-ja-viihde": "stand-up", "jazz-ja-viihdemusiikki": "viihde",
    "blues-ja-country": "blues", "dj-ja-klubit": "dj night",
    # Korjaamo genre classes
    "metalli": "metal", "rap-ja-hiphop": "rap", "rap-hiphop": "rap",
    "indie-ja-alternative": "indie", "punk-ja-hardcore": "punk", "punk-hardcore": "punk",
    "elektroninen-musiikki-edm": "electronic", "swing-ja-big-band": "jazz",
    "swing-big-band": "jazz", "soul-funk-ja-rb": "r&b", "soul-funk-rb": "r&b",
    "gospel-ja-kuoromusiikki": "gospel music", "kantri-ja-folk": "folk",
    "jazz": "jazz", "blues": "blues",
    # Veikkaus Arena (already mapped by its scraper)
    "metal": "metal", "indie": "indie", "r&b": "r&b",
}

MAX_TAGS = 6          # keep this many top tags per artist
LASTFM_MIN_WEIGHT = 15  # Last.fm tag weights are 0-100
MB_MIN_SCORE = 90     # MusicBrainz search score (0-100)


# ---------------------------------------------------------------------------
# Title -> artists
# ---------------------------------------------------------------------------

def _norm(name: str) -> str:
    """Casefold and strip accents/punctuation, for comparing names."""
    name = unicodedata.normalize("NFKD", name.casefold())
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


def parse_title(title: str) -> list[dict]:
    """
    Split an event title into a list of {"name", "country"} candidates.

    "Hola Ghost (DK), Black Magic Six, Hauntees" -> three artists
    "Michael Monroe plays Hanoi Rocks (K-18)"  -> Michael Monroe
    "STAM1NA – DIRTY YEARS 2026"                -> STAM1NA
    "Hellsinki Industrial Festival 2026 Pre-Club: Scheitan (SWE), Stuka"
                                                -> Scheitan, Stuka
    """
    acts = []
    # "Artist presents: Show name" -> the artist.
    m = re.match(r"^(.+?)\s+presents\s*:", title, flags=re.I)
    if m:
        title = m.group(1)
    # "<Festival / club night / show name>: band, band" -> just the bands.
    m = re.match(r"^([^:]*\b(?:festival|fest|club|klubi|presents|night|christmas|xmas|"
                 r"joulu\w*|tour|showcase|party|lisäkeikka|lisänäytös|extra show)\b[^:]*):\s*(.+)$",
                 title, flags=re.I)
    if m:
        title = m.group(2)
    else:
        # "<Show name>: band, band, band" -> the list after the colon.
        m = re.match(r"^[^:,]+:\s*(.+(?:,|\s\+\s|\sw/\s|\s/\s).+)$", title, flags=re.I)
        if m:
            title = m.group(1)
    # Split on commas, " + ", " w/ " and "&" right after a country code
    # ("Wyatt E (BE) & Five the Hierophant (UK)"); other " & " inside a band
    # name ("Kauko Röyhkä & Voimaeläin") is handled by trying the full name first.
    # " / " too ("AARO630 / JAAKKO KULTA / PIHALLA"); " // " is a different thing.
    for part in re.split(r",\s*|\s+\+\s+|\s+w/\s+|\s+/\s+|(?<=\))\s*&\s+", title, flags=re.I):
        part = part.strip()
        # DJs are rarely tagged usefully (and "DJ Anaheim" isn't a band);
        # "support (TBA)", "guests" and the like aren't bands either.
        if not part or re.match(r"^(djs?|support|tba|guests?|special guests?)\b",
                                part, flags=re.I):
            continue

        country = None
        m = re.search(r"\(([A-Za-z]{1,3})(?:-[A-Za-z]{1,3})?\)", part)
        if m and m.group(1).upper() in COUNTRY_CODES:
            country = COUNTRY_CODES[m.group(1).upper()]
            # "Ministry (US) Hate To Go – …": the name ends at the country code.
            part = part[:m.start()]

        # Drop quoted show names: Suzi Quatro “ROCKIN’ ON!”, X ”Ride The Lightning”.
        part = re.sub(r"\s*[“”\"«][^“”\"»]*[“”\"»]", "", part)
        # Drop all parentheses: country codes, age limits, release-party notes.
        part = re.sub(r"\s*\([^)]*\)", "", part)
        # "Maustetytöt lisäkeikka" (extra show) -> Maustetytöt.
        part = re.sub(r"\s+(?:lisäkeikka|lisänäytös|extra show)$", "", part, flags=re.I)
        # Headliner comes before a dash or colon: "X – tour name", "X: show".
        part = re.split(r"\s+[–—-]\s+|:\s+|\s+//\s+", part)[0]
        # Tribute / special shows: "X plays Y", "X goes Tavastia", "X feat. Y".
        part = re.split(r"\s+(?:plays|goes|feat\.?|featuring)\s+", part, flags=re.I)[0]
        # Trailing "Tour 2026", "X-mas special 2026", "20v", years.
        part = re.sub(r"\s+(tour|x-mas special|special)\b.*$", "", part, flags=re.I)
        part = re.sub(r"\s+\S*-?kiertue\b.*$", "", part, flags=re.I)  # Finnish "tour"
        part = re.sub(r"\s+\d{1,2}\.\d{1,2}\.(?:\d{2,4})?$", "", part)  # "… 18.3.2027"
        part = re.sub(r"\s+\d{4}$", "", part)
        # "levyjulkkarit", "-konsertti", "-hyväntekeväisyyskonsertti", "joulukonsertti"
        # (not "Wieniläiskonsertti" alone, which is the whole show name)
        part = re.sub(r"\s+(?:-?levyjulkkarit|-?konsertti|-\S+konsertti|joulukonsertti)$",
                      "", part, flags=re.I)
        part = re.sub(r"\s+\d+-vuotisjuhlakeikka$", "", part, flags=re.I)
        # Anniversaries: "Vainoa 10v.", "VIKI & KÖPI 10V SHOW", "Hector 60v juhla".
        part = re.sub(r"\s+\d+\s*(?:v\b\.?|vuotta\b).*$", "", part, flags=re.I)
        part = part.strip(" -–")
        if part:
            acts.append({"name": part, "country": country})
    return acts


# ---------------------------------------------------------------------------
# Tag sources
# ---------------------------------------------------------------------------

def clean_tags(raw: list[tuple[str, float]]) -> list[str]:
    """Normalise, de-junk and de-duplicate tags, keeping the strongest first."""
    seen, out = set(), []
    for name, _weight in sorted(raw, key=lambda t: -t[1]):
        tag = name.strip().lower()
        tag = TAG_ALIASES.get(tag, tag)
        if not tag or len(tag) > 30 or tag in JUNK_TAGS or JUNK_TAG_PATTERN.search(tag) or tag in seen or re.fullmatch(r"\d+s?", tag):
            continue
        seen.add(tag)
        out.append(tag)
        if len(out) >= MAX_TAGS:
            break
    return out


_last_mb_request = 0.0


def musicbrainz_lookup(name: str, country: str | None) -> dict | None:
    global _last_mb_request
    wait = 1.1 - (time.time() - _last_mb_request)
    if wait > 0:
        time.sleep(wait)
    _last_mb_request = time.time()

    resp = requests.get(
        "https://musicbrainz.org/ws/2/artist/",
        params={"query": f'artist:"{name}"', "fmt": "json", "limit": 10},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    if resp.status_code == 503:  # rate limited; back off once
        time.sleep(3)
        return musicbrainz_lookup(name, country)
    resp.raise_for_status()

    target = _norm(name)
    candidates = [
        a for a in resp.json().get("artists", [])
        if a.get("score", 0) >= MB_MIN_SCORE
        and (_norm(a["name"]) == target
             or any(_norm(al.get("name", "")) == target for al in a.get("aliases", [])))
    ]
    if not candidates:
        return None

    # Several artists share a name (e.g. "SARA"). Prefer the expected country
    # (Finland unless the title says otherwise), then the most-tagged one.
    want = country or "FI"
    candidates.sort(key=lambda a: (
        a.get("country") != want,
        -sum(t.get("count", 0) for t in a.get("tags", [])),
        -a.get("score", 0),
    ))
    best = candidates[0]
    tags = clean_tags([(t["name"], t.get("count", 0)) for t in best.get("tags", [])])
    return {
        "source": "musicbrainz",
        "matchedName": best["name"],
        "mbid": best["id"],
        "country": best.get("country"),
        "tags": tags,
    }


def lastfm_lookup(name: str) -> dict | None:
    if not LASTFM_API_KEY:
        return None
    resp = requests.get(
        "https://ws.audioscrobbler.com/2.0/",
        params={
            "method": "artist.gettoptags", "artist": name, "autocorrect": 1,
            "api_key": LASTFM_API_KEY, "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        return None
    raw = [
        (t["name"], float(t.get("count", 0)))
        for t in data.get("toptags", {}).get("tag", [])
        if float(t.get("count", 0)) >= LASTFM_MIN_WEIGHT
    ]
    tags = clean_tags(raw)
    if not tags:
        return None
    return {
        "source": "lastfm",
        "matchedName": data.get("toptags", {}).get("@attr", {}).get("artist", name),
        "tags": tags,
    }


def lookup_artist(name: str, country: str | None) -> dict:
    result = None
    try:
        result = lastfm_lookup(name) or musicbrainz_lookup(name, country)
    except requests.RequestException as e:
        print(f"  ! lookup failed for {name!r}: {e}", file=sys.stderr)
        return {"source": "error", "tags": []}
    if result is None:
        result = {"source": "notfound", "tags": []}
    result["fetched"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def resolve_artist(act: dict, cache: dict, overrides: dict, refresh: bool) -> tuple[str, list[str]]:
    """Return (display name, tags) for one act, splitting on '&' if needed."""
    name = act["name"]

    if name in overrides:
        return name, overrides[name].get("genres", [])
    if len(_norm(name)) <= 2:
        # "F", "M": far too ambiguous to look up; the venue's genre is used.
        return name, []

    def get(n):
        if refresh or n not in cache or cache[n].get("source") == "error":
            print(f"  looking up {n}")
            cache[n] = lookup_artist(n, act["country"])
        return cache[n]

    def tidy(tags: list[str]) -> list[str]:
        # Re-apply junk/alias rules to cached tags, keeping their order.
        return clean_tags([(t, len(tags) - i) for i, t in enumerate(tags)])

    entry = get(name)
    if entry["source"] != "notfound" or "&" not in name:
        return name, tidy(entry["tags"])

    # "Blues Pills & Graveyard" -> two artists.
    tags = []
    for sub in re.split(r"\s+&\s+", name):
        tags += [t for t in tidy(get(sub)["tags"]) if t not in tags]
    return name, tags


# ---------------------------------------------------------------------------
# Tribute gigs: the covered band's genres
# ---------------------------------------------------------------------------

_TRIBUTE_END = r"(?=\s+&\s+[^&]+?\s+plays\b|,|\s+(?:feat\.?|featuring|with)\s|\s+[–—-]\s+|\s*\(|$)"
_TRIBUTE_PATTERNS = [
    # "Bon Scott Boys plays AC/DC", "Screaming Thunders plays CCR & J.C. Fogerty"
    re.compile(r"\bplays\s+(.+?)" + _TRIBUTE_END, re.I),
    # "Rearviewmirror – A Tribute to Pearl Jam"
    re.compile(r"\btribute\s+to\s+(.+?)" + _TRIBUTE_END, re.I),
    # "The Miracle - A Night with Queen - Freddie Mercury 80v."
    re.compile(r"\ba night with\s+(.+?)" + _TRIBUTE_END, re.I),
]
# "Dolly Parton Tribute", "Roky Erickson -tribute", "A Pink Floyd Tribute Show",
# "Jiri Nikkinen The Beatles Tribute Band", "David Bowie 80th Anniversary Tribute":
# checked per title segment (between commas, dashes and colons).
_SEGMENT_SPLIT = re.compile(r",|\s[-–—]\s|[–—:]")
_X_TRIBUTE = re.compile(r"^\s*(.+?)\s*-?\s*tribute\b", re.I)


def _tidy_target(text: str) -> list[str]:
    text = re.sub(r"\s+\d+(?:st|nd|rd|th)?\s+anniversary\b.*$", "", text, flags=re.I)
    text = re.sub(r"^(?:a|an|the ultimate)\s+", "", text.strip(), flags=re.I)
    return [n.strip(" -–—.") for n in re.split(r"\s+&\s+|\s+and\s+", text) if n.strip(" -–—.")]


def tribute_targets(title: str) -> list[tuple[str, bool]]:
    """
    Bands a tribute gig covers, from its title, each with whether the name
    may have the tribute act's name in front ("Jiri Nikkinen The Beatles
    Tribute Band"). "Kill With Cover plays Manowar & BoneButton plays Iron
    Maiden" -> [("Manowar", False), ("Iron Maiden", False)]. Empty for an
    ordinary gig.
    """
    title = re.sub(r"\s*[“”\"«][^“”\"»]*[“”\"»]", "", title)  # quoted album names
    found: list[tuple[str, bool]] = []

    def add(names, loose):
        for name in names:
            if name.casefold() not in (f.casefold() for f, _ in found):
                found.append((name, loose))

    for pattern in _TRIBUTE_PATTERNS:
        for m in pattern.finditer(title):
            add(_tidy_target(m.group(1)), False)
        if found:
            return found
    for segment in _SEGMENT_SPLIT.split(title):
        m = _X_TRIBUTE.match(segment)
        if m:
            add(_tidy_target(m.group(1)), True)
    return found


def _covered_tags(name: str, loose: bool, cache: dict, overrides: dict, refresh: bool) -> list[str]:
    """Tags of a covered band; a loose name ("Jiri Nikkinen The Beatles")
    also tries its last three / two words ("The Beatles")."""
    words = name.split()
    tries = [name] + ([" ".join(words[-n:]) for n in (3, 2) if len(words) > n] if loose else [])
    for candidate in tries:
        if len(_norm(candidate)) <= 2:
            continue
        _name, tags = resolve_artist({"name": candidate, "country": None}, cache, overrides, refresh)
        if tags:
            return tags
    return []


def gig_tags(title: str, cache: dict, overrides: dict,
             refresh: bool = False) -> tuple[list[str], list[str]]:
    """
    (artists, tags) of a gig title. A tribute gig ("X plays Y", "Tribute to
    Y", "Y Tribute") gets the covered bands' tags: the tribute act itself is
    rarely known to Last.fm, or is a namesake. Its own tags are the fallback.
    """
    artists, tags = [], []
    for act in parse_title(title):
        name, act_tags = resolve_artist(act, cache, overrides, refresh)
        artists.append(name)
        tags += [t for t in act_tags if t not in tags]
    covered = []
    for target, loose in tribute_targets(title):
        covered += [t for t in _covered_tags(target, loose, cache, overrides, refresh)
                    if t not in covered]
    return artists, (covered or tags)


ALWAYS_SHOW_TOP_TAGS = 5  # as in frontend/lib/events.ts


def shown_by_default(genres: list[str], config: dict) -> bool:
    """
    Would the site show a gig with these genres by default? The same rule as
    isExcludedByGenre() in frontend/lib/events.ts: a core genre
    (alwaysShowGenres) among the strongest tags, or a header-genre tag while
    the strongest tag isn't excluded (pop, jazz, iskelmä…).
    """
    top = genres[:ALWAYS_SHOW_TOP_TAGS]
    core = [re.compile("^" + ".*".join(re.escape(p) for p in pattern.split("*")) + "$")
            for pattern in config.get("alwaysShowGenres", [])]
    if any(c.match(tag) for c in core for tag in top):
        return True
    if not top or top[0] in set(config.get("excludeGenres", [])):
        return False
    return any(re.search(p, tag, flags=re.I)
               for g in config.get("genreFilters", []) for p in g["patterns"] for tag in top)


# Genres kept by the scrapers that filter while scraping (Dubrovnik,
# Ääniwalli, Krapin Paja, Apollo) although the site hides them by default:
# they're listed under "Show hidden genres", like at every other venue.
KEEP_HIDDEN_GENRES = re.compile(r"\btrip[- ]?hop\b", re.I)


def keep_when_scraping(genres: list[str], config: dict) -> bool:
    """Should a filtering scraper keep a gig with these genres?"""
    return shown_by_default(genres, config) or any(KEEP_HIDDEN_GENRES.search(t) for t in genres)


DJ_TITLE = re.compile(r"\b(dj|djs|disko|disco)\b|-disko\b", re.I)
COMEDY_TITLE = re.compile(r"naurut|stand ?-?up|standup|komiikka|joka v\*tun keskiviikko", re.I)
QUIZ_TITLE = re.compile(r"pubivisa|\bvisailu|\bquiz\b|bingo", re.I)


def pick_genres(event: dict, artist_tags: list[str]) -> list[str]:
    """
    Decide a gig's genres, most reliable source first:
      1. the venue labels the gig a DJ night -> "dj night"; the title says
         it's a comedy or quiz night -> "stand-up" / "viihde" (namesake bands
         in such titles must not win)
      2. tags of the artists (Last.fm / MusicBrainz / overrides)
      3. the venue's own category for this gig (venueGenres)
      4. a DJ/disco title (checked late: band gigs often have DJs after)
      5. the venue's general default (venueDefault, e.g. a rock bar)
    """
    venue_cats = event.get("venueGenres") or []
    title = event["artist"]
    if "dj" in venue_cats:
        return ["dj night"]
    if COMEDY_TITLE.search(title):
        return ["stand-up"]
    if QUIZ_TITLE.search(title):
        return ["viihde"]
    if artist_tags:
        return artist_tags
    mapped = [VENUE_GENRES[g] for g in venue_cats if VENUE_GENRES.get(g)]
    if mapped:
        return mapped
    if DJ_TITLE.search(title):
        return ["dj night"]
    return [event["venueDefault"]] if event.get("venueDefault") else []


# Christmas concerts (choirs, "Christmas Jazz", "Joulun tuoksu"…) aren't listed
# at all, not even under "Show hidden genres". A Christmas gig by a band in
# Dark Suomi's genres stays (Stam1na's pikkujoulut), and so do comedy shows,
# which standup.py picks up for /standup.
CHRISTMAS_TITLE = re.compile(r"\bjoulu|\bjoulun|christmas|\bx-?mas\b|\bjul(?:konsert\w*)?\b", re.I)
COMEDY_TITLE = re.compile(r"stand.?up|komedia|comedy|koomik|qoomik", re.I)


def is_generic_christmas_show(event: dict, config: dict) -> bool:
    title = event.get("artist", "")
    genres = event.get("genres", [])
    return (bool(CHRISTMAS_TITLE.search(title)) and not COMEDY_TITLE.search(title)
            and "stand-up" not in genres and not shown_by_default(genres, config))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="re-fetch all artists")
    parser.add_argument("--report", action="store_true", help="print genre counts and exit")
    parser.add_argument("--city", help="tampere / oulu: that site's events.json")
    args = parser.parse_args()

    from eventstore import events_file
    events_path = events_file(args.city)
    events = load_json(events_path, [])
    cache = load_json(CACHE_FILE, {})
    config = load_json(CONFIG_FILE, {})
    overrides = config.get("artistOverrides", {})

    if not args.report:
        for event in events:
            artists, genres = gig_tags(event["artist"], cache, overrides, args.refresh)
            event["artists"] = artists
            event["genres"] = pick_genres(event, genres)
        save_json(CACHE_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))
        christmas = [e for e in events if is_generic_christmas_show(e, config)]
        if christmas:
            events = [e for e in events if e not in christmas]
            print(f"✓ Dropped {len(christmas)} Christmas shows outside Dark Suomi's genres")
        save_json(events_path, events)
        print(f"✓ Tagged {len(events)} events ({len(cache)} artists cached)")

    # Report: every genre with how many events carry it.
    counts = Counter(g for e in events for g in e.get("genres", []))
    excluded = set(config.get("excludeGenres", []))
    untagged = [e["artist"] for e in events if not e.get("genres")]
    print(f"\nGenres ({len(counts)}), events per genre; [x] = excluded by default:")
    for genre, n in counts.most_common():
        print(f"  {'[x]' if genre in excluded else '[ ]'} {n:3d}  {genre}")
    print(f"\nUntagged events ({len(untagged)}):")
    for title in sorted(set(untagged)):
        print(f"  - {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
