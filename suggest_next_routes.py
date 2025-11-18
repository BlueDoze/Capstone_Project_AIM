#!/usr/bin/env python3
"""
Analyze what routes exist and what routes are missing
Generate a prioritized list of routes to add next
"""

import json
from pathlib import Path
from typing import Dict, Set, List, Tuple

def load_config():
    """Load Building M configuration"""
    with open('config/building_m_rooms.json', 'r') as f:
        return json.load(f)['Building M']

def load_routes():
    """Load existing routes"""
    with open('map/corridor_segments_building_m.geojson', 'r') as f:
        return json.load(f)

def analyze_missing_routes(config: Dict, routes: Dict) -> Dict:
    """Analyze what routes are missing"""
    
    room_to_node = config['roomToNode']
    
    # Get all nodes that should exist
    all_nodes = set(room_to_node.values())
    
    # Get nodes that have routes
    existing_nodes = set()
    existing_connections = set()
    
    for feature in routes['features']:
        props = feature['properties']
        start = props.get('startNode')
        end = props.get('endNode')
        
        if start:
            existing_nodes.add(start)
        if end:
            existing_nodes.add(end)
        
        if start and end:
            # Store both directions
            existing_connections.add((start, end))
            existing_connections.add((end, start))
    
    # Find missing nodes
    missing_nodes = all_nodes - existing_nodes
    
    # Find rooms without connections
    rooms_without_routes = []
    for room_id, node_id in room_to_node.items():
        if node_id not in existing_nodes:
            rooms_without_routes.append((room_id, node_id))
    
    return {
        'all_nodes': all_nodes,
        'existing_nodes': existing_nodes,
        'missing_nodes': missing_nodes,
        'existing_connections': existing_connections,
        'rooms_without_routes': rooms_without_routes,
        'total_nodes': len(all_nodes),
        'covered_nodes': len(existing_nodes),
        'coverage_percent': (len(existing_nodes) / len(all_nodes) * 100) if all_nodes else 0
    }

def suggest_next_routes(config: Dict, analysis: Dict) -> List[Dict]:
    """Suggest what routes should be added next"""
    
    room_to_node = config['roomToNode']
    room_descriptions = config['roomDescriptions']
    
    suggestions = []
    
    # Priority 1: Connect critical rooms first
    critical_rooms = [
        ('Room_1018', 'M1_8', 'HIGH', 'Study Room - needs access'),
        ('Room_1030', 'M1_16', 'HIGH', 'Lab - needs access'),
        ('Room_1033', 'M1_12', 'HIGH', 'Classroom - high traffic'),
        ('Room_1035', 'M1_14', 'MEDIUM', 'Office'),
        ('Room_1037', 'M1_15', 'MEDIUM', 'Meeting Room'),
        ('Room_1040', 'M1_17', 'MEDIUM', 'Workshop'),
        ('Room_1041', 'M1_16', 'MEDIUM', 'Lab - shares node with Room_1030'),
        ('Room_1045', 'M1_Turn_2', 'MEDIUM', 'Studio'),
        ('Room_1049', 'M1_18', 'HIGH', 'Resource Center'),
    ]
    
    # Priority 2: Connect bathrooms
    bathroom_nodes = [
        ('Bathroom-Men', 'M1_9', 'HIGH', 'Essential facility'),
        ('Bathroom-Women', 'M1_11', 'HIGH', 'Essential facility'),
        ('Bathroom-Accessible', 'M1_10', 'HIGH', 'Essential accessibility'),
    ]
    
    # Check which are missing
    for room_id, node_id, priority, note in critical_rooms + bathroom_nodes:
        if node_id in analysis['missing_nodes']:
            suggestions.append({
                'type': 'room',
                'room_id': room_id,
                'node_id': node_id,
                'priority': priority,
                'description': room_descriptions.get(room_id, room_id),
                'note': note
            })
    
    # Priority 3: Connect intersections and turns
    intersections = [
        ('M1_Int_1', 'CRITICAL', 'Main intersection - already partially connected'),
        ('M1_Int_2', 'CRITICAL', 'Second intersection'),
        ('M1_Turn_1', 'HIGH', 'First corridor turn'),
        ('M1_Turn_2', 'HIGH', 'Second corridor turn'),
        ('M1_Turn_3', 'MEDIUM', 'Third corridor turn'),
    ]
    
    for node_id, priority, note in intersections:
        if node_id in analysis['missing_nodes']:
            suggestions.append({
                'type': 'intersection',
                'node_id': node_id,
                'priority': priority,
                'note': note
            })
    
    return suggestions

def generate_route_template(route_info: Dict) -> Dict:
    """Generate a template for the missing route"""
    
    template = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                ["LONGITUDE_START", "LATITUDE_START"],
                ["LONGITUDE_END", "LATITUDE_END"]
            ]
        },
        "properties": {
            "name": f"FILL_IN_NAME (e.g., {route_info.get('node_id', 'M1_X')}_to_Y)",
            "segmentType": "corridor",
            "startNode": "FILL_START_NODE",
            "endNode": route_info.get('node_id', 'FILL_END_NODE'),
            "description": f"Corridor to {route_info.get('description', 'FILL_DESCRIPTION')}",
            "connectsTo": [route_info.get('room_id', 'FILL_ROOM')],
            "keywords": ["FILL", "KEYWORDS"],
            "pointCount": 2,
            "length": 0.0,
            "timestamp": "TO_BE_GENERATED"
        }
    }
    
    return template

