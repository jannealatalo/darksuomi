#!/usr/bin/env python3
"""
Dark Suomi Multi-Venue Event Scraper
Scrapes events from multiple Helsinki venues and updates the event database
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Import scrapers
try:
    from scraper_advanced import TavastiaAdvancedScraper
except ImportError:
    # Fallback if advanced scraper not available
    sys.path.insert(0, os.path.dirname(__file__))


class MultiVenueScraper:
    """Master scraper for multiple venues"""
    
    def __init__(self, frontend_path: str = None):
        self.frontend_path = frontend_path or os.path.join(
            os.path.dirname(__file__), 'frontend'
        )
        self.events_file = os.path.join(self.frontend_path, 'data', 'events.json')
        self.scrapers = []
        self.initialize_scrapers()

    def initialize_scrapers(self):
        """Initialize all venue scrapers"""
        # Tavastia Klubi
        self.scrapers.append({
            'name': 'Tavastia Klubi',
            'scraper': TavastiaAdvancedScraper(self.frontend_path),
        })
        
        # Add more venues here as you create scrapers for them
        # Example:
        # self.scrapers.append({
        #     'name': 'Klubi Taverna',
        #     'scraper': TavernaScraper(self.frontend_path),
        # })

    def run_all(self) -> Dict:
        """Run all scrapers and collect results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'venues': [],
            'total_new_events': 0,
            'errors': []
        }
        
        print("=" * 60)
        print("🎸 Dark Suomi Multi-Venue Event Scraper")
        print("=" * 60)
        print()
        
        for scraper_info in self.scrapers:
            venue_name = scraper_info['name']
            scraper = scraper_info['scraper']
            
            print(f"🎤 Scraping {venue_name}...")
            print("-" * 60)
            
            try:
                success = scraper.run()
                
                if success:
                    results['venues'].append({
                        'name': venue_name,
                        'status': 'success',
                    })
                else:
                    results['venues'].append({
                        'name': venue_name,
                        'status': 'failed',
                        'error': 'Scraper returned false'
                    })
                    results['errors'].append(f"{venue_name}: Scraper returned false")
            
            except Exception as e:
                results['venues'].append({
                    'name': venue_name,
                    'status': 'error',
                    'error': str(e)
                })
                results['errors'].append(f"{venue_name}: {e}")
                print(f"✗ Error: {e}")
            
            print()
        
        # Print summary
        print("=" * 60)
        print("📊 Summary")
        print("=" * 60)
        
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
                total_events = len(events) if isinstance(events, list) else 0
                print(f"✓ Total events in database: {total_events}")
        except:
            print("✗ Could not read events file")
            total_events = 0
        
        successful = sum(1 for v in results['venues'] if v['status'] == 'success')
        print(f"✓ Scrapers succeeded: {successful}/{len(self.scrapers)}")
        
        if results['errors']:
            print(f"\n⚠ Errors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
        
        return results

    def save_results(self, results: Dict):
        """Save scraping results log"""
        log_dir = os.path.join(self.frontend_path, '.scraper-logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'scrape_{timestamp}.json')
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📝 Results saved to {log_file}")
        except Exception as e:
            print(f"\n✗ Error saving results: {e}")


def main():
    """Main entry point"""
    scraper = MultiVenueScraper()
    results = scraper.run_all()
    scraper.save_results(results)
    
    # Return non-zero exit code if there were errors
    if results['errors']:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
