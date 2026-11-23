#!/usr/bin/env python3
"""
Weekly Instagram post for @darksuomievents: "GIGS THIS WEEK", the next
7 days' gigs (bands · venue, grouped by day) in Helsinki, Tampere and Oulu,
as one post of 1–10 pictures (1080x1350) plus a caption.

The gigs are the site's default genres, cancelled ones left out. Cities
share a picture while they fit; a busy city continues on the next picture.

Pictures are drawn as HTML and screenshotted with headless Chrome or Edge,
then saved as JPEG (Instagram takes only JPEG) to instagram/<start date>/
together with caption.txt. Instagram's API fetches pictures from a public
URL, so --post uses the copies on GitHub (raw.githubusercontent.com): the
workflow commits and pushes the folder before posting.

Needs INSTAGRAM_ACCESS_TOKEN for --check and --post: the token from the
Meta app "DarkSuomi Poster" (Instagram API with Unified Login). The
Instagram account is looked up with it, so no account ID is needed.

Usage:
  python instagram_post.py                    # build this week's pictures (draft)
  python instagram_post.py --start 2026-11-30 # another week
  python instagram_post.py --check            # does the token work?
  python instagram_post.py --post             # build, then publish (pushed first!)
  python instagram_post.py --post --no-build  # publish the already built folder
"""

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

import genres as g
from eventstore import CITIES, load_events

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "instagram"
LOGO = ROOT / "frontend" / "public" / "logo.webp"
RAW_BASE = "https://raw.githubusercontent.com/jannealatalo/darksuomi/main/instagram"
GRAPH = "https://graph.facebook.com/v27.0"
USERNAME = "darksuomievents"
KEEP_WEEKS = 8  # older folders under instagram/ are removed

CITY_TITLES = {"helsinki": "HELSINKI", "tampere": "TAMPERE", "oulu": "OULU"}
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

# Picture layout in pixels (must match CSS below). The list area is what's
# left of 1350 after padding, the header and the footer.
WIDTH, HEIGHT = 1080, 1350
LIST_HEIGHT = 1350 - 2 * 48 - 150 - 60
CITY_H, DAY_H, GIG_H = 62, 44, 30
MAX_PICTURES = 10  # Instagram's carousel limit

CSS = """
*{margin:0;box-sizing:border-box} html,body{background:#000;width:1080px;height:1350px;overflow:hidden}
.card{width:1080px;height:1350px;padding:48px 64px;
 background:radial-gradient(ellipse at top,#2a0a3d 0%,#0b0610 55%,#000 100%);
 color:#e5e7eb;font-family:'Segoe UI','Noto Sans','DejaVu Sans','Liberation Sans',Arial,sans-serif;
 display:flex;flex-direction:column;overflow:hidden}
.head{display:flex;align-items:center;gap:28px;height:150px;padding-bottom:22px}
.head img{width:128px;height:128px}
.t1{font-size:56px;font-weight:800;color:#c084fc;letter-spacing:2px;white-space:nowrap}
.t2{font-size:30px;color:#9ca3af;margin-top:4px;white-space:nowrap}
.list{height:LIST_HEIGHTpx;overflow:hidden}
.city{height:62px;padding-top:16px;font-size:38px;line-height:46px;font-weight:800;color:#f472b6;letter-spacing:3px}
.day{height:44px;padding-top:12px;font-size:24px;line-height:32px;font-weight:700;color:#a855f7;letter-spacing:2px}
.gig{height:30px;font-size:24px;line-height:30px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.b{color:#f3f4f6;font-weight:600}.v{color:#9ca3af}
.foot{margin-top:auto;height:60px;padding-top:24px;font-size:26px;color:#a855f7;text-align:center;letter-spacing:1px}
""".replace("LIST_HEIGHT", str(LIST_HEIGHT))


# --- Gigs ------------------------------------------------------------------

def week_gigs(start: date) -> dict[str, list[dict]]:
    """The default-genre gigs of start..start+6 per city, in date order."""
    config = g.load_json(g.CONFIG_FILE, {})
    end = start + timedelta(days=7)
    out = {}
    for city in ("helsinki", *CITIES):
        gigs = [e for e in load_events(city)
                if e.get("status") != "cancelled"
                and start.isoformat() <= e["date"][:10] < end.isoformat()
                and g.shown_by_default(e.get("genres", []), config)]
        gigs.sort(key=lambda e: (e["date"], e["artist"].casefold()))
        if gigs:
            out[city] = gigs
    return out


def gig_name(e: dict) -> str:
    return ", ".join(e["artists"]) if e.get("artists") else e["artist"]


