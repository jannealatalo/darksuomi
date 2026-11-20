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
python scraper_tiivistamo.py
python scraper_jaahalli.py
python scraper_stadion.py
python scraper_korjaamo.py
python scraper_sellosali.py
python scraper_tuska.py
python genres.py
rem Experimental city sites (Tampere, Oulu)
for %%f in (scraper_tampere_*.py scraper_oulu_*.py) do python %%f
python genres.py --city tampere
python genres.py --city oulu
python setlists.py
python playlists.py
python bands.py
