#!/usr/bin/env python3
"""
Band directory for Dark Suomi: every band with an upcoming gig, with links to
their music on Spotify, Bandcamp, SoundCloud, Tidal, Apple Music, Deezer,
YouTube, Discogs, Metal Archives, homepage and Instagram.

Links come from MusicBrainz ("url-rels": the official links the MusicBrainz
community has attached to an artist). If MusicBrainz has no Spotify link, an
exact-name artist search in the Dark Suomi Spotify app fills it in (capped
per run, shares that app's limit with playlists.py). Links that are still
missing are shown on the site as search links instead.

Comedy, DJ and "entertainment" bills, and names nobody recognises, are left
out. Results: frontend/data/bands.json. Each band is re-checked monthly.

Usage:
  python bands.py              # look up new / stale bands
  python bands.py --refresh    # re-check every band
"""

import argparse
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

from genres import (USER_AGENT, _norm, load_json, musicbrainz_lookup,
                    parse_title, save_json)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "frontend" / "data"
EVENTS_FILE = DATA_DIR / "events.json"
ARTISTS_FILE = DATA_DIR / "artists.json"
CONFIG_FILE = DATA_DIR / "genre-config.json"
BANDS_FILE = DATA_DIR / "bands.json"

RECHECK_DAYS = 30
MAX_MB_REQUESTS = 900        # ~15 min at 1 request/second
MAX_SPOTIFY_SEARCHES = 60    # shares the playlist app's daily limit

# Gigs whose strongest genre is one of these are not band gigs.
NOT_BANDS = {"stand-up", "dj night", "viihde"}

_last_mb = 0.0
_mb_requests = 0


def mb_get(path: str, params: dict) -> dict | None:
    """MusicBrainz GET, at most 1 request/second."""
    global _last_mb, _mb_requests
    if _mb_requests >= MAX_MB_REQUESTS:
        raise RuntimeError("MusicBrainz request budget used")
    for attempt in range(3):
        wait = 1.1 - (time.time() - _last_mb)
        if wait > 0:
            time.sleep(wait)
        _last_mb = time.time()
        _mb_requests += 1
        resp = requests.get(f"https://musicbrainz.org/ws/2/{path}",
                            params={**params, "fmt": "json"},
                            headers={"User-Agent": USER_AGENT}, timeout=20)
        if resp.status_code == 503:
            time.sleep(3 + 2 * attempt)
            continue
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    return None