def date_range(start: date) -> str:
    end = start + timedelta(days=6)
    if start.month == end.month:
        return f"{start.day}.–{end.day}.{end.month}."
    return f"{start.day}.{start.month}.–{end.day}.{end.month}."


# --- Pictures --------------------------------------------------------------

def paginate(by_city: dict[str, list[dict]]) -> list[list[tuple]]:
    """Splits the week into pictures. Each picture is a list of rows:
    ("city", name) / ("day", date) / ("gig", event). A city shares the
    current picture only if it fits there whole; otherwise it starts a new
    one, and a city longer than a picture continues on the next one, split
    between days (a day only if it alone is longer than a picture)."""
    pages: list[list[tuple]] = [[]]
    used = 0

    def new_page():
        nonlocal used
        pages.append([])
        used = 0

    for city, gigs in by_city.items():
        days: dict[str, list[dict]] = {}
        for e in gigs:
            days.setdefault(e["date"][:10], []).append(e)
        city_h = CITY_H + sum(DAY_H + GIG_H * len(v) for v in days.values())
        if used > 0 and used + city_h > LIST_HEIGHT:
            new_page()
        city_on_page = False
        for day, events in days.items():
            need = (0 if city_on_page else CITY_H) + DAY_H + GIG_H * len(events)
            if used + need > LIST_HEIGHT and used > 0:
                new_page()
                city_on_page = False
                need = CITY_H + DAY_H + GIG_H * len(events)
            if not city_on_page:
                pages[-1].append(("city", city))
                used += CITY_H
                city_on_page = True
            pages[-1].append(("day", day))
            used += DAY_H
            for e in events:
                if used + GIG_H > LIST_HEIGHT:  # one huge day: continue on a new picture
                    new_page()
                    pages[-1] += [("city", city), ("day", day)]
                    used = CITY_H + DAY_H
                pages[-1].append(("gig", e))
                used += GIG_H
    return [p for p in pages if p]


def page_html(rows: list[tuple], start: date) -> str:
    cities = []
    for kind, value in rows:
        if kind == "city" and CITY_TITLES[value] not in cities:
            cities.append(CITY_TITLES[value])
    body = []
    for kind, value in rows:
        if kind == "city":
            body.append(f'<div class="city">{CITY_TITLES[value]}</div>')
        elif kind == "day":
            d = date.fromisoformat(value)
            body.append(f'<div class="day">{DAYS[d.weekday()]} {d.day}.{d.month}.</div>')
        else:
            body.append(f'<div class="gig"><span class="b">{html.escape(gig_name(value))}</span>'
                        f' <span class="v">· {html.escape(value["venue"])}</span></div>')
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="card"><div class="head"><img src="{LOGO.as_uri()}"><div>'
            f'<div class="t1">GIGS THIS WEEK</div>'
            f'<div class="t2">{" &amp; ".join(cities)} · {date_range(start)}</div></div></div>'
            f'<div class="list">{"".join(body)}</div>'
            f'<div class="foot">All gigs &amp; tickets: darksuomi.fi</div></div></body></html>')


def find_browser() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        if path := shutil.which(name):
            return path
    for path in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        if Path(path).exists():
            return path
    raise SystemExit("No Chrome, Chromium or Edge found for drawing the pictures.")


def screenshot(browser: str, html_file: Path, png: Path, profile: Path) -> None:
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--no-first-run", "--no-sandbox",
                    f"--user-data-dir={profile}", f"--window-size={WIDTH},{HEIGHT}",
                    f"--screenshot={png}", html_file.as_uri()],
                   check=True, capture_output=True, timeout=120)
    # Edge on Windows may hand the work to another process and return early.
    for _ in range(60):
        if png.exists() and png.stat().st_size > 0:
            time.sleep(0.5)  # let it finish writing
            return
        time.sleep(0.5)
    raise SystemExit(f"The browser didn't write {png.name}.")


def caption(by_city: dict[str, list[dict]], start: date) -> str:
    counts = " · ".join(f"{CITY_TITLES[c].title()} {len(gs)}" for c, gs in by_city.items())
    tags = ["#darksuomi", "#keikat", "#livemusic", "#metal", "#punk", "#goth", "#rock"]
    tags += ["#" + c for c in by_city]
    return (f"🦇 GIGS THIS WEEK · {date_range(start)}\n\n"
            f"{counts} gigs — swipe through the week 👉\n\n"
            "Full list, tickets and setlists: darksuomi.fi (link in bio)\n"
            "Something missing? Tell us in the comments.\n\n"
            + " ".join(tags))


