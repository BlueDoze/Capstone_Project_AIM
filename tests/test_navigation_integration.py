"""
Test Navigation Integration
Quick test to verify the navigation API responds correctly
"""

import requests
import json

API_URL = "http://localhost:8081"

def test_chat_navigation():
    """Test chat endpoint with navigation request"""
    print("\n" + "="*60)
    print("Testing Navigation Integration")
    print("="*60)
    
    # Test 1: Simple navigation request
    print("\n1. Testing: 'How do I get to room 1003?'")
    response = requests.post(
        f"{API_URL}/api/chat",
        json={"message": "How do I get to room 1003?"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Response received")
        print(f"  Reply: {data.get('reply', '')[:100]}...")
        
        if 'mapAction' in data:
            print("✓ mapAction present in response")
            map_action = data['mapAction']
            print(f"  Type: {map_action.get('type')}")
            print(f"  Start: Building {map_action.get('start', {}).get('building')}, Floor {map_action.get('start', {}).get('floor')}")
            print(f"  End: Building {map_action.get('end', {}).get('building')}, Floor {map_action.get('end', {}).get('floor')}")
            
            if 'directions' in map_action:
                directions = map_action['directions']
                print(f"✓ Directions generated: {directions.get('total_steps')} steps")
        else:
            print("⚠ No mapAction in response (might not be a navigation query)")
    else:
        print(f"✗ Request failed with status {response.status_code}")
    
    # Test 2: Navigation between two rooms
    print("\n2. Testing: 'Navigate from room 1003 to room 1018'")
    response = requests.post(
        f"{API_URL}/api/chat",
        json={"message": "Navigate from room 1003 to room 1018"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Response received")
        
        if 'mapAction' in data:
            print("✓ mapAction present")
            map_action = data['mapAction']
            if 'path' in map_action:
                path_type = map_action['path'].get('type')
                print(f"  Path type: {path_type}")
        else:
            print("⚠ No mapAction in response")
    else:
        print(f"✗ Request failed with status {response.status_code}")
    
    # Test 3: Check navigation endpoints directly
    print("\n3. Testing direct navigation API")
    response = requests.get(f"{API_URL}/api/navigation/buildings")
    
    if response.status_code == 200:
        data = response.json()
        buildings = data.get('buildings', [])
        print(f"✓ Available buildings: {buildings}")
    else:
        print(f"✗ Buildings endpoint failed")
    
    # Test 4: Calculate path directly
    print("\n4. Testing direct path calculation")
    response = requests.post(
        f"{API_URL}/api/navigation/calculate",
        json={
            "start": {"building": "M", "floor": "1", "room": "1003"},
            "end": {"building": "M", "floor": "1", "room": "1018"}
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Path calculated")
        if 'directions' in data:
            print(f"  Total steps: {data['directions'].get('total_steps')}")
            print(f"  Summary: {data.get('text_summary', '')[:100]}...")
    else:
        error_data = response.json()
        print(f"✗ Path calculation failed: {error_data.get('error')}")
    
    print("\n" + "="*60)
    print("Navigation Integration Test Complete")
    print("="*60 + "\n")


if __name__ == '__main__':
    print("\nStarting Flask server test...")
    print("Make sure the Flask server is running on http://localhost:8081")
    print("Run: python run_app.py\n")
    
    try:
        # Quick health check
        response = requests.get(f"{API_URL}/system/status", timeout=2)
        if response.status_code == 200:
            print("✓ Server is running\n")
            test_chat_navigation()
        else:
            print("✗ Server not responding correctly")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server")
        print("Please start the Flask server first: python run_app.py")
    except Exception as e:
        print(f"✗ Error: {e}")
