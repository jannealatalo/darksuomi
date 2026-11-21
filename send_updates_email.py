#!/usr/bin/env python3
"""
Email the nightly "new gigs" summary written by changelog.py --mail-file.

Settings come from environment variables (GitHub secrets in the nightly job):
  SMTP_USERNAME   the sending account, e.g. a Gmail address
  SMTP_PASSWORD   its app password (Gmail: Google account -> Security ->
                  2-Step Verification -> App passwords), not the real password
  MAIL_TO         where to send; several addresses separated by commas
  SMTP_HOST       optional, default smtp.gmail.com (port 465, SSL)

Without the settings, or without a body file (no new gigs), it does nothing.

Usage:
  python send_updates_email.py new-gigs.txt
"""

import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path


def main() -> int:
    body_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not body_file or not body_file.exists():
        print("No new gigs; no email.")
        return 0
    user, password, to = (os.environ.get(k, "").strip()
                          for k in ("SMTP_USERNAME", "SMTP_PASSWORD", "MAIL_TO"))
    if not (user and password and to):
        print("Email settings (SMTP_USERNAME, SMTP_PASSWORD, MAIL_TO) not set; no email.")
        return 0
    body = body_file.read_text(encoding="utf-8")
    msg = EmailMessage()
    msg["Subject"] = body.splitlines()[0]
    msg["From"] = f"Dark Suomi <{user}>"
    msg["To"] = to
    msg.set_content(body)
    host = os.environ.get("SMTP_HOST", "").strip() or "smtp.gmail.com"
    with smtplib.SMTP_SSL(host, 465, timeout=60) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"✓ Emailed: {msg['Subject']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
