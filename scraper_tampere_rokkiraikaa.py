#!/usr/bin/env python3
"""
Rokki Raikaa in Tampere: the summer festival at the Hakametsä ice hall area
and the "Tampereen suurimmat rokit" show. Parsing is in rokkiraikaa.py.

Usage:
  python scraper_tampere_rokkiraikaa.py
"""

import sys

from rokkiraikaa import run

if __name__ == "__main__":
    sys.exit(run("tampere"))
