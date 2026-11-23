#!/usr/bin/env python3
"""
Rokki Raikaa in Oulu: the summer festival at the Ouluhalli parking area
(and any "Oulun suurimmat rokit" show). Parsing is in rokkiraikaa.py.

Usage:
  python scraper_oulu_rokkiraikaa.py
"""

import sys

from rokkiraikaa import run

if __name__ == "__main__":
    sys.exit(run("oulu"))
