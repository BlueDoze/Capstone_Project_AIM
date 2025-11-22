#!/usr/bin/env python3
"""
Test script to validate that the chatbot can find entrance coordinates
when the user types "entrance" or related keywords.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def load_config() -> Dict:
    """Load Building M configuration"""
    config_path = Path('config/building_m_rooms.json')
    with open(config_path, 'r') as f:
        return json.load(f)['Building M']

def load_corridor_segments() -> Dict:
    """Load corridor segments GeoJSON"""
    geojson_path = Path('map/corridor_segments_building_m.geojson')
    with open(geojson_path, 'r') as f:
        return json.load(f)

def resolve_entrance(query: str, config: Dict) -> Optional[Tuple[str, str]]:
    """
    Resolve entrance from user query
    Returns: (room_id, node_id) or None
    """
    query_lower = query.lower().strip()
    
    # Check aliases
    aliases = config.get('aliases', {})
    if query_lower in aliases:
        room_id = aliases[query_lower]
        room_to_node = config.get('roomToNode', {})
        node_id = room_to_node.get(room_id)
        return (room_id, node_id)
    
    return None

def get_entrance_coordinates(room_id: str, config: Dict) -> Optional[Dict[str, float]]:
    """
    Get SVG coordinates for entrance
    Returns: {x, y} or None
    """
    room_centers = config.get('roomCentersSVG', {})
    if room_id in room_centers:
        return room_centers[room_id]
    return None

def find_entrance_in_geojson(geojson_data: Dict, keyword: str = "entrance") -> List[Dict]:
    """
    Find segments marked as entrances in GeoJSON
    Returns: List of matching features
    """
    results = []
    for feature in geojson_data.get('features', []):
        props = feature.get('properties', {})
        
        # Check if marked as entrance
        if props.get('isEntrance'):
            results.append({
                'name': props.get('name'),
                'description': props.get('description'),
                'building': props.get('building'),
                'coordinates': feature.get('geometry', {}).get('coordinates'),
                'keywords': props.get('keywords', [])
            })
        
        # Check keywords
        keywords = props.get('keywords', [])
        if any(keyword.lower() in kw.lower() for kw in keywords):
            if props not in [r['name'] for r in results]:
                results.append({
                    'name': props.get('name'),
                    'description': props.get('description'),
                    'building': props.get('building'),
                    'coordinates': feature.get('geometry', {}).get('coordinates'),
                    'keywords': keywords
                })
    
    return results

def test_entrance_search():
    """Main test function"""
    print("=" * 70)
    print("🧪 TESTING ENTRANCE SEARCH FUNCTIONALITY")
    print("=" * 70)
    
    # Load data
    print("\n📂 Loading configuration files...")
    config = load_config()
    geojson = load_corridor_segments()
    print("✅ Configuration loaded successfully")
    
    # Test queries
    test_queries = [
        "entrance",
        "main entrance",
        "h building",
        "building h",
        "entrance h",
        "h entrance",
        "entrance to h"
    ]
    
    print("\n" + "=" * 70)
    print("🔍 TESTING ALIAS RESOLUTION")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        result = resolve_entrance(query, config)
        if result:
            room_id, node_id = result
            coords = get_entrance_coordinates(room_id, config)
            print(f"   ✅ Found: {room_id} → Node: {node_id}")
            if coords:
                print(f"   📍 SVG Coordinates: x={coords['x']}, y={coords['y']}")
        else:
            print(f"   ❌ Not found in aliases")
    
    print("\n" + "=" * 70)
    print("🗺️  TESTING GEOJSON SEARCH")
    print("=" * 70)
    
    entrance_segments = find_entrance_in_geojson(geojson, "entrance")
    print(f"\n✅ Found {len(entrance_segments)} entrance segment(s):\n")
    
    for segment in entrance_segments:
        print(f"   📍 Segment: {segment['name']}")
        print(f"      Description: {segment['description']}")
        if segment.get('building'):
            print(f"      Building: {segment['building']}")
        print(f"      Keywords: {', '.join(segment['keywords'])}")
        if segment['coordinates']:
            coords = segment['coordinates']
            print(f"      Start: ({coords[0][0]:.8f}, {coords[0][1]:.8f})")
            print(f"      End:   ({coords[-1][0]:.8f}, {coords[-1][1]:.8f})")
        print()
    
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    # Count aliases for entrance-related terms
    aliases = config.get('aliases', {})
    entrance_aliases = [k for k in aliases.keys() if 'entrance' in k.lower() or 'h building' in k.lower()]
    
    print(f"\n✅ Total entrance-related aliases: {len(entrance_aliases)}")
    print(f"✅ Entrance segments in GeoJSON: {len(entrance_segments)}")
    print(f"✅ H-Building node: {config['roomToNode'].get('H-Building', 'NOT FOUND')}")
    
    if config['roomToNode'].get('H-Building'):
        print("\n🎉 SUCCESS! The chatbot should now find the entrance correctly!")
    else:
        print("\n⚠️  WARNING: H-Building not mapped to a node!")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_entrance_search()
