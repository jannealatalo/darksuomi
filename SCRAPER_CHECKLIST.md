# ✅ Dark Suomi Scraper - Setup Verification Checklist

## 🎯 Pre-Installation

- [ ] Python 3.8+ is installed
  ```bash
  python --version
  # Should show: Python 3.8.0 or higher
  ```

- [ ] pip is installed
  ```bash
  pip --version
  # Should show: pip 20.0+
  ```

- [ ] Internet connection is working
  ```bash
  ping google.com
  ```

---

## 📦 Installation

- [ ] Dependencies installed
  ```bash
  pip install -r scraper-requirements.txt
  # Should complete without errors
  ```

- [ ] Verify installations
  ```bash
  python -c "import requests; print('✓ requests')"
  python -c "import bs4; print('✓ beautifulsoup4')"
  python -c "import lxml; print('✓ lxml')"
  ```

---

## 🧪 Validation

- [ ] Run test suite
  ```bash
  python scraper-test.py
  # Should show: 7/7 tests passed
  ```

- [ ] All tests show ✓ (not ✗)
  - ✓ Python Version
  - ✓ Dependencies
  - ✓ Project Structure
  - ✓ Events File
  - ✓ Scraper Import
  - ✓ Internet Connection
  - ✓ Tavastia Access

---

## 🚀 First Run

- [ ] Run scraper
  ```bash
  python scraper-advanced.py
  ```

- [ ] Scraper produces output like:
  ```
  🎸 Starting Advanced Tavastia Klubi Scraper
  
  🔍 Trying https://tavastiakluki.fi/...
  ✓ Using https://tavastiakluki.fi
  Found X containers
    ✓ Found: Artist Name (2027-02-13)
  
  ✓ Found N new events
  ✓ Saved M events to frontend/data/events.json
  ```

- [ ] No error messages appear
- [ ] Script exits successfully (exit code 0)

---

## 📊 Data Verification

- [ ] Events file exists
  ```bash
  ls frontend/data/events.json
  # Or in PowerShell:
  Test-Path frontend\data\events.json
  ```

- [ ] Events file is valid JSON
  ```bash
  python -c "import json; json.load(open('frontend/data/events.json'))"
  # Should complete without error
  ```

- [ ] Events file contains events
  ```bash
  python -c "import json; events = json.load(open('frontend/data/events.json')); print(f'Events: {len(events)}')"
  # Should show: Events: X (where X > 0)
  ```

- [ ] Events have correct structure
  ```bash
  python -c "
  import json
  events = json.load(open('frontend/data/events.json'))
  if events:
      e = events[0]
      print('Sample event:')
      print(f\"  Artist: {e.get('artist')}\")
      print(f\"  Date: {e.get('date')}\")
      print(f\"  Venue: {e.get('venue')}\")
  "
  ```

- [ ] All events have required fields
  ```bash
  python -c "
  import json
  required = {'id', 'artist', 'venue', 'city', 'date', 'ticketUrl'}
  events = json.load(open('frontend/data/events.json'))
  for e in events:
      missing = required - set(e.keys())
      if missing:
          print(f\"Event {e.get('id')} missing: {missing}\")
  print('✓ All events valid' if not missing else '')
  "
  ```

---

## 🌐 Website Verification

- [ ] Events appear on darksuomi.fi
  ```
  Open http://localhost:3000 (or your deployed site)
  Should show events from frontend/data/events.json
  ```

- [ ] Events are sorted by date
  - Earlier events appear first
  - Dates are in correct format

- [ ] Event details are correct
  - Artist name correct
  - Venue is "Tavastia" or other venue
  - City is "Helsinki"
  - Date is formatted properly

- [ ] Ticket links work
  - Click "Tickets" link
  - Opens venue website or ticket page

---

## 📝 Logs Verification

- [ ] Log directory exists
  ```bash
  ls .scraper-logs/
  ```

- [ ] Log files are created
  ```bash
  ls .scraper-logs/scrape_*.json
  # Should show at least one file
  ```

- [ ] Latest log shows success
  ```bash
  python -c "
  import json, glob
  latest = sorted(glob.glob('.scraper-logs/scrape_*.json'))[-1]
  log = json.load(open(latest))
  print(f\"Status: {log.get('timestamp')}\")
  print(f\"Venues scraped: {len(log.get('venues', []))}\")
  print(f\"Errors: {len(log.get('errors', []))}\")
  "
  ```

