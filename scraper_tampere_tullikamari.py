#!/usr/bin/env python3
"""
Scraper for Tullikamari, Tampere (https://tullikamari.fi/ohjelma/): the big
hall Pakkahuone and the smaller Tullikamarin Klubi.

Same company and WordPress theme as Tavara-asema, so the parsing lives in
scraper_tampere_tavara_asema.py (program page cards + REST API titles; only
the "konsertti-keikka" category, no DJ club nights). Each card's
data-venue says the room, which becomes the venue name:
"Pakkahuone" -> Pakkahuone, "Klubi" -> Tullikamarin Klubi.

Usage:
  python scraper_tampere_tullikamari.py
"""

import sys

from scraper_tampere_tavara_asema import scrape

ROOMS = {"pakkahuone": "Pakkahuone", "klubi": "Tullikamarin Klubi"}


def venue_for(room: str) -> str:
    return ROOMS.get(room.strip().lower(), "Tullikamari")


if __name__ == "__main__":
    sys.exit(scrape("https://tullikamari.fi", venue_for, "Tullikamari (Pakkahuone + Klubi)"))
