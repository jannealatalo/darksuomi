# 🎸 Dark Suomi Event Scraper

Automated web scraper to fetch upcoming dark music events from Helsinki venues and populate darksuomi.fi with current gigs.

## 📦 What's Included

| File | Purpose |
|------|---------|
| `scraper-advanced.py` | Main Tavastia Klubi scraper with multiple parsing strategies |
| `scraper-multi.py` | Master scraper for multiple venues (extensible) |
| `scraper.py` | Basic/fallback scraper implementation |
| `scraper-test.py` | Test suite to validate setup |
| `scraper-requirements.txt` | Python dependencies |
| `SCRAPER_SETUP.md` | Complete setup and automation guide |
| `SCRAPER_GUIDE.md` | Detailed usage guide |

## 🚀 Quick Start (5 minutes)

### 1. Install Python
- **Windows**: https://www.python.org/downloads/ (check "Add to PATH")
- **macOS**: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

### 2. Install Dependencies
```bash
cd C:\repo\darksuomi
pip install -r scraper-requirements.txt
```

### 3. Test Installation
```bash
python scraper-test.py
```

Expected output:
```
✓ PASS - Python Version
✓ PASS - Dependencies
✓ PASS - Project Structure
✓ PASS - Events File
✓ PASS - Scraper Import
✓ PASS - Internet Connection
✓ PASS - Tavastia Access

📊 Test Summary
Total: 7/7 tests passed

🎉 All tests passed! Ready to scrape.
```

### 4. Run Scraper
```bash
python scraper-advanced.py
```

or for multiple venues:
```bash
python scraper-multi.py
```

Output:
```
🎸 Starting Advanced Tavastia Klubi Scraper

🔍 Trying https://tavastiakluki.fi/keikat...
✓ Using https://tavastiakluki.fi
Found 15 containers with selector...
  ✓ Found: Artist Name (2027-02-13)
  ✓ Found: Another Band (2027-02-20)

✓ Found 15 new events
✓ Saved 24 events to frontend/data/events.json

✓ Total events in database: 24
```

## 📋 How It Works

```
Tavastia Website
      ↓
   Scraper
      ↓
  Parse HTML
      ↓
Extract Events
      ↓
 Merge & Dedupe
      ↓
frontend/data/events.json
      ↓
   React App
      ↓
darksuomi.fi
```

### Parsing Strategy

The scraper uses multiple fallback strategies to handle different HTML structures:

1. **CSS Selectors** - Looks for `.event`, `.gig`, `.event-card` classes
2. **Table Parsing** - Handles events in HTML tables
3. **Schema.org Data** - Extracts from structured `<script type="application/ld+json">` tags
4. **Fallback Patterns** - Date regex and content analysis

### Duplicate Prevention

Events are deduplicated by:
- Artist name (case-insensitive)
- Event date

Existing events are always preserved.

## ⚙️ Configuration

### Change Scraper Settings

Edit `scraper-advanced.py`:

```python
# Change venue URLs
self.base_urls = [
    "https://tavastiakluki.fi",
    "https://tavastiaklubi.fi",
]

# Change event page paths
urls_to_try = [
    f"{base_url}/keikat",
    f"{base_url}/keikat-ja-tapahtumat",
]

# Add Finnish month names
months = {
    'tammikuu': 1,   # January
    'helmikuu': 2,   # February
    # ...
}
```

### Add New Venues

Create `scraper-myvenue.py`:
```python
from scraper_advanced import TavastiaAdvancedScraper

class MyVenueScraper(TavastiaAdvancedScraper):
    def __init__(self, frontend_path=None):
        super().__init__(frontend_path)
        self.base_urls = ["https://myvenue.fi"]
```

Then update `scraper-multi.py`:
```python
from scraper_myvenue import MyVenueScraper

def initialize_scrapers(self):
    # ... existing scrapers ...
    self.scrapers.append({
        'name': 'My Venue',
        'scraper': MyVenueScraper(self.frontend_path),
    })
```

## ⏰ Automate Running

### Windows Task Scheduler