---

## ⏰ Automation Verification (If Configured)

### Windows Task Scheduler
- [ ] Task created in Task Scheduler
- [ ] Task name: "Dark Suomi Event Scraper"
- [ ] Trigger: Daily at 2:00 AM (or your time)
- [ ] Action points to: run-scraper.bat
- [ ] Run test: Right-click task → Run
- [ ] Task completes successfully
- [ ] events.json updated after run

### GitHub Actions
- [ ] Workflow file exists: `.github/workflows/scrape-events.yml`
- [ ] Workflow syntax is valid
- [ ] Workflow runs on schedule (check Actions tab)
- [ ] Latest run shows "✓ success" or green checkmark
- [ ] Commit to events.json appears after run

### Cron (Linux/macOS)
- [ ] Entry added to crontab: `crontab -e`
- [ ] Command path is correct
- [ ] Log file location is correct (if specified)
- [ ] Logs directory exists: `mkdir -p logs/`
- [ ] Runs at specified time

---

## 🐛 Troubleshooting Checklist

If something fails, check these in order:

### Python/Dependencies
- [ ] Python installed: `python --version` shows 3.8+
- [ ] Python in PATH: Can run from any directory
- [ ] pip working: `pip --version` works
- [ ] Packages installed: Run each import test
- [ ] No package conflicts: `pip list` shows all packages

### Scraper
- [ ] File exists: `ls scraper-advanced.py`
- [ ] File is readable: `cat scraper-advanced.py` (first few lines)
- [ ] No syntax errors: `python -m py_compile scraper-advanced.py`
- [ ] Can import: `python -c "from scraper_advanced import TavastiaAdvancedScraper"`

### Website Access
- [ ] Website accessible: `ping tavastiakluki.fi`
- [ ] Internet working: `ping google.com`
- [ ] Browser can access: Open tavastiakluki.fi in browser
- [ ] No geographic blocking: Check site's terms of service
- [ ] User-Agent not blocked: Try different headers in scraper

### Data
- [ ] File path correct: `frontend/data/events.json`
- [ ] Directory writable: Can create test file in `frontend/data/`
- [ ] JSON valid: Use `python -c "import json; json.load(open('frontend/data/events.json'))"`
- [ ] File permissions: Check read/write permissions

### Automation (if used)
- [ ] Script path correct: Absolute path, no shortcuts
- [ ] Working directory correct: cd to repo before running
- [ ] Environment: Python and dependencies available to scheduler
- [ ] Logs: Check scheduler logs for errors
- [ ] Manual test: Run command manually to verify it works

---

## 📋 Final Checklist

Before considering setup complete:

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install -r scraper-requirements.txt`
- [ ] All tests pass: `python scraper-test.py` → 7/7
- [ ] Scraper runs: `python scraper-advanced.py` → Success
- [ ] Data created: `frontend/data/events.json` has events
- [ ] Events valid: All fields present, dates formatted correctly
- [ ] Website updated: darksuomi.fi shows events
- [ ] Logs created: `.scraper-logs/scrape_*.json` exists
- [ ] (Optional) Automation: Task Scheduler/GitHub Actions/Cron configured

**All items checked? You're done! 🎉**

---

## 🚀 Next Steps

1. **Short term:**
   - [ ] Monitor first automated run
   - [ ] Verify events update correctly
   - [ ] Check logs for any warnings

2. **Medium term:**
   - [ ] Add more venues (5+)
   - [ ] Test with different event formats
   - [ ] Improve error handling if needed

3. **Long term:**
   - [ ] Public beta launch
   - [ ] Gather user feedback
   - [ ] Scale to multiple cities
   - [ ] Add more features

---

## 📞 Support

If any checklist item fails:

1. **Quick issues:** See SCRAPER_QUICKSTART.txt
2. **Setup issues:** Read SCRAPER_SETUP.md
3. **Detailed help:** Read SCRAPER_GUIDE.md
4. **Still stuck:** Check .scraper-logs/ for error details

---

## 🎸 Success Criteria

Setup is successful when:

✅ `python scraper-test.py` passes all tests
✅ `python scraper-advanced.py` finds and saves events
✅ `frontend/data/events.json` contains valid event data
✅ Events display on darksuomi.fi
✅ Automation runs on schedule (if configured)

**You've got this! Rock on!** 🤘

---

**Checklist Version**: 1.0
**Last Updated**: 2024
**Status**: Ready to verify
