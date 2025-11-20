#!/usr/bin/env python3
"""
Diagnostic script to check for common issues with route visualization
"""

import json
from pathlib import Path

def check_geojson_validity():
    """Check if GeoJSON files are valid"""
    print("=" * 70)
    print("🔍 CHECKING GEOJSON FILES")
    print("=" * 70)
    
    files_to_check = [
        'map/corridor_segments_building_m.geojson',
        'map/route_segments_2025-11-17.geojson'
    ]
    
    for filepath in files_to_check:
        path = Path(filepath)
        print(f"\n📄 Checking: {filepath}")
        
        if not path.exists():
            print(f"   ❌ File not found!")
            continue
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Check structure
            if 'type' not in data:
                print(f"   ⚠️  Missing 'type' field")
            elif data['type'] != 'FeatureCollection':
                print(f"   ⚠️  Type is not 'FeatureCollection': {data['type']}")
            else:
                print(f"   ✅ Valid FeatureCollection")
            
            if 'features' not in data:
                print(f"   ❌ Missing 'features' array")
                continue
            
            features = data['features']
            print(f"   ✅ Contains {len(features)} features")
            
            # Check each feature
            for i, feature in enumerate(features):
                if 'type' not in feature or feature['type'] != 'Feature':
                    print(f"   ⚠️  Feature {i}: Invalid type")
                
                if 'geometry' not in feature:
                    print(f"   ⚠️  Feature {i}: Missing geometry")
                elif 'coordinates' not in feature['geometry']:
                    print(f"   ⚠️  Feature {i}: Missing coordinates")
                
                if 'properties' not in feature:
                    print(f"   ⚠️  Feature {i}: Missing properties")
            
            # Count special features
            entrances = sum(1 for f in features if f.get('properties', {}).get('isEntrance'))
            exits = sum(1 for f in features if f.get('properties', {}).get('isExit'))
            print(f"   📊 Entrances: {entrances}, Exits: {exits}")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Parse Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_coordinate_ranges():
    """Check if coordinates are in valid range for Fanshawe"""
    print("\n" + "=" * 70)
    print("📍 CHECKING COORDINATE RANGES")
    print("=" * 70)
    
    # Expected ranges for Fanshawe College
    expected_lat = (43.013, 43.015)
    expected_lon = (-81.200, -81.198)
    
    filepath = Path('map/corridor_segments_building_m.geojson')
    
    if not filepath.exists():
        print(f"   ❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    all_coords = []
    for feature in data.get('features', []):
        coords = feature.get('geometry', {}).get('coordinates', [])
        all_coords.extend(coords)
    
    if not all_coords:
        print("   ❌ No coordinates found")
        return
    
    lons = [c[0] for c in all_coords]
    lats = [c[1] for c in all_coords]
    
    print(f"\n   Longitude range: {min(lons):.8f} to {max(lons):.8f}")
    print(f"   Expected range:  {expected_lon[0]} to {expected_lon[1]}")
    
    print(f"\n   Latitude range:  {min(lats):.8f} to {max(lats):.8f}")
    print(f"   Expected range:  {expected_lat[0]} to {expected_lat[1]}")
    
    # Check if in range
    lon_ok = expected_lon[0] <= min(lons) and max(lons) <= expected_lon[1]
    lat_ok = expected_lat[0] <= min(lats) and max(lats) <= expected_lat[1]
    
    if lon_ok and lat_ok:
        print("\n   ✅ Coordinates are within expected range")
    else:
        if not lon_ok:
            print("\n   ⚠️  Longitudes are outside expected range")
        if not lat_ok:
            print("\n   ⚠️  Latitudes are outside expected range")

def check_node_connectivity():
    """Check if all nodes are properly connected"""
    print("\n" + "=" * 70)
    print("🔗 CHECKING NODE CONNECTIVITY")
    print("=" * 70)
    
    filepath = Path('map/corridor_segments_building_m.geojson')
    
    if not filepath.exists():
        print(f"   ❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Build connectivity graph
    connections = {}
    all_nodes = set()
    
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        start = props.get('startNode')
        end = props.get('endNode')
        
        if start:
            all_nodes.add(start)
            if start not in connections:
                connections[start] = []
            if end:
                connections[start].append(end)
        
        if end:
            all_nodes.add(end)
            if end not in connections:
                connections[end] = []
            if start:
                connections[end].append(start)
    
    print(f"\n   Total unique nodes: {len(all_nodes)}")
    print(f"   Nodes with connections: {len(connections)}")
    
    # Find isolated nodes
    isolated = [node for node in all_nodes if not connections.get(node)]
    
    if isolated:
        print(f"\n   ⚠️  Isolated nodes (no connections): {len(isolated)}")
        for node in isolated:
            print(f"      • {node}")
    else:
        print(f"\n   ✅ All nodes have connections")
    
    # Find nodes with only one connection
    dead_ends = [node for node, conns in connections.items() if len(conns) == 1]
    
    if dead_ends:
        print(f"\n   📍 Dead-end nodes (only 1 connection): {len(dead_ends)}")
        for node in dead_ends[:5]:  # Show first 5
            print(f"      • {node} → {connections[node]}")
        if len(dead_ends) > 5:
            print(f"      ... and {len(dead_ends) - 5} more")

def check_html_files():
    """Check if HTML visualization files exist and are accessible"""
    print("\n" + "=" * 70)
    print("🌐 CHECKING HTML FILES")
    print("=" * 70)
    
    html_files = [
        'tools/visualize_routes.html',
        'tools/route_viewer_standalone.html'
    ]
    
    for filepath in html_files:
        path = Path(filepath)
        print(f"\n   📄 {filepath}")
        
        if path.exists():
            size = path.stat().st_size
            print(f"      ✅ Exists ({size:,} bytes)")
            print(f"      📂 file://{path.absolute()}")
        else:
            print(f"      ❌ Not found")

def main():
    print("=" * 70)
    print("🔧 ROUTE VISUALIZATION DIAGNOSTIC")
    print("=" * 70)
    
    check_geojson_validity()
    check_coordinate_ranges()
    check_node_connectivity()
    check_html_files()
    
    print("\n" + "=" * 70)
    print("✅ DIAGNOSTIC COMPLETE")
    print("=" * 70)
    
    print("\n💡 QUICK FIX:")
    print("   If visualization still doesn't work, try:")
    print("   1. Open route_viewer_standalone.html (has data embedded)")
    print("   2. Check browser console (F12) for errors")
    print("   3. Make sure you're using a modern browser (Chrome/Firefox)")

if __name__ == "__main__":
    main()
