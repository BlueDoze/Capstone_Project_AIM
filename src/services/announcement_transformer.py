"""
Announcement Transformer Service
==================================

Transforms raw D2L scraper output into standardized format for chatbot consumption.
"""

from datetime import datetime
from typing import Dict, Any, List
import re


def transform_announcements(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw scraper output to standardized announcement format.

    Args:
        raw_data: Output from extract_all_announcements.py

    Returns:
        Standardized announcement data structure
    """
    announcements = []

    for raw_announcement in raw_data.get('announcements', []):
        # Skip error entries
        if raw_announcement.get('error'):
            continue

        # Parse announcement
        announcement = {
            'id': f"ann{raw_announcement['index']:03d}",
            'title': raw_announcement.get('title', 'Untitled'),
            'date': parse_announcement_date(raw_announcement.get('date', '')),
            'time': extract_time_from_date(raw_announcement.get('date', '')),
            'posted_by': extract_poster(raw_announcement.get('content', '')),
            'course': raw_data.get('course', 'Unknown'),
            'content': raw_announcement.get('content', ''),
            'url': raw_announcement.get('url', ''),
            'priority': determine_priority(raw_announcement),
            'action_required': detect_action_required(raw_announcement),
            'deadline': extract_deadline(raw_announcement)
        }

        announcements.append(announcement)

    # Sort by date (most recent first)
    announcements.sort(key=lambda x: x['date'], reverse=True)

    return {
        'announcements': announcements,
        'last_updated': datetime.now().isoformat(),
        'total': len(announcements),
        'course': raw_data.get('course', 'Unknown'),
        'source': 'D2L Scraper'
    }


def parse_announcement_date(date_str: str) -> str:
    """
    Parse announcement date string to ISO format.

    Examples:
        "Nov 18, 2025 10:15 AM" -> "2025-11-18"
        "Dec 1, 2025 2:30 PM" -> "2025-12-01"
    """
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')

    try:
        # Try parsing common D2L format: "Nov 18, 2025 10:15 AM"
        parts = date_str.split()
        if len(parts) >= 3:
            month_str = parts[0]
            day_str = parts[1].rstrip(',')
            year_str = parts[2]

            # Convert month abbreviation to number
            months = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }

            month_num = months.get(month_str, '01')
            day_num = day_str.zfill(2)

            return f"{year_str}-{month_num}-{day_num}"
    except:
        pass

    # Fallback
    return datetime.now().strftime('%Y-%m-%d')


def extract_time_from_date(date_str: str) -> str:
    """
    Extract time from date string.

    Example: "Nov 18, 2025 10:15 AM" -> "10:15 AM"
    """
    if not date_str:
        return ''

    # Look for time pattern (e.g., "10:15 AM")
    time_pattern = r'\d{1,2}:\d{2}\s*(?:AM|PM)'
    match = re.search(time_pattern, date_str, re.IGNORECASE)

    if match:
        return match.group(0)

    return ''


def extract_poster(content: str) -> str:
    """
    Extract who posted the announcement from content.

    Looks for patterns like:
        - "Dear all," -> "Instructor"
        - "Hello students," -> "Instructor"
        - Default: "Instructor"
    """
    if not content:
        return 'Instructor'

    # Common patterns
    patterns = [
        (r'(?:Dear|Hi|Hello)\s+(?:all|students|everyone)', 'Instructor'),
        (r'(?:Professor|Dr\.)\s+\w+', 'match'),  # Extract actual name
    ]

    content_lower = content.lower()

    for pattern, poster_type in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            if poster_type == 'match':
                return match.group(0)
            return poster_type

    return 'Instructor'


def determine_priority(announcement: Dict[str, Any]) -> str:
    """
    Determine announcement priority based on content and title.

    Returns: "high", "medium", or "low"
    """
    title = announcement.get('title', '').lower()
    content = announcement.get('content', '').lower()
    combined = title + ' ' + content

    # High priority indicators
    high_priority_keywords = [
        'urgent', 'important', 'deadline', 'exam', 'test', 'quiz',
        'submission', 'due', 'mandatory', 'required', 'cancelled',
        'emergency', 'reminder', 'last chance'
    ]

    # Medium priority indicators
    medium_priority_keywords = [
        'update', 'change', 'new', 'announcement', 'notice',
        'workshop', 'meeting', 'event', 'reminder'
    ]

    # Check for high priority
    for keyword in high_priority_keywords:
        if keyword in combined:
            return 'high'

    # Check for medium priority
    for keyword in medium_priority_keywords:
        if keyword in combined:
            return 'medium'

    return 'low'


def detect_action_required(announcement: Dict[str, Any]) -> bool:
    """
    Detect if announcement requires action from students.

    Returns: True if action is required, False otherwise
    """
    content = announcement.get('content', '').lower()
    title = announcement.get('title', '').lower()
    combined = title + ' ' + content

    # Action indicators
    action_keywords = [
        'submit', 'complete', 'attend', 'register', 'sign up',
        'respond', 'reply', 'confirm', 'fill out', 'please',
        'required', 'must', 'need to', 'have to', 'deadline',
        'due', 'by', 'before'
    ]

    for keyword in action_keywords:
        if keyword in combined:
            return True

    return False


def extract_deadline(announcement: Dict[str, Any]) -> str:
    """
    Extract deadline from announcement content if present.

    Returns: ISO date string or empty string
    """
    content = announcement.get('content', '')
    title = announcement.get('title', '')
    combined = title + ' ' + content

    # Look for date patterns
    # Example: "November 20", "Nov 20", "20/11/2025", "2025-11-20"
    date_patterns = [
        r'(?:due|deadline|by|before)\s+(\w+\s+\d{1,2}(?:,\s+\d{4})?)',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            try:
                # Try to parse and return ISO format
                date_str = match.group(1)
                # Simple parse attempt
                # This is a simplified version - could be enhanced
                return date_str
            except:
                continue

    return ''
