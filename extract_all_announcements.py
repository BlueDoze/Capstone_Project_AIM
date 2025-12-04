#!/usr/bin/env python3
"""
Wrapper script for D2L announcements scraper.
Maintains backward compatibility with old script location.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run from new location
from src.scrapers.d2l.announcements import extract_all_announcements
import asyncio

if __name__ == "__main__":
    asyncio.run(extract_all_announcements())
