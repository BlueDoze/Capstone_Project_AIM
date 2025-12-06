#!/usr/bin/env python3
"""
Test script for CALENDAR and GRADES handlers
Tests that the handlers correctly read and format data from JSON files
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from api.app import handle_calendar_query, handle_grades_query

def test_calendar_handler():
    """Test the calendar handler"""
    print("=" * 80)
    print("TESTING CALENDAR HANDLER")
    print("=" * 80)
    print()
    
    test_queries = [
        "What are my upcoming deadlines?",
        "When is the final project due?",
        "Show me what's due this week"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 80)
        result = handle_calendar_query(query, {})
        print(result.get('reply', 'No reply')[:500])  # First 500 chars
        print()
        print()

def test_grades_handler():
    """Test the grades handler"""
    print("=" * 80)
    print("TESTING GRADES HANDLER")
    print("=" * 80)
    print()
    
    test_queries = [
        "What are my grades?",
        "How am I doing in INFO-6154?",
        "Show me my performance in all courses"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 80)
        result = handle_grades_query(query, {})
        print(result.get('reply', 'No reply')[:500])  # First 500 chars
        print()
        print()

if __name__ == "__main__":
    print("Checking environment...")
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set in environment")
        sys.exit(1)
    print("✅ GEMINI_API_KEY found")
    print()
    
    test_calendar_handler()
    test_grades_handler()
    
    print("=" * 80)
    print("✅ Handler tests complete!")
    print("=" * 80)
