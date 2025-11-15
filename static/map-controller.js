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

    // Calculate path
    const path = findShortestPath(currentGraphData.graph, startNode, endNode);

    if (path) {
        // Draw on map
        drawPathOnMap(path, currentGraphData.nodePositions, currentSvgMap);

        // Get room names from nodes to find room centers
        const startRoomName = getRoomNameFromNode(startNode, currentGraphData.nodeMetadata);
        const endRoomName = getRoomNameFromNode(endNode, currentGraphData.nodeMetadata);

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

// Initialize map when DOM is ready
document.addEventListener('DOMContentLoaded', initializeMap);

// Export functions for global access
window.showRouteBuildingM = showRouteBuildingM;
window.clearRoute = clearRoute;
window.startMapNavigation = startMapNavigation;
