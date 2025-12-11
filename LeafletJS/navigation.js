/**
 * navigation.js - Consolidated Navigation Module
 * Consolidates scattered navigation logic from interactiveMap.html
 * 
 * Required window.* globals:
 *   - window.objectData: Object metadata and building data
 *   - window.floorPlans: Floor information including rooms, exits, navigation graphs
 *   - window.buildingGraphData: Pre-built navigation graphs with node positions
 *   - window.buildingSVGElements: SVG map elements by building name
 *   - window.buildingOverlays: Leaflet SVG overlays by building name
 *   - window.buildingConnections: Inter-building connection data
 *   - window.buildingInfoCache: Building bounds and metadata
 *   - window.map: Leaflet map instance
 *   - window.userPosition: Current user L.latLng position
 *   - window.userCurrentBuilding: Current user building
 *   - window.userCurrentFloor: Current user floor
 *   - window.pendingDestination: Multi-floor transition data
 *   - window.pathPolylines: Array of drawn path polylines
 * 
 * Required helper functions (from interactiveMap.html):
 *   - findShortestPath(graph, startNode, endNode)
 *   - drawPathOnMap(path, nodePositions, map, svgMap, clearPrevious, finalObjectId, overlay, ...)
 *   - drawMultiBuildingPath(pathResult, destinationInfo)
 *   - findNearestNodeToUser(userPos, nodePositions)
 *   - updateUserLocation()
 *   - objectToLatLng(objectElement, svgMap, overlay)
 *   - clearPath()
 */

/**
 * Find the closest door to a user position for a given room
 * Uses object_data.json to get door→node mappings, then calculates distance from user position
 * 
 * @param {string} roomId - The room ID (e.g., "M1003")
 * @param {L.latLng} userPosition - User's current position
 * @param {string} building - Building name (e.g., "Building M")
 * @param {string} floor - Floor number (e.g., "1")
 * @param {object} doorListOverride - Optional: pass doors directly (format: {"Door_1": "Node_1"})
 * @returns {string|null} - Closest door ID or null
 */
function findClosestDoorToPosition(roomId, userPosition, building, floor, doorListOverride = null) {
    console.log(`🚪 findClosestDoorToPosition: Room ${roomId}, Building ${building}, Floor ${floor}`);
    
    // Step 1: Get door→node mappings from object_data.json or use override
    let doorList = doorListOverride;
    
    if (!doorList) {
        const roomData = window.objectData?.[roomId];
        if (!roomData || !roomData.doors) {
            console.error(`❌ Room ${roomId} not found in object_data.json or has no doors`);
            return null;
        }
        doorList = roomData.doors; // {"Door_M1003_1": "M1_Path1_6", "Door_M1003_2": "M1_Int_2"}
    }
    
    if (Object.keys(doorList).length === 0) {
        console.error(`❌ Room ${roomId} has no doors`);
        return null;
    }
    
    console.log(`📋 Available doors:`, doorList);
    
    // Step 2: Get node positions from buildingGraphData - access with FLOOR
    const graphData = window.buildingGraphData?.[building]?.[floor];
    if (!graphData || !graphData.nodePositions) {
        console.error(`❌ No graph data found for ${building} Floor ${floor}`);
        return null;
    }
    
    const nodePositions = graphData.nodePositions;
    
    // Step 3: Calculate distance from user position to each door's node
    let closestDoorId = null;
    let minDistance = Infinity;
    
    Object.entries(doorList).forEach(([doorId, nodeId]) => {
        const doorNodePos = nodePositions[nodeId];
        if (doorNodePos) {
            // Calculate distance from user position to this door's node
            const distance = userPosition.distanceTo(doorNodePos);
            console.log(`   📏 ${doorId} (node: ${nodeId}): ${distance.toFixed(2)}m from user`);
            
            if (distance < minDistance) {
                minDistance = distance;
                closestDoorId = doorId;
            }
        } else {
            console.warn(`⚠️  Node ${nodeId} for door ${doorId} not found in node positions`);
        }
    });
    
    if (closestDoorId) {
        console.log(`✅ Selected closest door: ${closestDoorId} (${minDistance.toFixed(2)}m from user)`);
        return closestDoorId;
    } else {
        console.warn(`⚠️  No valid doors found, using fallback`);
        closestDoorId = Object.keys(doorList)[0];
        console.log(`✅ Fallback: ${closestDoorId}`);
        return closestDoorId;
    }
}

