#!/usr/bin/env python3
"""
Keeps the Dark Suomi Discord's Events list (the "N Events" pop-up at the
top of the channel list) in step with the site: the next 20 gigs of the
default genres in all cities, as Discord scheduled events with the venue
as location and links to darksuomi.fi and the tickets.

Each run creates the missing ones, updates changed ones (time, sold out…)
and deletes the bot's events that are no longer among the next 20. Every
event's description ends with the gig's darksuomi.fi link, which is how the
script recognises its own events; events made by hand are left alone.

Needs DISCORD_BOT_TOKEN (see discord_setup.py). Without --apply it only
prints what it would do.

Usage:
  python discord_events.py            # dry run
  python discord_events.py --apply
"""

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone

import genres as g
from changelog import CITY_PATHS, SITE
from discord_setup import Discord, windows_user_env
from eventstore import CITIES, load_events

import os

HOW_MANY = 20
GIG_HOURS = 3  # Discord needs an end time for events at a place
MARKER = re.compile(r"https://www\.darksuomi\.fi\S*#gig-[\w-]+")


def helsinki_to_utc(local: datetime) -> datetime:
    """Finnish local time -> UTC (EET +2, EEST +3 from the last Sunday of
    March to the last Sunday of October, switching at 01:00 UTC)."""
    def last_sunday(month: int) -> datetime:
        d = datetime(local.year, month, 31 if month in (3, 10) else 30)
        return d - timedelta(days=(d.weekday() + 1) % 7)
    utc_guess = local - timedelta(hours=3)
    summer = last_sunday(3) + timedelta(hours=1) <= utc_guess < last_sunday(10) + timedelta(hours=1)
    return (local - timedelta(hours=3 if summer else 2)).replace(tzinfo=timezone.utc)


def upcoming(config: dict, now: datetime) -> list[dict]:
    """The next gigs of the default genres in all cities, soonest first."""
    gigs = []
    for city in ("helsinki", *CITIES):
        for e in load_events(city):
            if e.get("status") == "cancelled" or not g.shown_by_default(e.get("genres", []), config):
                continue
            local = datetime.fromisoformat(e["date"][:19])
            no_time = local.hour == 0 and local.minute == 0
            if no_time:
                local = local.replace(hour=20)
            start = helsinki_to_utc(local)
            if start < now + timedelta(minutes=15):  # Discord wants a start in the future
                continue
            gigs.append({**e, "_city": city, "_start": start, "_noTime": no_time})
    gigs.sort(key=lambda e: (e["_start"], e["artist"].casefold()))
    return gigs[:HOW_MANY]


def event_body(e: dict) -> dict:
    url = f"{SITE}{CITY_PATHS[e['_city']]}#gig-{e['id']}"
    name = e["artist"]
    if e.get("status") == "sold out":
        name = f"SOLD OUT: {name}"
    place = e["venue"] if e.get("city", "") in e["venue"] else f"{e['venue']}, {e.get('city', '')}".strip(", ")
    lines = []
    if e["_noTime"]:
        lines.append("Time not announced yet.")
    elif e.get("doors"):
        lines.append(f"Doors {e['doors']}")
    facts = [", ".join(e.get("genres", [])[:4]), e.get("price", ""), e.get("age", "")]
    if any(facts):
        lines.append(" · ".join(f for f in facts if f))
    if e.get("ticketUrl") and e["ticketUrl"] != e.get("eventUrl"):
        lines.append(f"Tickets: {e['ticketUrl']}")
    elif e.get("eventUrl"):
        lines.append(f"Venue: {e['eventUrl']}")
    lines.append(f"Dark Suomi: {url}")
    description = "\n".join(lines)
    if len(description) > 1000:  # keep the marker link
        description = description[: 990 - len(url)] + "…\n" + url
    return {
        "name": name[:100],
        "privacy_level": 2,
        "entity_type": 3,  # external: at a place, not in a Discord channel
        "entity_metadata": {"location": place[:100]},
        "scheduled_start_time": e["_start"].isoformat(),
        "scheduled_end_time": (e["_start"] + timedelta(hours=GIG_HOURS)).isoformat(),
        "description": description,
    }


def differs(current: dict, body: dict) -> list[str]:
    def t(v: str) -> datetime:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    changed = [k for k in ("name", "description") if (current.get(k) or "") != body[k]]
    if (current.get("entity_metadata") or {}).get("location") != body["entity_metadata"]["location"]:
        changed.append("location")
    for k in ("scheduled_start_time", "scheduled_end_time"):
        if not current.get(k) or t(current[k]) != t(body[k]):
            changed.append(k.split("_")[1])
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--apply", action="store_true", help="make the changes (default: dry run)")
    args = parser.parse_args()

    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip() or windows_user_env("DISCORD_BOT_TOKEN")
    if not token:
        print("DISCORD_BOT_TOKEN not set; Discord events skipped.")
        return 0
    dc = Discord(token, args.apply)
    me = dc.call("GET", "/users/@me")
    gid = dc.call("GET", "/users/@me/guilds")[0]["id"]

    config = g.load_json(g.CONFIG_FILE, {})
    now = datetime.now(timezone.utc)
    wanted = {}
    for e in upcoming(config, now):
        body = event_body(e)
        wanted[MARKER.search(body["description"]).group(0)] = body

    mine = {}
    for ev in dc.call("GET", f"/guilds/{gid}/scheduled-events"):
        m = MARKER.search(ev.get("description") or "")
        if ev.get("creator_id") == me["id"] and m:
            if m.group(0) in mine:  # a duplicate from an interrupted run
                dc.call("DELETE", f"/guilds/{gid}/scheduled-events/{ev['id']}",
                        change=f"delete duplicate '{ev['name']}'")
                continue
            mine[m.group(0)] = ev

    for key, ev in mine.items():
        if key not in wanted:
            dc.call("DELETE", f"/guilds/{gid}/scheduled-events/{ev['id']}",
                    change=f"delete '{ev['name']}' (no longer among the next {HOW_MANY})")
    for key, body in wanted.items():
        ev = mine.get(key)
        when = body["scheduled_start_time"][:16]
        if ev is None:
            dc.call("POST", f"/guilds/{gid}/scheduled-events", body, f"create {when} '{body['name']}'")
        else:
            changed = differs(ev, body)
            if changed:
                dc.call("PATCH", f"/guilds/{gid}/scheduled-events/{ev['id']}", body,
                        f"update '{body['name']}': {', '.join(changed)}")
    print(f"✓ Discord events: the next {len(wanted)} gigs" if args.apply
          else "Dry run: nothing changed. Run with --apply to make these changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
