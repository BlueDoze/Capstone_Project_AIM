/**
 * Map Controller - Manages Leaflet map initialization and navigation interaction
 * Features:
 * - Load Building M Floor 1 automatically
 * - Handle room click selection for navigation
 * - Display routes with visual markers
 */

// Global variables for map management
let map = null;
let currentSvgMap = null;
let currentCorners = null;
let currentOverlay = null;
let currentGraphData = null;
let manualRoomCenters = {}; // Manual room center coordinates from config

// Navigation state
const navigationState = {
    mode: 'idle', // 'idle' | 'selecting_start' | 'selecting_end'
    startRoom: null,
    startNode: null,
    startCoords: null,
    endRoom: null,
    endNode: null,
    endCoords: null,
    currentFloor: 1,
    currentBuilding: 'M'
};

// Marker icons
const markerIcons = {
    start: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    }),
    end: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    })
};

// Store placed markers
window.navigationMarkers = {
    start: null,
    end: null
};

// Store highlighted nodes and paths
window.highlightedNodes = [];
window.pathLines = [];

// Store route polylines and GeoJSON data
window.routePolylines = [];
window.routeGeoJSONData = null;

// Debug mode flag
const DEBUG_COORDINATES = true;

/**
 * Log debug information about coordinates
 */
function debugLogCoordinates(label, coords, additionalInfo = {}) {
    if (!DEBUG_COORDINATES) return;
    
    console.log(`🔍 [DEBUG] ${label}:`, {
        lat: coords.lat.toFixed(6),
        lng: coords.lng.toFixed(6),
        ...additionalInfo
    });
}

/**
 * Initialize the map
 */
function initializeMap() {
    if (map) return; // Already initialized

    const mapBearing = 21.3;
    map = L.map('map', {
        maxZoom: 22,
        minZoom: 16,
        rotate: true,
        bearing: mapBearing,
        touchRotate: true,
        shiftKeyRotate: true
    }).setView([43.0125, -81.2002], 18);

    // Add tile layer
    L.tileLayer(
        "https://api.maptiler.com/maps/streets-v2/{z}/{x}/{y}.png?key=d3JSA6Uq18jaERqMgDqq",
        {
            attribution: '&copy; <a href="https://www.maptiler.com/">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
            maxZoom: 22
        }
    ).addTo(map);

    // Add rotation display
    const rotationDisplay = document.createElement('div');
    rotationDisplay.id = 'rotation-display';
    rotationDisplay.style.position = 'absolute';
    rotationDisplay.style.top = '10px';
    rotationDisplay.style.right = '10px';
    rotationDisplay.style.background = 'rgba(255, 255, 255, 0.9)';
    rotationDisplay.style.padding = '10px 15px';
    rotationDisplay.style.borderRadius = '5px';
    rotationDisplay.style.fontFamily = 'Arial, sans-serif';
    rotationDisplay.style.fontSize = '16px';
    rotationDisplay.style.fontWeight = 'bold';
    rotationDisplay.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
    rotationDisplay.style.zIndex = '1000';
    rotationDisplay.textContent = 'Rotation: ' + mapBearing + '°';
    document.getElementById('map-container').appendChild(rotationDisplay);

    // Update rotation display when map rotates
    map.on('rotate', function () {
        const bearing = map.getBearing();
        rotationDisplay.textContent = 'Rotation: ' + bearing.toFixed(1) + '°';
    });

    console.log('✅ Map initialized');

    // Load Building M Floor 1
    loadBuildingM();
}

/**
 * Load manual room center coordinates from configuration
 */
async function loadManualRoomCenters() {
    try {
        const response = await fetch('/api/navigation/room-centers');
        const data = await response.json();
        
        manualRoomCenters = data;
        
        // Count how many rooms have manual overrides
        const manualCount = Object.values(data).filter(center => 
            center && center.x !== undefined && center.y !== undefined
        ).length;
        
        console.log(`📍 Loaded room centers: ${manualCount} manual overrides, ${Object.keys(data).length - manualCount} will use auto-calculation`);
        
        return true;
    } catch (error) {
        console.error('❌ Error loading manual room centers:', error);
        manualRoomCenters = {};
        return false;
    }
}

/**
 * Load Building M Floor 1
 */
async function loadBuildingM() {
    if (!floorPlans || !floorPlans['Building M']) {
        console.error('❌ Building M floor plans not found');
        return;
    }

    // Load manual room centers first
    await loadManualRoomCenters();

    // Get building center and load GeoJSON for building bounds
    fetch('/LeafletJS/campus.geojson?ts=' + new Date().getTime())
        .then(response => response.json())
        .then(data => {
            // Find Building M in GeoJSON
            const buildingMFeature = data.features.find(f => f.properties.name === 'Building M');

            if (!buildingMFeature) {
                console.error('❌ Building M not found in GeoJSON');
                return;
            }

            // Get building bounds
            const layer = L.geoJSON(buildingMFeature);
            const bounds = layer.getBounds();
            const center = bounds.getCenter();

            // Calculate corners for SVG overlay
            const corners = [
                L.latLng(bounds.getNorth(), bounds.getWest()),  // top-left
                L.latLng(bounds.getNorth(), bounds.getEast()),  // top-right
                L.latLng(bounds.getSouth(), bounds.getEast()),  // bottom-right
                L.latLng(bounds.getSouth(), bounds.getWest())   // bottom-left
            ];

            const mapBearing = 21.3;
            currentCorners = corners.map(corner => rotatePoint(corner, center, mapBearing));

            // Load SVG floor plan
            const svgPath = '/LeafletJS/Floorplans/Building%20M/M1_official.svg?ts=' + new Date().getTime();

            fetch(svgPath)
                .then(r => r.text())
                .then(svgText => {
                    const svgDoc = new DOMParser().parseFromString(svgText, 'image/svg+xml');
                    currentSvgMap = svgDoc.documentElement;

                    // Add SVG overlay
                    currentOverlay = L.svgOverlay(currentSvgMap, currentCorners, {
                        interactive: true,
                        opacity: 0.5
                    }).addTo(map);

                    // Build navigation graph
                    const floorData = floorPlans['Building M']['floors']['floor1'];
                    const navigationGraph = floorData['navigationGraph'];

                    if (navigationGraph) {
                        currentGraphData = buildNavigationGraph(currentSvgMap, navigationGraph, currentCorners);

                        // Add roomToNode mapping from floor data
                        if (floorData['roomToNode']) {
                            currentGraphData.roomToNode = floorData['roomToNode'];
                            console.log('✅ Loaded roomToNode mapping:', Object.keys(currentGraphData.roomToNode).length, 'rooms');
                        }

                        window.currentGraphData = currentGraphData; // Store globally

                        // Setup room click handlers
                        setupRoomClickHandlers(floorData);

                        console.log('✅ Building M Floor 1 loaded successfully');
                    }
                })
                .catch(err => console.error('❌ Error loading SVG:', err));
        })
        .catch(err => console.error('❌ Error loading GeoJSON:', err));
}

/**
 * Rotate a point around a center by given angle in degrees
 */
function rotatePoint(point, center, angleDeg) {
    const angleRad = (angleDeg * Math.PI) / 180;
    const cos = Math.cos(angleRad);
    const sin = Math.sin(angleRad);

    const dx = point.lng - center.lng;
    const dy = point.lat - center.lat;

    return L.latLng(
        center.lat + (dy * cos - dx * sin),
        center.lng + (dx * cos + dy * sin)
    );
}

/**
 * Convert SVG coordinates to LatLng coordinates
 * Handles rotated elements by applying inverse rotation
 */
function svgCoordsToLatLng(svgX, svgY, svgMap, corners) {
    const svgBBox = svgMap.viewBox.baseVal || {
        x: 0,
        y: 0,
        width: svgMap.width.baseVal.value,
        height: svgMap.height.baseVal.value
    };

    // The nodes are rotated -21.3 degrees in SVG, so we need to handle this
    // For now, we'll work with the coordinates as-is since corners are already rotated
    const normX = (svgX - svgBBox.x) / svgBBox.width;
    const normY = (svgY - svgBBox.y) / svgBBox.height;

    const topLeft = corners[0], topRight = corners[1],
        bottomRight = corners[2], bottomLeft = corners[3];

    // Bilinear interpolation across the rotated quad
    const latTop = topLeft.lat + normX * (topRight.lat - topLeft.lat);
    const lngTop = topLeft.lng + normX * (topRight.lng - topLeft.lng);
    const latBottom = bottomLeft.lat + normX * (bottomRight.lat - bottomLeft.lat);
    const lngBottom = bottomLeft.lng + normX * (bottomRight.lng - bottomLeft.lng);

    const nodeLat = latTop + normY * (latBottom - latTop);
    const nodeLng = lngTop + normY * (lngBottom - lngTop);

    const result = L.latLng(nodeLat, nodeLng);
    debugLogCoordinates(`SVG→LatLng`, result, { 
        svgX: svgX.toFixed(2), 
        svgY: svgY.toFixed(2),
        normX: normX.toFixed(4),
        normY: normY.toFixed(4)
    });

    return result;
}

/**
 * Convert LatLng coordinates to SVG coordinates (inverse of svgCoordsToLatLng)
 * Uses bilinear interpolation to find SVG position from map position
 */
function latLngToSvgCoords(latlng, svgMap, corners) {
    if (!svgMap || !corners || corners.length !== 4) {
        console.error('❌ Invalid parameters for latLngToSvgCoords');
        return null;
    }

    const svgBBox = svgMap.viewBox.baseVal || {
        x: 0,
        y: 0,
        width: svgMap.width.baseVal.value,
        height: svgMap.height.baseVal.value
    };

    const topLeft = corners[0], topRight = corners[1],
        bottomRight = corners[2], bottomLeft = corners[3];

    const targetLat = latlng.lat;
    const targetLng = latlng.lng;

    // Use bilinear interpolation to find normalized coordinates
    // We need to solve:
    // targetLat = latTop + normY * (latBottom - latTop)
    // targetLng = lngTop + normY * (lngBottom - lngTop)
    // where latTop = topLeft.lat + normX * (topRight.lat - topLeft.lat), etc.

    let bestNormX = 0.5, bestNormY = 0.5;
    let bestError = Infinity;

    // Iterative approach: sample grid and refine
    for (let normX = 0; normX <= 1; normX += 0.01) {
        const latTop = topLeft.lat + normX * (topRight.lat - topLeft.lat);
        const lngTop = topLeft.lng + normX * (topRight.lng - topLeft.lng);
        const latBottom = bottomLeft.lat + normX * (bottomRight.lat - bottomLeft.lat);
        const lngBottom = bottomLeft.lng + normX * (bottomRight.lng - bottomLeft.lng);

        // Find normY for this normX
        if (Math.abs(latBottom - latTop) > 0.0001 || Math.abs(lngBottom - lngTop) > 0.0001) {
            // Prefer latitude for interpolation
            let normY;
            if (Math.abs(latBottom - latTop) > Math.abs(lngBottom - lngTop)) {
                normY = (targetLat - latTop) / (latBottom - latTop);
            } else {
                normY = (targetLng - lngTop) / (lngBottom - lngTop);
            }

            // Clamp normY to [0, 1]
            normY = Math.max(0, Math.min(1, normY));

            // Calculate resulting coordinates
            const resultLat = latTop + normY * (latBottom - latTop);
            const resultLng = lngTop + normY * (lngBottom - lngTop);

            // Calculate error
            const error = Math.pow(resultLat - targetLat, 2) + Math.pow(resultLng - targetLng, 2);
            if (error < bestError) {
                bestError = error;
                bestNormX = normX;
                bestNormY = normY;
            }
        }
    }

    // Convert normalized coordinates to SVG coordinates
    const svgX = svgBBox.x + bestNormX * svgBBox.width;
    const svgY = svgBBox.y + bestNormY * svgBBox.height;

    debugLogCoordinates(`LatLng→SVG`, latlng, {
        svgX: svgX.toFixed(2),
        svgY: svgY.toFixed(2),
        normX: bestNormX.toFixed(4),
        normY: bestNormY.toFixed(4),
        error: bestError.toFixed(6)
    });

    return {
        x: parseFloat(svgX.toFixed(2)),
        y: parseFloat(svgY.toFixed(2))
    };
}

