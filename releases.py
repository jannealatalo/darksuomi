#!/usr/bin/env python3
"""
Release radar for Dark Suomi: new and upcoming albums and EPs by the bands in
the band directory (every city's bands.json, one list for all), only those
in the Dark Suomi genres (the gig list's default genre filter).

- MusicBrainz finds the releases: each band's release groups of type Album or
  EP (no compilations, remixes, demos, DJ mixes or audio dramas), dated from
  WINDOW_DAYS ago onwards, which includes announced releases with a future
  date. The streaming links people have added to those releases on
  MusicBrainz (Spotify, Apple Music, Bandcamp, Deezer, Tidal…) come along.
- Deezer's free search API finds the album when MusicBrainz has no
  streaming link for it yet, and gives a cover when Cover Art Archive
  (MusicBrainz's covers) has none.
- song.link (Odesli) turns one streaming link into the others (Spotify,
  Apple Music, Tidal, Deezer, YouTube Music, Bandcamp, Amazon Music).

No Spotify API calls: the Dark Suomi Spotify app's development-mode quota
is needed for the playlists, and going over it blocks the app for a day.
Bands without a MusicBrainz ID are not covered.

Result: frontend/data/releases.json. Each band is re-checked every
RECHECK_DAYS days, within a time budget, so a run continues where the
previous one stopped.

Usage:
  python releases.py               # nightly run
  python releases.py --minutes 30  # a longer time budget (default 6 minutes)
"""

import argparse
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

from genres import USER_AGENT, _norm, load_json, save_json
from playlists import hidden_by_default

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "frontend" / "data"
RELEASES_FILE = DATA_DIR / "releases.json"
GENRE_CONFIG_FILE = DATA_DIR / "genre-config.json"
CITY_BAND_FILES = [DATA_DIR / "bands.json"] + [DATA_DIR / c / "bands.json"
                                                for c in ("tampere", "oulu", "turku")]

WINDOW_DAYS = 90             # keep releases from this many days back
RECHECK_DAYS = 3             # look at each band this often
LINKS_RECHECK_DAYS = 7       # look again for links of a release that has none
TIME_BUDGET_SECONDS = 6 * 60
SKIP_SECONDARY = {"Compilation", "Remix", "DJ-mix", "Mixtape/Street", "Demo", "Interview",
                  "Audiobook", "Audio drama", "Spokenword", "Field recording"}
# Episode series ("Folge 3: …") are audio dramas even when not tagged so.
SKIP_TITLE = re.compile(r"^(folge|episode|kapitel|chapter)\s+\d+\b", re.I)
MAX_ODESLI_CALLS = 30        # song.link allows ~10/minute without a key
ODESLI_DELAY = 6.5
ODESLI_PLATFORMS = {"spotify": "spotify", "appleMusic": "apple", "tidal": "tidal",
                    "deezer": "deezer", "youtubeMusic": "youtubeMusic",
                    "bandcamp": "bandcamp", "amazonMusic": "amazon"}

_last_mb = 0.0


def mb_get(path: str, params: dict) -> dict | None:
    """MusicBrainz GET, at most 1 request/second."""
    global _last_mb
    for attempt in range(3):
        wait = 1.1 - (time.time() - _last_mb)
        if wait > 0:
            time.sleep(wait)
        _last_mb = time.time()
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


def directory_bands() -> list[dict]:
    """Every directory band in the Dark Suomi genres with a MusicBrainz ID,
    once: {id (the MBID), display, genres}."""
    config = load_json(GENRE_CONFIG_FILE, {})
    out: dict[str, dict] = {}
    for path in CITY_BAND_FILES:
        for key, b in load_json(path, {}).items():
            mbid = b.get("mbid")
            if not mbid or mbid in out or hidden_by_default({"genres": b.get("genres")}, config):
                continue
            out[mbid] = {"id": mbid, "display": b.get("display") or key,
                         "genres": b.get("genres") or []}
    return list(out.values())


def mb_releases(mbid: str, since: str) -> list[dict]:
    """The artist's albums and EPs first released on or after `since`."""
    found, offset = [], 0
    while True:
        data = mb_get("release-group", {"artist": mbid, "type": "album|ep",
                                        "limit": 100, "offset": offset})
        if not data:
            break
        for rg in data.get("release-groups", []):
            when = rg.get("first-release-date") or ""
            secondary = set(rg.get("secondary-types") or [])
            if not when or when < since[:len(when)] or SKIP_SECONDARY & secondary \
                    or SKIP_TITLE.match(rg["title"]):
                continue
            kind = rg.get("primary-type") or "Album"
            if "Live" in secondary:
                kind = f"Live {kind.lower()}"
            found.append({"id": rg["id"], "title": rg["title"], "type": kind, "date": when,
                          "musicbrainz": f"https://musicbrainz.org/release-group/{rg['id']}"})
        offset += 100
        if offset >= data.get("release-group-count", 0) or offset >= 300:
            break
    # One per title: a band's release can be entered twice (two editions).
    seen, unique = set(), []
    for r in sorted(found, key=lambda r: r["date"]):
        if _norm(r["title"]) not in seen:
            seen.add(_norm(r["title"]))
            unique.append(r)
    return unique


def link_kind(url: str) -> str | None:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host == "open.spotify.com" and "/album/" in url:
        return "spotify"
    if host == "music.apple.com" and "/album/" in url:
        return "apple"
    if host.endswith("bandcamp.com") and "/album/" in url:
        return "bandcamp"
    if host == "deezer.com" and "/album/" in url:
        return "deezer"
    if host.endswith("tidal.com") and "/album/" in url:
        return "tidal"
    if host == "music.youtube.com":
        return "youtubeMusic"
    return None


