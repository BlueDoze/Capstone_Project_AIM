#!/usr/bin/env python3
"""
Quick route names lister - Simple output showing just route names and basic info
"""

import json
from pathlib import Path

def list_routes_simple():
    """Simple listing of all routes"""
    
    print("=" * 70)
    print("📍 LISTA DE ROTAS NO MAPA")
    print("=" * 70)
    
    # Main corridor segments file
    corridor_file = Path('map/corridor_segments_building_m.geojson')
    
    if corridor_file.exists():
        with open(corridor_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n📄 Arquivo: {corridor_file.name}")
        print("-" * 70)
        
        features = data.get('features', [])
        print(f"\nTotal de rotas: {features.__len__()}\n")
        
        for i, feature in enumerate(features, 1):
            props = feature.get('properties', {})
            name = props.get('name', 'Sem nome')
            desc = props.get('description', '')
            start = props.get('startNode', '?')
            end = props.get('endNode', '?')
            
            print(f"{i}. {name}")
            print(f"   {start} ➜ {end}")
            
            if desc:
                print(f"   💬 {desc}")
            
            # Special markers
            if props.get('isEntrance'):
                print(f"   🚪 ENTRADA PRINCIPAL")
            if props.get('isExit'):
                print(f"   🚪 SAÍDA")
            
            print()
    
    # Route segments file
    route_file = Path('map/route_segments_2025-11-17.geojson')
    
    if route_file.exists():
        with open(route_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n📄 Arquivo: {route_file.name}")
        print("-" * 70)
        
        features = data.get('features', [])
        print(f"\nTotal de rotas: {features.__len__()}\n")
        
        for i, feature in enumerate(features, 1):
            props = feature.get('properties', {})
            name = props.get('name', 'Sem nome')
            
            print(f"{i}. {name}")
            print()
    
    print("=" * 70)

if __name__ == "__main__":
    list_routes_simple()