/**
 * Convert SVG node to LatLng coordinates
 */
function nodeToLatLng(nodeElement, svgMap, corners) {
    const cx = parseFloat(nodeElement.getAttribute('cx'));
    const cy = parseFloat(nodeElement.getAttribute('cy'));

    return svgCoordsToLatLng(cx, cy, svgMap, corners);
}

/**
 * Calculate the center of a room polygon from SVG
 * Returns LatLng coordinates of the room's visual center
 * Checks for manual override first, then calculates from polygon
 */
function getRoomCenterFromSVG(roomId, svgMap, corners) {
    // Check for manual override first
    if (manualRoomCenters[roomId] && manualRoomCenters[roomId].x !== undefined && manualRoomCenters[roomId].y !== undefined) {
        const manual = manualRoomCenters[roomId];
        console.log(`📌 Using MANUAL center for ${roomId}: (${manual.x}, ${manual.y})`);
        return svgCoordsToLatLng(manual.x, manual.y, svgMap, corners);
    }

    // Find the room element in SVG for automatic calculation
    const roomElement = svgMap.getElementById(roomId);
    
    if (!roomElement) {
        console.warn(`⚠️ Room element ${roomId} not found in SVG`);
        return null;
    }

    try {
        // Get the bounding box of the room element
        const bbox = roomElement.getBBox();
        
        // Calculate center point
        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;

        console.log(`🏢 Room ${roomId} AUTO center in SVG: (${centerX.toFixed(2)}, ${centerY.toFixed(2)})`);

        // Convert to LatLng
        return svgCoordsToLatLng(centerX, centerY, svgMap, corners);
    } catch (error) {
        console.error(`❌ Error calculating center for ${roomId}:`, error);
        return null;
    }
}

/**
 * Build navigation graph from SVG and definitions
 */
function buildNavigationGraph(svgMap, graphDefinition, corners) {
    const graph = {};
    const nodePositions = {};
    const nodeMetadata = {};

    console.log('🔨 Building navigation graph...');

    Object.entries(graphDefinition).forEach(([nodeId, nodeData]) => {
        const nodeElement = svgMap.getElementById(nodeId);

        if (nodeElement) {
            nodePositions[nodeId] = nodeToLatLng(nodeElement, svgMap, corners);
            nodeMetadata[nodeId] = {
                connections: nodeData.connections || [],
                represents: nodeData.represents || null
            };
            console.log(`✓ Found node: ${nodeId}`);
        } else {
            console.error(`✗ Node ${nodeId} NOT FOUND in SVG!`);
        }
    });

    Object.entries(nodeMetadata).forEach(([nodeId, data]) => {
        if (!nodePositions[nodeId]) return;

        graph[nodeId] = data.connections.map(connectedId => {
            if (!nodePositions[connectedId]) {
                console.warn(`⚠️ Connected node ${connectedId} not found`);
                return null;
            }

            const distance = nodePositions[nodeId].distanceTo(nodePositions[connectedId]);
            return { node: connectedId, distance: distance };
        }).filter(n => n !== null);
    });

    console.log('✅ Navigation graph built!');
    return { graph, nodePositions, nodeMetadata };
}

/**
 * Dijkstra's shortest path algorithm
 */
function findShortestPath(graph, startNode, endNode) {
    console.log(`🔍 Finding path: ${startNode} → ${endNode}`);

    if (!graph[startNode] || !graph[endNode]) {
        console.error(`❌ Invalid start/end node`);
        return null;
    }

    const distances = {};
    const previous = {};
    const unvisited = new Set(Object.keys(graph));

    Object.keys(graph).forEach(node => {
        distances[node] = Infinity;
    });
    distances[startNode] = 0;

    while (unvisited.size > 0) {
        let currentNode = null;
        let minDistance = Infinity;
        unvisited.forEach(node => {
            if (distances[node] < minDistance) {
                minDistance = distances[node];
                currentNode = node;
            }
        });

        if (currentNode === null || currentNode === endNode) break;

        unvisited.delete(currentNode);

        if (graph[currentNode]) {
            graph[currentNode].forEach(({ node, distance }) => {
                const newDistance = distances[currentNode] + distance;
                if (newDistance < distances[node]) {
                    distances[node] = newDistance;
                    previous[node] = currentNode;
                }
            });
        }
    }

    const path = [];
    let current = endNode;
    while (current) {
        path.unshift(current);
        current = previous[current];
    }

    if (path[0] !== startNode) {
        console.warn('❌ No path found!');
        return null;
    }

    console.log(`✅ Path: ${path.join(' → ')}`);
    return path;
}

/**
 * Draw path on map
 */
function drawPathOnMap(path, nodePositions, svgMap) {
    console.log('🎨 Drawing path on map...');
    console.log('Path:', path);

    // Clear previous highlights
    if (window.highlightedNodes) {
        window.highlightedNodes.forEach(nodeId => {
            const node = svgMap.getElementById(nodeId);
            if (node) {
                node.style.fill = '';
                node.style.stroke = '';
                node.style.strokeWidth = '';
            }
        });
    }
    window.highlightedNodes = [];

    if (!path || path.length === 0) {
        console.error('❌ No path to draw!');
        return;
    }

    // Highlight each node in the path
    path.forEach((nodeId, index) => {
        const node = svgMap.getElementById(nodeId);
        if (node) {
            node.parentNode.appendChild(node);

            // Start node = green, end node = red, middle nodes = yellow
            if (index === 0) {
                node.style.fill = '#00FF00';
                node.style.stroke = '#00AA00';
            } else if (index === path.length - 1) {
                node.style.fill = '#FF0000';
                node.style.stroke = '#AA0000';
            } else {
                node.style.fill = '#FFFF00';
                node.style.stroke = '#AAAA00';
            }
            node.style.strokeWidth = '2';
            window.highlightedNodes.push(nodeId);
            console.log(`✅ Highlighted node ${index}: ${nodeId}`);
        } else {
            console.error(`❌ Node ${nodeId} not found in SVG!`);
        }
    });

    console.log(`✅ Highlighted ${window.highlightedNodes.length} nodes!`);
}

/**
 * Generate GeoJSON LineString from path
 * @param {Array} path - Array of node IDs representing the route
 * @param {Object} nodePositions - Map of node IDs to LatLng positions
 * @param {Object} nodeMetadata - Map of node IDs to metadata
 * @param {String} startRoom - Starting room ID (optional)
 * @param {String} endRoom - Ending room ID (optional)
 * @returns {Object} GeoJSON Feature object
 */
function generateRouteGeoJSON(path, nodePositions, nodeMetadata, startRoom = null, endRoom = null) {
    if (!path || path.length === 0) {
        console.error('❌ Cannot generate GeoJSON from empty path');
        return null;
    }

    // Build LineString coordinates from path
    const coordinates = path.map(nodeId => {
        const pos = nodePositions[nodeId];
        if (!pos) {
            console.warn(`⚠️ No position found for node ${nodeId}`);
            return null;
        }
        // GeoJSON uses [lng, lat] order (NOT [lat, lng])
        return [pos.lng, pos.lat];
    }).filter(coord => coord !== null);

    if (coordinates.length === 0) {
        console.error('❌ No valid coordinates in path');
        return null;
    }

    // Calculate total distance
    let totalDistance = 0;
    for (let i = 0; i < path.length - 1; i++) {
        const pos1 = nodePositions[path[i]];
        const pos2 = nodePositions[path[i + 1]];
        if (pos1 && pos2) {
            totalDistance += pos1.distanceTo(pos2);
        }
    }

    // Extract rooms along the route
    const roomsAlongRoute = [];
    path.forEach(nodeId => {
        const roomName = getRoomNameFromNode(nodeId, nodeMetadata);
        if (roomName && !roomsAlongRoute.includes(roomName)) {
            roomsAlongRoute.push(roomName);
        }
    });

    // Count turns (nodes with type: "turn" or "intersection")
    let turnCount = 0;
    path.forEach(nodeId => {
        const metadata = nodeMetadata[nodeId];
        if (metadata && metadata.represents) {
            const represents = Array.isArray(metadata.represents) ? metadata.represents : [metadata.represents];
            if (represents.some(r => r.type === 'turn' || r.type === 'intersection')) {
                turnCount++;
            }
        }
    });

    // Build GeoJSON Feature
    const geoJSON = {
        type: "Feature",
        geometry: {
            type: "LineString",
            coordinates: coordinates
        },
        properties: {
            start: startRoom || path[0],
            end: endRoom || path[path.length - 1],
            distance: parseFloat(totalDistance.toFixed(2)),
            distanceUnit: "meters",
            nodes: path,
            nodeCount: path.length,
            rooms: roomsAlongRoute,
            roomCount: roomsAlongRoute.length,
            turns: turnCount,
            building: "M",
            floor: 1,
            timestamp: new Date().toISOString()
        }
    };

    console.log(`✅ Generated GeoJSON route: ${geoJSON.properties.distance}m, ${path.length} nodes, ${turnCount} turns`);
    return geoJSON;
}

/**
 * Render route as Leaflet polyline from GeoJSON
 * @param {Object} geoJSON - GeoJSON Feature with LineString geometry
 * @param {Object} options - Optional styling options
 * @returns {Object} Leaflet polyline layer
 */
function renderRoutePolyline(geoJSON, options = {}) {
    if (!geoJSON || geoJSON.geometry.type !== 'LineString') {
        console.error('❌ Invalid GeoJSON for polyline rendering');
        return null;
    }

    // Default styling
    const defaultOptions = {
        color: '#2196F3',
        weight: 4,
        opacity: 0.8,
        smoothFactor: 1,
        lineJoin: 'round',
        lineCap: 'round'
    };

    const styleOptions = { ...defaultOptions, ...options };

    // Convert GeoJSON coordinates [lng, lat] back to LatLng objects
    const latlngs = geoJSON.geometry.coordinates.map(coord => L.latLng(coord[1], coord[0]));

    // Calculate map center for rotation
    const mapCenter = map.getCenter();
    const mapBearing = -21.3; // Negative to counter-rotate

    // Counter-rotate each point to compensate for the map's bearing
    // The node positions were rotated by +21.3°, but the map view is also rotated by +21.3°
    // This creates double rotation, so we need to apply inverse rotation
    const unrotatedLatLngs = latlngs.map(latlng => rotatePoint(latlng, mapCenter, mapBearing));

    // Create polyline with counter-rotated coordinates
    const polyline = L.polyline(unrotatedLatLngs, styleOptions);

    // Add popup with route info
    if (geoJSON.properties) {
        const props = geoJSON.properties;
        const popupContent = `
            <div style="min-width: 200px;">
                <strong>Route Information</strong><br>
                From: <strong>${props.start}</strong><br>
                To: <strong>${props.end}</strong><br>
                Distance: <strong>${props.distance} ${props.distanceUnit}</strong><br>
                Nodes: ${props.nodeCount}<br>
                Turns: ${props.turns}<br>
                Rooms: ${props.roomCount}
            </div>
        `;
        polyline.bindPopup(popupContent);
    }

    // Add hover effects
    polyline.on('mouseover', function (e) {
        this.setStyle({ weight: 6, opacity: 1 });
    });

    polyline.on('mouseout', function (e) {
        this.setStyle(styleOptions);
    });

    polyline.addTo(map);
    console.log(`✅ Rendered route polyline: ${geoJSON.properties.start} → ${geoJSON.properties.end}`);

    return polyline;
}

