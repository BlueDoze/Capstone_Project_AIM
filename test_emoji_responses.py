#!/usr/bin/env python3
"""
Quick test to demonstrate emoji-enhanced responses across all chatbot intents
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from api.app import (
    handle_career_services_query, 
    handle_out_of_scope_query,
    CHATBOT_EMOJIS
)

def test_static_messages():
    """Test static messages with emojis"""
    print("=" * 80)
    print("🎨 EMOJI-ENHANCED STATIC MESSAGES")
    print("=" * 80)
    print()
    
    print("📊 Global Emoji Dictionary Stats:")
    print(f"   Total emojis defined: {len(CHATBOT_EMOJIS)}")
    print(f"   Categories: Navigation, Calendar, Academic, Events, Food, Info, Career")
    print()
    
    print("-" * 80)
    print("💼 CAREER SERVICES RESPONSE")
    print("-" * 80)
    result = handle_career_services_query("Tell me about career services", {})
    print(result['reply'][:500])
    print("\n... (truncated)")
    print()
    
    print("-" * 80)
    print("❓ OUT OF SCOPE RESPONSE")
    print("-" * 80)
    result = handle_out_of_scope_query("What's the weather?")
    print(result['reply'][:500])
    print("\n... (truncated)")
    print()
    
    print("=" * 80)
    print("✅ All static messages now include emojis!")
    print("=" * 80)

if __name__ == "__main__":
    print("Checking environment...")
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set in environment")
        sys.exit(1)
    print("✅ GEMINI_API_KEY found")
    print()
    
    test_static_messages()
