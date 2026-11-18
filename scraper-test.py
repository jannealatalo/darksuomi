#!/usr/bin/env python3
"""
Scraper Test Suite
Validates scraper installation and functionality
"""

import sys
import os
import json
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")

def test_python_version():
    """Check Python version"""
    print("🔍 Testing Python version...")
    version = sys.version_info
    min_version = (3, 8)
    
    if version >= min_version:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} is too old")
        print(f"  Minimum required: Python {min_version[0]}.{min_version[1]}")
        return False

def test_dependencies():
    """Test if all required packages are installed"""
    print("🔍 Testing dependencies...")
    
    dependencies = [
        'requests',
        'bs4',
        'lxml',
    ]
    
    all_ok = True
    for package in dependencies:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Install missing packages with:")
        print("   pip install -r scraper-requirements.txt")
    
    return all_ok

def test_project_structure():
    """Check project directory structure"""
    print("🔍 Testing project structure...")
    
    repo_root = Path(__file__).parent
    required_dirs = [
        repo_root / 'frontend',
        repo_root / 'frontend' / 'data',
        repo_root / 'frontend' / 'lib',
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✓ {dir_path.relative_to(repo_root)}")
        else:
            print(f"✗ {dir_path.relative_to(repo_root)} - MISSING")
            all_ok = False
    
    return all_ok

def test_events_file():
    """Check events.json structure"""
    print("🔍 Testing events.json...")
    
    repo_root = Path(__file__).parent
    events_file = repo_root / 'frontend' / 'data' / 'events.json'
    
    if not events_file.exists():
        print(f"✗ {events_file.relative_to(repo_root)} - FILE NOT FOUND")
        return False
    
    try:
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        print(f"✓ File exists and is valid JSON")
        
        if not isinstance(events, list):
            print(f"✗ Root element should be array, got {type(events).__name__}")
            return False
        
        print(f"✓ Contains {len(events)} events")
        
        if events:
            # Check first event structure
            first = events[0]
            required_fields = ['id', 'artist', 'venue', 'city', 'date', 'ticketUrl']
            
            missing = [f for f in required_fields if f not in first]
            if missing:
                print(f"✗ Missing fields: {', '.join(missing)}")
                return False
            
            print(f"✓ Event structure valid")
            print(f"  Example: {first['artist']} @ {first['venue']} ({first['date']})")
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_scraper_import():
    """Test if scraper can be imported"""
    print("🔍 Testing scraper import...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Try importing the advanced scraper
        from scraper_advanced import TavastiaAdvancedScraper
        print(f"✓ scraper-advanced.py imports successfully")
        
        # Try instantiating
        scraper = TavastiaAdvancedScraper()
        print(f"✓ TavastiaAdvancedScraper instantiated")
        
        return True
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_connectivity():
    """Test internet connectivity"""
    print("🔍 Testing internet connectivity...")
    
    try:
        import requests
        response = requests.head('https://www.google.com', timeout=5)
        print(f"✓ Internet connection OK")
        return True
    except Exception as e:
        print(f"⚠ No internet connection: {e}")
        print(f"  Scraper will not work without internet")
        return False

def test_tavastia_access():
    """Test if Tavastia website is accessible"""
    print("🔍 Testing Tavastia website access...")
    
    try:
        import requests
        
        urls = [
            "https://tavastiakluki.fi",
            "https://tavastiaklubi.fi",
        ]
        
        for url in urls:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code < 400:
                    print(f"✓ {url} - Accessible (HTTP {response.status_code})")
                    return True
            except:
                pass
        
        print(f"⚠ Tavastia website not accessible")
        print(f"  Scraper may fail if site is down")
        return False
    
    except Exception as e:
        print(f"⚠ Could not test: {e}")
        return False

def run_full_test():
    """Run all tests and generate report"""
    print_header("🧪 Dark Suomi Scraper Test Suite")
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Project Structure", test_project_structure),
        ("Events File", test_events_file),
        ("Scraper Import", test_scraper_import),
        ("Internet Connection", test_connectivity),
        ("Tavastia Access", test_tavastia_access),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            results[name] = False
    
    # Print summary
    print_header("📊 Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to scrape.")
        print("\nNext steps:")
        print("  1. Run: python scraper-advanced.py")
        print("  2. Check: frontend/data/events.json")
        print("  3. Set up automation: See SCRAPER_SETUP.md")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Fix issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_full_test())
