#!/usr/bin/env python3
"""
Rokki Raikaa on the Helsinki site: the "Vantaan / Espoon / Helsingin
suurimmat rokit" shows (e.g. at Myyrmäkihalli). Parsing is in rokkiraikaa.py.

Usage:
  python scraper_rokkiraikaa.py
"""

import sys

from rokkiraikaa import run

if __name__ == "__main__":
    sys.exit(run("helsinki"))
