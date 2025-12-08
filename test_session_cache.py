#!/usr/bin/env python3
"""
Test script for session cache management
Tests the 10-message limit and archiving functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_manager():
    """Test SessionCacheManager functionality"""
    print("🧪 Testing SessionCacheManager")
    print("=" * 60)
    
    # Import after path setup
    from src.api.app import session_manager, sessions
    
    # Test 1: Create session
    print("\n1️⃣ Testing session creation...")
    session_id = session_manager.create_session()
    print(f"   Created session: {session_id[:8]}...")
    
    # Test 2: Add messages within limit
    print("\n2️⃣ Testing message addition (within 10-message limit)...")
    for i in range(5):
        session_manager.add_message(session_id, "user", f"User message {i+1}")
        session_manager.add_message(session_id, "assistant", f"Assistant response {i+1}")
    
    counts = session_manager.get_message_count(session_id)
    print(f"   Active messages: {counts['active']}")
    print(f"   Archived messages: {counts['archived']}")
    assert counts['active'] == 10, f"Expected 10 active messages, got {counts['active']}"
    assert counts['archived'] == 0, f"Expected 0 archived messages, got {counts['archived']}"
    print("   ✅ All 10 messages active, none archived")
    
    # Test 3: Add messages beyond limit (should trigger archiving)
    print("\n3️⃣ Testing message archiving (exceeding 10-message limit)...")
    session_manager.add_message(session_id, "user", "User message 6")
    session_manager.add_message(session_id, "assistant", "Assistant response 6")
    
    counts = session_manager.get_message_count(session_id)
    print(f"   Active messages: {counts['active']}")
    print(f"   Archived messages: {counts['archived']}")
    assert counts['active'] == 10, f"Expected 10 active messages, got {counts['active']}"
    assert counts['archived'] == 2, f"Expected 2 archived messages, got {counts['archived']}"
    print("   ✅ Oldest 2 messages archived, maintaining 10 active")
    
    # Test 4: Add more messages to verify continuous archiving
    print("\n4️⃣ Testing continuous archiving...")
    session_manager.add_message(session_id, "user", "User message 7")
    session_manager.add_message(session_id, "assistant", "Assistant response 7")
    
    counts = session_manager.get_message_count(session_id)
    print(f"   Active messages: {counts['active']}")
    print(f"   Archived messages: {counts['archived']}")
    assert counts['active'] == 10, f"Expected 10 active messages, got {counts['active']}"
    assert counts['archived'] == 4, f"Expected 4 archived messages, got {counts['archived']}"
    print("   ✅ Another 2 messages archived, maintaining 10 active")
    
    # Test 5: Check archive file
    print("\n5️⃣ Testing archive file persistence...")
    archive_dir = project_root / 'data' / 'sessions'
    archive_file = archive_dir / f"{session_id}_archive.json"
    assert archive_file.exists(), "Archive file not found"
    print(f"   Archive file exists: {archive_file}")
    
    import json
    with open(archive_file, 'r') as f:
        archive_data = json.load(f)
    
    print(f"   Archived message count in file: {archive_data['message_count']}")
    assert archive_data['message_count'] == 4, "Archive file has incorrect message count"
    print("   ✅ Archive file saved correctly")
    
    # Test 6: Get active messages
    print("\n6️⃣ Testing active message retrieval...")
    active_messages = session_manager.get_active_messages(session_id)
    print(f"   Retrieved {len(active_messages)} active messages")
    assert len(active_messages) == 10, f"Expected 10 messages, got {len(active_messages)}"
    
    # Verify oldest messages are not in active
    first_message = active_messages[0]
    print(f"   First active message: {first_message['content'][:30]}...")
    assert "message 3" in first_message['content'] or "response 3" in first_message['content'], \
        "First active message should be from pair 3 (messages 1-2 archived)"
    print("   ✅ Correct messages in active list")
    
    # Test 7: Clear session
    print("\n7️⃣ Testing session clear...")
    session_manager.clear_session(session_id, keep_archive=True)
    counts = session_manager.get_message_count(session_id)
    print(f"   Active messages after clear: {counts['active']}")
    print(f"   Archived messages retained: {counts['archived']}")
    assert counts['active'] == 0, "Session not cleared"
    assert counts['archived'] == 4, "Archive should be retained"
    print("   ✅ Session cleared, archive retained")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("\n📊 Summary:")
    print(f"   - Session caching: Working")
    print(f"   - 10-message limit: Enforced")
    print(f"   - Automatic archiving: Working")
    print(f"   - Archive persistence: Working")
    print(f"   - Session management: Working")

if __name__ == "__main__":
    try:
        test_session_manager()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
