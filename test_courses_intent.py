#!/usr/bin/env python3
"""
Test script for COURSES intent classification and handling
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.app import classify_user_intent, handle_courses_query, load_courses_info

def test_courses_intent_classification():
    """Test if courses queries are correctly classified as COURSES"""
    
    test_queries = [
        "What courses am I enrolled in?",
        "Show me my courses",
        "Tell me about my Machine Learning course",
        "List all my courses",
        "What's the INFO6154 course about?",
        "Do I have any courses with announcements?",
        "Show me information about Natural Language Processing course",
        "What courses do I have this semester?",
    ]
    
    print("=" * 70)
    print("TESTING COURSES INTENT CLASSIFICATION")
    print("=" * 70)
    
    correct = 0
    total = len(test_queries)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = classify_user_intent(query)
        intent = result['intent']
        confidence = result['confidence']
        
        if intent == "COURSES":
            print(f"✅ Correctly classified as COURSES (confidence: {confidence:.2f})")
            correct += 1
        else:
            print(f"❌ Incorrectly classified as {intent} (confidence: {confidence:.2f})")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {correct}/{total} correct ({correct/total*100:.1f}%)")
    print("=" * 70)

def test_courses_data_loading():
    """Test if courses data can be loaded"""
    print("\n" + "=" * 70)
    print("TESTING COURSES DATA LOADING")
    print("=" * 70)
    
    courses_data = load_courses_info()
    
    if courses_data:
        print(f"✅ Successfully loaded courses data")
        print(f"📊 Total courses: {courses_data.get('total_courses', 0)}")
        print(f"📚 Processed: {courses_data.get('processed', 0)}")
        print(f"❌ Failed: {courses_data.get('failed', 0)}")
        
        # Show course titles
        courses_list = courses_data.get('courses', [])
        if courses_list:
            print(f"\n📋 Course List:")
            for i, course in enumerate(courses_list, 1):
                title = course.get('title', 'Unknown')
                code = course.get('code', 'N/A')
                print(f"  {i}. {title} ({code})")
        
        # Show sample data for first course
        if courses_list:
            first_course = courses_list[0]
            print(f"\n📖 Sample data for first course:")
            print(f"  Title: {first_course.get('title', 'Unknown')}")
            print(f"  Code: {first_course.get('code', 'N/A')}")
            print(f"  Course ID: {first_course.get('course_id', 'N/A')}")
            print(f"  Widgets: {len(first_course.get('widgets', []))}")
            print(f"  Links: {len(first_course.get('links', []))}")
    else:
        print("❌ Failed to load courses data")
    
    print("=" * 70)

def test_courses_handler():
    """Test the courses query handler"""
    print("\n" + "=" * 70)
    print("TESTING COURSES HANDLER")
    print("=" * 70)
    
    test_queries = [
        "What courses am I enrolled in?",
        "Tell me about my Machine Learning course",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 70)
        
        result = handle_courses_query(query, {})
        reply = result.get('reply', 'No reply generated')
        
        # Show first 500 characters of response
        preview = reply[:500] + "..." if len(reply) > 500 else reply
        print(f"🤖 Response:\n{preview}")
        print("-" * 70)
    
    print("=" * 70)

def test_intent_distinction():
    """Test that COURSES queries don't get confused with other intents"""
    print("\n" + "=" * 70)
    print("TESTING INTENT DISTINCTION")
    print("=" * 70)
    
    test_cases = [
        # Should be COURSES
        ("What courses am I taking?", "COURSES"),
        ("Show me my enrolled courses", "COURSES"),
        ("Tell me about INFO6154", "COURSES"),
        
        # Should NOT be COURSES
        ("What announcements do I have?", "ANNOUNCEMENTS"),
        ("What are my grades?", "GRADES"),
        ("Show me my calendar", "CALENDAR"),
        ("What buildings are on campus?", "BUILDING_INFO"),
    ]
    
    correct = 0
    total = 0
    
    for query, expected_intent in test_cases:
        result = classify_user_intent(query)
        intent = result['intent']
        confidence = result['confidence']
        
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
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {correct}/{total} correct ({correct/total*100:.1f}%)")
    print("=" * 70)

def main():
    """Run all tests"""
    print("\n🧪 COURSES INTENT TESTING SUITE")
    print("=" * 70)
    
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("   Please set it to test the AI model functionality.")
        return
    
    try:
        # Test 1: Intent Classification
        test_courses_intent_classification()
        
        # Test 2: Courses Data Loading
        test_courses_data_loading()
        
        # Test 3: Handler Function
        test_courses_handler()
        
        # Test 4: Intent Distinction
        test_intent_distinction()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