/**
 * Converts an object ID to L.latLng coordinates
 * Handles rooms (returns first door position) and exits/stairs
 * 
 * @param {string} objectId - The ID of the object
 * @param {object} objectInfo - {type, building, floor}
 * @returns {object|null} - {coords: L.latLng, floor: string} or null
 */
function getObjectCoordinates(objectId, objectInfo) {
    console.log(`🔍 getObjectCoordinates: ${objectId}, type=${objectInfo.type}, building=${objectInfo.building}, floor=${objectInfo.floor}`);
    
    const building = objectInfo.building;
    const floor = objectInfo.floor;
    
    const buildingInfo = window.floorPlans[building];
    if (!buildingInfo || !buildingInfo.floors[floor]) {
        console.error(`❌ Building ${building} Floor ${floor} not found`);
        return null;
    }
    
    const floorData = buildingInfo.floors[floor];
    const svgMap = window.buildingSVGElements[building];
    const overlay = window.buildingOverlays?.[building];
    
    if (!svgMap) {
        console.warn(`⚠️ SVG not loaded for ${building}`);
        return { coords: null, floor: floor };
    }
    
    // Handle room types (typeCategory 'room' covers classroom, bathroom, eatery, etc.)
    if (objectInfo.typeCategory === 'room') {
        const doorList = objectInfo.doors;
        if (!doorList || Object.keys(doorList).length === 0) {
            console.error(`❌ Room ${objectId} has no doors`);
            return null;
        }
        
        // Get first door ID from object_data doors object
        const firstDoorId = Object.keys(doorList)[0];
        const doorElement = svgMap.getElementById(firstDoorId);
        if (!doorElement) {
            console.error(`❌ Door ${firstDoorId} not found in SVG`);
            return null;
        }
        
        const coords = objectToLatLng(doorElement, svgMap, overlay);
        console.log(`✅ Found room door coordinates:`, coords);
        return { coords: coords, floor: floor };
        
    } else if (objectInfo.typeCategory === 'exit') {
        // For exits, use the object ID directly as the SVG element ID
        const exitElement = svgMap.getElementById(objectId);
        if (!exitElement) {
            console.error(`❌ Exit ${objectId} not found in SVG`);
            return null;
        }
        
        const coords = objectToLatLng(exitElement, svgMap, overlay);
        console.log(`✅ Found exit coordinates:`, coords);
        return { coords: coords, floor: floor };
    }
    
    console.warn(`⚠️ Unknown typeCategory: ${objectInfo.typeCategory} for ${objectId}`);
    return null;
}

/**
 * Navigate from coordinates + floor to an arrival object
 * 
 * @param {L.latLng} departureCoords - Starting position
 * @param {string} departureFloor - Starting floor
 * @param {string} arrivalObjectId - Destination object ID
 * @returns {boolean}
 */
function navigateFromCoordinates(departureCoords, departureFloor, arrivalObjectId) {
    console.log(`🧭 navigateFromCoordinates: ${arrivalObjectId} from Floor ${departureFloor}`);
    
    if (!departureCoords || typeof departureCoords.lat !== 'number' || typeof departureCoords.lng !== 'number') {
        console.error(`❌ Invalid coordinates`);
        alert("Invalid starting position");
        return false;
    }
    
    console.log(`📍 Departure: [${departureCoords.lat.toFixed(6)}, ${departureCoords.lng.toFixed(6)}]`);
    
    // Find departure building
    let departureBuilding = null;
    Object.entries(window.buildingInfoCache || {}).forEach(([buildingName, buildingData]) => {
        if (buildingData.bounds.contains(departureCoords)) {
            departureBuilding = buildingName;
        }
    });
    
    if (!departureBuilding) {
        console.error(`❌ Coordinates not in any building`);
        alert("Starting position is outside all buildings");
        return false;
    }
    
    console.log(`✅ Departure building: ${departureBuilding}`);
    window.userPosition = departureCoords;
    window.userCurrentBuilding = departureBuilding;
    window.userCurrentFloor = departureFloor;
    
    return findAndDisplayPath(departureCoords, departureFloor, arrivalObjectId, 'gps');
}

/**
 * Navigate from one object ID to another
 * 
 * @param {string} departureObjectId - Starting object
 * @param {string} arrivalObjectId - Destination object
 * @returns {boolean}
 */
