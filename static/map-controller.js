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
});

// Export functions for global access
window.showRouteBuildingM = showRouteBuildingM;
window.clearRoute = clearRoute;
window.startMapNavigation = startMapNavigation;
window.reloadCoordinates = reloadCoordinates;
window.coordinateEditor = coordinateEditor;
window.calibrationMode = calibrationMode;
window.roomCenterVisualizer = roomCenterVisualizer;
