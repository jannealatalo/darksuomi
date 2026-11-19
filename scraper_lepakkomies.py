#!/usr/bin/env python3
"""
Scraper for Lepakkomies ("Lepis"), Helsinki (https://www.lepis.fi/tapahtumat/).

Lepakkomies is On the Rocks' sister bar and its site is built the same way,
so this reuses scraper_rocks.py. Note: lepakkomies.fi is NOT the venue any
more (an unrelated blog); the bar's site is lepis.fi.

Usage:
  python scraper_lepakkomies.py
"""

import sys

from scraper_rocks import main

if __name__ == "__main__":
    sys.exit(main("https://www.lepis.fi/tapahtumat/", "Lepakkomies"))