function navigateFromObjectId(departureObjectId, arrivalObjectId) {
    console.log(`🧭 navigateFromObjectId: ${departureObjectId} → ${arrivalObjectId}`);
    
    const userLocation = updateUserLocation();
    const departureBuilding = userLocation.building;
    const departureFloor = userLocation.floor || "1";
    
    if (!departureBuilding) {
        console.error(`❌ User location not determined`);
        alert("Cannot determine your current location");
        return false;
    }
    
    // Look up departure object in object_data
    const depInfo = window.objectData?.[departureObjectId];
    if (!depInfo) {
        console.error(`❌ Departure object ${departureObjectId} not found`);
        alert(`Departure location "${departureObjectId}" not found`);
        return false;
    }
    
    // Get coordinates for departure object
    const departure = getObjectCoordinates(departureObjectId, depInfo);
    if (!departure || !departure.coords) {
        console.error(`❌ Could not get coordinates for ${departureObjectId}`);
        alert(`Cannot find starting position for ${departureObjectId}`);
        return false;
    }
    
    console.log(`✅ Departure coordinates obtained:`, departure.coords);
    
    return findAndDisplayPath(departure.coords, departure.floor, arrivalObjectId, 'objectid', departureObjectId);
}

/**
 * Helper to calculate path distance
 */
function calculatePathDistance(path, nodePositions) {
    let totalDistance = 0;
    for (let i = 0; i < path.length - 1; i++) {
        const currentPos = nodePositions[path[i]];
        const nextPos = nodePositions[path[i + 1]];
        if (currentPos && nextPos) {
            totalDistance += currentPos.distanceTo(nextPos);
        }
    }
    return totalDistance;
}

/**
 * Core unified pathfinding function
 * Handles single-floor, multi-floor, and multi-building navigation
 * Consolidates: navigateToObject(), findPathAcrossBuildings(), findMultiFloorPath(), navigateMultiFloor()
 * 
 * @param {L.latLng} departureCoords - Starting position
 * @param {string} departureFloor - Starting floor
 * @param {string} arrivalObjectId - Destination object ID
 * @param {string} departureSource - 'gps' for GPS/pin drop, 'objectid' for object ID navigation
 * @param {string} departureObjectId - Optional: the departure object ID (if departureSource is 'objectid')
 * @returns {boolean}
 */
