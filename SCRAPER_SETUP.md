# 🎸 Dark Suomi Event Scraper Setup

Complete guide to setting up and running the event scrapers for Dark Suomi.

## 📋 Quick Start

### 1. Install Python 3.8+

**Windows:**
- Download from https://www.python.org/downloads/
- ✅ Check "Add Python to PATH" during installation

**macOS:**
```bash
brew install python3
```

**Linux:**
```bash
sudo apt-get install python3 python3-pip
```

### 2. Install Dependencies

```bash
cd C:\repo\darksuomi
pip install -r scraper-requirements.txt
```

This installs:
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP client
- `lxml` - Fast XML/HTML parser

### 3. Run the Scraper

```bash
python scraper-advanced.py
```

or for multiple venues:

```bash
python scraper-multi.py
```

**Expected output:**
```
🎸 Starting Advanced Tavastia Klubi Scraper

🔍 Trying https://tavastiakluki.fi/keikat...
✓ Using https://tavastiakluki.fi
Found 15 containers with selector: {'class': re.compile(...)}
  ✓ Found: Artist Name (2027-02-13)
  ✓ Found: Another Band (2027-02-20)
  ...

✓ Found 15 new events
✓ Saved 24 events to frontend/data/events.json

✓ Total events in database: 24
```

---

## 🔧 Configuration

### Customizing Scrapers

Edit `scraper-advanced.py` to adjust:

#### 1. Base URLs
```python
self.base_urls = [
    "https://tavastiakluki.fi",
    "https://tavastiaklubi.fi",
    "https://www.tavastiakluki.fi",
]
```

#### 2. Event Page Paths
```python
urls_to_try = [
    f"{base_url}/keikat",
    f"{base_url}/keikat-ja-tapahtumat",
    f"{base_url}/tapahtumat",
    f"{base_url}/events",
]
```

#### 3. HTML Selectors
Update in `_find_event_containers()`:
```python
selectors = [
    {'class': re.compile(r'event-?item|event-?card|gig|show')},
    {'class': re.compile(r'event')},
    {'data-event': True},
]
```

#### 4. Date Parsing
Add Finnish month names in `_parse_date()`:
```python
months = {
    'tammikuu': 1,   # January
    'helmikuu': 2,   # February
    # ...
}
```

### Adding New Venues

Create a new scraper file (e.g., `scraper-taverna.py`):

```python
from scraper_advanced import TavastiaAdvancedScraper

class TavernaScraper(TavastiaAdvancedScraper):
    def __init__(self, frontend_path=None):
        super().__init__(frontend_path)
        self.base_urls = [
            "https://klubitaverna.fi",
            "https://www.klubitaverna.fi",
        ]
```

Then add to `scraper-multi.py`:

```python
from scraper_taverna import TavernaScraper

def initialize_scrapers(self):
    # ... existing scrapers ...
    
    # Klubi Taverna
    self.scrapers.append({
        'name': 'Klubi Taverna',
        'scraper': TavernaScraper(self.frontend_path),
    })
```

---

## ⏰ Automation Setup

### Option 1: Windows Task Scheduler (Easiest for Windows Users)

1. **Create a batch file** at `C:\repo\darksuomi\run-scraper.bat`:

```batch
@echo off
cd /d C:\repo\darksuomi
python scraper-multi.py
pause
```

2. **Open Task Scheduler:**
   - Win + R → `taskschd.msc`

3. **Create Basic Task:**
   - Name: `Dark Suomi Event Scraper`
   - Description: `Automatically fetch events from venues`
   - Trigger: `Daily` at `2:00 AM`
   - Action: `Start a program`
     - Program: `C:\repo\darksuomi\run-scraper.bat`
   - Finish

4. **Test it:**
   - Right-click task → Run
   - Check output in command window

### Option 2: GitHub Actions (Recommended for CI/CD)

Create `.github/workflows/scrape-events.yml`:

```yaml
name: Scrape Events

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r scraper-requirements.txt
      
      - name: Run scraper
        run: python scraper-multi.py
      
      - name: Commit and push
        run: |
          git config user.name "🤖 Dark Suomi Bot"
          git config user.email "bot@darksuomi.fi"
          git add frontend/data/events.json
          git commit -m "chore: update events from venues" || true
          git push
```

### Option 3: Cron (Linux/macOS)

