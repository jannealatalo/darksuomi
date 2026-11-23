#!/usr/bin/env python3
"""
Dark Suomi's recommended bands: the artists the Dark Suomi Spotify account
follows. Follow a band there and its gigs show up under "Filter what
DarkSuomi recommends" on the site after the next nightly run.

Writes the lowercased artist names to frontend/data/recommended.json.
Uses the same Spotify app and refresh token as playlists.py; the token needs
the user-follow-read scope (run spotify_authorize.py again if Spotify
answers 403). On failure the file is left as it was.

Usage:
  python recommended.py
"""

import sys

import requests

from genres import save_json
from playlists import DATA_DIR, RateLimited, Spotify

RECOMMENDED_FILE = DATA_DIR / "recommended.json"


def followed_artists(spotify: Spotify) -> list[str]:
    names: set[str] = set()
    after = None
    while True:
        params = {"type": "artist", "limit": 50}
        if after:
            params["after"] = after
        data = spotify.call("GET", "/me/following", params=params)["artists"]
        names.update(a["name"].lower() for a in data.get("items", []))
        after = (data.get("cursors") or {}).get("after")
        if not after:
            return sorted(names)


def main() -> int:
    try:
        spotify = Spotify()
        artists = followed_artists(spotify)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (401, 403):
            print("Spotify refused to list the followed artists: the token probably "
                  "lacks the user-follow-read scope. Run spotify_authorize.py again "
                  "and update the SPOTIFY_PLAYLIST_REFRESH_TOKEN secret.",
                  file=sys.stderr)
        print(e, file=sys.stderr)
        return 1
    except RateLimited as e:
        print(e, file=sys.stderr)
        return 1

    save_json(RECOMMENDED_FILE, {"artists": artists})
    print(f"{len(artists)} recommended artists (followed by the Dark Suomi account)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
