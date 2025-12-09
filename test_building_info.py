#!/usr/bin/env python3
"""
Test script for BUILDING_INFO intent classification and handling
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.app import classify_user_intent, handle_building_info_query, load_building_info

def test_building_info_intent():
    """Test if building info queries are correctly classified as BUILDING_INFO"""
    
    test_queries = [
        "What is in Building M?",
        "Tell me about the A building",
        "What departments are in Building F?",
        "What facilities does Building H have?",
        "Can you describe Building B?",
        "What's inside the M building?",
        "Which departments are located in the student center?",
        "What can I find in Building A?",
    ]
    
    print("=" * 70)
    print("TESTING BUILDING_INFO INTENT CLASSIFICATION")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = classify_user_intent(query)
        intent = result['intent']
        confidence = result['confidence']
        
        if intent == "BUILDING_INFO":
            print(f"✅ Correctly classified as BUILDING_INFO (confidence: {confidence:.2f})")
        else:
            print(f"❌ Incorrectly classified as {intent} (confidence: {confidence:.2f})")
    
    print("\n" + "=" * 70)

def test_building_data_loading():
    """Test if building data can be loaded"""
    print("\n" + "=" * 70)
    print("TESTING BUILDING DATA LOADING")
    print("=" * 70)
    
    building_data = load_building_info()
    
    if building_data:
        print(f"✅ Successfully loaded building data")
        print(f"📊 Number of buildings: {len(building_data)}")
        print(f"🏢 Buildings found: {', '.join(building_data.keys())}")
        
        # Show sample data for first building
        if building_data:
            first_building = list(building_data.keys())[0]
            print(f"\n📋 Sample data for Building {first_building}:")
            building_info = building_data[first_building]
            for key, value in building_info.items():
                if isinstance(value, list):
                    print(f"  - {key}: {', '.join(str(v) for v in value) if value else 'None'}")
                else:
                    print(f"  - {key}: {value}")
    else:
        print("❌ Failed to load building data")
    
    print("=" * 70)

def test_building_info_handler():
    """Test the building info query handler"""
    print("\n" + "=" * 70)
    print("TESTING BUILDING_INFO HANDLER")
    print("=" * 70)
    
    test_queries = [
        "What is in Building M?",
        "Tell me about all the buildings on campus",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 70)
        
        result = handle_building_info_query(query, {})
        reply = result.get('reply', 'No reply generated')
        
        print(f"🤖 Response:\n{reply}")
        print("-" * 70)
    
    print("=" * 70)

def main():
    """Run all tests"""
    print("\n🧪 BUILDING_INFO INTENT TESTING SUITE")
    print("=" * 70)
    
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("   Please set it to test the AI model functionality.")
        return
    
    try:
        # Test 1: Intent Classification
        test_building_info_intent()
        
        # Test 2: Building Data Loading
        test_building_data_loading()
        
        # Test 3: Handler Function
        test_building_info_handler()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
