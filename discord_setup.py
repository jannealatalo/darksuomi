#!/usr/bin/env python3
"""
Sets up the Dark Suomi Discord server from discord/setup.json: server
settings, roles, categories and channels with their permissions, AutoMod
rules, the #announcements webhook and the pinned rules messages.

Safe to run again: things that exist (matched by name) are updated, nothing
is duplicated. Without --apply it only prints what it would do.

Needs a bot that is in the server with the Administrator permission, its
token in DISCORD_BOT_TOKEN (an environment variable; on Windows the user
variable is read too).

Usage:
  python discord_setup.py                    # dry run: print the plan
  python discord_setup.py --apply            # make the changes
  python discord_setup.py --apply --messages # ...and post/update the pinned messages
  python discord_setup.py --apply --remove   # ...and delete the channels in "remove"
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "discord" / "setup.json"
API = "https://discord.com/api/v10"
UA = "DiscordBot (https://darksuomi.fi, 1.0)"

PERMS = {
    "KICK_MEMBERS": 1 << 1, "BAN_MEMBERS": 1 << 2, "ADD_REACTIONS": 1 << 6,
    "VIEW_AUDIT_LOG": 1 << 7, "VIEW_CHANNEL": 1 << 10, "SEND_MESSAGES": 1 << 11,
    "MANAGE_MESSAGES": 1 << 13, "MANAGE_NICKNAMES": 1 << 27, "MANAGE_THREADS": 1 << 34,
    "CREATE_PUBLIC_THREADS": 1 << 35, "CREATE_PRIVATE_THREADS": 1 << 36,
    "SEND_MESSAGES_IN_THREADS": 1 << 38, "MODERATE_MEMBERS": 1 << 40,
}
NO_POSTING = (PERMS["SEND_MESSAGES"] | PERMS["CREATE_PUBLIC_THREADS"]
              | PERMS["CREATE_PRIVATE_THREADS"] | PERMS["SEND_MESSAGES_IN_THREADS"])
TEXT, VOICE, CATEGORY = 0, 2, 4
NOTIFICATIONS = {"all": 0, "mentions": 1}
PRESETS = {"PROFANITY": 1, "SEXUAL_CONTENT": 2, "SLURS": 3}


def windows_user_env(name: str) -> str:
    if os.name != "nt":
        return ""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::GetEnvironmentVariable('{name}','User')"],
        capture_output=True, text=True)
    return out.stdout.strip()


def save_windows_user_env(name: str, value: str) -> bool:
    if os.name != "nt":
        return False
    # The value goes through the child's environment, not its command line.
    env = dict(os.environ, DS_VALUE=value)
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::SetEnvironmentVariable('{name}', $env:DS_VALUE, 'User')"],
        env=env, capture_output=True, text=True)
    return out.returncode == 0


class Discord:
    def __init__(self, token: str, apply: bool):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bot {token}", "User-Agent": UA})
        self.apply = apply

    def call(self, method: str, path: str, body=None, change: str | None = None):
        """GET always; other methods only with --apply (else print `change`)."""
        if method != "GET":
            print(("  ✓ " if self.apply else "  would ") + (change or f"{method} {path}"))
            if not self.apply:
                return None
        for _ in range(5):
            r = self.s.request(method, API + path, json=body, timeout=30)
            if r.status_code == 429:
                time.sleep(float(r.json().get("retry_after", 1)) + 0.2)
                continue
            if r.status_code >= 400:
                raise SystemExit(f"Discord API {method} {path}: {r.status_code} {r.text[:300]}")
            return r.json() if r.content else None
        raise SystemExit(f"Discord API {method} {path}: rate limited")


def overwrite(target_id: str, allow: int = 0, deny: int = 0) -> dict:
    return {"id": target_id, "type": 0, "allow": str(allow), "deny": str(deny)}


def same_overwrites(a: list, b: list) -> bool:
    key = lambda o: (o["id"], int(o["allow"]), int(o["deny"]))
    return sorted(map(key, a)) == sorted(map(key, b))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--apply", action="store_true", help="make the changes (default: dry run)")
    parser.add_argument("--messages", action="store_true", help="post/update the pinned messages")
    parser.add_argument("--remove", action="store_true", help='delete the channels listed in "remove"')
    args = parser.parse_args()

    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip() or windows_user_env("DISCORD_BOT_TOKEN")
    if not token:
        print("DISCORD_BOT_TOKEN is not set.", file=sys.stderr)
        return 1
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    dc = Discord(token, args.apply)
    me = dc.call("GET", "/users/@me")
    guilds = dc.call("GET", "/users/@me/guilds")
    if len(guilds) != 1:
        print(f"The bot is in {len(guilds)} servers; expected exactly one.", file=sys.stderr)
        return 1
    gid = guilds[0]["id"]
    guild = dc.call("GET", f"/guilds/{gid}")
    print(f"Server: {guild['name']} ({'applying' if args.apply else 'dry run'})")

    # --- Server settings -----------------------------------------------------
    s = cfg["server"]
    want = {"name": s["name"], "verification_level": s["verificationLevel"],
            "explicit_content_filter": s["explicitContentFilter"],
            "default_message_notifications": NOTIFICATIONS[s["defaultNotifications"]]}
    patch = {k: v for k, v in want.items() if guild.get(k) != v}
    if s.get("icon") and not guild.get("icon"):
        data = base64.b64encode((ROOT / s["icon"]).read_bytes()).decode()
        patch["icon"] = f"data:image/png;base64,{data}"
    if patch:
        dc.call("PATCH", f"/guilds/{gid}", patch,
                f"server settings: {', '.join(sorted(patch))}")

    # --- Roles ---------------------------------------------------------------
    roles = {r["name"]: r for r in guild["roles"]}
    everyone = gid  # the @everyone role has the server's id
    for spec in cfg["roles"]:
        perms = sum(PERMS[p] for p in spec["permissions"])
        body = {"name": spec["name"], "permissions": str(perms), "hoist": spec.get("hoist", False),
                "color": int(spec.get("color", "#000000").lstrip("#"), 16), "mentionable": True}
        role = roles.get(spec["name"])
        if role is None:
            roles[spec["name"]] = dc.call("POST", f"/guilds/{gid}/roles", body,
                                          f"create role {spec['name']}") or {"id": f"<{spec['name']}>"}
        elif (int(role["permissions"]) != perms or role["color"] != body["color"]
              or role["hoist"] != body["hoist"]):
            dc.call("PATCH", f"/guilds/{gid}/roles/{role['id']}", body, f"update role {spec['name']}")
    mod_id = roles["Moderator"]["id"]

    # --- Channels --------------------------------------------------------------
    channels = dc.call("GET", f"/guilds/{gid}/channels")
    by_key = {(c["type"], c["name"]): c for c in channels}
    named: dict[str, str] = {}  # channel name -> id
    position = 0
    for cat in cfg["categories"]:
        cat_over = ([overwrite(everyone, deny=PERMS["VIEW_CHANNEL"]),
                     overwrite(mod_id, allow=PERMS["VIEW_CHANNEL"])] if cat.get("private") else [])
        existing = by_key.get((CATEGORY, cat["name"]))
        body = {"name": cat["name"], "type": CATEGORY, "position": position,
                "permission_overwrites": cat_over}
        if existing is None:
            existing = dc.call("POST", f"/guilds/{gid}/channels", body,
                               f"create category {cat['name']}") or {"id": f"<{cat['name']}>"}
        elif not same_overwrites(existing["permission_overwrites"], cat_over) or existing["position"] != position:
            dc.call("PATCH", f"/channels/{existing['id']}", body, f"update category {cat['name']}")
        position += 1
        for i, ch in enumerate(cat["channels"]):
            over = list(cat_over)
            if ch.get("readOnly"):
                over = [overwrite(everyone, deny=NO_POSTING),
                        overwrite(mod_id, allow=PERMS["SEND_MESSAGES"])]
            body = {"name": ch["name"], "type": TEXT, "topic": ch.get("topic", ""),
                    "rate_limit_per_user": ch.get("slowmodeSeconds", 0),
                    "parent_id": existing["id"], "position": i, "permission_overwrites": over}
            current = by_key.get((TEXT, ch["name"]))
            if current is None:
                current = dc.call("POST", f"/guilds/{gid}/channels", body,
                                  f"create #{ch['name']} in {cat['name']}") or {"id": f"<#{ch['name']}>"}
            else:
                changed = [k for k in ("topic", "rate_limit_per_user", "parent_id", "position")
                           if (current.get(k) or ("" if k == "topic" else 0)) != (body[k] or ("" if k == "topic" else 0))]
                if not same_overwrites(current["permission_overwrites"], over):
                    changed.append("permissions")
                if changed:
                    dc.call("PATCH", f"/channels/{current['id']}", body,
                            f"update #{ch['name']}: {', '.join(changed)}")
            named[ch["name"]] = current["id"]

    if args.remove:
        listed = {c["name"] for cat in cfg["categories"] for c in cat["channels"]} | \
                 {cat["name"] for cat in cfg["categories"]}
        for c in channels:
            if c["name"] in cfg.get("remove", []) and c["name"] not in listed:
                dc.call("DELETE", f"/channels/{c['id']}", change=f"delete channel {c['name']} (type {c['type']})")

    # --- AutoMod -------------------------------------------------------------
    am = cfg["automod"]
    rules = {r["name"]: r for r in dc.call("GET", f"/guilds/{gid}/auto-moderation/rules")}
    alert = named.get(am["alertChannel"])
    for spec in am["rules"]:
        meta, trigger = {}, None
        if "keywords" in spec or "regex" in spec:
            trigger = 1
            meta = {"keyword_filter": spec.get("keywords", []), "regex_patterns": spec.get("regex", []),
                    "allow_list": spec.get("allow", [])}
        elif spec.get("spam"):
            trigger = 3
        elif "presets" in spec:
            trigger = 4
            meta = {"presets": [PRESETS[p] for p in spec["presets"]]}
        elif "mentionLimit" in spec:
            trigger = 5
            meta = {"mention_total_limit": spec["mentionLimit"], "mention_raid_protection_enabled": True}
        block = {"type": 1, "metadata": {}}
        if spec.get("blockMessage"):
            block["metadata"]["custom_message"] = spec["blockMessage"][:150]
        actions = [block]
        if alert and not alert.startswith("<"):
            actions.append({"type": 2, "metadata": {"channel_id": alert}})
        exempt = []
        if spec.get("onlyIn"):
            exempt = [cid for name, cid in named.items() if name not in spec["onlyIn"] and not cid.startswith("<")]
        body = {"name": spec["name"], "event_type": 1, "trigger_type": trigger,
                "trigger_metadata": meta, "actions": actions, "enabled": True,
                "exempt_channels": exempt[:50],
                "exempt_roles": [mod_id] if trigger == 1 and not mod_id.startswith("<") else []}
        rule = rules.get(spec["name"])
        if rule is None:
            dc.call("POST", f"/guilds/{gid}/auto-moderation/rules", body, f"create AutoMod rule '{spec['name']}'")
        else:
            body.pop("trigger_type")
            dc.call("PATCH", f"/guilds/{gid}/auto-moderation/rules/{rule['id']}", body,
                    f"update AutoMod rule '{spec['name']}'")

    # --- Webhook -------------------------------------------------------------
    wh = cfg["webhook"]
    wh_channel = named.get(wh["channel"], "")
    if wh_channel and not wh_channel.startswith("<"):
        hooks = [h for h in dc.call("GET", f"/channels/{wh_channel}/webhooks") if h["name"] == wh["name"]]
        hook = hooks[0] if hooks else dc.call("POST", f"/channels/{wh_channel}/webhooks", {"name": wh["name"]},
                                              f"create webhook '{wh['name']}' in #{wh['channel']}")
        if hook and hook.get("token"):
            url = f"https://discord.com/api/webhooks/{hook['id']}/{hook['token']}"
            if args.apply and windows_user_env(wh["envVar"]) != url:
                ok = save_windows_user_env(wh["envVar"], url)
                print(f"  ✓ webhook URL saved to the Windows user variable {wh['envVar']}" if ok
                      else f"  ! could not save {wh['envVar']}")
    else:
        print(f"  would create webhook '{wh['name']}' in #{wh['channel']}")

    # --- Pinned messages -------------------------------------------------------
    if args.messages:
        for msg in cfg["messages"]:
            cid = named.get(msg["channel"], "")
            if cid.startswith("<") or not cid:
                print(f"  would post the #{msg['channel']} message")
                continue
            # Matched by the start of the first line (up to " – "), so that
            # editing the rest of it updates the message instead of reposting.
            def head(text):
                return text.split("\n", 1)[0].split(" – ", 1)[0]
            mine = [m for m in dc.call("GET", f"/channels/{cid}/messages?limit=50")
                    if m["author"]["id"] == me["id"] and head(m["content"]) == head(msg["text"])]
            if not mine:
                posted = dc.call("POST", f"/channels/{cid}/messages", {"content": msg["text"]},
                                 f"post the #{msg['channel']} message")
            else:
                posted = mine[0]
                if posted["content"] != msg["text"]:
                    dc.call("PATCH", f"/channels/{cid}/messages/{posted['id']}", {"content": msg["text"]},
                            f"update the #{msg['channel']} message")
            if posted and msg.get("pin") and not posted.get("pinned"):
                dc.call("PUT", f"/channels/{cid}/pins/{posted['id']}", change=f"pin the #{msg['channel']} message")
    print("Done." if args.apply else "Dry run: nothing changed. Run with --apply to make these changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
