#!/usr/bin/env python3
"""
Expected setlists for Dark Suomi events, built from setlist.fm.

For every artist in frontend/data/events.json (the `artists` field written by
genres.py), fetch their recent setlists from setlist.fm and work out a likely
setlist: songs played in a good share of recent shows, in their usual order,
with encores last. Results go to frontend/data/setlists.json, keyed by artist.

Needs SETLISTFM_API_KEY in the environment.

Usage:
  python setlists.py            # update artists not fetched in the last 7 days
  python setlists.py --refresh  # re-fetch every artist
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

from genres import _norm, load_json, parse_title, save_json

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "frontend" / "data"
EVENTS_FILE = DATA_DIR / "events.json"
ARTISTS_FILE = DATA_DIR / "artists.json"
SETLISTS_FILE = DATA_DIR / "setlists.json"

API = "https://api.setlist.fm/rest/1.0"
API_KEY = os.environ.get("SETLISTFM_API_KEY")

MAX_SETLISTS = 15        # use at most this many recent shows
MIN_SETLISTS = 3         # fewer than this -> no prediction
MAX_AGE_DAYS = 730       # ignore shows older than two years
MAX_PAGES = 3            # 20 setlists per page
MIN_SHARE = 0.25         # a song must be in at least 25% of shows
CACHE_DAYS = 7           # re-fetch an artist after this many days

# setlist.fm allows 2 requests/second and 1440/day per API key.
MAX_FETCHES_PER_RUN = 40     # artists (re)fetched per run, oldest first
MAX_REQUESTS_PER_RUN = 1000  # hard stop, leaves room for manual runs

_last_request = 0.0
_requests_made = 0


class BudgetExhausted(Exception):
    pass


def api_get(path: str, params: dict | None = None) -> dict | None:
    """GET from setlist.fm, staying under its 2 requests/second limit."""
    global _last_request, _requests_made
    for attempt in range(3):
        if _requests_made >= MAX_REQUESTS_PER_RUN:
            raise BudgetExhausted()
        _requests_made += 1
        wait = 0.6 - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.time()
        resp = requests.get(
            f"{API}{path}",
            params=params,
            headers={"x-api-key": API_KEY, "Accept": "application/json",
                     "Accept-Language": "en"},
            timeout=20,
        )
        if resp.status_code == 429:
            time.sleep(2 + 2 * attempt)
            continue
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"setlist.fm kept rate-limiting {path}")


def find_artist(name: str, mbid: str | None) -> tuple[dict | None, bool]:
    """
    Return (setlist.fm artist record, ambiguous). Looks up by MusicBrainz ID
    when known; otherwise searches by name. `ambiguous` is True when several
    setlist.fm artists share the exact name, i.e. a namesake is possible.
    """
    if mbid:
        found = api_get(f"/artist/{mbid}")
        if found:
            return found, False
    result = api_get("/search/artists", {"artistName": name, "sort": "relevance"})
    matches = [a for a in (result or {}).get("artist", [])
               if _norm(a["name"]) == _norm(name)]
    return (matches[0] if matches else None), len(matches) > 1


def recent_setlists(mbid: str) -> list[dict]:
    """Recent past setlists that actually list songs, newest first."""
    today = date.today()
    oldest = today - timedelta(days=MAX_AGE_DAYS)
    found = []
    for page in range(1, MAX_PAGES + 1):
        data = api_get(f"/artist/{mbid}/setlists", {"p": page})
        if not data:
            break
        for s in data.get("setlist", []):
            played = datetime.strptime(s["eventDate"], "%d-%m-%Y").date()
            if played > today:
                continue
            if played < oldest:
                return found
            songs = song_list(s)
            if songs:
                found.append({
                    "date": played,
                    "country": s.get("venue", {}).get("city", {}).get("country", {}).get("code"),
                    "songs": songs,
                })
                if len(found) >= MAX_SETLISTS:
                    return found
        if page * data.get("itemsPerPage", 20) >= data.get("total", 0):
            break
    return found


def song_list(setlist: dict) -> list[dict]:
    """Flatten a setlist into songs, skipping intro tapes."""
    songs = []
    for s in setlist.get("sets", {}).get("set", []):
        encore = "encore" in s
        for song in s.get("song", []):
            if song.get("tape") or not song.get("name", "").strip():
                continue
            songs.append({
                "name": song["name"].strip(),
                "encore": encore,
                "cover": (song.get("cover") or {}).get("name"),
            })
    return songs


def predict(setlists: list[dict]) -> list[dict]:
    """Songs likely to be played, in their usual order."""
    stats: dict[str, dict] = {}
    for s in setlists:
        n = len(s["songs"])
        seen = set()
        for i, song in enumerate(s["songs"]):
            key = song["name"].casefold()
            if key in seen:
                continue
            seen.add(key)
            st = stats.setdefault(key, {"name": song["name"], "count": 0,
                                        "positions": [], "encores": 0,
                                        "cover": song["cover"]})
            st["count"] += 1
            st["positions"].append(i / max(n - 1, 1))
            st["encores"] += song["encore"]

    total = len(setlists)
    typical_length = round(statistics.median(len(s["songs"]) for s in setlists))
    likely = sorted(
        (st for st in stats.values() if st["count"] / total >= MIN_SHARE),
        key=lambda st: -st["count"],
    )[:typical_length]

    songs = [{
        "name": st["name"],
        "encore": st["encores"] * 2 > st["count"],
        "cover": st["cover"],
        "playedPct": round(100 * st["count"] / total),
        "_pos": statistics.mean(st["positions"]),
    } for st in likely]
    songs.sort(key=lambda s: (s["encore"], s["_pos"]))
    for s in songs:
        del s["_pos"]
    return songs


def build(name: str, country: str | None, mbid: str | None) -> dict:
    today = date.today().isoformat()
    artist, ambiguous = find_artist(name, mbid)
    if not artist:
        return {"status": "artist-not-found", "fetched": today}

    setlists = recent_setlists(artist["mbid"])
    base = {"mbid": artist["mbid"], "url": artist.get("url"), "fetched": today}

    # Guard against namesakes: when several artists share the name, an act
    # billed without a country code is assumed Finnish, so at least one
    # recent show should be in Finland.
    if (ambiguous and country is None and setlists
            and not any(s["country"] == "FI" for s in setlists)):
        return {**base, "status": "no-finnish-shows"}
    if len(setlists) < MIN_SETLISTS:
        return {**base, "status": "too-few-setlists", "basedOn": len(setlists)}

    return {
        **base,
        "status": "ok",
        "basedOn": len(setlists),
        "from": min(s["date"] for s in setlists).isoformat(),
        "to": max(s["date"] for s in setlists).isoformat(),
        "songs": predict(setlists),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="re-fetch all artists")
    args = parser.parse_args()

    if not API_KEY:
        print("SETLISTFM_API_KEY is not set", file=sys.stderr)
        return 1

    events = load_json(EVENTS_FILE, [])
    genre_cache = load_json(ARTISTS_FILE, {})
    cache = load_json(SETLISTS_FILE, {})
    stale_before = (date.today() - timedelta(days=CACHE_DAYS)).isoformat()

    # Artist name -> country code from the title, e.g. "Crashdiet (SWE)".
    wanted: dict[str, str | None] = {}
    for event in events:
        countries = {a["name"]: a["country"] for a in parse_title(event["artist"])}
        for name in event.get("artists", []):
            wanted.setdefault(name, countries.get(name))

    # New artists first, then the longest-unrefreshed ones; capped per run so
    # refreshes spread over several days instead of all landing on one.
    due = [n for n in wanted
           if args.refresh or n not in cache
           or cache[n].get("fetched", "") < stale_before]
    due.sort(key=lambda n: cache.get(n, {}).get("fetched", ""))
    if len(due) > MAX_FETCHES_PER_RUN:
        print(f"  {len(due)} artists due, fetching {MAX_FETCHES_PER_RUN} this run")
        due = due[:MAX_FETCHES_PER_RUN]

    for name in due:
        country = wanted[name]
        print(f"  {name}")
        try:
            entry = build(name, country, genre_cache.get(name, {}).get("mbid"))
            # "Blues Pills & Graveyard" -> look up each act separately.
            if entry["status"] == "artist-not-found" and " & " in name:
                parts = [p.strip() for p in name.split(" & ") if p.strip()]
                entry = {"status": "split", "parts": parts, "fetched": entry["fetched"]}
                for part in parts:
                    cache[part] = build(part, country, genre_cache.get(part, {}).get("mbid"))
            cache[name] = entry
        except BudgetExhausted:
            print(f"  ! stopped after {_requests_made} requests (daily budget)",
                  file=sys.stderr)
            break
        except (requests.RequestException, RuntimeError) as e:
            print(f"  ! {name}: {e}", file=sys.stderr)

    print(f"  setlist.fm requests this run: {_requests_made}")

    # Drop artists that no longer have events (keeping parts of split names).
    keep = set(wanted)
    for name in wanted:
        keep.update(cache.get(name, {}).get("parts", []))
    cache = {k: v for k, v in cache.items() if k in keep}
    save_json(SETLISTS_FILE, dict(sorted(cache.items(), key=lambda kv: kv[0].casefold())))

    ok = sum(v.get("status") == "ok" for v in cache.values())
    print(f"✓ Expected setlists for {ok} of {len(cache)} artists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
