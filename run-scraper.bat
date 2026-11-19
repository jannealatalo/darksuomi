@echo off
rem Manual local run of the nightly job (it normally runs on GitHub Actions).
cd /d C:\repo\darksuomi
python scraper_advanced.py
python enrich_tavastia.py
python scraper_rocks.py
python genres.py
python setlists.py
python playlists.py