def main():
    print("=" * 80)
    print("📋 NEXT ROUTES TO ADD - PRIORITY LIST")
    print("=" * 80)
    
    config = load_config()
    routes = load_routes()
    
    analysis = analyze_missing_routes(config, routes)
    
    # Print coverage summary
    print(f"\n📊 CURRENT COVERAGE:")
    print(f"   Total nodes defined: {analysis['total_nodes']}")
    print(f"   Nodes with routes: {analysis['covered_nodes']}")
    print(f"   Missing nodes: {len(analysis['missing_nodes'])}")
    print(f"   Coverage: {analysis['coverage_percent']:.1f}%")
    
    # Print existing routes
    print(f"\n✅ EXISTING ROUTES ({len(routes['features'])}):")
    for feature in routes['features']:
        props = feature['properties']
        name = props.get('name', 'Unknown')
        desc = props.get('description', '')
        print(f"   • {name}")
        if desc:
            print(f"     {desc}")
    
    # Print missing rooms
    if analysis['rooms_without_routes']:
        print(f"\n❌ ROOMS WITHOUT ROUTES ({len(analysis['rooms_without_routes'])}):")
        for room_id, node_id in sorted(analysis['rooms_without_routes']):
            desc = config['roomDescriptions'].get(room_id, room_id)
            print(f"   • {room_id} ({node_id}) - {desc}")
    
    # Get suggestions
    suggestions = suggest_next_routes(config, analysis)
    
    # Sort by priority
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    suggestions.sort(key=lambda x: priority_order.get(x.get('priority', 'LOW'), 99))
    
    # Print prioritized list
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDED ROUTES TO ADD NEXT")
    print("=" * 80)
    
    current_priority = None
    count = 1
    
    for suggestion in suggestions:
        priority = suggestion.get('priority', 'MEDIUM')
        
        if priority != current_priority:
            print(f"\n{'🔴' if priority == 'CRITICAL' else '🟡' if priority == 'HIGH' else '🟢'} {priority} PRIORITY:")
            current_priority = priority
        
        if suggestion['type'] == 'room':
            print(f"\n{count}. Connect {suggestion['room_id']} (Node: {suggestion['node_id']})")
            print(f"   Description: {suggestion['description']}")
            print(f"   Note: {suggestion['note']}")
            print(f"   Route name: M1_X_{suggestion['node_id']} (X = connecting node)")
        else:
            print(f"\n{count}. Connect {suggestion['node_id']}")
            print(f"   Note: {suggestion['note']}")
        
        count += 1
    
    # Suggested route sequences
    print("\n" + "=" * 80)
    print("🗺️  SUGGESTED ROUTE SEQUENCES")
    print("=" * 80)
    
    sequences = [
        {
            "name": "PATH 2: Continue from M1_Int_1",
            "routes": [
                "M1_Int_1 → M1_Turn_1 (T-intersection)",
                "M1_Turn_1 → M1_8 (Room 1018)",
                "M1_8 → M1_9 (Bathroom-Men)",
                "M1_9 → M1_10 (Bathroom-Accessible)",
                "M1_10 → M1_11 (Bathroom-Women)",
            ]
        },
        {
            "name": "PATH 3: Continue from M1_Int_1 to north wing",
            "routes": [
                "M1_Int_1 → M1_Int_2 (Second intersection)",
                "M1_Int_2 → M1_12 (Room 1033)",
                "M1_12 → M1_Turn_2 (Turn)",
                "M1_Turn_2 → M1_13 (Stairs_2 + Exit_3)",
            ]
        },
        {
            "name": "PATH 4: West wing from M1_Int_2",
            "routes": [
                "M1_Int_2 → M1_14 (Room 1035)",
                "M1_14 → M1_15 (Room 1037)",
                "M1_15 → M1_16 (Room 1030 + Room 1041)",
                "M1_16 → M1_Turn_3 (Turn + Room 1045)",
                "M1_Turn_3 → M1_17 (Room 1040)",
                "M1_17 → M1_18 (Room 1049)",
                "M1_18 → M1_19 (Stairs_3 + Exit_4)",
            ]
        }
    ]
    
    for i, sequence in enumerate(sequences, 1):
        print(f"\n{i}. {sequence['name']}")
        for route in sequence['routes']:
            print(f"   → {route}")
    
    # Next 5 routes recommendation
    print("\n" + "=" * 80)
    print("🎯 IMMEDIATE NEXT 5 ROUTES TO ADD")
    print("=" * 80)
    
    next_five = [
        ("M1_Int_1_M1_Turn_1", "M1_Int_1", "M1_Turn_1", "Main corridor T-intersection"),
        ("M1_Turn_1_M1_8", "M1_Turn_1", "M1_8", "Corridor to Room 1018 (Study Room)"),
        ("M1_8_M1_9", "M1_8", "M1_9", "Corridor to Men's Bathroom"),
        ("M1_9_M1_10", "M1_9", "M1_10", "Between bathrooms"),
        ("M1_10_M1_11", "M1_10", "M1_11", "To Women's Bathroom"),
    ]
    
    print("\nThese routes will connect:")
    print("  • The main intersection to the bathroom area")
    print("  • Room 1018 (Study Room)")
    print("  • All three bathrooms (Men's, Women's, Accessible)")
    print()
    
    for i, (name, start, end, desc) in enumerate(next_five, 1):
        print(f"{i}. {name}")
        print(f"   Start: {start}")
        print(f"   End: {end}")
        print(f"   Description: {desc}")
        print()
    
    print("=" * 80)
    print("\n💡 TIP: Use the coordinate tool to trace these routes on the map!")
    print("   Open: tools/find_room_centers_no_rotation.html")
    print()

if __name__ == "__main__":
    main()