1. Create `run-scraper.bat`:
```batch
@echo off
cd /d C:\repo\darksuomi
python scraper-multi.py
pause
```

2. Task Scheduler → Create Basic Task
   - Trigger: Daily 2 AM
   - Action: `C:\repo\darksuomi\run-scraper.bat`

### GitHub Actions

Create `.github/workflows/scrape-events.yml`:
```yaml
name: Scrape Events
on:
  schedule:
    - cron: '0 2 * * *'  # Daily 2 AM UTC
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r scraper-requirements.txt
      - run: python scraper-multi.py
      - run: |
          git config user.name "🤖 Bot"
          git config user.email "bot@darksuomi.fi"
          git add frontend/data/events.json
          git commit -m "chore: update events" || true
          git push
```

### Cron (Linux/macOS)

```bash
crontab -e
# Add:
0 2 * * * cd /path/to/darksuomi && python scraper-multi.py >> logs/scraper.log 2>&1
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip install beautifulsoup4 requests lxml` |
| No events found | Run `python scraper-test.py` and check output |
| Website blocked | Try different User-Agent header or add delays |
| Events not updating | Check Task Scheduler/GitHub Actions logs |
| Duplicate events | Check artist name capitalization |

See **SCRAPER_SETUP.md** for detailed troubleshooting.

## 📊 Data Structure

Events in `frontend/data/events.json`:

```json
[
  {
    "id": 1,
    "artist": "Oranssi Pazuzu",
    "venue": "Tavastia",
    "city": "Helsinki",
    "date": "2027-02-13",
    "ticketUrl": "https://tavastiakluki.fi/..."
  }
]
```

Supported date formats:
- `12.02.2027` (Finnish numeric)
- `12. helmikuuta 2027` (Finnish text)
- `2027-02-12` (ISO)
- `12/02/2027` (Slash separated)

## 📝 Logs

Scraper logs are saved in `.scraper-logs/`:

```
.scraper-logs/
├── scrape_20240218_020000.json
├── scrape_20240219_020000.json
└── scrape_20240220_020000.json
```

Each contains:
```json
{
  "timestamp": "2024-02-18T02:00:00",
  "venues": [{"name": "Tavastia", "status": "success"}],
  "total_new_events": 5,
  "errors": []
}
```

## 🔍 Debugging

Enable verbose output by editing scraper:

```python
# In _find_event_containers()
print(f"Found {len(containers)} containers")
if containers:
    print(f"First: {containers[0]}")
```

Or run with Python verbose mode:
```bash
python -v scraper-advanced.py 2>&1 | grep -i error
```

## 🤝 Contributing

Found parsing issues?
1. Run `python scraper-advanced.py` and check output
2. Inspect website HTML (F12 developer tools)
3. Update CSS selectors in `_find_event_containers()`
4. Test with multiple events
5. Submit improvements!

## 📚 Additional Resources

- **Full Setup Guide**: [SCRAPER_SETUP.md](SCRAPER_SETUP.md)
- **Usage Guide**: [SCRAPER_GUIDE.md](SCRAPER_GUIDE.md)
- **BeautifulSoup Docs**: https://www.crummy.com/software/BeautifulSoup/
- **Requests Docs**: https://docs.python-requests.org/

## 🎯 Next Steps

1. ✅ Install dependencies: `pip install -r scraper-requirements.txt`
2. ✅ Test setup: `python scraper-test.py`
3. ✅ Run scraper: `python scraper-advanced.py`
4. ✅ Verify events: Check `frontend/data/events.json`
5. ✅ Set up automation: See SCRAPER_SETUP.md

## 📞 Support

Having issues? Check:
1. This README's Troubleshooting section
2. `python scraper-test.py` output
3. `.scraper-logs/` for error details
4. Website's HTML structure (might have changed)

---

**Status**: ✅ Ready to use
**Latest Version**: 1.0
**Last Updated**: 2024
**Maintained by**: Dark Suomi Team 🤘

---

## 🎸 Rock On!

Your Dark Suomi events are now automatically updated. Keep the music playing! 🤘
