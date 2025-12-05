#!/usr/bin/env python3
"""
Test script for navigation request parsing
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variable for testing
os.environ.setdefault('GEMINI_API_KEY', 'test_key_not_needed_for_pattern_matching')

print("=" * 80)
print("Testing Navigation Request Parsing")
print("=" * 80)

# Test queries
test_queries = [
    "How do I get to room M1018?",
    "How can I get to M1003?",
    "Navigate to room 1018",
    "Where is room M2004?",
    "Take me to the cafeteria",
    "How do I get to building H room 1005?",
]

print("\n[TEST] Testing Pattern Matching (no AI needed)...\n")

for query in test_queries:
    print(f"\n{'=' * 80}")
    print(f"Query: {query}")
    print(f"{'=' * 80}")
    
    # Import here to trigger initialization
    try:
        from api.app import parse_navigation_request
        result = parse_navigation_request(query, user_position=None)
        
        if result.get('is_navigation'):
            print(f"[OK] SUCCESS - Navigation Request Detected")
            print(f"   Start: {result['start']['location']} ({result['start']['building']}/{result['start']['floor']}) -> {result['start']['node']}")
            print(f"   End: {result['end']['location']} ({result['end']['building']}/{result['end']['floor']}) -> {result['end']['node']}")
        else:
            print(f"[FAIL] FAILED - Not recognized as navigation")
            if 'error' in result:
                print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'=' * 80}")
print("Testing Complete")
print("=" * 80)
