"""
Tavastia Klubi Event Scraper
Scrapes upcoming events from tavastiaklubi.fi and updates events.json
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
from typing import List, Dict, Optional
import re

class TavastiaAmoScraper:
    def __init__(self):
        self.base_url = "https://tavastiaklubi.fi"
        self.events_url = f"{self.base_url}/keikat-ja-tapahtumat"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.events_file = os.path.join(
            os.path.dirname(__file__),
            'frontend/data/events.json'
        )

    def fetch_events(self) -> Optional[List[Dict]]:
        """Fetch events from Tavastia website"""
        try:
            response = requests.get(
                self.events_url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return self.parse_events(response.text)
        except requests.RequestException as e:
            print(f"Error fetching events: {e}")
            return None

    def parse_events(self, html: str) -> List[Dict]:
        """Parse HTML and extract event information"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Find event containers - adjust selector based on actual HTML structure
        # Common patterns: .event, .gig, [data-event], etc.
        event_containers = soup.find_all(
            class_=re.compile(r'event|gig|show', re.I)
        )
        
        # If no containers found, try alternative selectors
        if not event_containers:
            event_containers = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'item'))
        
        event_id = self._get_max_event_id() + 1
        
        for container in event_containers:
            event = self._extract_event_data(container, event_id)
            if event:
                events.append(event)
                event_id += 1
        
        return events

    def _extract_event_data(self, container, event_id: int) -> Optional[Dict]:
        """Extract event details from a container element"""
        try:
            # Try to extract artist/title
            artist = None
            for tag in ['h2', 'h3', 'h4']:
                artist_elem = container.find(tag)
                if artist_elem:
                    artist = artist_elem.get_text(strip=True)
                    break
            
            if not artist:
                return None
            
            # Try to extract date
            date = self._extract_date(container)
            if not date:
                return None
            
            # Try to extract venue/location
            venue = "Tavastia Club"  # Default
            city = "Helsinki"  # Default
            location_elem = container.find(class_=re.compile(r'location|venue|place'))
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                # Parse if format is "Venue · City"
                if '·' in location_text:
                    venue, city = location_text.split('·')
                    venue = venue.strip()
                    city = city.strip()
                else:
                    venue = location_text
            
            # Try to find ticket URL
            ticket_url = self.base_url
            link_elem = container.find('a', href=True)
            if link_elem:
                ticket_url = link_elem['href']
                if not ticket_url.startswith('http'):
                    ticket_url = self.base_url + ticket_url
            
            return {
                'id': event_id,
                'artist': artist,
                'venue': venue,
                'city': city,
                'date': date.isoformat(),
                'ticketUrl': ticket_url
            }
        except Exception as e:
            print(f"Error extracting event data: {e}")
            return None

    def _extract_date(self, container) -> Optional[datetime]:
        """Extract and parse date from container"""
        # Look for date patterns in various places
        date_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',    # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',    # DD/MM/YYYY
        ]
        
        # Search in text content
        text = container.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return self._parse_date_match(match, pattern)
        
        # Try date attributes
        for attr in ['data-date', 'datetime']:
            elem = container.find(attrs={attr: True})
            if elem:
                try:
                    return datetime.fromisoformat(elem[attr])
                except:
                    pass
        
        return None

    def _parse_date_match(self, match, pattern: str) -> Optional[datetime]:
        """Parse date from regex match"""
        try:
            if '.' in pattern:  # DD.MM.YYYY
                day, month, year = match.groups()
                return datetime(int(year), int(month), int(day))
            elif '-' in pattern and pattern.index('-') == 4:  # YYYY-MM-DD
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
            elif '/' in pattern:  # DD/MM/YYYY
                day, month, year = match.groups()
                return datetime(int(year), int(month), int(day))
        except:
            pass
        return None

    def _get_max_event_id(self) -> int:
        """Get the highest event ID from existing events"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
                if events:
                    return max(e.get('id', 0) for e in events)
        except:
            pass
        return 0

    def merge_with_existing(self, new_events: List[Dict]) -> List[Dict]:
        """Merge new events with existing ones, avoiding duplicates"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            existing = []
        
        # Create a set of existing artist+date combinations to avoid duplicates
        existing_keys = {
            (e['artist'].lower(), e['date']) 
            for e in existing
        }
        
        # Add new events that aren't duplicates
        merged = existing.copy()
        for event in new_events:
            key = (event['artist'].lower(), event['date'])
            if key not in existing_keys:
                merged.append(event)
        
        # Sort by date
        merged.sort(key=lambda e: e['date'])
        
        return merged

    def save_events(self, events: List[Dict]) -> bool:
        """Save events to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(events)} events to {self.events_file}")
            return True
        except Exception as e:
            print(f"Error saving events: {e}")
            return False

    def run(self) -> bool:
        """Run the scraper"""
        print("🎸 Starting Tavastia Klubi scraper...")
        
        events = self.fetch_events()
        if not events:
            print("✗ No events found")
            return False
        
        print(f"✓ Found {len(events)} new events")
        
        merged = self.merge_with_existing(events)
        print(f"✓ Merged with existing events (total: {len(merged)})")
        
        return self.save_events(merged)


if __name__ == '__main__':
    scraper = TavastiaAmoScraper()
    success = scraper.run()
    exit(0 if success else 1)
