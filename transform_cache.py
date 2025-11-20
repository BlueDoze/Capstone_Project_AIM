#!/usr/bin/env python3
"""
Script to transform all_announcements.json to d2l_announcements.json format
"""

import json
from pathlib import Path
from src.services.announcement_transformer import transform_announcements

# Read raw scraper output
with open('all_announcements.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Transform to standardized format
standardized = transform_announcements(raw_data)

# Create data directory if it doesn't exist
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Save to cache
cache_path = data_dir / 'd2l_announcements.json'
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(standardized, f, indent=2, ensure_ascii=False)

print(f"✅ Transformed {len(standardized['announcements'])} announcements")
print(f"📁 Saved to: {cache_path}")
print(f"📅 Last updated: {standardized['last_updated']}")