/**
 * Clear all route polylines from map
 */
function clearRoutePolylines() {
    if (window.routePolylines && window.routePolylines.length > 0) {
        window.routePolylines.forEach(polyline => {
            if (polyline && map.hasLayer(polyline)) {
                map.removeLayer(polyline);
            }
        });
        window.routePolylines = [];
        console.log('✅ Cleared all route polylines');
    }
}

/**
 * Get room name from node
 */
function getRoomNameFromNode(nodeId, nodeMetadata) {
    const metadata = nodeMetadata[nodeId];
    if (!metadata || !metadata.represents) return null;

    const represents = Array.isArray(metadata.represents) ? metadata.represents : [metadata.represents];
    if (represents.length > 0) {
        return represents[0].id;
    }
    return null;
}

/**
 * Setup room click handlers
 */
function setupRoomClickHandlers(floorData) {
    const rooms = floorData['objects']['rooms'];
    const exits = floorData['objects']['exits'];

    // Room click handlers
    Object.entries(rooms).forEach(([roomId, doorList]) => {
        const room = currentSvgMap.getElementById(roomId);
        if (room) {
            room.style.pointerEvents = 'all';
            room.style.cursor = 'pointer';
            room.addEventListener('click', (e) => {
                e.stopPropagation();
                handleRoomClick(roomId, currentGraphData, currentSvgMap);
            });
        }
    });

    // Exit click handlers
    Object.entries(exits).forEach(([exitId, destinationsList]) => {
        const exit = currentSvgMap.getElementById(exitId);
        if (exit) {
            exit.style.pointerEvents = 'all';
            exit.style.cursor = 'pointer';
            exit.addEventListener('click', (e) => {
                e.stopPropagation();
                handleRoomClick(exitId, currentGraphData, currentSvgMap);
            });
        }
    });
}

/**
 * Handle room click (for Feature 2: Map → Chat)
 */
function handleRoomClick(roomId, graphData, svgMap) {
    if (navigationState.mode === 'idle') {
        return; // Not in selection mode
    }

    if (navigationState.mode === 'selecting_start') {
        // Set start room
        navigationState.startRoom = roomId;
        navigationState.startCoords = getCoordinatesForRoom(roomId, graphData, svgMap);
        navigationState.startNode = getRoomNodeId(roomId, graphData);

        // Place start marker
        if (navigationMarkers.start) {
            map.removeLayer(navigationMarkers.start);
        }
        navigationMarkers.start = L.marker(navigationState.startCoords, {
            icon: markerIcons.start
        }).addTo(map).bindPopup(`Start: ${roomId}`);

        // Update UI
        updateModeIndicator(`Select destination: Click on the destination room`);
        navigationState.mode = 'selecting_end';

        console.log(`✅ Selected start room: ${roomId}`);
    } else if (navigationState.mode === 'selecting_end') {
        // Set end room
        navigationState.endRoom = roomId;
        navigationState.endCoords = getCoordinatesForRoom(roomId, graphData, svgMap);
        navigationState.endNode = getRoomNodeId(roomId, graphData);

        // Place end marker
        if (navigationMarkers.end) {
            map.removeLayer(navigationMarkers.end);
        }
        navigationMarkers.end = L.marker(navigationState.endCoords, {
            icon: markerIcons.end
        }).addTo(map).bindPopup(`Destination: ${roomId}`);

        // Calculate and display path
        const path = findShortestPath(graphData.graph, navigationState.startNode, navigationState.endNode);
        if (path) {
            drawPathOnMap(path, graphData.nodePositions, svgMap);
            map.fitBounds([navigationState.startCoords, navigationState.endCoords]);
        }

        // Send to chat
        sendNavigationRequestToChat(navigationState.startRoom, navigationState.endRoom);

        // Reset mode
        navigationState.mode = 'idle';
        updateModeIndicator('');

        console.log(`✅ Navigation complete: ${navigationState.startRoom} → ${navigationState.endRoom}`);
    }
}

/**
 * Get room node ID from room name
 */
function getRoomNodeId(roomId, graphData) {
    // Search through node metadata for matching room
    for (const [nodeId, metadata] of Object.entries(graphData.nodeMetadata)) {
        if (!metadata.represents) continue;

        const represents = Array.isArray(metadata.represents) ? metadata.represents : [metadata.represents];
        for (const rep of represents) {
            if (rep.id === roomId) {
                return nodeId;
            }
        }
    }
    return null;
}

/**
 * Get coordinates for a room
 * Tries to get room center first (more accurate for markers)
 * Falls back to corridor node position if room center not available
 */
function getCoordinatesForRoom(roomId, graphData, svgMap) {
    // Try to get room center first (more accurate visual position)
    const roomCenter = getRoomCenterFromSVG(roomId, svgMap, currentCorners);
    if (roomCenter) {
        console.log(`✅ Using room center for ${roomId}`);
        return roomCenter;
    }
    
    // Fallback to corridor node (for navigation graph)
    console.log(`⚠️ Room center not found for ${roomId}, using corridor node`);
    const nodeId = getRoomNodeId(roomId, graphData);
    if (nodeId && graphData.nodePositions[nodeId]) {
        return graphData.nodePositions[nodeId];
    }
    
    console.error(`❌ No coordinates found for ${roomId}`);
    return null;
}

/**
 * Update mode indicator
 */
function updateModeIndicator(text) {
    const indicator = document.getElementById('map-mode-indicator');
    if (indicator) {
        indicator.textContent = text;
        if (text) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    }
}

/**
 * Send navigation request to chat
 */
function sendNavigationRequestToChat(startRoom, endRoom) {
    const message = `Navigate from ${startRoom} to ${endRoom}`;

    // Add user message to chat
    const chatWindow = document.getElementById('chat-window');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', 'user-message');
    messageElement.textContent = message;
    chatWindow.appendChild(messageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Send to server
    fetch('/api/navigation/from-clicks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            startRoom: startRoom,
            endRoom: endRoom,
            building: 'M',
            floor: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.reply) {
            const aiMessageElement = document.createElement('div');
            aiMessageElement.classList.add('message', 'ai-message');
            aiMessageElement.innerHTML = data.reply;
            chatWindow.appendChild(aiMessageElement);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    })
    .catch(error => {
        console.error('Error sending navigation request:', error);
    });
}

/**
 * Show route from Feature 1 (Chat → Map)
 */
function showRouteBuildingM(startNode, endNode) {
    if (!currentGraphData) {
        console.error('❌ Navigation graph not loaded');
        return;
    }

    console.log(`🎯 Showing route: ${startNode} → ${endNode}`);

    // Get room names from nodes
    const startRoomName = getRoomNameFromNode(startNode, currentGraphData.nodeMetadata);
    const endRoomName = getRoomNameFromNode(endNode, currentGraphData.nodeMetadata);

    console.log(`📍 Start room: ${startRoomName}, End room: ${endRoomName}`);

    // Check if we have saved segments that match this route
    if (window.routeSegmentsLoader && window.routeSegmentsLoader.loadedSegments.length > 0) {
        const matchingSegment = window.routeSegmentsLoader.findMatchingSegment(
            startRoomName || startNode,
            endRoomName || endNode
        );

        if (matchingSegment) {
            console.log(`✅ Found matching saved segment: ${matchingSegment.properties.name}`);
            // Highlight the matching segment
            window.routeSegmentsLoader.highlightSegment(matchingSegment);
            
            // Add markers for start/end
            const startCoords = getCoordinatesForRoom(startRoomName, currentGraphData, currentSvgMap);
            const endCoords = getCoordinatesForRoom(endRoomName, currentGraphData, currentSvgMap);
            
            if (startCoords && endCoords) {
                // Clear previous markers
                if (navigationMarkers.start) map.removeLayer(navigationMarkers.start);
                if (navigationMarkers.end) map.removeLayer(navigationMarkers.end);

                navigationMarkers.start = L.marker(startCoords, { icon: markerIcons.start })
                    .addTo(map)
                    .bindPopup(`Start: ${startRoomName || startNode}`);
                navigationMarkers.end = L.marker(endCoords, { icon: markerIcons.end })
                    .addTo(map)
                    .bindPopup(`Destination: ${endRoomName || endNode}`);

                // Fit map to show the route
                map.fitBounds([startCoords, endCoords], { padding: [50, 50] });
            }
            
            return; // Use saved segment instead of calculating
        } else {
            console.log('ℹ️ No matching saved segment found, calculating route...');
        }
    }

    // Calculate path using Dijkstra's algorithm
    const path = findShortestPath(currentGraphData.graph, startNode, endNode);

    if (path) {
        // Generate GeoJSON for the route
        const routeGeoJSON = generateRouteGeoJSON(
            path,
            currentGraphData.nodePositions,
            currentGraphData.nodeMetadata,
            startRoomName || startNode,
            endRoomName || endNode
        );

        // Store GeoJSON data globally
        window.routeGeoJSONData = routeGeoJSON;

        // Clear previous polylines
        clearRoutePolylines();

        // Render route as polyline
        if (routeGeoJSON) {
            const polyline = renderRoutePolyline(routeGeoJSON);
            if (polyline) {
                window.routePolylines.push(polyline);
            }
        }

        // Also draw on SVG for backward compatibility (optional - can be disabled)
        drawPathOnMap(path, currentGraphData.nodePositions, currentSvgMap);

        // Get coordinates - prefer room centers for markers
        let startCoords, endCoords;

        if (startRoomName) {
            startCoords = getCoordinatesForRoom(startRoomName, currentGraphData, currentSvgMap);
            console.log(`✅ Using room center for start: ${startRoomName}`);
        } else {
            startCoords = currentGraphData.nodePositions[startNode];
            console.log(`⚠️ Using node position for start: ${startNode}`);
        }

        if (endRoomName) {
            endCoords = getCoordinatesForRoom(endRoomName, currentGraphData, currentSvgMap);
            console.log(`✅ Using room center for end: ${endRoomName}`);
        } else {
            endCoords = currentGraphData.nodePositions[endNode];
            console.log(`⚠️ Using node position for end: ${endNode}`);
        }

        if (startCoords && endCoords) {
            // Add temporary markers
            if (navigationMarkers.start) map.removeLayer(navigationMarkers.start);
            if (navigationMarkers.end) map.removeLayer(navigationMarkers.end);

            const startLabel = startRoomName || startNode;
            const endLabel = endRoomName || endNode;

            navigationMarkers.start = L.marker(startCoords, { icon: markerIcons.start })
                .addTo(map)
                .bindPopup(`Start: ${startLabel}`);
            navigationMarkers.end = L.marker(endCoords, { icon: markerIcons.end })
                .addTo(map)
                .bindPopup(`Destination: ${endLabel}`);

            // Fit bounds
            map.fitBounds([startCoords, endCoords]);
        }
    } else {
        console.error('❌ Could not calculate path');
    }
}

/**
 * Clear route and markers
 */
