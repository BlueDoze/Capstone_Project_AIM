#!/usr/bin/env python3
"""
Test script to ensure NAVIGATION and BUILDING_INFO intents are correctly distinguished
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.app import classify_user_intent

def test_intent_distinction():
    """Test that navigation and building info queries are correctly distinguished"""
    
    test_cases = [
        # Navigation queries - should be NAVIGATION
        ("How do I get to room M1063?", "NAVIGATION"),
        ("Where is Building A?", "NAVIGATION"),
        ("Take me to the cafeteria", "NAVIGATION"),
        ("I need directions to the library", "NAVIGATION"),
        ("How do I find room A101?", "NAVIGATION"),
        ("Show me the way to Building F", "NAVIGATION"),
        ("Navigate to M1063", "NAVIGATION"),
        
        # Building info queries - should be BUILDING_INFO
        ("What is in Building M?", "BUILDING_INFO"),
        ("Tell me about Building A", "BUILDING_INFO"),
        ("What departments are in Building F?", "BUILDING_INFO"),
        ("What facilities does Building H have?", "BUILDING_INFO"),
        ("Describe Building B", "BUILDING_INFO"),
        ("What's inside the M building?", "BUILDING_INFO"),
        ("Which departments are in the student center?", "BUILDING_INFO"),
        ("What can I find in Building A?", "BUILDING_INFO"),
        ("Tell me about the structure of Building C", "BUILDING_INFO"),
        
        # Edge cases
        ("What's in Building M and how do I get there?", None),  # Could be either
    ]
    
    print("=" * 80)
    print("TESTING NAVIGATION vs BUILDING_INFO INTENT DISTINCTION")
    print("=" * 80)
    
    correct = 0
    total = 0
    
    for query, expected_intent in test_cases:
        result = classify_user_intent(query)
        intent = result['intent']
        confidence = result['confidence']
        
        if expected_intent is None:
            # Edge case - just show what it classified as
            print(f"\n📝 Query: '{query}'")
            print(f"   ➡️  Classified as: {intent} (confidence: {confidence:.2f})")
        else:
            total += 1
            match = intent == expected_intent
            if match:
                correct += 1
                emoji = "✅"
            else:
                emoji = "❌"
            
            print(f"\n📝 Query: '{query}'")
            print(f"   Expected: {expected_intent}")
            print(f"   {emoji} Got: {intent} (confidence: {confidence:.2f})")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {correct}/{total} correct ({correct/total*100:.1f}%)")
    print("=" * 80)
    
    if correct == total:
        print("✅ All test cases passed!")
    else:
        print(f"⚠️  {total - correct} test case(s) failed")

def main():
    """Run all tests"""
    print("\n🧪 INTENT DISTINCTION TESTING")
    
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("   Please set it to test the AI model functionality.")
        return
    
    try:
        test_intent_distinction()
        print("\n✅ Testing completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