def build(start: date) -> Path | None:
    from PIL import Image

    by_city = week_gigs(start)
    if not by_city:
        print(f"No gigs for {date_range(start)}: nothing to post.")
        return None
    pages = paginate(by_city)
    if len(pages) > MAX_PICTURES:
        print(f"{len(pages)} pictures is over Instagram's {MAX_PICTURES}; the rest are left out.")
        pages = pages[:MAX_PICTURES]

    folder = OUT_DIR / start.isoformat()
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    browser = find_browser()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, rows in enumerate(pages, 1):
            html_file = tmp_dir / f"{i}.html"
            html_file.write_text(page_html(rows, start), encoding="utf-8")
            png = tmp_dir / f"{i}.png"
            screenshot(browser, html_file, png, tmp_dir / "profile")
            with Image.open(png) as im:
                im.convert("RGB").crop((0, 0, WIDTH, HEIGHT)).save(
                    folder / f"{i}.jpg", "JPEG", quality=90, optimize=True)
    (folder / "caption.txt").write_text(caption(by_city, start) + "\n", encoding="utf-8")

    # Keep the last weeks only.
    for old in OUT_DIR.iterdir():
        try:
            if old.is_dir() and date.fromisoformat(old.name) < start - timedelta(weeks=KEEP_WEEKS):
                shutil.rmtree(old)
        except ValueError:
            pass

    total = sum(len(v) for v in by_city.values())
    print(f"{total} gigs on {len(pages)} picture(s) in {folder.relative_to(ROOT)}")
    return folder


# --- Instagram API ---------------------------------------------------------

def api(method: str, path: str, **params) -> dict:
    params["access_token"] = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    r = requests.request(method, f"{GRAPH}/{path}", params=params, timeout=60)
    data = r.json() if r.content else {}
    if not r.ok or "error" in data:
        err = data.get("error", {})
        raise SystemExit(f"Instagram API {method} /{path}: HTTP {r.status_code} "
                         f"{err.get('message', r.text[:300])} (code {err.get('code')})")
    return data


def account_id() -> str:
    data = api("GET", "me/assigned_instagram_accounts", fields="id,username").get("data", [])
    for a in data:
        if a.get("username", "").lower() == USERNAME:
            return a["id"]
    if len(data) == 1:
        return data[0]["id"]
    raise SystemExit(f"The token gives no access to @{USERNAME} (accounts: "
                     f"{[a.get('username') for a in data]}).")


def wait_ready(container: str) -> None:
    for _ in range(30):
        status = api("GET", container, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Instagram couldn't process media {container}: {status}")
        time.sleep(5)
    raise SystemExit(f"Instagram media {container} still not ready.")


def publish(folder: Path) -> None:
    ig = account_id()
    pictures = sorted(folder.glob("*.jpg"), key=lambda p: int(p.stem))
    text = (folder / "caption.txt").read_text(encoding="utf-8").strip()
    urls = [f"{RAW_BASE}/{folder.name}/{p.name}" for p in pictures]
    for url in urls:  # pushed and reachable?
        if requests.head(url, timeout=30).status_code != 200:
            raise SystemExit(f"{url} isn't reachable: push the folder first.")

    if len(urls) == 1:
        container = api("POST", f"{ig}/media", image_url=urls[0], caption=text)["id"]
    else:
        children = [api("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"]
                    for u in urls]
        for c in children:
            wait_ready(c)
        container = api("POST", f"{ig}/media", media_type="CAROUSEL",
                        children=",".join(children), caption=text)["id"]
    wait_ready(container)
    media = api("POST", f"{ig}/media_publish", creation_id=container)["id"]
    link = api("GET", media, fields="permalink").get("permalink", media)
    print(f"Posted {len(urls)} picture(s): {link}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, help="first day (default: today)")
    p.add_argument("--check", action="store_true", help="only check the token and account")
    p.add_argument("--post", action="store_true", help="publish to Instagram")
    p.add_argument("--no-build", action="store_true", help="publish the folder built earlier")
    args = p.parse_args()

    if (args.check or args.post) and not os.environ.get("INSTAGRAM_ACCESS_TOKEN"):
        print("INSTAGRAM_ACCESS_TOKEN is not set.", file=sys.stderr)
        return 1
    if args.check:
        ig = account_id()
        info = api("GET", ig, fields="username,media_count")
        print(f"Token works: @{info.get('username')} ({info.get('media_count')} posts), id {ig}")
        return 0

    start = args.start or datetime.now().date()
    folder = OUT_DIR / start.isoformat()
    if not args.no_build:
        folder = build(start)
        if folder is None:
            return 0
    if args.post:
        if not (folder / "caption.txt").exists():
            print(f"Nothing built in {folder}.", file=sys.stderr)
            return 1
        publish(folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
