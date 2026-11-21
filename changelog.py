#!/usr/bin/env python3
"""
Daily updates log: which gigs tonight's scrape found that weren't there before.

Run by the nightly job after the scrapers and genre tagging, before the data
is committed. It compares each city's events.json with the last commit
(`git show HEAD:<file>`): a gig whose id wasn't in the committed file is new.

  - frontend/data/updates.json gets a day entry (newest first, 120 days
    kept); a second run on the same day adds to that day's entry.
  - Only upcoming gigs the site shows by default (genres.shown_by_default)
    are listed; the others are just counted per city ("hidden").
  - With --mail-file, a plain-text email body is written there when there
    is something new (send_updates_email.py sends it).

Usage:
  python changelog.py
  python changelog.py --mail-file new-gigs.txt
  python changelog.py --dry-run          # print, save nothing
"""

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import genres as g
from eventstore import CITIES, DATA_DIR, events_file

ROOT = Path(__file__).resolve().parent
UPDATES_FILE = DATA_DIR / "updates.json"
KEEP_DAYS = 120
SITE = "https://www.darksuomi.fi"
CITY_NAMES = {"helsinki": "Helsinki & Espoo", "tampere": "Tampere", "oulu": "Oulu"}
CITY_PATHS = {"helsinki": "/", "tampere": "/tampere", "oulu": "/oulu"}


def committed_events(path: Path) -> list[dict] | None:
    """The file as in the last commit; None when it isn't in git (yet)."""
    rel = path.relative_to(ROOT).as_posix()
    try:
        out = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, check=True,
                             capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None
    return json.loads(out.decode("utf-8"))


def new_gigs(city: str, config: dict, today: str) -> tuple[list[dict], int]:
    path = events_file(city)
    if not path.exists():
        return [], 0
    old = committed_events(path)
    if old is None:
        return [], 0  # a brand-new city file: everything would look new
    known = {e.get("id") for e in old}
    current = json.loads(path.read_text(encoding="utf-8"))
    shown, hidden = [], 0
    for e in current:
        if e.get("id") in known or e["date"][:10] < today:
            continue
        if not g.shown_by_default(e.get("genres") or [], config):
            hidden += 1
            continue
        gig = {"id": e["id"], "city": city, "artist": e["artist"], "venue": e["venue"],
               "place": e.get("city", ""), "date": e["date"],
               "genres": (e.get("genres") or [])[:3]}
        if e.get("status"):
            gig["status"] = e["status"]
        shown.append(gig)
    shown.sort(key=lambda x: x["date"])
    return shown, hidden


def fi_date(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()]} {d.day}.{d.month}.{d.year}"


def mail_body(day: str, gigs: list[dict], hidden: dict[str, int]) -> str:
    lines = [f"Dark Suomi: {len(gigs)} new gig{'s' if len(gigs) != 1 else ''} "
             f"found on {fi_date(day)}", ""]
    for city in ("helsinki", *CITIES):
        mine = [x for x in gigs if x["city"] == city]
        if not mine:
            continue
        lines += [CITY_NAMES[city].upper(), ""]
        for x in mine:
            where = x["venue"] + (f", {x['place']}" if x["place"] not in ("", "Helsinki") else "")
            extra = f"  [{x['status']}]" if x.get("status") else ""
            lines.append(f"{fi_date(x['date'])}  {x['artist']}{extra}")
            lines.append(f"    {where} · {', '.join(x['genres'])}")
            lines.append(f"    {SITE}{CITY_PATHS[city]}#gig-{x['id']}")
        lines.append("")
    more = sum(hidden.values())
    if more:
        lines += [f"(+ {more} more not shown by the default genre filter)", ""]
    lines += [f"All daily updates: {SITE}/updates"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--mail-file", help="write an email body here when there are new gigs")
    parser.add_argument("--dry-run", action="store_true", help="print, save nothing")
    args = parser.parse_args()

    config = g.load_json(g.CONFIG_FILE, {})
    today = date.today().isoformat()
    gigs, hidden = [], {}
    for city in ("helsinki", *CITIES):
        shown, n_hidden = new_gigs(city, config, today)
        gigs += shown
        if n_hidden:
            hidden[city] = n_hidden
    print(f"✓ {len(gigs)} new gigs shown by default, {sum(hidden.values())} more hidden")
    if args.dry_run:
        print(mail_body(today, gigs, hidden))
        return 0

    log = g.load_json(UPDATES_FILE, [])
    entry = next((d for d in log if d["day"] == today), None)
    if gigs or hidden:
        if entry is None:
            entry = {"day": today, "gigs": [], "hidden": {}}
            log.append(entry)
        seen = {(x["city"], x["id"]) for x in entry["gigs"]}
        entry["gigs"] += [x for x in gigs if (x["city"], x["id"]) not in seen]
        entry["gigs"].sort(key=lambda x: x["date"])
        for city, n in hidden.items():
            entry["hidden"][city] = entry["hidden"].get(city, 0) + n
    cutoff = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    log = sorted((d for d in log if d["day"] >= cutoff), key=lambda d: d["day"], reverse=True)
    with open(UPDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if args.mail_file and gigs:
        Path(args.mail_file).write_text(mail_body(today, gigs, hidden), encoding="utf-8")
        print(f"✓ Email body written to {args.mail_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
