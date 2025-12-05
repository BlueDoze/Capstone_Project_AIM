"""
Simple test script for navigation services
Run without pytest dependency
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.navigation_service import get_navigation_service
from src.services.direction_service import get_direction_service


def test_navigation_service():
    """Test NavigationService basic functionality"""
    print("\n=== Testing Navigation Service ===")
    
    nav_service = get_navigation_service()
    
    # Test 1: Check data loaded
    print("✓ Navigation service initialized")
    assert nav_service.navigation_data is not None, "Navigation data not loaded"
    print("✓ Navigation data loaded")
    
    # Test 2: Get available buildings
    buildings = nav_service.get_available_buildings()
    print(f"✓ Available buildings: {buildings}")
    assert len(buildings) > 0, "No buildings available"
    
    # Test 3: Get floors for Building M
    floors = nav_service.get_available_floors('M')
    print(f"✓ Available floors for Building M: {floors}")
    
    # Test 4: Get building data
    if 'M' in buildings and '1' in floors:
        data = nav_service.get_building_data('M', '1')
        assert data is not None, "Could not get building data"
        print("✓ Building M Floor 1 data retrieved")
        
        graph = data.get('navigationGraph', {})
        print(f"✓ Navigation graph has {len(graph)} nodes")
        
        # Test 5: Get all rooms
        rooms = nav_service.get_all_rooms('M', '1')
        print(f"✓ Building M Floor 1 has {len(rooms)} rooms")
        
        # Test 6: Test pathfinding if we have enough nodes
        if len(graph) >= 2:
            nodes = list(graph.keys())
            start_node = nodes[0]
            end_node = nodes[min(5, len(nodes) - 1)]
            
            result = nav_service.find_path_single_building('M', '1', start_node, end_node)
            if result:
                print(f"✓ Found path from {start_node} to {end_node}")
                print(f"  Path length: {len(result['path'])} nodes")
            else:
                print(f"  No path exists between {start_node} and {end_node}")
    
    # Test 7: Test building connections
    connection = nav_service.find_building_connection('M', 'H')
    if connection:
        print(f"✓ Found connection between Building M and H")
        print(f"  Exit node: {connection.get('exit')}")
        print(f"  Entry node: {connection.get('entry')}")
    else:
        print("  No direct connection between M and H found")
    
    print("\n=== Navigation Service Tests Passed ===\n")


def test_direction_service():
    """Test DirectionService basic functionality"""
    print("\n=== Testing Direction Service ===")
    
    dir_service = get_direction_service()
    print("✓ Direction service initialized")
    
    # Test 1: Cardinal direction
    assert dir_service.get_cardinal_direction(0) == "north"
    assert dir_service.get_cardinal_direction(90) == "east"
    print("✓ Cardinal direction calculation works")
    
    # Test 2: Turn direction
    assert dir_service.get_turn_direction(0, 0) == "straight"
    turn_right = dir_service.get_turn_direction(0, 90)
    assert "right" in turn_right.lower()
    print("✓ Turn direction calculation works")
    
    # Test 3: Node description
    node = {
        'represents': [{'type': 'room', 'id': '1003'}]
    }
    desc = dir_service.format_node_description(node)
    assert 'room' in desc.lower()
    print("✓ Node description formatting works")
    
    # Test 4: Generate directions for sample path
    path_data = {
        'type': 'single-building',
        'building': 'M',
        'floor': '1',
        'path': ['M1_1', 'M1_2', 'M1_3'],
        'nodes': [
            {'lat': 0, 'lng': 0, 'represents': [{'type': 'room', 'id': '1003'}]},
            {'lat': 1, 'lng': 0, 'represents': [{'type': 'intersection', 'id': 'Int1'}]},
            {'lat': 1, 'lng': 1, 'represents': [{'type': 'room', 'id': '1018'}]}
        ]
    }
    
    directions = dir_service.generate_directions(path_data)
    assert directions['type'] == 'single-building'
    assert len(directions['steps']) == 3
    print(f"✓ Generated {len(directions['steps'])} direction steps")
    
    # Test 5: Text summary
    text = dir_service.generate_text_summary(directions)
    assert len(text) > 0
    print("✓ Text summary generation works")
    
    print("\n=== Direction Service Tests Passed ===\n")


def test_integration():
    """Test full navigation workflow"""
    print("\n=== Testing Integration ===")
    
    nav_service = get_navigation_service()
    dir_service = get_direction_service()
    
    # Get Building M data
    floor_data = nav_service.get_building_data('M', '1')
    if not floor_data:
        print("  Building M Floor 1 data not available - skipping integration test")
        return
    
    graph = floor_data.get('navigationGraph', {})
    nodes = list(graph.keys())
    
    if len(nodes) < 2:
        print("  Not enough nodes for integration test - skipping")
        return
    
    # Find a path
    start_node = nodes[0]
    end_node = nodes[min(5, len(nodes) - 1)]
    
    print(f"  Finding path from {start_node} to {end_node}...")
    path_result = nav_service.find_path('M', '1', start_node, 'M', '1', end_node)
    
    if not path_result:
        print("  No path found between test nodes")
        return
    
    print(f"✓ Path found with {len(path_result['path'])} nodes")
    
    # Generate directions
    directions = dir_service.generate_directions(path_result)
    assert directions is not None
    print(f"✓ Generated {len(directions['steps'])} turn-by-turn instructions")
    
    # Generate text summary
    text = dir_service.generate_text_summary(directions)
    print("✓ Text summary generated:")
    print("\n" + text[:200] + "...\n")
    
    print("=== Integration Test Passed ===\n")


def test_json_files():
    """Test that required JSON files exist and are valid"""
    print("\n=== Testing JSON Files ===")
    
    import json
    
    files = {
        'all_node_data.json': project_root / 'LeafletJS' / 'all_node_data.json',
        'Building positions.JSON': project_root / 'LeafletJS' / 'Building positions.JSON',
        'building_connections.JSON': project_root / 'LeafletJS' / 'building_connections.JSON'
    }
    
    for name, file_path in files.items():
        assert file_path.exists(), f"Required file not found: {file_path}"
        print(f"✓ {name} exists")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, dict), f"{name} is not a valid JSON object"
        print(f"✓ {name} is valid JSON")
    
    print("\n=== JSON Files Tests Passed ===\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("NAVIGATION SYSTEM TEST SUITE")
    print("="*60)
    
    try:
        test_json_files()
        test_navigation_service()
        test_direction_service()
        test_integration()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
