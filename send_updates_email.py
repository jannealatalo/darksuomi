#!/usr/bin/env python3
"""
Send the nightly "new gigs" summary written by changelog.py:

  1. to the site owner by SMTP (plain text), and
  2. to the newsletter subscribers through Buttondown (Markdown), which
     keeps the subscriber list, confirmations and unsubscribe links.

Settings come from environment variables (GitHub secrets in the nightly job):
  SMTP_USERNAME       the sending account, e.g. a Gmail address
  SMTP_PASSWORD       its app password, not the account password
  MAIL_TO             where to send; several addresses separated by commas
  SMTP_HOST           optional, default smtp.gmail.com (port 465, SSL)
  BUTTONDOWN_API_KEY  the newsletter's API key (buttondown.com/requests)

Missing settings, or no body file (no new gigs), skip that part.

Usage:
  python send_updates_email.py new-gigs.txt [new-gigs.md]
"""

import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

import requests

BUTTONDOWN_API = "https://api.buttondown.com/v1/emails"


def env(name: str) -> str:
    return os.environ.get(name, "").strip()


def send_smtp(body: str) -> None:
    user, password, to = env("SMTP_USERNAME"), env("SMTP_PASSWORD"), env("MAIL_TO")
    if not (user and password and to):
        print("Owner email settings (SMTP_USERNAME, SMTP_PASSWORD, MAIL_TO) not set; skipped.")
        return
    msg = EmailMessage()
    msg["Subject"] = body.splitlines()[0]
    msg["From"] = f"Dark Suomi <{user}>"
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP_SSL(env("SMTP_HOST") or "smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"✓ Emailed the owner: {msg['Subject']}")


def send_newsletter(subject: str, markdown: str) -> None:
    key = env("BUTTONDOWN_API_KEY")
    if not key:
        print("BUTTONDOWN_API_KEY not set; newsletter skipped.")
        return
    resp = requests.post(
        BUTTONDOWN_API,
        headers={"Authorization": f"Token {key}"},
        json={"subject": subject, "body": markdown, "status": "about_to_send"},
        timeout=60,
    )
    if resp.status_code >= 300:
        # Show Buttondown's reason (e.g. a field or plan problem), not the key.
        raise SystemExit(f"Buttondown refused the email: HTTP {resp.status_code} {resp.text[:500]}")
    status = resp.json().get("status", "?") if resp.content else "?"
    print(f"✓ Newsletter sent to Buttondown (status: {status}): {subject}")


def main() -> int:
    text_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    md_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if not text_file or not text_file.exists():
        print("No new gigs; no email.")
        return 0
    body = text_file.read_text(encoding="utf-8")
    subject = body.splitlines()[0]
    failed = False
    try:
        send_smtp(body)
    except (smtplib.SMTPException, OSError) as e:
        print(f"! Owner email failed: {e}", file=sys.stderr)
        failed = True
    if md_file and md_file.exists():
        try:
            send_newsletter(subject, md_file.read_text(encoding="utf-8"))
        except (requests.RequestException, SystemExit) as e:
            print(f"! Newsletter failed: {e}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
