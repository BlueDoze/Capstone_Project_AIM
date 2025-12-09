"""
Centralized path configuration for data storage locations.
This module provides consistent paths across the application for all data files.
"""
import os
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / 'src'
DATA_DIR = SRC_DIR / 'data'

# Announcements paths
ANNOUNCEMENTS_DIR = DATA_DIR / 'announcements'
ANNOUNCEMENTS_FILE = ANNOUNCEMENTS_DIR / 'all_courses_announcements.json'

# Ensure directories exist
ANNOUNCEMENTS_DIR.mkdir(parents=True, exist_ok=True)
