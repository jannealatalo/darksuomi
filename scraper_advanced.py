"""
Advanced Tavastia Klubi Event Scraper
Specifically tailored for tavastiaklubi.fi event structure
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin

class TavastiaAdvancedScraper:
    """Advanced scraper with Tavastia-specific logic"""
    
    def __init__(self, frontend_path: str = None):
        self.base_url = "https://tavastiakluki.fi"
        self.base_urls = [
            "https://tavastiakluki.fi",
            "https://www.tavastiakluki.fi",
            "https://tavastiaklubi.fi",
            "https://www.tavastiaklubi.fi",
        ]
        
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9,fi;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
        }
        
        self.frontend_path = frontend_path or 'frontend'
        self.events_file = os.path.join(self.frontend_path, 'data', 'events.json')
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def find_working_url(self) -> Optional[str]:
        """Test which base URL works"""
        for url in self.base_urls:
            try:
                response = self.session.head(url, timeout=5)
                if response.status_code < 400:
                    print(f"✓ Using {url}")
                    return url
            except:
                pass
        return None

    def fetch_events(self) -> Optional[List[Dict]]:
        """Fetch and parse events"""
        base_url = self.find_working_url()
        if not base_url:
            print("✗ Could not connect to any Tavastia URL")
            return None
        
        try:
            # Try different event page URLs
            urls_to_try = [
                f"{base_url}/keikat",
                f"{base_url}/keikat-ja-tapahtumat",
                f"{base_url}/tapahtumat",
                f"{base_url}/events",
                base_url,
            ]
            
            for url in urls_to_try:
                print(f"🔍 Trying {url}...")
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        events = self.parse_events(response.text, base_url)
                        if events:
                            return events
                        print(f"  No events found on this page")
                except Exception as e:
                    print(f"  Error: {e}")
                time.sleep(1)  # Rate limiting
            
            return None
        except Exception as e:
            print(f"Error fetching events: {e}")
            return None

    def parse_events(self, html: str, base_url: str) -> List[Dict]:
        """Parse HTML with Tavastia-specific structure"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Tavastia uses <a class="tiketti-list-item"> for events
        event_links = soup.find_all('a', class_=lambda x: x and 'tiketti-list-item' in x)
        
        print(f"  Found {len(event_links)} event links")
        
        event_id = self._get_max_event_id() + 1
        
        for link in event_links:
            try:
                # Get artist name from <h3>
                h3 = link.find('h3')
                if not h3:
                    continue
                artist = h3.get_text(strip=True)
                
                # Get date from data-begin-date attribute
                date_str = link.get('data-begin-date', '')
                if not date_str:
                    continue
                
                # Parse date (format: 2026-11-19)
                date_obj = self._parse_iso_date(date_str)
                if not date_obj:
                    continue
                
                # Get venue from class name
                class_str = link.get('class', [])
                class_str = ' '.join(class_str) if isinstance(class_str, list) else str(class_str)
                venue = 'Tavastia'
                if 'location-' in class_str:
                    # Extract venue from class like "location-tavastia-klubi"
                    for part in class_str.split():
                        if 'location-' in part:
                            venue_name = part.replace('location-', '').replace('-', ' ').title()
                            if venue_name:
                                venue = venue_name
                            break
                
                # Get ticket URL from href
                ticket_url = link.get('href', base_url)
                if not ticket_url.startswith('http'):
                    ticket_url = urljoin(base_url, ticket_url)
                
                event = {
                    'id': event_id,
                    'artist': artist,
                    'venue': venue,
                    'city': 'Helsinki',
                    'date': date_obj.isoformat(),
                    'ticketUrl': ticket_url
                }
                
                events.append(event)
                event_id += 1
                print(f"  ✓ Found: {artist} ({date_obj.isoformat()})")
            
            except Exception as e:
                print(f"  ⚠ Parse error: {e}")
                continue
        
        return events

    def _find_event_containers(self, soup: BeautifulSoup) -> list:
        """Find event container elements"""
        selectors = [
            {'class': re.compile(r'event-?item|event-?card|gig|show')},
            {'class': re.compile(r'event')},
            {'data-event': True},
            {'itemtype': re.compile(r'Event', re.I)},
        ]
        
        for selector in selectors:
            containers = soup.find_all(['div', 'article'], selector)
            if containers:
                print(f"  Found {len(containers)} containers with selector: {selector}")
                return containers
        
        return []

    def _find_table_rows(self, soup: BeautifulSoup) -> list:
        """Find events in table rows"""
        tables = soup.find_all('table')
        rows = []
        
        for table in tables:
            table_rows = table.find_all('tr')
            if len(table_rows) > 1:  # Skip header
                rows.extend(table_rows[1:])
        
        return rows if rows else []

    def _extract_from_schema(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract events from schema.org structured data"""
        events = []
        
        for script in soup.find_all('script', {'type': 'application/ld+json'}):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Event':
                        event = self._parse_schema_event(data)
                        if event:
                            events.append(event)
                    elif data.get('@type') == 'ItemList':
                        for item in data.get('itemListElement', []):
                            if item.get('@type') == 'Event':
                                event = self._parse_schema_event(item)
                                if event:
                                    events.append(event)
            except Exception as e:
                print(f"  Schema parse error: {e}")
        
        return events

    def _parse_schema_event(self, data: dict) -> Optional[Dict]:
        """Parse schema.org Event object"""
        try:
            artist = data.get('name', '')
            if not artist:
                return None
            
            # Parse date
            date_str = data.get('startDate', '')
            if not date_str:
                return None
            
            # Handle different date formats
            date_obj = self._parse_iso_date(date_str)
            if not date_obj:
                return None
            
            # Extract venue info
            location = data.get('location', {})
            if isinstance(location, dict):
                venue = location.get('name', 'Tavastia')
                city = location.get('address', {}).get('addressLocality', 'Helsinki')
            else:
                venue = str(location)
                city = 'Helsinki'
            
            # Get URL
            url = data.get('url', '') or data.get('sameAs', '')
            
            return {
                'id': 0,  # Will be set during save
                'artist': artist,
                'venue': venue or 'Tavastia',
                'city': city or 'Helsinki',
                'date': date_obj.isoformat(),
                'ticketUrl': url or 'https://tavastiaklubi.fi'
            }
        except Exception as e:
            print(f"  Schema event parse error: {e}")
            return None

    def _extract_event(self, container, base_url: str, event_id: int) -> Optional[Dict]:
        """Extract event from container element"""
        # Get artist name
        artist = None
        for tag_name in ['h2', 'h3', 'h4', 'span', 'a']:
            tag = container.find(tag_name, class_=re.compile(r'artist|title|name|event-name'))
            if tag:
                artist = tag.get_text(strip=True)
                break
        
        if not artist:
            # Try without class filter
            for tag_name in ['h2', 'h3', 'h4']:
                tag = container.find(tag_name)
                if tag:
                    artist = tag.get_text(strip=True)
                    if artist and len(artist) > 2:
                        break
        
        if not artist:
            return None
        
        # Get date
        date_str = self._extract_date_string(container)
        if not date_str:
            return None
        
        date_obj = self._parse_date(date_str)
        if not date_obj:
            return None
        
        # Get venue and city
        venue = 'Tavastia'
        city = 'Helsinki'
        
        # Get ticket URL
        link = container.find('a', href=True)
        ticket_url = link['href'] if link else base_url
        
        if not ticket_url.startswith('http'):
            ticket_url = urljoin(base_url, ticket_url)
        
        return {
            'id': event_id,
            'artist': artist.strip(),
            'venue': venue,
            'city': city,
            'date': date_obj.isoformat(),
            'ticketUrl': ticket_url
        }

    def _extract_date_string(self, container) -> Optional[str]:
        """Extract date string from container"""
        # Look for date patterns in various places
        date_elements = container.find_all(
            class_=re.compile(r'date|time|when', re.I)
        )
        
        for elem in date_elements:
            text = elem.get_text(strip=True)
            if text and re.search(r'\d', text):
                return text
        
        # Search in all text
        text = container.get_text()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if re.search(r'\d{1,2}[.\/-]\d{1,2}', line):
                return line
        
        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Finnish month names
        months = {
            'tammikuu': 1, 'helmikuu': 2, 'maaliskuu': 3, 'huhtikuu': 4,
            'toukokuu': 5, 'kesäkuu': 6, 'heinäkuu': 7, 'elokuu': 8,
            'syyskuu': 9, 'lokakuu': 10, 'marraskuu': 11, 'joulukuu': 12,
            'tammi': 1, 'helmi': 2, 'maalis': 3, 'huhti': 4,
            'touko': 5, 'kesä': 6, 'heinä': 7, 'elo': 8,
            'syys': 9, 'loka': 10, 'marra': 11, 'joulu': 12,
        }
        
        # Pattern: "12. helmikuuta 2027"
        for month_name, month_num in months.items():
            pattern = rf'(\d{{1,2}})\.?\s+{month_name}\s+(\d{{4}})'
            match = re.search(pattern, date_str, re.I)
            if match:
                day, year = match.groups()
                try:
                    return datetime(int(year), month_num, int(day))
                except:
                    pass
        
        # Pattern: DD.MM.YYYY
        match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except:
                pass
        
        # Pattern: DD/MM/YYYY
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except:
                pass
        
        # Pattern: YYYY-MM-DD (ISO)
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except:
                pass
        
        return None

    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO date format"""
        try:
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.split('T')[0])
            else:
                return datetime.fromisoformat(date_str)
        except:
            return None

    def _get_max_event_id(self) -> int:
        """Get highest event ID from existing events"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
                if events and isinstance(events, list):
                    ids = [e.get('id', 0) for e in events if isinstance(e, dict)]
                    return max(ids) if ids else 0
        except:
            pass
        return 0

    def merge_with_existing(self, new_events: List[Dict]) -> List[Dict]:
        """Merge new events with existing, avoiding duplicates"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
        except:
            existing = []
        
        # Create set of existing events (artist + date)
        existing_set = {
            (e['artist'].lower().strip(), e['date'][:10])  # day only: doors time is added later
            for e in existing if isinstance(e, dict)
        }
        
        # Add new non-duplicate events
        merged = existing.copy()
        # Track the next ID locally: the file on disk isn't updated until
        # save, so reading it per event gave every new event the same ID.
        next_id = max((e.get('id', 0) for e in existing if isinstance(e, dict)), default=0) + 1
        for event in new_events:
            key = (event['artist'].lower().strip(), event['date'][:10])
            if key not in existing_set:
                event['id'] = next_id
                next_id += 1
                merged.append(event)
                existing_set.add(key)
        
        # Sort by date
        merged.sort(key=lambda e: e.get('date', ''))
        
        return merged

    def save_events(self, events: List[Dict]) -> bool:
        """Save events to file"""
        try:
            os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(events)} events to {self.events_file}")

            # Record when the scrape happened; the site shows it in the header.
            meta_file = os.path.join(os.path.dirname(self.events_file), 'meta.json')
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'lastScraped': datetime.now().astimezone().isoformat(timespec='seconds')},
                    f, indent=2,
                )
                f.write('\n')
            return True
        except Exception as e:
            print(f"✗ Error saving events: {e}")
            return False

    def run(self) -> bool:
        """Run the scraper"""
        print("🎸 Starting Advanced Tavastia Klubi Scraper\n")
        
        new_events = self.fetch_events()
        if not new_events:
            print("\n✗ No events found")
            return False
        
        print(f"\n✓ Found {len(new_events)} new events")
        
        merged = self.merge_with_existing(new_events)
        saved = self.save_events(merged)
        
        if saved:
            print(f"\n✓ Total events in database: {len(merged)}")
        
        return saved


if __name__ == '__main__':
    scraper = TavastiaAdvancedScraper()
    success = scraper.run()
    exit(0 if success else 1)
