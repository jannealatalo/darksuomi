# darksuomi

Dark Suomi is a curated calendar of alternative music events in Finland.

## Genres

- Doom
- Stoner
- Goth
- Darkwave
- Industrial
- Punk
- Hardcore
- Post-Metal
- Black Metal

## Why?

Finding interesting gigs in Finland is harder than it should be.

Events are scattered across venue websites, ticketing services and social media.

Dark Suomi aims to bring them together in one place.

## Current Goal

Display the first real event on darksuomi.fi.

## Status

🚧 Early development

## Development

### Frontend
- Next.js React app at `frontend/`
- Events listed from `frontend/data/events.json`
- Automatic date formatting (Finnish locale)

### Event Scraper
- Automated scraper for venue websites
- Currently supports Tavastia Klubi
- Extensible for multiple venues
- Runs on schedule (GitHub Actions, Task Scheduler, Cron)

**Setup**: See [SCRAPER_README.md](SCRAPER_README.md)

## Running Locally

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Scraper
```bash
pip install -r scraper-requirements.txt
python scraper-advanced.py
```

## Inspiration

- Dark Seattle (https://www.darkseattle.net/)
- Bandsintown
- Songkick