function clearRoute() {
    // Remove markers
    if (navigationMarkers.start) {
        map.removeLayer(navigationMarkers.start);
        navigationMarkers.start = null;
    }
    if (navigationMarkers.end) {
        map.removeLayer(navigationMarkers.end);
        navigationMarkers.end = null;
    }

    // Clear highlighted nodes
    if (window.highlightedNodes) {
        window.highlightedNodes.forEach(nodeId => {
            const node = currentSvgMap.getElementById(nodeId);
            if (node) {
                node.style.fill = '';
                node.style.stroke = '';
                node.style.strokeWidth = '';
            }
        });
    }
    window.highlightedNodes = [];

    // Clear path
    if (window.pathLines) {
        window.pathLines.forEach(line => {
            if (line.parentNode) {
                line.parentNode.removeChild(line);
            }
        });
    }
    window.pathLines = [];

    // Clear polylines
    clearRoutePolylines();

    // Clear GeoJSON data
    window.routeGeoJSONData = null;

    console.log('✅ Route cleared');
}

/**
 * Start navigation mode (Feature 2: Map → Chat)
 */
function startMapNavigation() {
    navigationState.mode = 'selecting_start';
    navigationState.startRoom = null;
    navigationState.startNode = null;
    navigationState.startCoords = null;
    navigationState.endRoom = null;
    navigationState.endNode = null;
    navigationState.endCoords = null;

    clearRoute();
    updateModeIndicator('Click on your starting location');
    console.log('🗺️ Map navigation mode started');
}

/**
 * Reload room center coordinates from the server
 */
async function reloadCoordinates() {
    const btn = document.getElementById('reloadCoordinatesBtn');

    try {
        // Add loading state
        btn.classList.add('loading');
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = '⟳ Reloading...';

        // Call reload API
        const response = await fetch('/api/navigation/room-centers/reload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Failed to reload coordinates');
        }

        // Reload the manual room centers from the updated config
        await loadManualRoomCenters();

        // Show success message
        btn.textContent = '✓ Reloaded!';
        console.log(`✅ Coordinates reloaded: ${data.room_count} rooms updated`);

        // Reset button after 2 seconds
        setTimeout(() => {
            btn.classList.remove('loading');
            btn.disabled = false;
            btn.textContent = originalText;
        }, 2000);

    } catch (error) {
        console.error('❌ Error reloading coordinates:', error);
        btn.textContent = '✗ Error!';

        // Reset button after 3 seconds
        setTimeout(() => {
            btn.classList.remove('loading');
            btn.disabled = false;
            btn.textContent = '⟲ Reload Coordinates';
        }, 3000);
    }
}

/**
 * Coordinate Editor Modal Functions
 */
