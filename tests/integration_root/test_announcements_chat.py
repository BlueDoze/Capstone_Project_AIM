#!/usr/bin/env python3
"""
Test script for announcements chatbot integration
"""

import requests
import json

# Test queries
test_queries = [
    "What are the latest announcements?",
    "Show me recent D2L news",
    "Any important class updates?",
    "What announcements do I have for my course?"
]

print("=" * 60)
print("TESTING ANNOUNCEMENTS CHATBOT INTEGRATION")
print("=" * 60)

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {query}")
    print("="*60)

    try:
        response = requests.post(
            'http://localhost:5000/chat',
            json={'message': query},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: SUCCESS")
            print(f"📝 Response:\n{data.get('reply', 'No reply')[:500]}...")
        else:
            print(f"❌ Status: FAILED ({response.status_code})")
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*60}")
print("TESTING COMPLETE")
print("="*60)
