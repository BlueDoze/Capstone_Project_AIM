#!/usr/bin/env python3
"""
Test script for AI-only intent classification (Phase 1)
Tests the classify_user_intent() function with various query types
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from api.app import classify_user_intent

# Test cases covering all intent categories
TEST_QUERIES = [
    # NAVIGATION queries
    ("How do I get to room 1003?", "NAVIGATION"),
    ("Where is the bathroom?", "NAVIGATION"),
    ("Navigate from Building M to Building H", "NAVIGATION"),
    ("Show me the way to the library", "NAVIGATION"),
    
    # RESTAURANTS queries (including the problematic "hungry" query)
    ("I'm hungry, where should I go?", "RESTAURANTS"),
    ("Where can I eat lunch?", "RESTAURANTS"),
    ("What restaurants are open now?", "RESTAURANTS"),
    ("Is there coffee available?", "RESTAURANTS"),
    
    # EVENTS queries
    ("What events are happening this week?", "EVENTS"),
    ("Are there any workshops today?", "EVENTS"),
    ("Show me upcoming career fairs", "EVENTS"),
    ("What's happening on campus?", "EVENTS"),
    
    # ANNOUNCEMENTS queries
    ("Show me recent D2L announcements", "ANNOUNCEMENTS"),
    ("What are the latest course updates?", "ANNOUNCEMENTS"),
    ("Any new messages from my instructor?", "ANNOUNCEMENTS"),
    ("Check class notifications", "ANNOUNCEMENTS"),
    
    # CAREER_SERVICES queries
    ("How can I improve my resume?", "CAREER_SERVICES"),
    ("Help me prepare for an interview", "CAREER_SERVICES"),
    ("What co-op opportunities are available?", "CAREER_SERVICES"),
    ("Where do I get career counseling?", "CAREER_SERVICES"),
    
    # CALENDAR queries
    ("What are my upcoming deadlines?", "CALENDAR"),
    ("When is the final project due?", "CALENDAR"),
    ("Show me my academic calendar", "CALENDAR"),
    ("What deadlines do I have this week?", "CALENDAR"),
    ("When do I need to submit my assignments?", "CALENDAR"),
    
    # GRADES queries
    ("What are my grades?", "GRADES"),
    ("How am I doing in my courses?", "GRADES"),
    ("Show me my assessment results", "GRADES"),
    ("What's my performance in INFO-6154?", "GRADES"),
    ("Did I pass the midterm exam?", "GRADES"),
    
    # OUT_OF_SCOPE queries
    ("What's the weather today?", "OUT_OF_SCOPE"),
    ("Who won the game last night?", "OUT_OF_SCOPE"),
    ("Tell me a joke", "OUT_OF_SCOPE"),
]

def run_tests():
    """Run all test cases and report results"""
    print("=" * 80)
    print("PHASE 1: AI-ONLY INTENT CLASSIFICATION TEST")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    results = []
    
    for query, expected_intent in TEST_QUERIES:
        try:
            result = classify_user_intent(query)
            actual_intent = result['intent']
            confidence = result['confidence']
            
            # Check if classification matches expected
            is_correct = actual_intent == expected_intent
            
            if is_correct:
                passed += 1
                status = "✅ PASS"
            else:
                failed += 1
                status = "❌ FAIL"
            
            results.append({
                'query': query,
                'expected': expected_intent,
                'actual': actual_intent,
                'confidence': confidence,
                'status': status
            })
            
            print(f"{status} | {confidence:.2f} | {actual_intent:15} | {query[:50]}")
            
        except Exception as e:
            failed += 1
            print(f"❌ ERROR | Exception for query: {query}")
            print(f"   Error: {str(e)}")
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(TEST_QUERIES)}")
    print(f"Passed: {passed} ({passed/len(TEST_QUERIES)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(TEST_QUERIES)*100:.1f}%)")
    print()
    
    # Show failures
    if failed > 0:
        print("FAILED TESTS:")
        print("-" * 80)
        for r in results:
            if r['status'] == "❌ FAIL":
                print(f"Query: {r['query']}")
                print(f"  Expected: {r['expected']}")
                print(f"  Got: {r['actual']} (confidence: {r['confidence']:.2f})")
                print()
    
    return passed, failed

if __name__ == "__main__":
    print("Checking environment...")
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set in environment")
        sys.exit(1)
    print("✅ GEMINI_API_KEY found")
    print()
    
    passed, failed = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
