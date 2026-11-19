#!/usr/bin/env python3
"""
Spotify playlists of expected setlists, in the Dark Suomi Spotify account.

For every upcoming event with an expected setlist (frontend/data/setlists.json),
find the songs on Spotify and create or update one public playlist per event.
Support acts come first and the headliner last, like at the gig. Event ->
playlist links go to frontend/data/playlists.json (read by the site); song ->
Spotify track lookups are cached in frontend/data/spotify-tracks.json.

Uses the separate "Dark Suomi playlists" Spotify app, so this job can't
rate-limit the website's login. Needs SPOTIFY_PLAYLIST_CLIENT_ID,
SPOTIFY_PLAYLIST_CLIENT_SECRET and SPOTIFY_PLAYLIST_REFRESH_TOKEN (set up by
spotify_authorize.py; on Windows they're read from the user environment).

Usage:
  python playlists.py              # create/update playlists
  python playlists.py --dry-run    # only show which songs were found
  python playlists.py --limit 2    # handle at most 2 events (for testing)
"""

import argparse
import base64
import hashlib
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

import requests

from genres import _norm, load_json, save_json
from spotify_authorize import user_env

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "frontend" / "data"
EVENTS_FILE = DATA_DIR / "events.json"
SETLISTS_FILE = DATA_DIR / "setlists.json"
PLAYLISTS_FILE = DATA_DIR / "playlists.json"
GENRE_CONFIG_FILE = DATA_DIR / "genre-config.json"
TRACKS_FILE = DATA_DIR / "spotify-tracks.json"

API = "https://api.spotify.com/v1"
MIN_TRACKS = 5          # skip events where fewer songs were found
MIN_FOUND_SHARE = 0.5   # ...or less than half of the expected songs

# Development-mode Spotify apps have a low rate limit, and going over it can
# block the whole app (including the website's login features) for a day.
# Song lookups are cached, so a capped run just continues the next night.
MAX_SEARCHES_PER_RUN = 150
REQUEST_DELAY = 0.5     # seconds between API calls
MAX_RETRY_WAIT = 60     # give up (and save) instead of waiting longer


class RateLimited(Exception):
    pass


