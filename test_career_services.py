#!/usr/bin/env python3
"""
Test script for Career Services integration
Tests the new CAREER_SERVICES intent and handler functionality
"""

import requests
import json

# Test queries for Career Services
test_queries = [
    "How can I get help with my resume?",
    "I need career counseling",
    "Where can I find co-op opportunities?",
    "Tell me about career services",
    "I need help with job interviews",
    "What mentorship programs are available?",
    "Career fair information",
    "Professional headshot services"
]

print("=" * 70)
print("TESTING CAREER SERVICES INTEGRATION")
print("=" * 70)

base_url = "http://localhost:5000"

# Test each query
for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {query}")
    print("="*70)

    try:
        response = requests.post(
            f'{base_url}/chat',
            json={'message': query},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: SUCCESS")
            print(f"📝 Response:\n{data.get('reply', 'No reply')[:800]}...")
        else:
            print(f"❌ Status: FAILED ({response.status_code})")
            print(f"Response: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Server not running at {base_url}")
        print(f"   Please start the server first with: python3 src/api/app.py")
        break
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT: Request took too long")
    except Exception as e:
        print(f"❌ ERROR: {e}")

print(f"\n{'='*70}")
print("Testing completed!")
print("="*70)
