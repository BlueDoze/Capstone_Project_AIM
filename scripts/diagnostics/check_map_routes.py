#!/usr/bin/env python3
"""
Script to analyze and display all routes in the map files.
Shows route names, connections, coordinates, and metadata.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import os

def load_geojson_file(filepath: Path) -> Dict:
    """Load a GeoJSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return {}

def analyze_geojson(filepath: Path, data: Dict) -> Dict[str, Any]:
    """Analyze a GeoJSON file and extract route information"""
    features = data.get('features', [])
    
    analysis = {
        'file': filepath.name,
        'total_features': len(features),
        'routes': [],
        'nodes': set(),
        'buildings': set(),
        'keywords': set()
    }
    
    for feature in features:
        props = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        route_info = {
            'name': props.get('name', 'Unnamed'),
            'type': props.get('segmentType', 'unknown'),
            'start_node': props.get('startNode'),
            'end_node': props.get('endNode'),
            'description': props.get('description'),
            'connects_to': props.get('connectsTo', []),
            'keywords': props.get('keywords', []),
            'length': props.get('length'),
            'point_count': props.get('pointCount'),
            'is_entrance': props.get('isEntrance', False),
            'is_exit': props.get('isExit', False),
            'building': props.get('building'),
            'coordinates': geometry.get('coordinates', [])
        }
        
        analysis['routes'].append(route_info)
        
        # Collect nodes
        if route_info['start_node']:
            analysis['nodes'].add(route_info['start_node'])
        if route_info['end_node']:
            analysis['nodes'].add(route_info['end_node'])
        
        # Collect buildings
        if route_info['building']:
            analysis['buildings'].add(route_info['building'])
        
        # Collect keywords
        for keyword in route_info['keywords']:
            analysis['keywords'].add(keyword)
    
    return analysis

def print_route_analysis(analysis: Dict[str, Any]):
    """Print detailed route analysis"""
    print("\n" + "=" * 80)
    print(f"📄 FILE: {analysis['file']}")
    print("=" * 80)
    
    print(f"\n📊 STATISTICS:")
    print(f"   Total Routes: {analysis['total_features']}")
    print(f"   Unique Nodes: {len(analysis['nodes'])}")
    print(f"   Buildings Connected: {len(analysis['buildings'])}")
    print(f"   Total Keywords: {len(analysis['keywords'])}")
    
    # Count special routes
    entrances = sum(1 for r in analysis['routes'] if r['is_entrance'])
    exits = sum(1 for r in analysis['routes'] if r['is_exit'])
    print(f"   Entrance Routes: {entrances}")
    print(f"   Exit Routes: {exits}")
    
    print(f"\n🗺️  ROUTES:")
    print("-" * 80)
    
    for i, route in enumerate(analysis['routes'], 1):
        print(f"\n{i}. {route['name']}")
        print(f"   Type: {route['type']}")
        
        if route['start_node'] or route['end_node']:
            print(f"   Connection: {route['start_node'] or '?'} → {route['end_node'] or '?'}")
        
        if route['description']:
            print(f"   Description: {route['description']}")
        
        if route['connects_to']:
            print(f"   Connects To: {', '.join(route['connects_to'])}")
        
        if route['building']:
            print(f"   Building: {route['building']}")
        
        if route['keywords']:
            print(f"   Keywords: {', '.join(route['keywords'])}")
        
        if route['length']:
            print(f"   Length: {route['length']:.2f} meters")
        
        if route['is_entrance']:
            print(f"   🚪 ENTRANCE")
        if route['is_exit']:
            print(f"   🚪 EXIT")
        
        if route['coordinates']:
            coord_count = len(route['coordinates'])
            start_coord = route['coordinates'][0]
            end_coord = route['coordinates'][-1]
            print(f"   Coordinates: {coord_count} points")
            print(f"      Start: ({start_coord[0]:.8f}, {start_coord[1]:.8f})")
            print(f"      End:   ({end_coord[0]:.8f}, {end_coord[1]:.8f})")
    
    if analysis['nodes']:
        print("\n" + "-" * 80)
        print(f"\n🔗 ALL NODES ({len(analysis['nodes'])}):")
        nodes_sorted = sorted(analysis['nodes'])
        for i in range(0, len(nodes_sorted), 5):
            print("   " + ", ".join(nodes_sorted[i:i+5]))
    
    if analysis['keywords']:
        print("\n" + "-" * 80)
        print(f"\n🏷️  ALL KEYWORDS ({len(analysis['keywords'])}):")
        keywords_sorted = sorted(analysis['keywords'])
        for i in range(0, len(keywords_sorted), 4):
            print("   " + ", ".join(keywords_sorted[i:i+4]))
    
    if analysis['buildings']:
        print("\n" + "-" * 80)
        print(f"\n🏢 BUILDINGS CONNECTED ({len(analysis['buildings'])}):")
        print("   " + ", ".join(sorted(analysis['buildings'])))

def compare_files(analyses: List[Dict[str, Any]]):
    """Compare multiple GeoJSON files"""
    print("\n\n" + "=" * 80)
    print("📊 COMPARISON BETWEEN FILES")
    print("=" * 80)
    
    for analysis in analyses:
        print(f"\n{analysis['file']}:")
        print(f"   Routes: {analysis['total_features']}")
        print(f"   Nodes: {len(analysis['nodes'])}")
        print(f"   Entrances: {sum(1 for r in analysis['routes'] if r['is_entrance'])}")
        print(f"   Exits: {sum(1 for r in analysis['routes'] if r['is_exit'])}")
    
    # Find common nodes
    if len(analyses) > 1:
        all_nodes = [set(a['nodes']) for a in analyses]
        common_nodes = set.intersection(*all_nodes)
        
        if common_nodes:
            print(f"\n🔗 COMMON NODES ({len(common_nodes)}):")
            print("   " + ", ".join(sorted(common_nodes)))

def main():
    """Main function"""
    print("=" * 80)
    print("🗺️  MAP ROUTES ANALYZER")
    print("=" * 80)
    
    # Find all GeoJSON files in map directory
    map_dir = Path('map')
    
    if not map_dir.exists():
        print(f"❌ Map directory not found: {map_dir}")
        return
    
    geojson_files = [
        map_dir / 'corridor_segments_building_m.geojson',
        map_dir / 'route_segments_2025-11-17.geojson',
        map_dir / '_corridor_segments_building_m.geojson'
    ]
    
    # Filter existing files
    existing_files = [f for f in geojson_files if f.exists()]
    
    if not existing_files:
        print(f"❌ No GeoJSON files found in {map_dir}")
        return
    
    print(f"\n📂 Found {len(existing_files)} GeoJSON file(s):")
    for f in existing_files:
        print(f"   • {f.name}")
    
    # Analyze each file
    analyses = []
    for filepath in existing_files:
        data = load_geojson_file(filepath)
        if data:
            analysis = analyze_geojson(filepath, data)
            analyses.append(analysis)
            print_route_analysis(analysis)
    
    # Compare files
    if len(analyses) > 1:
        compare_files(analyses)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