const coordinateEditor = {
    MIN_COORD: -1000,
    MAX_COORD: 2000,
    editedCoords: {},
    originalCoords: {},

    /**
     * Initialize the coordinate editor modal
     */
    init() {
        const editBtn = document.getElementById('editCoordinatesBtn');
        const modal = document.getElementById('coordinateEditorModal');
        const closeBtn = document.getElementById('modalCloseBtn');
        const cancelBtn = document.getElementById('cancelEditorBtn');
        const saveBtn = document.getElementById('saveEditorBtn');
        const exportBtn = document.getElementById('exportJsonBtn');
        const importBtn = document.getElementById('importJsonBtn');
        const fileInput = document.getElementById('jsonFileInput');

        if (editBtn) {
            editBtn.addEventListener('click', () => this.openEditor());
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeEditor());
        }
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeEditor());
        }
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveChanges());
        }
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportJson());
        }
        if (importBtn) {
            importBtn.addEventListener('click', () => fileInput.click());
        }
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.importJson(e));
        }

        // Close modal when clicking outside
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeEditor();
                }
            });
        }
    },

    /**
     * Open the coordinate editor modal
     */
    async openEditor() {
        const modal = document.getElementById('coordinateEditorModal');
        if (!modal) return;

        // Load current coordinates
        this.originalCoords = { ...manualRoomCenters };
        this.editedCoords = { ...manualRoomCenters };

        // Populate table
        this.populateTable();

        // Show modal
        modal.classList.remove('hidden');
    },

    /**
     * Close the coordinate editor modal
     */
    closeEditor() {
        const modal = document.getElementById('coordinateEditorModal');
        if (modal) {
            modal.classList.add('hidden');
        }
        this.editedCoords = {};
    },

    /**
     * Populate the coordinate table with all rooms
     */
    populateTable() {
        const tbody = document.getElementById('coordinateTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        // Get all room IDs from current coordinates
        const roomIds = Object.keys(this.editedCoords).filter(k => !k.startsWith('_')).sort();

        roomIds.forEach(roomId => {
            const coords = this.editedCoords[roomId];
            const row = document.createElement('tr');

            const x = coords.x !== undefined ? coords.x : '';
            const y = coords.y !== undefined ? coords.y : '';

            const isValid = this.isValidCoordinate(x, y);
            const hasValue = x !== '' && y !== '';

            let statusClass = 'auto';
            if (hasValue) {
                statusClass = isValid ? 'valid' : 'invalid';
            }

            row.innerHTML = `
                <td><strong>${roomId}</strong></td>
                <td><input type="number" class="coord-input coord-x" data-room="${roomId}" value="${x}" step="0.1"></td>
                <td><input type="number" class="coord-input coord-y" data-room="${roomId}" value="${y}" step="0.1"></td>
                <td><span class="status-badge ${statusClass}">${statusClass.toUpperCase()}</span></td>
                <td><button class="highlight-btn" data-room="${roomId}">Show</button></td>
            `;

            // Add event listeners to inputs
            const xInput = row.querySelector('.coord-x');
            const yInput = row.querySelector('.coord-y');
            const highlightBtn = row.querySelector('.highlight-btn');

            [xInput, yInput].forEach(input => {
                input.addEventListener('input', (e) => {
                    const room = e.target.dataset.room;
                    const x = parseFloat(row.querySelector('.coord-x').value) || '';
                    const y = parseFloat(row.querySelector('.coord-y').value) || '';

                    this.editedCoords[room] = { x, y };

                    // Update status badge
                    const isValid = this.isValidCoordinate(x, y);
                    const statusBadge = row.querySelector('.status-badge');
                    const hasValue = x !== '' && y !== '';

                    statusBadge.className = 'status-badge';
                    if (hasValue) {
                        statusBadge.classList.add(isValid ? 'valid' : 'invalid');
                        statusBadge.textContent = isValid ? 'VALID' : 'INVALID';
                    } else {
                        statusBadge.classList.add('auto');
                        statusBadge.textContent = 'AUTO';
                    }

                    // Update input styling
                    [xInput, yInput].forEach(inp => {
                        inp.classList.remove('valid', 'invalid');
                        if (inp.value) {
                            inp.classList.add(isValid ? 'valid' : 'invalid');
                        }
                    });
                });
            });

            if (highlightBtn) {
                highlightBtn.addEventListener('click', () => {
                    console.log(`Would highlight room: ${roomId}`);
                });
            }

            tbody.appendChild(row);
        });
    },

    /**
     * Validate if coordinates are within acceptable bounds
     */
    isValidCoordinate(x, y) {
        if (x === '' || y === '') return true; // Empty is okay (auto-calculate)
        if (typeof x !== 'number' || typeof y !== 'number') return false;
        return x >= this.MIN_COORD && x <= this.MAX_COORD &&
               y >= this.MIN_COORD && y <= this.MAX_COORD;
    },

    /**
     * Save changes to the server
     */
    async saveChanges() {
        const saveBtn = document.getElementById('saveEditorBtn');
        if (!saveBtn) return;

        try {
            saveBtn.disabled = true;
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '💾 Saving...';

            // Prepare data - only include rooms with coordinates
            const dataToSave = {};
            for (const [roomId, coords] of Object.entries(this.editedCoords)) {
                if (coords.x !== '' && coords.y !== '') {
                    // Validate before sending
                    if (!this.isValidCoordinate(coords.x, coords.y)) {
                        throw new Error(`Invalid coordinates for ${roomId}: (${coords.x}, ${coords.y})`);
                    }
                    dataToSave[roomId] = {
                        x: parseFloat(coords.x),
                        y: parseFloat(coords.y)
                    };
                }
            }

            if (Object.keys(dataToSave).length === 0) {
                throw new Error('No valid coordinates to save');
            }

            // Send to server
            const response = await fetch('/api/navigation/room-centers/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dataToSave)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Failed to save coordinates');
            }

            console.log(`✅ Saved ${result.updated_count} room coordinates`);

            // Reload coordinates and close modal
            await loadManualRoomCenters();
            this.closeEditor();

            // Show success message
            saveBtn.textContent = '✓ Saved!';
            setTimeout(() => {
                saveBtn.disabled = false;
                saveBtn.textContent = originalText;
            }, 2000);

        } catch (error) {
            console.error('❌ Error saving coordinates:', error);
            saveBtn.textContent = '✗ Error!';
            alert(`Error: ${error.message}`);

            setTimeout(() => {
                saveBtn.disabled = false;
                saveBtn.textContent = '💾 Save Changes';
            }, 3000);
        }
    },

    /**
     * Export current coordinates as JSON
     */
    exportJson() {
        const data = {};
        for (const [roomId, coords] of Object.entries(this.editedCoords)) {
            if (coords.x !== '' && coords.y !== '') {
                data[roomId] = {
                    x: parseFloat(coords.x),
                    y: parseFloat(coords.y)
                };
            }
        }

        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `room_coordinates_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    /**
     * Import coordinates from JSON file
     */
    importJson(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);

                // Merge imported data with existing
                for (const [roomId, coords] of Object.entries(data)) {
                    if (coords.x !== undefined && coords.y !== undefined) {
                        this.editedCoords[roomId] = {
                            x: coords.x,
                            y: coords.y
                        };
                    }
                }

                // Refresh table
                this.populateTable();
                console.log(`✅ Imported ${Object.keys(data).length} room coordinates`);

            } catch (error) {
                alert(`Error importing JSON: ${error.message}`);
            }
        };

        reader.readAsText(file);

        // Reset input
        event.target.value = '';
    }
};

/**
 * Calibration Mode - Visual coordinate adjustment without LLM calls
 */
const calibrationMode = {
    active: false,
    selectedRoom: null,
    originalCoords: null,
    previewCoords: null,
    MIN_COORD: -1000,
    MAX_COORD: 2000,

    /**
     * Initialize calibration mode
     */
    init() {
        const calibrateBtn = document.getElementById('calibrateBtn');
        const calibPanel = document.getElementById('calibrationPanel');
        const closeBtn = document.getElementById('calibrationCloseBtn');
        const cancelBtn = document.getElementById('cancelCalibBtn');
        const confirmBtn = document.getElementById('confirmCalibBtn');
        const roomSelect = document.getElementById('calibrationRoomSelect');
        const calibX = document.getElementById('calibX');
        const calibY = document.getElementById('calibY');

        if (calibrateBtn) {
            calibrateBtn.addEventListener('click', () => this.openCalibration());
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeCalibration());
        }
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeCalibration());
        }
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.saveCalibration());
        }
        if (roomSelect) {
            roomSelect.addEventListener('change', (e) => this.selectRoom(e.target.value));
        }
        if (calibX) {
            calibX.addEventListener('input', () => this.updatePreview());
        }
        if (calibY) {
            calibY.addEventListener('input', () => this.updatePreview());
        }
    },

    /**
     * Open calibration panel
     */
    openCalibration() {
        const panel = document.getElementById('calibrationPanel');
        if (!panel) return;

        // Populate room select dropdown
        this.populateRoomSelect();

        // Show panel
        panel.classList.remove('hidden');
        setTimeout(() => panel.classList.add('visible'), 10);
    },

    /**
     * Close calibration panel
     */
    closeCalibration() {
        const panel = document.getElementById('calibrationPanel');
        if (panel) {
            panel.classList.remove('visible');
            setTimeout(() => panel.classList.add('hidden'), 300);
        }

        // Disable map click mode
        this.enableMapClickMode(false);

        // Reset state
        this.selectedRoom = null;
        this.originalCoords = null;
        this.previewCoords = null;
        this.active = false;
    },

    /**
     * Populate room select dropdown with available rooms
     */
    populateRoomSelect() {
        const select = document.getElementById('calibrationRoomSelect');
        if (!select) return;

        // Get all room IDs from manual room centers
        const roomIds = Object.keys(manualRoomCenters)
            .filter(k => !k.startsWith('_'))
            .sort();

        // Keep existing options and add rooms
        const currentValue = select.value;
        const options = select.querySelectorAll('option');

        // Remove room options (keep the first placeholder)
        for (let i = options.length - 1; i > 0; i--) {
            select.removeChild(options[i]);
        }

        // Add room options
        roomIds.forEach(roomId => {
            const option = document.createElement('option');
            option.value = roomId;
            option.textContent = roomId;
            select.appendChild(option);
        });

        // Restore selection if still valid
        if (roomIds.includes(currentValue)) {
            select.value = currentValue;
        }
    },

    /**
     * Select a room for calibration
     */
    selectRoom(roomId) {
        if (!roomId) {
            this.active = false;
            this.enableMapClickMode(false);
            document.getElementById('calibrationInputs').classList.add('hidden');
            document.getElementById('calibrationComparison').classList.add('hidden');
            return;
        }

        this.active = true;
        this.selectedRoom = roomId;
        this.originalCoords = { ...manualRoomCenters[roomId] } || {};

        // Initialize preview with original coordinates
        this.previewCoords = { ...this.originalCoords };

        // Show input section
        const inputsDiv = document.getElementById('calibrationInputs');
        const comparisonDiv = document.getElementById('calibrationComparison');

        if (inputsDiv) inputsDiv.classList.add('hidden'); // Hide inputs, will click on map instead
        if (comparisonDiv) comparisonDiv.classList.remove('hidden');

        // Update display
        this.updateCoordinateDisplay();
        this.showMessage(`Click on the map to set the center for ${roomId}`, 'info');

        // Enable map click mode for calibration
        this.enableMapClickMode(true);
    },

    /**
     * Enable/disable map click mode for calibration
     */
    enableMapClickMode(enable) {
        if (enable && this.selectedRoom) {
            // Show instruction
            const msgDiv = document.getElementById('calibrationMessage');
            if (msgDiv) {
                msgDiv.textContent = `👆 Click on the map to set position for ${this.selectedRoom}`;
                msgDiv.className = 'calibration-message show info';
            }

            // Add map click listener
            if (!this.mapClickListener) {
                this.mapClickListener = (e) => this.handleMapClick(e);
            }
            map.on('click', this.mapClickListener);
        } else {
            // Remove map click listener
            if (this.mapClickListener) {
                map.off('click', this.mapClickListener);
            }
        }
    },

    /**
     * Handle map click during calibration
     */
    handleMapClick(e) {
        if (!this.selectedRoom) return;

        try {
            // Convert Leaflet LatLng to SVG coordinates
            const latlng = e.latlng;
            const svgCoords = latLngToSvgCoords(latlng, currentSvgMap, currentCorners);

            if (!svgCoords) {
                this.showMessage('Click outside map bounds. Try again.', 'error');
                return;
            }

            // Update preview coordinates
            this.previewCoords = {
                x: parseFloat(svgCoords.x.toFixed(2)),
                y: parseFloat(svgCoords.y.toFixed(2))
            };

            // Update display
            this.updateCoordinateDisplay();
            this.showMessage(`Position set: X: ${this.previewCoords.x}, Y: ${this.previewCoords.y} - Click "Save" to confirm`, 'info');

            // Enable save button
            const confirmBtn = document.getElementById('confirmCalibBtn');
            if (confirmBtn) {
                confirmBtn.disabled = false;
            }

            console.log(`📍 Map click captured: (${this.previewCoords.x}, ${this.previewCoords.y})`);

        } catch (error) {
            console.error('❌ Error processing map click:', error);
            this.showMessage('Error reading position. Try again.', 'error');
        }
    },

    /**
     * Update preview coordinates from inputs
     */
    updatePreview() {
        const calibX = document.getElementById('calibX');
        const calibY = document.getElementById('calibY');

        const x = calibX ? parseFloat(calibX.value) || '' : '';
        const y = calibY ? parseFloat(calibY.value) || '' : '';

        this.previewCoords = { x, y };

        // Validate coordinates
        const isValid = this.isValidCoordinate(x, y);

        // Update input styling
        if (calibX) {
            calibX.classList.remove('valid', 'invalid');
            if (x !== '') {
                calibX.classList.add(isValid ? 'valid' : 'invalid');
            }
        }
        if (calibY) {
            calibY.classList.remove('valid', 'invalid');
            if (y !== '') {
                calibY.classList.add(isValid ? 'valid' : 'invalid');
            }
        }

        // Enable/disable save button
        const confirmBtn = document.getElementById('confirmCalibBtn');
        if (confirmBtn) {
            confirmBtn.disabled = !isValid || (x === '' && y === '');
        }

        // Update display
        this.updateCoordinateDisplay();
    },

    /**
     * Validate coordinates
     */
    isValidCoordinate(x, y) {
        if (x === '' || y === '') return false;
        if (typeof x !== 'number' || typeof y !== 'number') return false;
        return x >= this.MIN_COORD && x <= this.MAX_COORD &&
               y >= this.MIN_COORD && y <= this.MAX_COORD;
    },

    /**
     * Update coordinate display
     */
    updateCoordinateDisplay() {
        const currentDisplay = document.getElementById('currentCoordDisplay');
        const previewDisplay = document.getElementById('previewCoordDisplay');

        if (currentDisplay) {
            const x = this.originalCoords.x !== undefined ? this.originalCoords.x : '-';
            const y = this.originalCoords.y !== undefined ? this.originalCoords.y : '-';
            currentDisplay.textContent = `X: ${x}, Y: ${y}`;
        }

        if (previewDisplay) {
            const x = this.previewCoords.x !== '' ? this.previewCoords.x : '-';
            const y = this.previewCoords.y !== '' ? this.previewCoords.y : '-';
            previewDisplay.textContent = `X: ${x}, Y: ${y}`;
        }
    },

    /**
     * Save calibration - update coordinates without LLM call
     */
    async saveCalibration() {
        if (!this.selectedRoom || !this.previewCoords) return;

        const confirmBtn = document.getElementById('confirmCalibBtn');
        if (!confirmBtn) return;

        try {
            confirmBtn.disabled = true;
            const originalText = confirmBtn.textContent;
            confirmBtn.textContent = '💾 Saving...';

            // Validate coordinates
            const x = parseFloat(this.previewCoords.x);
            const y = parseFloat(this.previewCoords.y);

            if (!this.isValidCoordinate(x, y)) {
                throw new Error('Invalid coordinates');
            }

            // Prepare data
            const dataToSave = {
                [this.selectedRoom]: { x, y }
            };

            // Save to server - NO LLM CALL, just coordinate update
            const response = await fetch('/api/navigation/room-centers/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dataToSave)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Failed to save coordinates');
            }

            // Reload coordinates in memory
            await loadManualRoomCenters();

            console.log(`✅ Calibrated ${this.selectedRoom}: (${x}, ${y})`);

            // Show visual feedback on map
            roomCenterVisualizer.showCalibrationFeedback(this.selectedRoom, { x, y });

            // Update room center marker in real-time if centers are visible
            roomCenterVisualizer.updateRoomMarker(this.selectedRoom, { x, y });

            // Show success and close
            this.showMessage('Calibration saved successfully!', 'success');
            confirmBtn.textContent = '✓ Saved!';

            setTimeout(() => {
                this.closeCalibration();
            }, 1500);

        } catch (error) {
            console.error('❌ Error saving calibration:', error);
            this.showMessage(`Error: ${error.message}`, 'error');
            confirmBtn.textContent = '✗ Error!';

            setTimeout(() => {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Save Calibration';
            }, 2000);
        }
    },

    /**
     * Show message in calibration panel
     */
    showMessage(text, type) {
        const msgDiv = document.getElementById('calibrationMessage');
        if (!msgDiv) return;

        msgDiv.textContent = text;
        msgDiv.className = `calibration-message show ${type}`;

        // Auto-hide after 4 seconds for info messages
        if (type === 'info') {
            setTimeout(() => {
                msgDiv.classList.remove('show');
            }, 4000);
        }
    }
};

/**
 * Room Center Visualization - Show calibrated room centers on map
 */
const roomCenterVisualizer = {
    roomCenterLayer: null,
    roomCenterMarkers: {},
    centersVisible: false,

    /**
     * Initialize room center visualizer
     */
    init() {
        const showCentersBtn = document.getElementById('showCentersBtn');
        if (showCentersBtn) {
            showCentersBtn.addEventListener('click', () => this.toggleRoomCenters());
        }
    },

    /**
     * Toggle visibility of room center markers
     */
    toggleRoomCenters() {
        if (this.centersVisible) {
            this.hideRoomCenters();
        } else {
            this.showRoomCenters();
        }
    },

    /**
     * Show all room center markers on map
     */
    showRoomCenters() {
        if (this.roomCenterLayer) {
            map.addLayer(this.roomCenterLayer);
            this.centersVisible = true;
            const btn = document.getElementById('showCentersBtn');
            if (btn) btn.classList.add('active');
            console.log('✅ Room centers displayed');
            return;
        }

        const markerGroup = L.featureGroup();

        // Create markers for all rooms with manual coordinates
        Object.entries(manualRoomCenters).forEach(([roomId, coords]) => {
            if (coords.x !== undefined && coords.y !== undefined) {
                const latlng = svgCoordsToLatLng(coords.x, coords.y, currentSvgMap, currentCorners);

                const marker = L.marker(latlng, {
                    icon: L.icon({
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                        iconSize: [15, 24],
                        iconAnchor: [7.5, 24],
                        popupAnchor: [0, -24],
                        shadowSize: [21, 21]
                    })
                })
                .bindPopup(`<strong>${roomId}</strong><br/>X: ${coords.x.toFixed(2)}<br/>Y: ${coords.y.toFixed(2)}`)
                .on('click', function() {
                    this.openPopup();
                });

                markerGroup.addLayer(marker);
                this.roomCenterMarkers[roomId] = marker;
            }
        });

        markerGroup.addTo(map);
        this.roomCenterLayer = markerGroup;
        this.centersVisible = true;

        const btn = document.getElementById('showCentersBtn');
        if (btn) btn.classList.add('active');

        console.log(`✅ Displayed ${Object.keys(this.roomCenterMarkers).length} room centers`);
    },

    /**
     * Hide all room center markers
     */
    hideRoomCenters() {
        if (this.roomCenterLayer) {
            map.removeLayer(this.roomCenterLayer);
            this.centersVisible = false;

            const btn = document.getElementById('showCentersBtn');
            if (btn) btn.classList.remove('active');

            console.log('✅ Room centers hidden');
        }
    },

    /**
     * Show temporary feedback marker after calibration
     */
    showCalibrationFeedback(roomId, coords) {
        if (!currentSvgMap || !currentCorners) {
            console.warn('Map not fully loaded yet');
            return;
        }

        const latlng = svgCoordsToLatLng(coords.x, coords.y, currentSvgMap, currentCorners);

        // Create feedback marker with special styling
        const feedbackMarker = L.marker(latlng, {
            icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            })
        })
        .addTo(map)
        .bindPopup(`<strong>Calibrated: ${roomId}</strong><br/>X: ${coords.x.toFixed(2)}<br/>Y: ${coords.y.toFixed(2)}<br/><small>Position updated!</small>`, {
            closeButton: true,
            autoClose: false
        })
        .openPopup();

        // Pan map to show the calibrated room
        map.panTo(latlng, {
            animate: true,
            duration: 0.5
        });

        // Optional: Zoom in a bit if too zoomed out
        if (map.getZoom() < 18) {
            map.setZoom(18, { animate: true });
        }

        // Remove feedback marker after 4 seconds
        setTimeout(() => {
            map.removeLayer(feedbackMarker);
            console.log(`✅ Calibration feedback removed for ${roomId}`);
        }, 4000);

        console.log(`✅ Calibration feedback shown for ${roomId} at (${coords.x}, ${coords.y})`);
    },

    /**
     * Update a specific room marker with new coordinates (for real-time updates during calibration)
     */
    updateRoomMarker(roomId, coords) {
        // Only update if centers are currently visible
        if (!this.centersVisible || !this.roomCenterLayer) {
            return;
        }

        if (!currentSvgMap || !currentCorners) {
            console.warn('Map not fully loaded yet');
            return;
        }

        try {
            // Remove old marker if it exists
            if (this.roomCenterMarkers[roomId]) {
                this.roomCenterLayer.removeLayer(this.roomCenterMarkers[roomId]);
            }

            // Create new marker at updated coordinates
            const latlng = svgCoordsToLatLng(coords.x, coords.y, currentSvgMap, currentCorners);

            const newMarker = L.marker(latlng, {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                    iconSize: [15, 24],
                    iconAnchor: [7.5, 24],
                    popupAnchor: [0, -24],
                    shadowSize: [21, 21]
                })
            })
            .bindPopup(`<strong>${roomId}</strong><br/>X: ${coords.x.toFixed(2)}<br/>Y: ${coords.y.toFixed(2)}`)
            .on('click', function() {
                this.openPopup();
            });

            // Add to layer and update reference
            this.roomCenterLayer.addLayer(newMarker);
            this.roomCenterMarkers[roomId] = newMarker;

            console.log(`✅ Updated marker for ${roomId} to (${coords.x}, ${coords.y})`);

        } catch (error) {
            console.error(`❌ Error updating marker for ${roomId}:`, error);
        }
    }
};

// Route Tracer Object
const routeTracer = {
    active: false,
    startRoom: null,
    endRoom: null,
    adjustments: {
        translateX: 0,
        translateY: 0,
        rotation: 0
    },
    currentPolyline: null,
    originalCoordinates: null,

    /**
     * Initialize route tracer
     */
    init() {
        const tracerBtn = document.getElementById('routeTracerBtn');
        const closeBtn = document.getElementById('routeTracerCloseBtn');
        const calculateBtn = document.getElementById('calculateRouteBtn');
        const clearBtn = document.getElementById('clearRouteBtn');
        const exportBtn = document.getElementById('exportGeoJSONBtn');
        const startSelect = document.getElementById('startRoomSelect');
        const endSelect = document.getElementById('endRoomSelect');

        // Adjustment controls
        const translateXSlider = document.getElementById('routeTranslateX');
        const translateYSlider = document.getElementById('routeTranslateY');
        const rotateSlider = document.getElementById('routeRotate');
        const resetBtn = document.getElementById('resetAdjustmentsBtn');

        if (tracerBtn) {
            tracerBtn.addEventListener('click', () => this.openTracer());
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeTracer());
        }
        if (calculateBtn) {
            calculateBtn.addEventListener('click', () => this.calculateRoute());
        }
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearCurrentRoute());
        }
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportGeoJSON());
        }

        // Adjustment event listeners
        if (translateXSlider) {
            translateXSlider.addEventListener('input', (e) => {
                this.adjustments.translateX = parseFloat(e.target.value);
                document.getElementById('translateXValue').textContent = e.target.value;
                this.applyAdjustments();
            });
        }
        if (translateYSlider) {
            translateYSlider.addEventListener('input', (e) => {
                this.adjustments.translateY = parseFloat(e.target.value);
                document.getElementById('translateYValue').textContent = e.target.value;
                this.applyAdjustments();
            });
        }
        if (rotateSlider) {
            rotateSlider.addEventListener('input', (e) => {
                this.adjustments.rotation = parseFloat(e.target.value);
                document.getElementById('rotateValue').textContent = e.target.value;
                this.applyAdjustments();
            });
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetAdjustments());
        }

        if (startSelect) {
            startSelect.addEventListener('change', (e) => this.selectStartRoom(e.target.value));
        }
        if (endSelect) {
            endSelect.addEventListener('change', (e) => this.selectEndRoom(e.target.value));
        }
    },

    /**
     * Open route tracer panel
     */
    openTracer() {
        const panel = document.getElementById('routeTracerPanel');
        if (!panel) return;

        // Populate room dropdowns
        this.populateRoomSelects();

        // Show panel
        panel.classList.remove('hidden');
        setTimeout(() => panel.classList.add('visible'), 10);

        // Activate button
        const tracerBtn = document.getElementById('routeTracerBtn');
        if (tracerBtn) tracerBtn.classList.add('active');

        this.active = true;
    },

    /**
     * Close route tracer panel
     */
    closeTracer() {
        const panel = document.getElementById('routeTracerPanel');
        if (panel) {
            panel.classList.remove('visible');
            setTimeout(() => panel.classList.add('hidden'), 300);
        }

        // Deactivate button
        const tracerBtn = document.getElementById('routeTracerBtn');
        if (tracerBtn) tracerBtn.classList.remove('active');

        // Reset state
        this.startRoom = null;
        this.endRoom = null;
        this.active = false;
    },

    /**
     * Populate room select dropdowns
     */
    populateRoomSelects() {
        const startSelect = document.getElementById('startRoomSelect');
        const endSelect = document.getElementById('endRoomSelect');

        if (!startSelect || !endSelect) return;

        // Get all room IDs from manual room centers
        const roomIds = Object.keys(manualRoomCenters)
            .filter(k => !k.startsWith('_'))
            .sort();

        // Clear existing options (keep placeholder)
        while (startSelect.options.length > 1) {
            startSelect.remove(1);
        }
        while (endSelect.options.length > 1) {
            endSelect.remove(1);
        }

        // Add room options
        roomIds.forEach(roomId => {
            const startOption = document.createElement('option');
            startOption.value = roomId;
            startOption.textContent = roomId;
            startSelect.appendChild(startOption);

            const endOption = document.createElement('option');
            endOption.value = roomId;
            endOption.textContent = roomId;
            endSelect.appendChild(endOption);
        });
    },

    /**
     * Select start room
     */
    selectStartRoom(roomId) {
        this.startRoom = roomId;
        this.updateCalculateButton();
    },

    /**
     * Select end room
     */
    selectEndRoom(roomId) {
        this.endRoom = roomId;
        this.updateCalculateButton();
    },

    /**
     * Update calculate button state
     */
    updateCalculateButton() {
        const calculateBtn = document.getElementById('calculateRouteBtn');
        if (calculateBtn) {
            calculateBtn.disabled = !(this.startRoom && this.endRoom);
        }
    },

    /**
     * Calculate and display route
     */
    calculateRoute() {
        if (!this.startRoom || !this.endRoom) {
            this.showMessage('Please select both start and end rooms', 'error');
            return;
        }

        if (!currentGraphData) {
            this.showMessage('Navigation graph not loaded', 'error');
            return;
        }

        // Get node IDs for rooms
        const startNode = currentGraphData.roomToNode?.[this.startRoom];
        const endNode = currentGraphData.roomToNode?.[this.endRoom];

        if (!startNode || !endNode) {
            this.showMessage('Could not find navigation nodes for selected rooms', 'error');
            return;
        }

        // Calculate path
        const path = findShortestPath(currentGraphData.graph, startNode, endNode);

        if (!path) {
            this.showMessage('Could not calculate route', 'error');
            return;
        }

        // Generate GeoJSON
        const routeGeoJSON = generateRouteGeoJSON(
            path,
            currentGraphData.nodePositions,
            currentGraphData.nodeMetadata,
            this.startRoom,
            this.endRoom
        );

        if (!routeGeoJSON) {
            this.showMessage('Could not generate GeoJSON', 'error');
            return;
        }

        // Store GeoJSON globally and save original coordinates
        window.routeGeoJSONData = routeGeoJSON;
        this.originalCoordinates = routeGeoJSON.geometry.coordinates.map(coord => [...coord]);

        // Clear previous routes
        clearRoutePolylines();
        clearRoute();

        // Render route polyline
        const polyline = renderRoutePolyline(routeGeoJSON);
        if (polyline) {
            window.routePolylines.push(polyline);
            this.currentPolyline = polyline;
        }

        // Add start/end markers
        const startCoords = getCoordinatesForRoom(this.startRoom, currentGraphData, currentSvgMap);
        const endCoords = getCoordinatesForRoom(this.endRoom, currentGraphData, currentSvgMap);

        if (startCoords && endCoords) {
            navigationMarkers.start = L.marker(startCoords, { icon: markerIcons.start })
                .addTo(map)
                .bindPopup(`Start: ${this.startRoom}`);
            navigationMarkers.end = L.marker(endCoords, { icon: markerIcons.end })
                .addTo(map)
                .bindPopup(`Destination: ${this.endRoom}`);

            // Fit bounds
            map.fitBounds([startCoords, endCoords]);
        }

        // Update stats display
        this.updateStatsDisplay(routeGeoJSON.properties);

        // Show adjustment controls
        const adjustmentControls = document.getElementById('routeAdjustmentControls');
        if (adjustmentControls) adjustmentControls.classList.remove('hidden');

        // Enable export button
        const exportBtn = document.getElementById('exportGeoJSONBtn');
        if (exportBtn) exportBtn.disabled = false;

        this.showMessage('Route calculated successfully!', 'success');
    },

    /**
     * Update route statistics display
     */
    updateStatsDisplay(props) {
        const statsDisplay = document.getElementById('routeStatsDisplay');
        const distanceEl = document.getElementById('routeDistance');
        const nodesEl = document.getElementById('routeNodes');
        const turnsEl = document.getElementById('routeTurns');
        const roomsEl = document.getElementById('routeRooms');

        if (statsDisplay) statsDisplay.classList.remove('hidden');
        if (distanceEl) distanceEl.textContent = `${props.distance} ${props.distanceUnit}`;
        if (nodesEl) nodesEl.textContent = props.nodeCount;
        if (turnsEl) turnsEl.textContent = props.turns;
        if (roomsEl) roomsEl.textContent = props.roomCount;
    },

    /**
     * Clear current route
     */
    clearCurrentRoute() {
        clearRoutePolylines();
        clearRoute();

        // Reset adjustment state
        this.currentPolyline = null;
        this.originalCoordinates = null;
        this.resetAdjustments();

        const statsDisplay = document.getElementById('routeStatsDisplay');
        if (statsDisplay) statsDisplay.classList.add('hidden');

        // Hide adjustment controls
        const adjustmentControls = document.getElementById('routeAdjustmentControls');
        if (adjustmentControls) adjustmentControls.classList.add('hidden');

        const exportBtn = document.getElementById('exportGeoJSONBtn');
        if (exportBtn) exportBtn.disabled = true;

        window.routeGeoJSONData = null;

        this.showMessage('Route cleared', 'info');
    },

    /**
     * Export route as GeoJSON file
     */
    exportGeoJSON() {
        if (!window.routeGeoJSONData) {
            this.showMessage('No route to export', 'error');
            return;
        }

        try {
            // Create JSON string
            const jsonString = JSON.stringify(window.routeGeoJSONData, null, 2);

            // Create download link
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // Generate filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const filename = `route_${window.routeGeoJSONData.properties.start}_to_${window.routeGeoJSONData.properties.end}_${timestamp}.geojson`;
            a.download = filename;

            // Trigger download
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showMessage(`Exported: ${filename}`, 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showMessage('Error exporting GeoJSON', 'error');
        }
    },

    /**
     * Show message in panel
     */
    showMessage(text, type = 'info') {
        const msgDiv = document.getElementById('routeTracerMessage');
        if (!msgDiv) return;

        msgDiv.textContent = text;
        msgDiv.className = `route-tracer-message show ${type}`;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            msgDiv.classList.remove('show');
        }, 5000);
    },

    /**
     * Apply manual adjustments to the route
     */
    applyAdjustments() {
        if (!this.currentPolyline || !this.originalCoordinates) {
            console.warn('No active route to adjust');
            return;
        }

        // Get map center for rotation
        const mapCenter = map.getCenter();

        // Apply transformations to original coordinates
        const adjustedCoords = this.originalCoordinates.map(([lng, lat]) => {
            let newLat = lat;
            let newLng = lng;

            // Apply translation
            newLng += this.adjustments.translateX;
            newLat += this.adjustments.translateY;

            // Apply rotation around map center
            if (this.adjustments.rotation !== 0) {
                const angleRad = (this.adjustments.rotation * Math.PI) / 180;
                const cos = Math.cos(angleRad);
                const sin = Math.sin(angleRad);

                const dx = newLng - mapCenter.lng;
                const dy = newLat - mapCenter.lat;

                newLat = mapCenter.lat + (dy * cos - dx * sin);
                newLng = mapCenter.lng + (dx * cos + dy * sin);
            }

            return L.latLng(newLat, newLng);
        });

        // Update the polyline with new coordinates
        this.currentPolyline.setLatLngs(adjustedCoords);

        console.log(`🔧 Applied adjustments - X: ${this.adjustments.translateX}, Y: ${this.adjustments.translateY}, Rotation: ${this.adjustments.rotation}°`);
    },

    /**
     * Reset all adjustments to default
     */
    resetAdjustments() {
        // Reset adjustment values
        this.adjustments.translateX = 0;
        this.adjustments.translateY = 0;
        this.adjustments.rotation = 0;

        // Reset slider positions
        const translateXSlider = document.getElementById('routeTranslateX');
        const translateYSlider = document.getElementById('routeTranslateY');
        const rotateSlider = document.getElementById('routeRotate');

        if (translateXSlider) {
            translateXSlider.value = 0;
            document.getElementById('translateXValue').textContent = '0';
        }
        if (translateYSlider) {
            translateYSlider.value = 0;
            document.getElementById('translateYValue').textContent = '0';
        }
        if (rotateSlider) {
            rotateSlider.value = 0;
            document.getElementById('rotateValue').textContent = '0';
        }

        // Apply reset (which restores original coordinates)
        this.applyAdjustments();

        this.showMessage('Adjustments reset to default', 'info');
        console.log('🔄 Reset all route adjustments');
    }
};

// ============================================
// Route Builder - Manual Route Segment Creator
// ============================================
const routeBuilder = {
    active: false,
    currentSegment: {
        name: '',
        type: 'corridor',
        points: [],
        polyline: null
    },
    savedSegments: [],
    mapClickHandler: null,

    init() {
        console.log('🔧 Initializing Route Builder...');

        const openBtn = document.getElementById('routeBuilderBtn');
        const closeBtn = document.getElementById('routeBuilderCloseBtn');
        const clearBtn = document.getElementById('clearPointsBtn');
        const undoBtn = document.getElementById('undoPointBtn');
        const saveBtn = document.getElementById('saveSegmentBtn');
        const exportBtn = document.getElementById('exportSegmentsBtn');
        const nameInput = document.getElementById('segmentName');
        const typeSelect = document.getElementById('segmentType');

        if (openBtn) {
            openBtn.addEventListener('click', () => this.openBuilder());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeBuilder());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearPoints());
        }

        if (undoBtn) {
            undoBtn.addEventListener('click', () => this.undoLastPoint());
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                console.log('💾 Save Segment button clicked');
                console.log('   Button disabled:', saveBtn.disabled);
                console.log('   Current segment:', this.currentSegment);
                this.saveSegment();
            });
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportAllSegments());
        }

        if (nameInput) {
            nameInput.addEventListener('input', (e) => {
                this.currentSegment.name = e.target.value;
                this.updateSaveButton();
            });
        }

        if (typeSelect) {
            typeSelect.addEventListener('change', (e) => {
                this.currentSegment.type = e.target.value;
            });
        }

        console.log('✅ Route Builder initialized');
    },

    openBuilder() {
        console.log('📐 Opening Route Builder...');

        const panel = document.getElementById('routeBuilderPanel');
        if (panel) {
            panel.classList.remove('hidden');
            // Force reflow to ensure transition works
            panel.offsetHeight;
            panel.classList.add('visible');
            this.active = true;

            // Enable map click mode
            this.enableMapClickMode();

            // Show indicator on map
            const indicator = document.getElementById('map-mode-indicator');
            if (indicator) {
                indicator.textContent = '✏️ Route Builder - Click to add points';
                indicator.classList.add('active');
            }

            this.showMessage('Click on the map to trace your route segment', 'info');
            console.log('✅ Route Builder panel opened');
        }
    },

    closeBuilder() {
        console.log('📐 Closing Route Builder...');

        const panel = document.getElementById('routeBuilderPanel');
        if (panel) {
            panel.classList.remove('visible');
            this.active = false;

            // Disable map click mode
            this.disableMapClickMode();

            // Clear current segment preview
            if (this.currentSegment.polyline) {
                map.removeLayer(this.currentSegment.polyline);
                this.currentSegment.polyline = null;
            }

            // Hide indicator
            const indicator = document.getElementById('map-mode-indicator');
            if (indicator) {
                indicator.textContent = '';
                indicator.classList.remove('active');
            }

            // Wait for animation to complete before hiding
            setTimeout(() => {
                panel.classList.add('hidden');
            }, 300);

            console.log('✅ Route Builder panel closed');
        }
    },

    enableMapClickMode() {
        console.log('🖱️ Enabling map click mode...');

        // Create click handler
        this.mapClickHandler = (e) => {
            if (this.active) {
                this.addPoint(e.latlng);
            }
        };

        // Add to map
        map.on('click', this.mapClickHandler);

        // Change cursor
        document.getElementById('map').style.cursor = 'crosshair';

        console.log('✅ Map click mode enabled');
    },

    disableMapClickMode() {
        console.log('🖱️ Disabling map click mode...');

        // Remove click handler
        if (this.mapClickHandler) {
            map.off('click', this.mapClickHandler);
            this.mapClickHandler = null;
        }

        // Reset cursor
        document.getElementById('map').style.cursor = '';

        console.log('✅ Map click mode disabled');
    },

    addPoint(latlng) {
        console.log('📍 Adding point:', latlng.lat, latlng.lng);

        // Add to points array
        this.currentSegment.points.push(latlng);

        // Update or create polyline preview
        if (this.currentSegment.polyline) {
            map.removeLayer(this.currentSegment.polyline);
        }

        if (this.currentSegment.points.length > 0) {
            this.currentSegment.polyline = L.polyline(this.currentSegment.points, {
                color: '#9C27B0',
                weight: 4,
                opacity: 0.8,
                dashArray: '10, 5'
            }).addTo(map);
        }

        // Update statistics
        this.updateStats();

        // Update save button
        this.updateSaveButton();

        this.showMessage(`Point ${this.currentSegment.points.length} added`, 'success');
        console.log(`✅ Point added (total: ${this.currentSegment.points.length})`);
    },

    undoLastPoint() {
        if (this.currentSegment.points.length === 0) {
            this.showMessage('No points to undo', 'warning');
            return;
        }

        console.log('↩️ Undoing last point...');

        // Remove last point
        this.currentSegment.points.pop();

        // Update polyline
        if (this.currentSegment.polyline) {
            map.removeLayer(this.currentSegment.polyline);
            this.currentSegment.polyline = null;
        }

        if (this.currentSegment.points.length > 0) {
            this.currentSegment.polyline = L.polyline(this.currentSegment.points, {
                color: '#9C27B0',
                weight: 4,
                opacity: 0.8,
                dashArray: '10, 5'
            }).addTo(map);
        }

        // Update statistics
        this.updateStats();

        // Update save button
        this.updateSaveButton();

        this.showMessage(`Point removed (${this.currentSegment.points.length} remaining)`, 'info');
        console.log(`✅ Point removed (total: ${this.currentSegment.points.length})`);
    },

    clearPoints() {
        console.log('🗑️ Clearing all points...');

        // Clear points array
        this.currentSegment.points = [];

        // Remove polyline
        if (this.currentSegment.polyline) {
            map.removeLayer(this.currentSegment.polyline);
            this.currentSegment.polyline = null;
        }

        // Update statistics
        this.updateStats();

        // Update save button
        this.updateSaveButton();

        this.showMessage('All points cleared', 'info');
        console.log('✅ All points cleared');
    },

    updateStats() {
        const pointCount = this.currentSegment.points.length;
        const distance = this.calculateSegmentLength();

        // Update point count
        const pointCountEl = document.getElementById('pointCount');
        if (pointCountEl) {
            pointCountEl.textContent = pointCount;
        }

        // Update distance
        const distanceEl = document.getElementById('segmentLength');
        if (distanceEl) {
            distanceEl.textContent = distance > 0 ? `${distance.toFixed(2)} m` : '0 m';
        }

        // Show/hide stats display
        const statsDisplay = document.getElementById('builderStats');
        if (statsDisplay) {
            if (pointCount > 0) {
                statsDisplay.classList.remove('hidden');
            } else {
                statsDisplay.classList.add('hidden');
            }
        }
    },

    calculateSegmentLength() {
        if (this.currentSegment.points.length < 2) {
            return 0;
        }

        let totalDistance = 0;

        for (let i = 0; i < this.currentSegment.points.length - 1; i++) {
            const p1 = this.currentSegment.points[i];
            const p2 = this.currentSegment.points[i + 1];
            totalDistance += map.distance(p1, p2);
        }

        return totalDistance;
    },

    updateSaveButton() {
        const saveBtn = document.getElementById('saveSegmentBtn');
        if (saveBtn) {
            const hasName = this.currentSegment.name.trim().length > 0;
            const hasPoints = this.currentSegment.points.length >= 2;
            const shouldEnable = hasName && hasPoints;
            saveBtn.disabled = !shouldEnable;

            console.log('🔘 Update Save Button:', {
                hasName,
                hasPoints,
                shouldEnable,
                currentName: this.currentSegment.name,
                pointCount: this.currentSegment.points.length
            });
        }
    },

    saveSegment() {
        console.log('💾 Saving segment...');

        if (this.currentSegment.points.length < 2) {
            this.showMessage('Need at least 2 points to save a segment', 'error');
            return;
        }

        if (!this.currentSegment.name.trim()) {
            this.showMessage('Please enter a segment name', 'error');
            return;
        }

        // Create segment object with clean coordinates
        const segment = {
            name: this.currentSegment.name,
            type: this.currentSegment.type,
            coordinates: this.currentSegment.points.map(p => [p.lng, p.lat]),
            pointCount: this.currentSegment.points.length,
            length: this.calculateSegmentLength(),
            timestamp: new Date().toISOString()
        };

        // Add to saved segments
        this.savedSegments.push(segment);

        console.log('✅ Segment saved:', segment);

        this.showMessage(`Segment "${segment.name}" saved successfully! (${this.savedSegments.length} total)`, 'success');

        // Clear current segment and start fresh
        this.clearPoints();
        document.getElementById('segmentName').value = '';
        this.currentSegment.name = '';
    },

    exportAllSegments() {
        console.log('📦 Exporting all segments...');

        if (this.savedSegments.length === 0) {
            this.showMessage('No segments to export', 'warning');
            return;
        }

        // Create GeoJSON FeatureCollection
        const geoJSON = {
            type: 'FeatureCollection',
            features: this.savedSegments.map(segment => ({
                type: 'Feature',
                geometry: {
                    type: 'LineString',
                    coordinates: segment.coordinates
                },
                properties: {
                    name: segment.name,
                    segmentType: segment.type,
                    pointCount: segment.pointCount,
                    length: segment.length,
                    timestamp: segment.timestamp
                }
            }))
        };

        // Create download
        const dataStr = JSON.stringify(geoJSON, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `route_segments_${new Date().toISOString().split('T')[0]}.geojson`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        console.log('✅ Exported GeoJSON:', geoJSON);
        this.showMessage(`Exported ${this.savedSegments.length} segments as GeoJSON`, 'success');
    },

    showMessage(message, type = 'info') {
        const messageEl = document.getElementById('routeBuilderMessage');
        if (!messageEl) return;

        messageEl.textContent = message;
        messageEl.className = 'route-builder-message show';

        if (type === 'success') {
            messageEl.classList.add('success');
        } else if (type === 'error') {
            messageEl.classList.add('error');
        } else if (type === 'warning') {
            messageEl.classList.add('warning');
        } else {
            messageEl.classList.add('info');
        }

        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageEl.classList.remove('show');
        }, 5000);
    }
};

// ============================================
// Route Segments Loader - Load and display saved route segments
// ============================================
const routeSegmentsLoader = {
    loadedSegments: [],
    segmentLayers: [],

    /**
     * Initialize route segments loader
     */
    init() {
        console.log('🔧 Initializing Route Segments Loader...');

        const loadBtn = document.getElementById('loadSegmentsBtn');
        const clearBtn = document.getElementById('clearSegmentsBtn');

        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadSegments());
        }
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearSegments());
        }

        console.log('✅ Route Segments Loader initialized');
    },

    /**
     * Load route segments from file
     */
    async loadSegments() {
        try {
            console.log('📥 Loading route segments...');

            // Check if map is initialized
            if (!map) {
                this.showMessage('Map not initialized yet', 'error');
                console.error('❌ Map not initialized');
                return;
            }

            // Fetch the latest route segments file
            const response = await fetch('/map/route_segments_2025-11-17.geojson?ts=' + new Date().getTime());
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (!data || !data.features || data.features.length === 0) {
                this.showMessage('No route segments found in file', 'warning');
                return;
            }

            console.log(`📦 Loaded GeoJSON with ${data.features.length} features`);

            // Store loaded segments (don't render them yet)
            this.loadedSegments = data.features;

            console.log(`✅ Loaded ${data.features.length} route segments (available for navigation)`);
            this.showMessage(`Loaded ${data.features.length} route segments - ready for navigation!`, 'success');

            // Enable clear button
            const clearBtn = document.getElementById('clearSegmentsBtn');
            if (clearBtn) clearBtn.disabled = false;

        } catch (error) {
            console.error('❌ Error loading route segments:', error);
            console.error('Error details:', error.message);
            this.showMessage(`Error: ${error.message}`, 'error');
        }
    },

    /**
     * Render a single segment on the map
     */
    renderSegment(feature, index) {
        if (!feature || !feature.geometry || feature.geometry.type !== 'LineString') {
            console.warn(`⚠️ Invalid segment at index ${index}`);
            return null;
        }

        const props = feature.properties || {};

        // Convert GeoJSON coordinates to LatLng
        const latlngs = feature.geometry.coordinates.map(coord => 
            L.latLng(coord[1], coord[0])
        );

        if (latlngs.length === 0) {
            console.warn(`⚠️ No coordinates in segment ${index}`);
            return null;
        }

        // DON'T apply rotation compensation - these coordinates were captured 
        // from the already-rotated map during manual tracing
        // They're already in the correct coordinate system for display

        // Determine color based on segment type
        const colors = {
            'corridor': '#9C27B0',      // Purple
            'room_entrance': '#FF5722', // Red-Orange
            'connection': '#00BCD4'     // Cyan
        };
        const color = colors[props.segmentType] || '#9C27B0';

        console.log(`🎨 Rendering segment "${props.name || 'Segment ' + index}" with color ${color}`);

        // Create polyline (use latlngs directly, no rotation)
        const polyline = L.polyline(latlngs, {
            color: color,
            weight: 3,
            opacity: 0.7,
            dashArray: '5, 5'
        });

        // Add popup with segment info
        const popupContent = `
            <div style="min-width: 180px;">
                <strong>${props.name || 'Unnamed Segment'}</strong><br>
                Type: <strong>${props.segmentType || 'unknown'}</strong><br>
                Points: ${props.pointCount || latlngs.length}<br>
                Length: <strong>${props.length ? props.length.toFixed(2) + ' m' : 'N/A'}</strong><br>
                <small>Created: ${props.timestamp ? new Date(props.timestamp).toLocaleString() : 'Unknown'}</small>
            </div>
        `;
        polyline.bindPopup(popupContent);

        // Add hover effects
        polyline.on('mouseover', function () {
            this.setStyle({ weight: 5, opacity: 1 });
        });

        polyline.on('mouseout', function () {
            this.setStyle({ weight: 3, opacity: 0.7 });
        });

        try {
            polyline.addTo(map);
            console.log(`✅ Rendered segment: ${props.name || 'Segment ' + index}`);
            return polyline;
        } catch (error) {
            console.error(`❌ Error adding segment ${index} to map:`, error);
            return null;
        }
    },

    /**
     * Clear all loaded segments from map
     */
    clearSegments() {
        console.log('🗑️ Clearing route segments...');

        // Remove all layers from map
        this.segmentLayers.forEach(layer => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });

        // Reset state
        this.segmentLayers = [];
        this.loadedSegments = [];

        // Disable clear button
        const clearBtn = document.getElementById('clearSegmentsBtn');
        if (clearBtn) clearBtn.disabled = true;

        this.showMessage('Route segments cleared', 'info');
        console.log('✅ Route segments cleared');
    },

    /**
     * Find a matching segment for a route
     */
    findMatchingSegment(startRoom, endRoom) {
        if (this.loadedSegments.length === 0) {
            console.log('❌ No segments loaded');
            return null;
        }

        console.log(`🔍 Looking for segment: "${startRoom}" → "${endRoom}"`);

        // Normalize room names - extract just the number
        const normalizeRoom = (room) => {
            if (!room) return '';
            // Extract numbers from strings like "Room_1006", "M1006", "1006", etc.
            const match = room.match(/(\d{4})/);
            return match ? match[1] : room.toUpperCase().replace(/^M/, '').replace('ROOM_', '');
        };

        const startNorm = normalizeRoom(startRoom);
        const endNorm = normalizeRoom(endRoom);

        console.log(`📝 Normalized: "${startNorm}" → "${endNorm}"`);

        // Look for segments that connect these rooms
        for (const segment of this.loadedSegments) {
            const props = segment.properties || {};
            
            console.log(`  Checking segment: ${props.name}, startRoom: ${props.startRoom}, endRoom: ${props.endRoom}`);
            
            // Method 1: Check explicit startRoom and endRoom properties
            if (props.startRoom && props.endRoom) {
                const segStartNorm = normalizeRoom(props.startRoom);
                const segEndNorm = normalizeRoom(props.endRoom);
                
                console.log(`    Segment normalized: "${segStartNorm}" → "${segEndNorm}"`);
                
                if ((segStartNorm === startNorm && segEndNorm === endNorm) ||
                    (segStartNorm === endNorm && segEndNorm === startNorm)) {
                    console.log(`✅ Found exact match: ${props.name}`);
                    return segment;
                }
            }
            
            // Method 2: Check segment name for room references
            const name = (props.name || '').toLowerCase();
            
            if ((name.includes(startNorm.toLowerCase()) && name.includes(endNorm.toLowerCase())) ||
                (name.includes(endNorm.toLowerCase()) && name.includes(startNorm.toLowerCase()))) {
                console.log(`✅ Found name match: ${props.name}`);
                return segment;
            }
        }

        console.log('❌ No matching segment found');
        return null;
    },

    /**
     * Highlight a specific segment
     */
    highlightSegment(segment) {
        if (!segment || !segment.geometry) {
            return;
        }

        console.log(`✨ Highlighting segment: ${segment.properties?.name || 'Unnamed'}`);

        // Clear previous route displays
        clearRoutePolylines();
        clearRoute();

        // Convert GeoJSON coordinates to LatLng
        const latlngs = segment.geometry.coordinates.map(coord => 
            L.latLng(coord[1], coord[0])
        );

        // DON'T apply rotation compensation - these coordinates were captured 
        // from the already-rotated map, so they're already in the correct system
        console.log(`📍 Using ${latlngs.length} points directly (no rotation compensation needed)`);

        // Create highlighted polyline (blue, solid, thick)
        const polyline = L.polyline(latlngs, {
            color: '#2196F3',    // Blue - same as calculated routes
            weight: 5,
            opacity: 0.9,
            dashArray: ''        // Solid line for highlight
        });

        const props = segment.properties || {};
        const popupContent = `
            <div style="min-width: 200px;">
                <strong>🎯 ${props.name || 'Route Segment'}</strong><br>
                <em>Saved Route</em><br><br>
                Type: <strong>${props.segmentType || 'unknown'}</strong><br>
                Length: <strong>${props.length ? props.length.toFixed(2) + ' m' : 'N/A'}</strong><br>
                Points: ${props.pointCount || latlngs.length}
            </div>
        `;
        polyline.bindPopup(popupContent);
        // Don't auto-open popup - let user click to see details

        polyline.addTo(map);
        window.routePolylines.push(polyline);

        // Fit map to segment bounds
        map.fitBounds(polyline.getBounds(), { padding: [80, 80] });

        console.log('✅ Segment highlighted with blue line');
    },

    /**
     * Show message to user
     */
    showMessage(text, type = 'info') {
        console.log(`💬 ${text}`);
        
        // Show in map indicator
        const indicator = document.getElementById('map-mode-indicator');
        if (indicator) {
            indicator.textContent = text;
            indicator.classList.add('active');
            
            setTimeout(() => {
                indicator.classList.remove('active');
                indicator.textContent = '';
            }, 3000);
        }
    }
};

// Initialize map when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();

    // Add event listener for reload button
    const reloadBtn = document.getElementById('reloadCoordinatesBtn');
    if (reloadBtn) {
        reloadBtn.addEventListener('click', reloadCoordinates);
    }

    // Initialize coordinate editor modal
    coordinateEditor.init();

    // Initialize calibration mode
    calibrationMode.init();

    // Initialize room center visualizer
    roomCenterVisualizer.init();

    // Initialize route tracer
    routeTracer.init();

    // Initialize route builder
    routeBuilder.init();

    // Initialize route segments loader
    routeSegmentsLoader.init();
});

// Export functions for global access
window.showRouteBuildingM = showRouteBuildingM;
window.clearRoute = clearRoute;
window.startMapNavigation = startMapNavigation;
window.reloadCoordinates = reloadCoordinates;
window.coordinateEditor = coordinateEditor;
window.calibrationMode = calibrationMode;
window.roomCenterVisualizer = roomCenterVisualizer;
window.routeTracer = routeTracer;
window.routeBuilder = routeBuilder;
window.routeSegmentsLoader = routeSegmentsLoader;
window.generateRouteGeoJSON = generateRouteGeoJSON;
window.renderRoutePolyline = renderRoutePolyline;