function findAndDisplayPath(departureCoords, departureFloor, arrivalObjectId, departureSource = 'gps', departureObjectId = null) {
    console.log(`🗺️ findAndDisplayPath: ${arrivalObjectId} from Floor ${departureFloor} (source: ${departureSource})`);
    console.log(`   Departure: [${departureCoords.lat.toFixed(6)}, ${departureCoords.lng.toFixed(6)}]`);
    
    // Step 1: Look up destination object in object_data.json
    const destObjectData = window.objectData?.[arrivalObjectId];
    
    if (!destObjectData) {
        console.error(`❌ Destination ${arrivalObjectId} not found in object_data.json`);
        alert(`Destination ${arrivalObjectId} not found`);
        return false;
    }
    
    const targetBuilding = destObjectData.building;
    const targetFloor = destObjectData.floor;
    const objectType = destObjectData.typeCategory; // 'room' or 'exit'
    const doorList = destObjectData.doors || null;
    
    console.log(`✅ Found ${objectType} ${arrivalObjectId} in ${targetBuilding} Floor ${targetFloor}`);
    
    // Step 2: Find departure building from coordinates
    // If departure is from object ID, use object_data for more accuracy
    let departureBuilding = null;
    
    if (departureSource === 'objectid' && departureObjectId) {
        // Use object_data.json for direct lookup - more accurate
        const departureObjData = window.objectData?.[departureObjectId];
        if (departureObjData) {
            departureBuilding = departureObjData.building;
            console.log(`📍 Departure building (from object_data): ${departureBuilding}`);
        }
    }
    
    // Fallback to GPS bounds checking (for GPS/pin drop or if object_data lookup failed)
    if (!departureBuilding) {
        let smallestBoundsArea = Infinity;
        
        Object.entries(window.buildingInfoCache || {}).forEach(([name, data]) => {
            if (data.bounds.contains(departureCoords)) {
                // Calculate bounds area to find the most specific (smallest) building
                const boundingBox = data.bounds.toBBoxString().split(',').map(Number);
                const width = boundingBox[2] - boundingBox[0];
                const height = boundingBox[3] - boundingBox[1];
                const area = width * height;
                
                if (area < smallestBoundsArea) {
                    smallestBoundsArea = area;
                    departureBuilding = name;
                }
            }
        });
    }
    
    if (!departureBuilding) {
        console.error(`❌ Departure location not in any building`);
        alert("Starting position is outside all buildings");
        return false;
    }
    
    console.log(`📍 Departure: ${departureBuilding} Floor ${departureFloor}`);
    console.log(`🎯 Target: ${targetBuilding} Floor ${targetFloor}`);
    
    // Step 3: Find destination node using object_data.json
    // Get the arrival object metadata (building, floor, doors, etc.)
    const arrivalObjData = window.objectData?.[arrivalObjectId];
    if (!arrivalObjData) {
        console.error(`❌ Arrival object ${arrivalObjectId} not found in object_data.json`);
        alert(`Destination ${arrivalObjectId} not found`);
        return false;
    }
    
    console.log(`📦 Arrival object data:`, arrivalObjData);
    
    let destinationNode = null;
    let finalDestinationDoor = null;
    
    // For rooms: extract and use door information
    if (arrivalObjData.typeCategory === 'room' && arrivalObjData.doors) {
        const doorIds = Object.keys(arrivalObjData.doors);
        
        if (doorIds.length === 0) {
            console.error(`❌ Room ${arrivalObjectId} has no doors`);
            alert(`Room has no accessible doors`);
            return false;
        } else if (doorIds.length === 1) {
            // Single door: use it directly
            finalDestinationDoor = doorIds[0];
            destinationNode = arrivalObjData.doors[finalDestinationDoor];
            console.log(`✅ Single door for ${arrivalObjectId}: ${finalDestinationDoor} → node ${destinationNode}`);
        } else {
            // Multiple doors: will determine closest door later based on user location
            console.log(`📋 Room ${arrivalObjectId} has ${doorIds.length} doors, will find closest after floor transition`);
            // Set a placeholder - we'll resolve the actual door after we know the arrival position
            destinationNode = arrivalObjData.doors[doorIds[0]];
            finalDestinationDoor = doorIds[0];
            console.log(`✅ Placeholder door for ${arrivalObjectId}: ${finalDestinationDoor} → node ${destinationNode}`);
        }
    } 
    // For exits: use the node from object_data
    else if (arrivalObjData.typeCategory === 'exit') {
        destinationNode = arrivalObjData.node;
        console.log(`✅ Exit destination: ${arrivalObjectId} → node ${destinationNode}`);
    }
    
    if (!destinationNode) {
        console.error(`❌ Could not determine destination node for ${arrivalObjectId}`);
        alert(`Cannot navigate to ${arrivalObjectId}`);
        return false;
    }
    
    // Step 4: Multi-floor navigation (same building, different floors)
    if (departureBuilding === targetBuilding && departureFloor !== targetFloor) {
        console.log(`🏢 Multi-floor: Floor ${departureFloor} → Floor ${targetFloor}`);
        
        // WILL UPDATE
        // update dynamic door selection
        let departureCoord = departureCoords;
        if (departureSource === 'objectid' && departureObjectId) {
            const depObjData = window.objectData?.[departureObjectId];
            if (depObjData) {
                // Get coordinates for departure object (use first door for rooms, node for exits)
                let departureElement = null;
                const svgMap = window.buildingSVGElements[departureBuilding];
                
                if (depObjData.typeCategory === 'room' && depObjData.doors) {
                    const doorIds = Object.keys(depObjData.doors);
                    const firstDoor = doorIds[0];
                    departureElement = svgMap?.getElementById(firstDoor);
                } else if (depObjData.typeCategory === 'exit') {
                    departureElement = svgMap?.getElementById(departureObjectId);
                }
                
                if (departureElement) {
                    const overlay = window.buildingOverlays?.[departureBuilding];
                    const coords = objectToLatLng(departureElement, svgMap, overlay);
                    if (coords) {
                        departureCoord = coords;
                        console.log(`📍 Updated departure coordinates for object: ${departureObjectId}`);
                    }
                }
            }
        }
        
        const startFloorData = window.floorPlans[departureBuilding]?.floors?.[departureFloor];
        if (!startFloorData || !startFloorData.verticalConnectors) {
            alert(`No vertical connectors found on Floor ${departureFloor}`);
            return false;
        }
        
        const validConnectors = Object.entries(startFloorData.verticalConnectors)
            .filter(([id, conn]) => conn.verticalConnections && conn.verticalConnections[targetFloor])
            .map(([id, conn]) => ({ id, ...conn }));
        
        if (validConnectors.length === 0) {
            alert(`No stairs/elevators found between Floor ${departureFloor} and Floor ${targetFloor}`);
            return false;
        }
        
        console.log(`✅ Found ${validConnectors.length} vertical connectors`);
        
        // Use graph data for the DEPARTURE floor
        const graphData = window.buildingGraphData[departureBuilding]?.[departureFloor];
        if (!graphData) {
            alert(`Navigation graph not found for ${departureBuilding} Floor ${departureFloor}`);
            return false;
        }
        
        const startNode = findNearestNodeToUser(departureCoord, graphData.nodePositions);
        if (!startNode) {
            alert("Cannot find your position on the graph");
            return false;
        }
        
        console.log(`📍 Starting from node: ${startNode}`);
        
        // Find closest vertical connector
        let nearestConnector = null;
        let shortestPath = null;
        let shortestDistance = Infinity;
        
        for (const connector of validConnectors) {
            const path = findShortestPath(graphData.graph, startNode, connector.nodeId);
            if (path && path.length > 0) {
                const distance = calculatePathDistance(path, graphData.nodePositions);
                if (distance < shortestDistance) {
                    shortestDistance = distance;
                    shortestPath = path;
                    nearestConnector = connector;
                }
            }
        }
        
        if (!nearestConnector || !shortestPath) {
            alert("Cannot find a path to stairs/elevator");
            return false;
        }
        
        console.log(`✅ Nearest connector: ${nearestConnector.id} (${nearestConnector.type})`);
        
        // Get the destination connector ID on target floor from verticalConnections
        const departurePointNewFloor = nearestConnector.verticalConnections?.[targetFloor];
        console.log(`📍 Departure point on Floor ${targetFloor}: ${departurePointNewFloor}`);
        
        // Look up the destination connector to get its nodeId
        const destFloorData = window.floorPlans[departureBuilding]?.floors?.[targetFloor];
        let departurePointNewFloorNode = null;
        if (destFloorData && departurePointNewFloor) {
            const destConnectorData = destFloorData.verticalConnectors?.[departurePointNewFloor];
            if (destConnectorData) {
                departurePointNewFloorNode = destConnectorData.nodeId;
                console.log(`✅ Departure point node on Floor ${targetFloor}: ${departurePointNewFloorNode}`);
            }
        }
        
        const svgMap = window.buildingSVGElements[departureBuilding];
        const buildingOverlay = window.buildingOverlays?.[departureBuilding];
        
        if (svgMap && buildingOverlay && shortestPath.length > 0) {
            drawPathOnMap(shortestPath, graphData.nodePositions, window.map, svgMap, true, null, buildingOverlay);
            
            window.pendingFloorTransition = {
                targetFloor: targetFloor,
                targetBuilding: departureBuilding,
                objectId: arrivalObjectId,
                objectType: objectType,
                arrivalObjectData: arrivalObjData,
                departurePointNewFloor: departurePointNewFloor,
                departurePointNewFloorNode: departurePointNewFloorNode,
                verticalConnectorNodeOnTargetFloor: departurePointNewFloorNode,
                verticalConnectorType: nearestConnector.type,
                verticalConnector: {
                    id: nearestConnector.id,
                    type: nearestConnector.type,
                    nodeId: nearestConnector.nodeId
                },
                segment: {
                    path: shortestPath,
                    building: departureBuilding,
                    floor: departureFloor
                }
            };
            
            const panel = document.getElementById('multiFloorPanel');
            if (panel) {
                const instructionText = document.getElementById('multiFloorInstruction');
                const floorDisplay = document.getElementById('multiFloorTarget');
                if (instructionText) instructionText.textContent = `Take the ${nearestConnector.type} to Floor ${targetFloor}`;
                if (floorDisplay) floorDisplay.textContent = `Destination: ${arrivalObjectId} (Floor ${targetFloor})`;
                panel.style.display = 'block';
            }
            
            return true;
        }
        
        return false;
    }
    
    // Step 5: Multi-building navigation
    if (departureBuilding !== targetBuilding) {
        console.log(`🌉 Multi-building: ${departureBuilding} → ${targetBuilding}`);
        
        const connection = window.buildingConnections?.[departureBuilding]?.[targetBuilding];
        if (!connection) {
            console.error(`❌ No connection between ${departureBuilding} and ${targetBuilding}`);
            alert(`No route between ${departureBuilding} and ${targetBuilding}`);
            return false;
        }
        
        console.log("✅ Found connection:", connection);
        
        // Use graph data for the DEPARTURE floor
        const startGraphData = window.buildingGraphData[departureBuilding]?.[departureFloor];
        if (!startGraphData) {
            alert(`Navigation graph not found for ${departureBuilding} Floor ${departureFloor}`);
            return false;
        }
        
        const startNode = findNearestNodeToUser(departureCoords, startGraphData.nodePositions);
        console.log(`   Start: ${startNode} → Exit: ${connection.exitNode}`);
        
        const pathToExit = findShortestPath(startGraphData.graph, startNode, connection.exitNode);
        if (!pathToExit) {
            alert(`Could not find path to exit`);
            return false;
        }
        console.log(`✅ Path to exit (${pathToExit.length} nodes)`);
        
        // Use graph data for the TARGET floor
        const endGraphData = window.buildingGraphData[targetBuilding]?.[targetFloor];
        if (!endGraphData) {
            alert(`Navigation graph not found for ${targetBuilding} Floor ${targetFloor}`);
            return false;
        }
        
        console.log(`   Entry: ${connection.entryNode} → Destination: ${destinationNode}`);
        const pathToDestination = findShortestPath(endGraphData.graph, connection.entryNode, destinationNode);
        
        if (!pathToDestination) {
            alert(`Could not find path to destination`);
            return false;
        }
        console.log(`✅ Path to destination (${pathToDestination.length} nodes)`);
        
        const pathResult = {
            type: 'multi-building',
            segments: [
                {
                    building: departureBuilding,
                    floor: departureFloor,
                    path: pathToExit,
                    description: `Navigate to ${targetBuilding}`
                },
                {
                    building: targetBuilding,
                    floor: targetFloor,
                    path: pathToDestination,
                    description: `Navigate to destination`
                }
            ],
            connection: connection
        };
        
        const destinationInfo = {
            objectId: arrivalObjectId,
            objectType: objectType,
            doorList: doorList,
            building: targetBuilding
        };
        
        drawMultiBuildingPath(pathResult, destinationInfo);
        return true;
    }
    
    // Step 6: Same building, same floor
    console.log("✅ Same building/floor - simple pathfinding");
    
    // Use graph data for the correct FLOOR
    const graphData = window.buildingGraphData[departureBuilding]?.[departureFloor];
    if (!graphData) {
        alert(`Navigation graph not found for ${departureBuilding} Floor ${departureFloor}`);
        return false;
    }
    
    const startNode = findNearestNodeToUser(departureCoords, graphData.nodePositions);
    const path = findShortestPath(graphData.graph, startNode, destinationNode);
    
    if (!path || path.length === 0) {
        alert(`Could not find path to ${arrivalObjectId}`);
        return false;
    }
    
    const svgMap = window.buildingSVGElements[departureBuilding];
    const buildingOverlay = window.buildingOverlays?.[departureBuilding];
    
    if (!svgMap || !buildingOverlay) {
        alert(`Building data not loaded`);
        return false;
    }
    
    let finalObjectId = null;
    let destinationNodeId = destinationNode; // Use the room's navigation node by default
    
    if (objectType === 'room' && doorList && Object.keys(doorList).length > 0) {
        // Find the closest door using object_data.json door→node mappings
        const closestDoorId = findClosestDoorToPosition(arrivalObjectId, departureCoords, departureBuilding, departureFloor);
        if (closestDoorId) {
            finalObjectId = closestDoorId;
            // Get the node for this door from object_data.json
            const roomData = window.objectData?.[arrivalObjectId];
            if (roomData && roomData.doors && roomData.doors[closestDoorId]) {
                destinationNodeId = roomData.doors[closestDoorId];
                console.log(`🎯 Closest door: ${closestDoorId} → node: ${destinationNodeId}`);
            }
        } else {
            // Fallback to first door if calculation fails
            finalObjectId = Object.keys(doorList)[0];
            destinationNodeId = doorList[finalObjectId];
            console.warn(`⚠️  Fallback to first door: ${finalObjectId} (node: ${destinationNodeId})`);
        }
    } else if (objectType === 'exit') {
        finalObjectId = arrivalObjectId;
        console.log(`✅ Using exit: ${finalObjectId}`);
    }
    
    // Recalculate path to the correct destination node
    const finalPath = findShortestPath(graphData.graph, startNode, destinationNodeId);
    if (!finalPath || finalPath.length === 0) {
        alert(`Could not find path to ${arrivalObjectId}`);
        return false;
    }
    
    drawPathOnMap(finalPath, graphData.nodePositions, window.map, svgMap, true, finalObjectId, buildingOverlay);
    alert(`✅ Navigating to ${arrivalObjectId}`);
    
    return true;
}