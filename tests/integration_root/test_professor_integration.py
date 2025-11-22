"""
Manual test for professor information extraction.
Based on the D2L page screenshot, we know the actual data is:
  Name: Mohammad Noorchenarboo
  Office: By appointment only
  Office Hours: Please email to arrange a meeting
  Email: mnoorchenarboo@fanshawec.ca

This script creates a sample JSON file for testing the integration.
"""

import json
from pathlib import Path
from datetime import datetime

def create_sample_professor_info(course_id='2001540'):
    """Create sample professor info based on visible data from screenshot."""
    
    professor_data = {
        "course_id": course_id,
        "extracted_at": datetime.now().isoformat(),
        "source_url": f"https://www.fanshaweonline.ca/d2l/home/{course_id}",
        "extraction_method": "manual_from_screenshot",
        "name": "Mohammad Noorchenarboo",
        "email": "mnoorchenarboo@fanshawec.ca",
        "office": "By appointment only",
        "office_hours": "Please email to arrange a meeting",
        "raw_text_preview": "Professor Information\nName: Mohammad Noorchenarboo\nOffice: By appointment only\nOffice Hours: Please email to arrange a meeting\nEmail: mnoorchenarboo@fanshawec.ca"
    }
    
    # Save to expected location
    course_dir = Path(f'data/course_{course_id}')
    course_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = course_dir / 'professor_info.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(professor_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created sample professor info: {output_file}")
    print(f"   Name: {professor_data['name']}")
    print(f"   Email: {professor_data['email']}")
    print(f"   Office: {professor_data['office']}")
    print(f"   Office Hours: {professor_data['office_hours']}")
    
    return professor_data


def test_transformer_integration():
    """Test that announcement transformer can read professor info."""
    
    print("\n" + "="*80)
    print("TESTING ANNOUNCEMENT TRANSFORMER INTEGRATION")
    print("="*80)
    
    from src.services.announcement_transformer import load_professor_info, extract_poster
    
    # Test loading professor info
    prof_info = load_professor_info('2001540')
    
    if prof_info:
        print(f"\n✅ Professor info loaded successfully:")
        print(f"   Name: {prof_info.get('name')}")
        print(f"   Email: {prof_info.get('email')}")
    else:
        print(f"\n❌ Failed to load professor info")
        return False
    
    # Test poster extraction with different announcement patterns
    test_cases = [
        {
            "content": "Dear all,\n\nPlease submit your assignment by Friday.\n\nThank you,\nMohammad",
            "expected": "Mohammad Noorchenarboo"  # Should use cached name
        },
        {
            "content": "Hello students,\n\nClass is cancelled tomorrow.\n\nBest regards,\nMohammad Noorchenarboo",
            "expected": "Mohammad Noorchenarboo"  # Should extract from signature
        },
        {
            "content": "Assignment 2 is now available. Please check the course content.",
            "expected": "Mohammad Noorchenarboo"  # Should use cached name based on content
        }
    ]
    
    print("\n" + "-"*80)
    print("Testing poster extraction:")
    print("-"*80)
    
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        content = test_case["content"]
        expected = test_case["expected"]
        
        result = extract_poster(content, prof_info)
        
        passed = result == expected
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"  Content: {content[:50]}...")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
    
    return all_passed


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  PROFESSOR INFO - MANUAL TEST & INTEGRATION".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Create sample data
    create_sample_professor_info('2001540')
    
    # Test integration
    test_transformer_integration()
    
    print("\n✅ Manual test completed!\n")
