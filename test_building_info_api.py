#!/usr/bin/env python3
"""
End-to-end test for BUILDING_INFO intent through the API
"""
import requests
import json

def test_api_building_info():
    """Test building info queries through the API"""
    
    # Start the Flask server in the background first with: ./devserver.sh
    base_url = "http://localhost:5000"
    
    test_queries = [
        {
            "query": "What is in Building M?",
            "expected_intent": "BUILDING_INFO"
        },
        {
            "query": "Tell me about the student center",
            "expected_intent": "BUILDING_INFO"
        },
        {
            "query": "What facilities does Building A have?",
            "expected_intent": "BUILDING_INFO"
        },
        {
            "query": "Describe all buildings on campus",
            "expected_intent": "BUILDING_INFO"
        }
    ]
    
    print("=" * 80)
    print("TESTING BUILDING_INFO INTENT VIA API")
    print("=" * 80)
    print("\n⚠️  NOTE: This test requires the Flask server to be running.")
    print("   Start it with: ./devserver.sh")
    print()
    
    for test_case in test_queries:
        query = test_case["query"]
        print(f"\n📝 Testing: '{query}'")
        print("-" * 80)
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get('reply', 'No reply')
                
                # Show first 300 characters of response
                preview = reply[:300] + "..." if len(reply) > 300 else reply
                print(f"✅ Status: {response.status_code}")
                print(f"🤖 Response preview:\n{preview}")
                
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Server not running")
            print("   Please start the server with: ./devserver.sh")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)

def main():
    """Run API tests"""
    print("\n🧪 BUILDING_INFO API INTEGRATION TEST")
    test_api_building_info()
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main()