class Spotify:
    def __init__(self):
        cid = user_env("SPOTIFY_PLAYLIST_CLIENT_ID")
        secret = user_env("SPOTIFY_PLAYLIST_CLIENT_SECRET")
        refresh = user_env("SPOTIFY_PLAYLIST_REFRESH_TOKEN")
        if not (cid and secret and refresh):
            raise SystemExit("SPOTIFY_PLAYLIST_CLIENT_ID, SPOTIFY_PLAYLIST_CLIENT_SECRET "
                             "and SPOTIFY_PLAYLIST_REFRESH_TOKEN are required "
                             "(run spotify_authorize.py)")
        basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
        resp = requests.post("https://accounts.spotify.com/api/token",
                             headers={"Authorization": f"Basic {basic}"},
                             data={"grant_type": "refresh_token", "refresh_token": refresh},
                             timeout=20)
        resp.raise_for_status()
        self.headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        self.searches = 0
        self.user_id = self.call("GET", "/me")["id"]

    def call(self, method: str, path: str, **kwargs):
        for attempt in range(5):
            resp = requests.request(method, API + path, headers=self.headers,
                                    timeout=20, **kwargs)
            time.sleep(REQUEST_DELAY)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", "5"))
                if wait > MAX_RETRY_WAIT:
                    raise RateLimited(f"Spotify asks to wait {wait} s ({wait / 3600:.1f} h)")
                time.sleep(wait + 1)
                continue
            if resp.status_code in (500, 502, 503, 504):  # transient Spotify errors
                time.sleep(2 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                raise requests.HTTPError(
                    f"{method} {path} -> {resp.status_code}: {resp.text[:300]}",
                    response=resp)
            return resp.json() if resp.content else None
        raise RuntimeError(f"Spotify kept failing on {path}")

    def find_track(self, song: str, artist: str) -> str | None:
        """Spotify URI of the artist's recording of a song, if any."""
        if self.searches >= MAX_SEARCHES_PER_RUN:
            raise RateLimited(f"search budget of {MAX_SEARCHES_PER_RUN} used")
        self.searches += 1
        query = f'track:"{song}" artist:"{artist}"'
        items = self.call("GET", "/search", params={"q": query, "type": "track",
                                                    "limit": 10})["tracks"]["items"]
        by_artist = [t for t in items
                     if any(_norm(a["name"]) == _norm(artist) for a in t["artists"])]
        if not by_artist:
            return None

        def base(name: str) -> str:
            # "Song - Remastered 2011" / "Song (Live)" -> "song"
            return _norm(re.split(r"\s+-\s+|\s*\(", name)[0])

        exact = [t for t in by_artist if base(t["name"]) == base(song)]
        return (exact or by_artist)[0]["uri"]


def hidden_by_default(event: dict, config: dict) -> bool:
    """Same rule as the website (frontend/lib/events.ts isExcludedByGenre)."""
    genres = event.get("genres") or []
    patterns = [re.compile("^" + ".*".join(map(re.escape, p.split("*"))) + "$")
                for p in config.get("alwaysShowGenres", [])]
    if any(p.match(g) for g in genres for p in patterns):
        return False
    return not genres or genres[0] in set(config.get("excludeGenres", []))


def acts_with_setlists(event: dict, setlists: dict) -> list[tuple[str, dict]]:
    """(artist, setlist) for each act on the bill, in bill order."""
    acts = []

    def add(name: str):
        entry = setlists.get(name)
        if not entry:
            return
        if entry.get("status") == "split":
            for part in entry.get("parts", []):
                add(part)
        elif entry.get("status") == "ok" and entry.get("songs"):
            acts.append((name, entry))

    for name in event.get("artists", []):
        add(name)
    return acts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="don't touch playlists")
    parser.add_argument("--limit", type=int, default=0, help="max events to handle")
    args = parser.parse_args()

    events = load_json(EVENTS_FILE, [])
    setlists = load_json(SETLISTS_FILE, {})
    playlists: dict = load_json(PLAYLISTS_FILE, {})
    tracks: dict = load_json(TRACKS_FILE, {})

    try:
        sp = Spotify()
    except RateLimited as e:
        print(f"  ! Spotify is rate-limiting this app: {e}. Skipping playlists.")
        return 0
    today = date.today().isoformat()
    handled = 0

    def save():
        # Song lookups are saved even in a dry run, so they aren't repeated.
        save_json(PLAYLISTS_FILE, dict(sorted(playlists.items())))
        save_json(TRACKS_FILE, dict(sorted(tracks.items())))

    try:
        # Gigs shown on the site by default first, hidden-genre gigs last,
        # so the nightly search budget goes where people actually look.
        config = load_json(GENRE_CONFIG_FILE, {})
        for event in sorted(events, key=lambda e: (hidden_by_default(e, config), e["date"])):
            if event["date"][:10] < today:
                continue
            acts = acts_with_setlists(event, setlists)
            if not acts:
                continue
            if args.limit and handled >= args.limit:
                break
            handled += 1

            # Support acts play first, so reverse the bill order.
            uris, expected = [], 0
            for artist, entry in reversed(acts):
                for song in entry["songs"]:
                    expected += 1
                    key = f"{artist}|||{song['name']}"
                    if key not in tracks:
                        uri = sp.find_track(song["name"], artist)
                        if uri is None and song.get("cover"):
                            uri = sp.find_track(song["name"], song["cover"])
                        tracks[key] = uri
                    if tracks[key] and tracks[key] not in uris:
                        uris.append(tracks[key])

            headliner = acts[0][0]
            when = datetime.fromisoformat(event["date"]).strftime("%-d.%-m.%Y") \
                if sys.platform != "win32" else \
                datetime.fromisoformat(event["date"]).strftime("%#d.%#m.%Y")
            print(f"{when} {event['artist'][:50]}: {len(uris)}/{expected} songs found")

            if len(uris) < MIN_TRACKS or len(uris) < expected * MIN_FOUND_SHARE:
                continue
            if args.dry_run:
                continue

            name = f"{headliner} – {event['venue']} {when}"[:100]
            description = (
                f"Expected setlist for {event['artist']} at {event['venue']}, "
                f"{event['city']} on {when}, based on recent setlist.fm setlists. "
                f"Updated nightly by darksuomi.fi"
            )[:300]
            digest = hashlib.sha1(("\n".join(uris) + name + description).encode()).hexdigest()

            key = event["ticketUrl"]
            existing = playlists.get(key)
            if existing and existing.get("hash") == digest:
                continue
            if existing:
                sp.call("PUT", f"/playlists/{existing['id']}",
                        json={"name": name, "description": description})
                playlist_id, url = existing["id"], existing["url"]
            else:
                # Development-mode apps must use /me/playlists and .../items;
                # the older /users/{id}/playlists and .../tracks return 403.
                created = sp.call("POST", "/me/playlists",
                                  json={"name": name, "description": description,
                                        "public": True})
                playlist_id, url = created["id"], created["external_urls"]["spotify"]
            sp.call("PUT", f"/playlists/{playlist_id}/items", json={"uris": uris[:100]})
            playlists[key] = {"id": playlist_id, "url": url, "hash": digest,
                              "tracks": len(uris)}
            print(f"   -> {'updated' if existing else 'created'} {url}")
            save()

    except RateLimited as e:
        # Expected when the per-run budget runs out; continue next night.
        print(f"  ! stopping early: {e}. Progress is saved.")
    finally:
        save()

    print(f"✓ {len(playlists)} playlists, {len(tracks)} song lookups cached, "
          f"{sp.searches} searches this run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
