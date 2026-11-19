@echo off
rem Manual local run of the nightly job (it normally runs on GitHub Actions).
cd /d C:\repo\darksuomi
python scraper_advanced.py
python enrich_tavastia.py
python scraper_rocks.py
python scraper_lepakkomies.py
python scraper_kulttuuritalo.py
python scraper_barloose.py
python scraper_veikkausarena.py
python genres.py
python setlists.py
python playlists.py
python bands.py