def classify(url: str, rel_type: str) -> str | None:
    """Which of our link kinds a MusicBrainz URL is, if any."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host == "open.spotify.com" and "/artist/" in url:
        return "spotify"
    if host.endswith("bandcamp.com"):
        return "bandcamp"
    if host == "soundcloud.com":
        return "soundcloud"
    if host.endswith("tidal.com"):
        return "tidal"
    if host == "music.apple.com":
        return "apple"
    if host == "deezer.com":
        return "deezer"
    if host == "youtube.com":
        return "youtube"
    if host == "discogs.com" and "/artist/" in url:
        return "discogs"
    if host == "metal-archives.com":
        return "metalArchives"
    if host == "instagram.com":
        return "instagram"
    if host.endswith("wikipedia.org"):
        return "wikipedia"
    if host == "wikidata.org":
        return "wikidata"  # used to find the Wikipedia page, not shown
    if rel_type == "official homepage":
        return "homepage"
    return None


def mb_links(mbid: str) -> dict:
    data = mb_get(f"artist/{mbid}", {"inc": "url-rels"}) or {}
    links: dict[str, str] = {}
    for rel in data.get("relations", []):
        if rel.get("ended"):
            continue
        url = rel.get("url", {}).get("resource", "")
        kind = classify(url, rel.get("type", ""))
        if kind and kind not in links:
            links[kind] = url
    return links


def add_wikipedia_links(bands: dict[str, dict]) -> int:
    """Fill links.wikipedia from Wikidata (English page, else Finnish)."""
    todo = {}
    for band in bands.values():
        links = band.get("links") or {}
        if links.get("wikidata") and not links.get("wikipedia"):
            qid = links["wikidata"].rstrip("/").rsplit("/", 1)[-1]
            if re.fullmatch(r"Q\d+", qid):
                todo.setdefault(qid, []).append(links)
    ids = list(todo)
    added = 0
    for i in range(0, len(ids), 50):  # the API takes up to 50 ids at once
        resp = requests.get("https://www.wikidata.org/w/api.php", params={
            "action": "wbgetentities", "ids": "|".join(ids[i:i + 50]),
            "props": "sitelinks/urls", "sitefilter": "enwiki|fiwiki", "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        for qid, entity in resp.json().get("entities", {}).items():
            sitelinks = entity.get("sitelinks", {})
            page = sitelinks.get("enwiki") or sitelinks.get("fiwiki")
            if page and page.get("url"):
                for links in todo.get(qid, []):
                    links["wikipedia"] = page["url"]
                    added += 1
        time.sleep(1)
    return added


class SpotifySearch:
    """Exact-name artist search with the Dark Suomi playlist app."""

    def __init__(self):
        self.client = None
        self.searches = 0
        try:
            from playlists import Spotify, RateLimited
            self.client, self.RateLimited = Spotify(), RateLimited
        except (SystemExit, Exception) as e:  # no credentials, or rate limited
            print(f"  (Spotify search unavailable: {e})")

    def artist_url(self, name: str) -> str | None:
        if not self.client or self.searches >= MAX_SPOTIFY_SEARCHES:
            return None
        self.searches += 1
        try:
            items = self.client.call("GET", "/search", params={
                "q": f'artist:"{name}"', "type": "artist", "limit": 5,
            })["artists"]["items"]
        except Exception as e:
            print(f"  ! Spotify search stopped: {e}")
            self.client = None
            return None
        for item in items:
            if _norm(item["name"]) == _norm(name):
                return item["external_urls"]["spotify"]
        return None


def band_names_by_event(events: list[dict], genre_cache: dict) -> dict[str, list[int]]:
    """Band name -> ids of upcoming gigs, skipping comedy/DJ/entertainment."""
    today = date.today().isoformat()
    bands: dict[str, list[int]] = {}
    for event in events:
        if event["date"][:10] < today:
            continue
        genres = event.get("genres") or []
        if genres and genres[0] in NOT_BANDS:
            continue
        for name in event.get("artists") or []:
            # "Blues Pills & Graveyard" was looked up as two bands.
            entry = genre_cache.get(name, {})
            names = ([n.strip() for n in name.split(" & ")]
                     if entry.get("source") == "notfound" and " & " in name else [name])
            for n in names:
                if genre_cache.get(n, {}).get("source") in ("lastfm", "musicbrainz"):
                    bands.setdefault(n, []).append(event["id"])
    return bands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="re-check every band")
    args = parser.parse_args()

    events = load_json(EVENTS_FILE, [])
    genre_cache = load_json(ARTISTS_FILE, {})
    overrides = load_json(CONFIG_FILE, {}).get("artistOverrides", {})
    old = load_json(BANDS_FILE, {})
    wanted = band_names_by_event(events, genre_cache)
    for name in overrides:  # hand-checked artists count as known
        for event in events:
            if name in (event.get("artists") or []) and event["id"] not in wanted.get(name, []):
                wanted.setdefault(name, []).append(event["id"])

    stale = (date.today() - timedelta(days=RECHECK_DAYS)).isoformat()
    spotify = SpotifySearch()
    bands: dict[str, dict] = {}
    looked_up = 0
    try:
        for name in sorted(wanted, key=str.casefold):
            entry = dict(old.get(name, {}))
            genre_entry = genre_cache.get(name, {})
            entry["genres"] = genre_entry.get("tags", [])[:3]
            # Last.fm / MusicBrainz spelling: "Amorphis", not "AMORPHIS".
            matched = genre_entry.get("matchedName") or name
            entry["display"] = matched if _norm(matched) == _norm(name) else name
            entry["eventIds"] = sorted(set(wanted[name]))
            if not args.refresh and entry.get("fetched", "") >= stale:
                bands[name] = entry
                continue

            mbid = genre_entry.get("mbid") or entry.get("mbid")
            if not mbid:
                found = musicbrainz_lookup(name, None)
                mbid = found.get("mbid") if found else None
            links = mb_links(mbid) if mbid else {}
            if "spotify" not in links:
                url = spotify.artist_url(name)
                if url:
                    links["spotify"] = url
            entry.update({"mbid": mbid, "links": links,
                          "fetched": date.today().isoformat()})
            bands[name] = entry
            looked_up += 1
            print(f"  {name}: {', '.join(links) or 'no links'}")
    except RuntimeError as e:
        print(f"  ! stopping early: {e}. Progress is saved.")
        # Keep everything not reached yet as it was.
        for name in wanted:
            if name not in bands and name in old:
                bands[name] = {**old[name], "eventIds": sorted(set(wanted[name]))}
    finally:
        try:
            print(f"  Wikipedia links added: {add_wikipedia_links(bands)}")
        except requests.RequestException as e:
            print(f"  ! Wikipedia lookup failed: {e}")
        save_json(BANDS_FILE, dict(sorted(bands.items(), key=lambda kv: kv[0].casefold())))

    with_links = sum(1 for b in bands.values() if b.get("links"))
    print(f"✓ {len(bands)} bands ({with_links} with links), {looked_up} looked up, "
          f"{_mb_requests} MusicBrainz requests, {spotify.searches} Spotify searches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