Add to crontab: `crontab -e`

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/darksuomi && python scraper-multi.py >> logs/scraper.log 2>&1
```

Create log directory:
```bash
mkdir -p /path/to/darksuomi/logs
```

---

## 📊 Data Structure

Events are stored in `frontend/data/events.json`:

```json
[
  {
    "id": 1,
    "artist": "Band Name",
    "venue": "Venue Name",
    "city": "Helsinki",
    "date": "2027-02-13",
    "ticketUrl": "https://tavastiaklubi.fi/event/..."
  },
  {
    "id": 2,
    "artist": "Another Artist",
    "venue": "Tavastia",
    "city": "Helsinki",
    "date": "2027-02-20",
    "ticketUrl": "https://tavastiaklubi.fi/event/..."
  }
]
```

### Supported Date Formats

The scraper handles multiple date formats:
- Finnish: `12. helmikuuta 2027` (12. February 2027)
- Numeric: `12.02.2027` or `12/02/2027`
- ISO: `2027-02-12`

---

## 🐛 Troubleshooting

### "Module not found: beautifulsoup4"

**Solution:**
```bash
pip install beautifulsoup4 requests lxml
```

### "No events found"

1. Check site is accessible:
   ```bash
   python -c "import requests; print(requests.get('https://tavastiaklubi.fi').status_code)"
   ```

2. Inspect the page source:
   - Open tavastiaklubi.fi in browser
   - Right-click → Inspect Element
   - Look for event containers (class names, IDs)

3. Update selectors in `scraper-advanced.py`:
   ```python
   def _find_event_containers(self, soup):
       # Update these selectors to match new HTML
   ```

4. Enable debug output:
   ```python
   # Add to _find_event_containers()
   print(f"Found containers: {len(containers)}")
   print(f"First container HTML: {containers[0] if containers else 'None'}")
   ```

### "Connection refused" or "Connection timeout"

1. Check internet connection
2. Website might be blocking requests - add delays:
   ```python
   time.sleep(2)  # 2 second delay between requests
   ```

3. Try a different User-Agent in headers

### Events not updating automatically

1. **Windows Task Scheduler:**
   - Right-click task → Properties
   - Verify correct file path and program
   - Check "Run whether user is logged in or not"
   - Check "Run with highest privileges"

2. **GitHub Actions:**
   - Check Actions tab in GitHub
   - Verify credentials have write access
   - Check workflow YAML syntax

3. **Check logs:**
   ```bash
   cd C:\repo\darksuomi
   python scraper-multi.py  # Run manually to see output
   ```

### Duplicate events appearing

The scraper prevents duplicates by checking:
- Artist name (case-insensitive)
- Event date

If duplicates appear:
1. Check if artist name slightly differs (e.g., "Band" vs "BAND")
2. Verify date format is consistent
3. Clear events.json and re-run:
   ```bash
   # Backup first!
   cp frontend/data/events.json frontend/data/events.json.backup
   echo "[]" > frontend/data/events.json
   python scraper-multi.py
   ```

---

## 📈 Monitoring

### View Scraper Logs

Logs are saved in `.scraper-logs/`:

```bash
cd C:\repo\darksuomi
dir .scraper-logs\
```

Each run creates a file like `scrape_20240218_020000.json`:

```json
{
  "timestamp": "2024-02-18T02:00:00",
  "venues": [
    {"name": "Tavastia Klubi", "status": "success"}
  ],
  "total_new_events": 5,
  "errors": []
}
```

### Check Event Count

```bash
cd C:\repo\darksuomi\frontend
# Windows PowerShell
Get-Content data/events.json | ConvertFrom-Json | Measure-Object

# Or in Python
python -c "import json; print(len(json.load(open('data/events.json'))))"
```

---

## 🔐 Best Practices

1. **Respect robots.txt**
   - Check website's robots.txt before scraping
   - Add delays between requests if needed

2. **Handle errors gracefully**
   - Scraper won't overwrite file if error occurs
   - Check logs for issues

3. **Regular backups**
   ```bash
   cp frontend/data/events.json frontend/data/events.json.backup
   ```

4. **Monitor changes**
   - Review git diffs to spot data issues
   - Set up alerts for failed scrapes

5. **Rate limiting**
   - Add `time.sleep()` between venue requests
   - Don't hammer servers with requests

---

## 📝 Adding Site-Specific Logic

If a venue has unique requirements:

```python
class CustomVenueScraper(TavastiaAdvancedScraper):
    def parse_events(self, html, base_url):
        # Custom parsing logic
        soup = BeautifulSoup(html, 'html.parser')
        
        # Venue-specific selectors
        events = []
        for item in soup.select('.custom-event-class'):
            event = {
                'artist': item.select_one('.artist-name').text,
                'date': item['data-date'],
                # ...
            }
            events.append(event)
        
        return events
```

---

## 🤝 Contributing

Found issues with event scraping?

1. Test locally: `python scraper-advanced.py`
2. Update selectors as needed
3. Test with multiple event formats
4. Document changes
5. Submit PR with improvements

---

## 📞 Support

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Review scraper logs in `.scraper-logs/`
3. Inspect website's HTML structure
4. Update selectors if site layout changed
5. Test manually with `python scraper-advanced.py`

---

**Last updated:** 2024
**Maintained by:** Dark Suomi Team 🤘
