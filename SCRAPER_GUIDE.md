# Tavastia Klubi Event Scraper

A Python-based web scraper to automatically fetch upcoming events from Tavastia Klubi Helsinki and populate your Dark Suomi events database.

## 🎸 Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r scraper-requirements.txt
   ```

   This installs:
   - `beautifulsoup4` - HTML parsing
   - `requests` - HTTP requests
   - `lxml` - XML/HTML parsing engine

2. **Verify installation:**
   ```bash
   python scraper.py
   ```

## 🚀 Usage

### Run the scraper

```bash
python scraper.py
```

This will:
1. Fetch events from tavastiaklubi.fi
2. Parse event details (artist, date, venue, ticket URL)
3. Merge with existing events (avoiding duplicates)
4. Update `frontend/data/events.json`

### Example output
```
🎸 Starting Tavastia Klubi scraper...
✓ Found 12 new events
✓ Merged with existing events (total: 24)
✓ Saved 24 events to frontend/data/events.json
```

## 🔧 Automation

### Windows Task Scheduler (Recommended)

1. **Create a batch file** (`run-scraper.bat`):
   ```batch
   @echo off
   cd /d C:\repo\darksuomi
   python scraper.py
   pause
   ```

2. **Schedule it:**
   - Open Task Scheduler
   - Create Basic Task
   - Name: "Dark Suomi Event Scraper"
   - Trigger: Daily at 2:00 AM (or your preferred time)
   - Action: Start a program → `run-scraper.bat`

### GitHub Actions (For CI/CD)

Create `.github/workflows/scrape-events.yml`:
```yaml
name: Scrape Tavastia Events

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r scraper-requirements.txt
      
      - name: Run scraper
        run: python scraper.py
      
      - name: Commit changes
        run: |
          git config user.name "Dark Suomi Bot"
          git config user.email "bot@darksuomi.fi"
          git add frontend/data/events.json
          git commit -m "chore: update events from Tavastia" || true
          git push
```

## 📝 Event Data Structure

Events are stored in `frontend/data/events.json`:
```json
{
  "id": 1,
  "artist": "Band Name",
  "venue": "Venue Name",
  "city": "Helsinki",
  "date": "2027-02-13",
  "ticketUrl": "https://tavastiaklubi.fi/event/..."
}
```

## 🛠️ Customization

### Adding more venues

Duplicate the scraper for other venues:
```python
# scraper-tavastia.py (existing)
# scraper-aamuwalli.py (new)
# scraper-taverna.py (new)
```

Then create a master scraper:
```python
# scraper-all.py
import scraper_tavastia
import scraper_aamuwalli

tavastia = scraper_tavastia.TavastiaAmoScraper()
aamuwalli = scraper_aamuwalli.AamuwalliBrScraper()

tavastia.run()
aamuwalli.run()
```

### Adjusting HTML selectors

If the site changes, update the CSS selectors in `scraper.py`:

```python
# In parse_events() method
event_containers = soup.find_all(
    class_=re.compile(r'event|gig|show', re.I)
)
```

Common selectors:
- `.event-item`, `.event-card` - event containers
- `.event-title`, `.artist` - artist name
- `.event-date`, `.date` - date
- `.venue`, `.location` - venue name
- `.ticket-link`, `.buy-tickets` - ticket URL

## ⚠️ Troubleshooting

### "Module not found: beautifulsoup4"
```bash
pip install beautifulsoup4 requests lxml
```

### No events found
1. Check if tavastiaklubi.fi is accessible in your browser
2. Verify HTML structure hasn't changed
3. Update CSS selectors in `scraper.py`
4. Check site's robots.txt and terms of service

### Events not updating
- Verify file permissions on `frontend/data/events.json`
- Check if the site is blocking requests (consider adding delays)
- Review scraper output for errors

## 📋 Best Practices

1. **Rate limiting**: Add delays between requests if scraping multiple venues
2. **Error handling**: Check logs regularly for parsing errors
3. **Deduplication**: The scraper automatically avoids duplicate events
4. **Backup**: Keep a backup of events.json before major changes
5. **Respect robots.txt**: Always check site's terms of service

## 🤝 Contributing

Found issues with event parsing? 
1. Test locally: `python scraper.py`
2. Update selectors as needed
3. Test with different event formats
4. Submit improvements!

---

**Last updated**: 2024
**Maintained by**: Dark Suomi Team
