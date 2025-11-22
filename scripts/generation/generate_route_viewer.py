#!/usr/bin/env python3
"""
Generate a standalone HTML file with embedded route data for visualization
"""

import json
from pathlib import Path

def generate_html():
    """Generate HTML with embedded GeoJSON data"""
    
    # Load GeoJSON data
    geojson_path = Path('map/corridor_segments_building_m.geojson')
    
    if not geojson_path.exists():
        print(f"❌ Error: {geojson_path} not found")
        return
    
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    # Convert to JSON string for embedding
    geojson_str = json.dumps(geojson_data, indent=2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route Visualization - Building M</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 350px;
            max-height: 90vh;
            overflow-y: auto;
            z-index: 1000;
        }}
        .info-panel h2 {{
            margin-top: 0;
            color: #333;
            font-size: 18px;
        }}
        .route-item {{
            padding: 10px;
            margin: 8px 0;
            border-radius: 5px;
            border-left: 4px solid;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .route-item:hover {{
            transform: translateX(-5px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .route-item.entrance {{
            border-left-color: #28a745;
            background: #d4edda;
        }}
        .route-item.exit {{
            border-left-color: #dc3545;
            background: #f8d7da;
        }}
        .route-item.normal {{
            border-left-color: #007bff;
            background: #d1ecf1;
        }}
        .route-item.selected {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .route-name {{
            font-weight: bold;
            color: #333;
            font-size: 14px;
        }}
        .route-desc {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .route-nodes {{
            font-size: 11px;
            color: #999;
            margin-top: 3px;
        }}
        .legend {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 13px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 3px;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 13px;
        }}
        .stats-item {{
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }}
        .toggle-btn {{
            margin: 5px;
            padding: 8px 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
        }}
        .toggle-btn:hover {{
            background: #0056b3;
        }}
        .toggle-btn.active {{
            background: #28a745;
        }}
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 10px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h2>🗺️ Visualização de Rotas</h2>
        
        <div class="stats">
            <div class="stats-item">
                <span>Total de Rotas:</span>
                <strong id="totalRoutes">0</strong>
            </div>
            <div class="stats-item">
                <span>Entradas:</span>
                <strong id="totalEntrances">0</strong>
            </div>
            <div class="stats-item">
                <span>Saídas:</span>
                <strong id="totalExits">0</strong>
            </div>
            <div class="stats-item">
                <span>Nós:</span>
                <strong id="totalNodes">0</strong>
            </div>
        </div>

        <div style="margin: 10px 0;">
            <button class="toggle-btn active" onclick="toggleRoutes('all')">Todas</button>
            <button class="toggle-btn" onclick="toggleRoutes('entrance')">Entradas</button>
            <button class="toggle-btn" onclick="toggleRoutes('exit')">Saídas</button>
            <button class="toggle-btn" onclick="toggleRoutes('normal')">Normais</button>
        </div>
        
        <div id="routeList"></div>
        
        <div class="legend">
            <strong>Legenda:</strong>
            <div class="legend-item">
                <div class="legend-color" style="background: #28a745;"></div>
                <span>Entrada Principal</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #dc3545;"></div>
                <span>Saída</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #007bff;"></div>
                <span>Corredor Normal</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffc107;"></div>
                <span>Rota Selecionada</span>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Embedded GeoJSON data
        const ROUTE_DATA = {geojson_str};

        // Initialize map
        const map = L.map('map').setView([43.01411, -81.19855], 19);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 22,
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        let routeLayers = [];
        let markerLayers = [];
        let allRoutes = [];

        // Color scheme
        const colors = {{
            entrance: '#28a745',
            exit: '#dc3545',
            normal: '#007bff',
            highlight: '#ffc107'
        }};

        // Load and display routes
        function loadRoutes() {{
            try {{
                allRoutes = ROUTE_DATA.features;
                displayRoutes(allRoutes);
                updateStats(allRoutes);
                createRouteList(allRoutes);
                console.log('✅ Routes loaded successfully:', allRoutes.length);
            }} catch (error) {{
                console.error('❌ Error loading routes:', error);
                document.getElementById('routeList').innerHTML = 
                    '<div class="error-message">Erro ao carregar rotas: ' + error.message + '</div>';
            }}
        }}

        function displayRoutes(routes) {{
            // Clear existing layers
            routeLayers.forEach(layer => map.removeLayer(layer));
            markerLayers.forEach(layer => map.removeLayer(layer));
            routeLayers = [];
            markerLayers = [];

            routes.forEach((feature, index) => {{
                const props = feature.properties;
                const coords = feature.geometry.coordinates;
                
                // Determine color
                let color = colors.normal;
                if (props.isEntrance) color = colors.entrance;
                else if (props.isExit) color = colors.exit;
                
                // Convert coordinates to LatLng
                const latLngs = coords.map(coord => [coord[1], coord[0]]);
                
                // Create polyline
                const polyline = L.polyline(latLngs, {{
                    color: color,
                    weight: 4,
                    opacity: 0.7,
                    routeId: index
                }}).addTo(map);
                
                // Add popup
                let popupContent = `<strong>${{props.name}}</strong><br>`;
                if (props.description) popupContent += `${{props.description}}<br>`;
                if (props.startNode || props.endNode) {{
                    popupContent += `<em>${{props.startNode || '?'}} → ${{props.endNode || '?'}}</em><br>`;
                }}
                if (props.length) {{
                    popupContent += `Comprimento: ${{props.length.toFixed(2)}}m`;
                }}
                
                polyline.bindPopup(popupContent);
                
                // Add start/end markers
                const startMarker = L.circleMarker(latLngs[0], {{
                    radius: 6,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                startMarker.bindPopup(`<strong>Início:</strong> ${{props.startNode || 'N/A'}}`);
                
                const endMarker = L.circleMarker(latLngs[latLngs.length - 1], {{
                    radius: 6,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                endMarker.bindPopup(`<strong>Fim:</strong> ${{props.endNode || 'N/A'}}`);
                
                routeLayers.push(polyline);
                markerLayers.push(startMarker, endMarker);
                
                // Store reference
                polyline.routeData = props;
            }});

            // Fit bounds to all routes
            if (routeLayers.length > 0) {{
                const group = L.featureGroup(routeLayers);
                map.fitBounds(group.getBounds().pad(0.1));
            }}
        }}

        function updateStats(routes) {{
            const entrances = routes.filter(r => r.properties.isEntrance).length;
            const exits = routes.filter(r => r.properties.isExit).length;
            const nodes = new Set();
            
            routes.forEach(r => {{
                if (r.properties.startNode) nodes.add(r.properties.startNode);
                if (r.properties.endNode) nodes.add(r.properties.endNode);
            }});
            
            document.getElementById('totalRoutes').textContent = routes.length;
            document.getElementById('totalEntrances').textContent = entrances;
            document.getElementById('totalExits').textContent = exits;
            document.getElementById('totalNodes').textContent = nodes.size;
        }}

        function createRouteList(routes) {{
            const listDiv = document.getElementById('routeList');
            listDiv.innerHTML = '';
            
            routes.forEach((feature, index) => {{
                const props = feature.properties;
                
                let className = 'normal';
                if (props.isEntrance) className = 'entrance';
                else if (props.isExit) className = 'exit';
                
                const routeItem = document.createElement('div');
                routeItem.className = `route-item ${{className}}`;
                routeItem.id = `route-item-${{index}}`;
                routeItem.onclick = () => highlightRoute(index);
                
                let html = `<div class="route-name">${{props.name}}</div>`;
                if (props.description) {{
                    html += `<div class="route-desc">${{props.description}}</div>`;
                }}
                html += `<div class="route-nodes">${{props.startNode || '?'}} ➜ ${{props.endNode || '?'}}</div>`;
                
                routeItem.innerHTML = html;
                listDiv.appendChild(routeItem);
            }});
        }}

        function highlightRoute(index) {{
            // Remove previous selection
            document.querySelectorAll('.route-item').forEach(item => {{
                item.classList.remove('selected');
            }});
            
            // Add selection to clicked item
            const selectedItem = document.getElementById(`route-item-${{index}}`);
            if (selectedItem) {{
                selectedItem.classList.add('selected');
            }}
            
            // Reset all routes
            routeLayers.forEach((layer, i) => {{
                const props = allRoutes[i].properties;
                let color = colors.normal;
                if (props.isEntrance) color = colors.entrance;
                else if (props.isExit) color = colors.exit;
                
                layer.setStyle({{ 
                    color: color, 
                    weight: 4,
                    opacity: 0.7
                }});
            }});
            
            // Highlight selected route
            const selectedLayer = routeLayers[index];
            selectedLayer.setStyle({{ 
                color: colors.highlight,
                weight: 6,
                opacity: 1
            }});
            selectedLayer.openPopup();
            
            // Pan to route
            map.fitBounds(selectedLayer.getBounds().pad(0.2));
        }}

        function toggleRoutes(type) {{
            // Update button states
            document.querySelectorAll('.toggle-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            let filteredRoutes = allRoutes;
            
            if (type === 'entrance') {{
                filteredRoutes = allRoutes.filter(r => r.properties.isEntrance);
            }} else if (type === 'exit') {{
                filteredRoutes = allRoutes.filter(r => r.properties.isExit);
            }} else if (type === 'normal') {{
                filteredRoutes = allRoutes.filter(r => !r.properties.isEntrance && !r.properties.isExit);
            }}
            
            displayRoutes(filteredRoutes);
            createRouteList(filteredRoutes);
        }}

        // Load routes on page load
        loadRoutes();
    </script>
</body>
</html>"""
    
    # Save HTML file
    output_path = Path('tools/route_viewer_standalone.html')
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Generated: {output_path}")
    print(f"📊 Routes included: {len(geojson_data.get('features', []))}")
    print(f"\n🌐 Open this file in your browser:")
    print(f"   file://{output_path.absolute()}")
    print(f"\n   Or double-click the file to open it.")

if __name__ == "__main__":
    generate_html()