def mb_release_links(rg_id: str) -> dict:
    """Streaming links of the release group's releases on MusicBrainz."""
    data = mb_get("release", {"release-group": rg_id, "inc": "url-rels", "limit": 25}) or {}
    links: dict[str, str] = {}
    for release in data.get("releases", []):
        for rel in release.get("relations", []):
            url = rel.get("url", {}).get("resource", "")
            kind = link_kind(url)
            if kind and kind not in links:
                links[kind] = url
    return links


def cover_url(rg_id: str) -> str | None:
    """The Cover Art Archive front cover (250 px), if there is one."""
    url = f"https://coverartarchive.org/release-group/{rg_id}/front-250"
    try:
        resp = requests.head(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    except requests.RequestException:
        return None
    return url if resp.status_code in (200, 302, 307) else None


def deezer_album(band: str, title: str) -> dict | None:
    """The album on Deezer (free API, no key): {link, cover}, if found."""
    resp = requests.get("https://api.deezer.com/search/album", params={"q": f"{band} {title}"},
                        headers={"User-Agent": USER_AGENT}, timeout=20)
    time.sleep(0.3)
    if resp.status_code >= 400:
        return None
    want = re.sub(r"\s*[(\[].*$", "", title)
    for a in (resp.json() or {}).get("data") or []:
        if _norm(a["artist"]["name"]) == _norm(band) and _norm(re.sub(r"\s*[(\[].*$", "", a["title"])) == _norm(want):
            return {"link": a["link"], "cover": a.get("cover_medium")}
    return None


def odesli_links(url: str) -> dict | None:
    resp = requests.get("https://api.song.link/v1-alpha.1/links",
                        params={"url": url, "userCountry": "FI"},
                        headers={"User-Agent": USER_AGENT}, timeout=20)
    time.sleep(ODESLI_DELAY)
    if resp.status_code == 429:
        raise RuntimeError("song.link rate limit")
    if resp.status_code >= 400:
        return {}
    by = resp.json().get("linksByPlatform", {})
    return {ours: by[theirs]["url"] for theirs, ours in ODESLI_PLATFORMS.items() if theirs in by}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--minutes", type=float, default=TIME_BUDGET_SECONDS / 60)
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60

    today = date.today()
    since = (today - timedelta(days=WINDOW_DAYS)).isoformat()
    recheck = (today - timedelta(days=RECHECK_DAYS)).isoformat()
    links_recheck = (today - timedelta(days=LINKS_RECHECK_DAYS)).isoformat()
    data = load_json(RELEASES_FILE, {})
    checked: dict[str, str] = data.get("checked", {})
    # (Ids other than MusicBrainz ones are from an earlier version: dropped.)
    releases: dict[str, dict] = {r["id"]: r for r in data.get("releases", [])
                                 if ":" not in r["id"]}

    bands = directory_bands()
    current = {b["id"] for b in bands}
    todo = sorted((b for b in bands if checked.get(b["id"], "") < recheck),
                  key=lambda b: checked.get(b["id"], ""))
    print(f"{len(bands)} bands, {len(todo)} due")
    odesli_calls = looked = 0

    def save():
        keep = [r for r in releases.values()
                if r["date"] >= since[:len(r["date"])] and r["bandId"] in current]
        keep.sort(key=lambda r: (r["date"], r["band"].casefold()))
        save_json(RELEASES_FILE, {"checked": dict(sorted(checked.items())), "releases": keep})

    try:
        for band in todo:
            if time.time() > deadline:
                print("  ! time budget used; the rest next run")
                break
            looked += 1
            found = mb_releases(band["id"], since)
            ids = {r["id"] for r in found}
            # Releases MusicBrainz no longer lists for the band (moved, merged).
            for rid in [k for k, r in releases.items() if r["bandId"] == band["id"] and k not in ids]:
                del releases[rid]
            for r in found:
                releases[r["id"]] = {**releases.get(r["id"], {}), **r, "band": band["display"],
                                     "bandId": band["id"], "genres": band["genres"][:5]}
            checked[band["id"]] = today.isoformat()
            if found:
                print(f"  {band['display']}: " + ", ".join(f"{r['title']} ({r['date']})" for r in found))

        # Links and cover, per release: again after a week while none are known
        # (MusicBrainz editors and the services add them around release day).
        for r in releases.values():
            if time.time() > deadline + 180:
                break
            if r.get("linksChecked") and (r.get("links") or r["linksChecked"] > links_recheck):
                continue
            links = {**r.get("links", {}), **mb_release_links(r["id"])}
            out = r["date"] <= today.isoformat()[:len(r["date"])]
            deezer = deezer_album(r["band"], r["title"]) if out and not links else None
            if deezer:
                links["deezer"] = deezer["link"]
            if not r.get("cover"):
                r["cover"] = cover_url(r["id"]) or (deezer or {}).get("cover")
            r["links"] = links
            r["linksChecked"] = today.isoformat()

        # The other services from one known link, once per release (song.link
        # allows only a few lookups a minute, so the rest wait for the next run).
        for r in releases.values():
            links = r.get("links") or {}
            source = links.get("spotify") or links.get("apple") or links.get("deezer") \
                or links.get("tidal")
            if not source or r.get("songLink") or odesli_calls >= MAX_ODESLI_CALLS \
                    or time.time() > deadline + 300:
                continue
            odesli_calls += 1
            r["links"] = {**(odesli_links(source) or {}), **links}
            r["songLink"] = today.isoformat()
    except Exception as e:  # noqa: BLE001 - keep what we have
        print(f"  ! stopping early: {e}. Progress is saved.")
    finally:
        save()
    print(f"✓ {len(releases)} releases; {looked} bands looked up, {odesli_calls} song.link lookups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
