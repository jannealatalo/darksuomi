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
    "eurovision",
}
# Event / contest tags such as "eurovision 2023 artists" or "umk 2025".
JUNK_TAG_PATTERN = re.compile(r"eurovision|^umk\b|^\d{4}$")

# Map spelling variants onto one name so the genre list stays readable.
TAG_ALIASES = {
    "hip-hop": "hip hop",
    "hiphop": "hip hop",
    "suomirap": "rap",
    "finnish rap": "rap",
    "finnish hip hop": "hip hop",
    "suomi-rap": "rap",
    "schlager": "iskelmä",
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
    "rock 'n' roll": "rock & roll",
}

# Country codes used in Tavastia titles, e.g. "Crashdiet (SWE)".
COUNTRY_CODES = {
    "SWE": "SE", "UK": "GB", "USA": "US", "US": "US", "ITA": "IT",
    "DK": "DK", "UA": "UA", "EST": "EE", "JPN": "JP", "CAN": "CA", "AU": "AU",
    "AUS": "AU", "ES": "ES", "FRA": "FR", "FR": "FR", "NOR": "NO", "GER": "DE",
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
    """
    acts = []
    # Split on commas and on " & " between acts; " & " inside a band name
    # ("Kauko Röyhkä & Voimaeläin") is handled by trying the full name first.
    for part in re.split(r",\s*", title):
        part = part.strip()
        if not part:
            continue

        country = None
        m = re.search(r"\(([A-Za-z]{1,3})(?:-[A-Za-z]{1,3})?\)", part)
        if m and m.group(1).upper() in COUNTRY_CODES:
            country = COUNTRY_CODES[m.group(1).upper()]

        # Drop all parentheses: country codes, age limits, release-party notes.
        part = re.sub(r"\s*\([^)]*\)", "", part)
        # Headliner comes before a dash or colon: "X – tour name", "X: show".
        part = re.split(r"\s+[–—-]\s+|:\s+", part)[0]
        # Tribute / special shows: "X plays Y", "X goes Tavastia", "X feat. Y".
        part = re.split(r"\s+(?:plays|goes|feat\.?|featuring)\s+", part, flags=re.I)[0]
        # Trailing "Tour 2026", "X-mas special 2026", "20v", years.
        part = re.sub(r"\s+(tour|x-mas special|special)\b.*$", "", part, flags=re.I)
        part = re.sub(r"\s+\d{4}$", "", part)
        part = re.sub(r"\s+-?(levyjulkkarit|konsertti)$", "", part, flags=re.I)
        part = re.sub(r"\s+\d+-vuotisjuhlakeikka$", "", part, flags=re.I)
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
        if not tag or tag in JUNK_TAGS or JUNK_TAG_PATTERN.search(tag) or tag in seen or re.fullmatch(r"\d+s?", tag):
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

    def get(n):
        if refresh or n not in cache or cache[n].get("source") == "error":
            print(f"  looking up {n}")
            cache[n] = lookup_artist(n, act["country"])
        return cache[n]

    entry = get(name)
    if entry["source"] != "notfound" or "&" not in name:
        return name, entry["tags"]

    # "Blues Pills & Graveyard" -> two artists.
    tags = []
    for sub in re.split(r"\s+&\s+", name):
        tags += [t for t in get(sub)["tags"] if t not in tags]
    return name, tags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="re-fetch all artists")
    parser.add_argument("--report", action="store_true", help="print genre counts and exit")
    args = parser.parse_args()

    events = load_json(EVENTS_FILE, [])
    cache = load_json(CACHE_FILE, {})
    config = load_json(CONFIG_FILE, {})
    overrides = config.get("artistOverrides", {})

    if not args.report:
        for event in events:
            artists, genres = [], []
            for act in parse_title(event["artist"]):
                name, tags = resolve_artist(act, cache, overrides, args.refresh)
                artists.append(name)
                genres += [t for t in tags if t not in genres]
            event["artists"] = artists
            event["genres"] = genres
        save_json(CACHE_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))
        save_json(EVENTS_FILE, events)
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
