/**
 * NavigationEngine.js
 * 
 * Core navigation pathfinding engine ported from set_start_end.html
 * Implements Dijkstra's algorithm for single and multi-building navigation
 */

/**
 * Find shortest path using Dijkstra's algorithm
 * @param {Object} graph - Navigation graph with node connections
 * @param {String} startNode - Starting node ID
 * @param {String} endNode - Destination node ID
 * @returns {Array|null} - Array of node IDs representing the path, or null if no path exists
 */
export function findShortestPath(graph, startNode, endNode) {
  if (!graph || !startNode || !endNode) {
    console.error('❌ Missing required parameters for pathfinding');
    return null;
  }

  if (!graph[startNode]) {
    console.error(`❌ Start node ${startNode} not found in graph`);
    return null;
  }

  if (!graph[endNode]) {
    console.error(`❌ End node ${endNode} not found in graph`);
    return null;
  }

  if (startNode === endNode) {
    return [startNode];
  }

  // Initialize distances and visited set
  const distances = {};
  const previous = {};
  const unvisited = new Set();

  // Set all distances to infinity except start node
  Object.keys(graph).forEach(node => {
    distances[node] = Infinity;
    previous[node] = null;
    unvisited.add(node);
  });
  distances[startNode] = 0;

  while (unvisited.size > 0) {
    // Find unvisited node with smallest distance
    let currentNode = null;
    let smallestDistance = Infinity;

    unvisited.forEach(node => {
      if (distances[node] < smallestDistance) {
        smallestDistance = distances[node];
        currentNode = node;
      }
    });

    if (currentNode === null || smallestDistance === Infinity) {
      // No path exists
      console.warn(`⚠️ No path found from ${startNode} to ${endNode}`);
      return null;
    }

    unvisited.delete(currentNode);

    // Found the destination
    if (currentNode === endNode) {
      break;
    }

    // Update distances to neighbors
    const neighbors = graph[currentNode].connections || [];
    neighbors.forEach(neighbor => {
      if (unvisited.has(neighbor)) {
        const altDistance = distances[currentNode] + 1; // Assuming unit distance
        if (altDistance < distances[neighbor]) {
          distances[neighbor] = altDistance;
          previous[neighbor] = currentNode;
        }
      }
    });
  }

  // Reconstruct path
  if (distances[endNode] === Infinity) {
    console.warn(`⚠️ No path found from ${startNode} to ${endNode}`);
    return null;
  }

  const path = [];
  let current = endNode;
  while (current !== null) {
    path.unshift(current);
    current = previous[current];
  }

  console.log(`✅ Found path (${path.length} nodes): ${startNode} → ${endNode}`);
  return path;
}

/**
 * Find nearest navigation node to a geographic position
 * @param {Object} userPos - Leaflet LatLng object
 * @param {Object} nodePositions - Map of nodeId -> LatLng position
 * @returns {String|null} - Nearest node ID or null
 */
export function findNearestNode(userPos, nodePositions) {
  if (!userPos || !nodePositions) {
    console.error('❌ Missing parameters for nearest node search');
    return null;
  }

  let nearestNode = null;
  let minDistance = Infinity;

  Object.entries(nodePositions).forEach(([nodeId, nodePos]) => {
    if (!nodePos || !nodePos.lat || !nodePos.lng) {
      return;
    }

    // Calculate distance using Leaflet's distanceTo (in meters)
    const latLng = L?.latLng ? L.latLng(nodePos.lat, nodePos.lng) : nodePos;
    const distance = userPos.distanceTo ? userPos.distanceTo(latLng) : 
                     Math.sqrt(Math.pow(userPos.lat - nodePos.lat, 2) + Math.pow(userPos.lng - nodePos.lng, 2));
    
    if (distance < minDistance) {
      minDistance = distance;
      nearestNode = nodeId;
    }
  });

  if (nearestNode) {
    console.log(`✅ Nearest node: ${nearestNode} (${minDistance.toFixed(2)}m away)`);
  }

  return nearestNode;
}

/**
 * Find path across multiple buildings
 * Ported from set_start_end.html lines 1441-1538
 * 
 * @param {Object} params - Navigation parameters
 * @param {String} params.startBuilding - Starting building ID (e.g., "Building M")
 * @param {String} params.startFloor - Starting floor number
 * @param {String} params.endBuilding - Destination building ID
 * @param {String} params.endFloor - Destination floor number
 * @param {String} params.destinationNodeId - Target node ID in destination building
 * @param {Object} params.userPosition - User's current LatLng position
 * @param {Object} params.buildingGraphs - Map of building IDs to graph data
 * @param {Object} params.buildingConnections - Building connection configuration
 * @returns {Object|null} - Path object with segments or null if no path exists
 */
export function findPathAcrossBuildings({
  startBuilding,
  startFloor,
  endBuilding,
  endFloor,
  destinationNodeId,
  userPosition,
  buildingGraphs,
  buildingConnections
}) {
  console.log(`🗺️ Finding path: ${startBuilding} Floor ${startFloor} → ${endBuilding} Floor ${endFloor}`);
  console.log(`   Destination node: ${destinationNodeId}`);

  // Case 1: Same building, same floor - simple pathfinding
  if (startBuilding === endBuilding && startFloor === endFloor) {
    console.log("✅ Same building/floor - using simple pathfinding");
    const graphData = buildingGraphs[startBuilding];

    if (!graphData || !graphData.graph) {
      console.error(`❌ No graph data for ${startBuilding}`);
      return null;
    }

    const startNode = findNearestNode(userPosition, graphData.nodePositions);
    if (!startNode) {
      console.error(`❌ Could not find start node near user position`);
      return null;
    }

    const path = findShortestPath(graphData.graph, startNode, destinationNodeId);

    if (!path) {
      return null;
    }

    return {
      type: 'single-building',
      path: path,
      building: startBuilding,
      floor: startFloor,
      startNode: startNode,
      endNode: destinationNodeId
    };
  }

  // Case 2: Different buildings - need to use connector
  if (startBuilding !== endBuilding) {
    console.log("🌉 Different buildings - checking connections");

    const connection = buildingConnections?.[startBuilding]?.[endBuilding];

    if (!connection) {
      console.error(`❌ No connection defined between ${startBuilding} and ${endBuilding}`);
      return null;
    }

    console.log("✅ Found connection:", connection);

    // Path segment 1: User position → exit node in current building
    const startGraphData = buildingGraphs[startBuilding];
    if (!startGraphData || !startGraphData.graph) {
      console.error(`❌ No graph data for start building: ${startBuilding}`);
      return null;
    }

    const startNode = findNearestNode(userPosition, startGraphData.nodePositions);
    if (!startNode) {
      console.error(`❌ Could not find start node`);
      return null;
    }

    console.log(`   Start node: ${startNode} → Exit node: ${connection.exitNode}`);

    const pathToExit = findShortestPath(startGraphData.graph, startNode, connection.exitNode);

    if (!pathToExit) {
      console.error(`❌ Could not find path to exit in ${startBuilding}`);
      return null;
    }
    console.log(`✅ Path to exit (${pathToExit.length} nodes)`);

    // Path segment 2: entry node in destination building → destination
    const endGraphData = buildingGraphs[endBuilding];
    if (!endGraphData || !endGraphData.graph) {
      console.error(`❌ No graph data for end building: ${endBuilding}`);
      return null;
    }

    console.log(`   Entry node: ${connection.entryNode} → Destination: ${destinationNodeId}`);
    const pathToDestination = findShortestPath(endGraphData.graph, connection.entryNode, destinationNodeId);

    if (!pathToDestination) {
      console.error(`❌ Could not find path from entry to destination in ${endBuilding}`);
      return null;
    }
    console.log(`✅ Path to destination (${pathToDestination.length} nodes)`);

    return {
      type: 'multi-building',
      segments: [
        {
          building: startBuilding,
          floor: startFloor,
          path: pathToExit,
          startNode: startNode,
          endNode: connection.exitNode,
          description: `Navigate to ${endBuilding} connector`
        },
        {
          building: endBuilding,
          floor: endFloor,
          path: pathToDestination,
          startNode: connection.entryNode,
          endNode: destinationNodeId,
          description: `Navigate to destination in ${endBuilding}`
        }
      ],
      connection: connection,
      totalNodes: pathToExit.length + pathToDestination.length
    };
  }

  // Case 3: Same building, different floors
  // TODO: Implement multi-floor navigation with stairs/elevators
  console.warn("⚠️ Multi-floor navigation not yet implemented");
  return null;
}

/**
 * Convert path (array of node IDs) to coordinates for map display
 * @param {Array} path - Array of node IDs
 * @param {Object} nodePositions - Map of nodeId -> {lat, lng}
 * @returns {Array} - Array of [lat, lng] coordinate pairs
 */
export function pathToCoordinates(path, nodePositions) {
  if (!path || !nodePositions) {
    return [];
  }

  return path.map(nodeId => {
    const pos = nodePositions[nodeId];
    if (!pos) {
      console.warn(`⚠️ No position found for node ${nodeId}`);
      return null;
    }
    return [pos.lat, pos.lng];
  }).filter(coord => coord !== null);
}

/**
 * Calculate total path distance in meters
 * @param {Array} coordinates - Array of [lat, lng] pairs
 * @returns {Number} - Total distance in meters
 */
export function calculatePathDistance(coordinates) {
  if (!coordinates || coordinates.length < 2) {
    return 0;
  }

  let totalDistance = 0;
  for (let i = 1; i < coordinates.length; i++) {
    const [lat1, lng1] = coordinates[i - 1];
    const [lat2, lng2] = coordinates[i];
    
    // Simple distance calculation (could use Haversine for accuracy)
    const latLng1 = L?.latLng ? L.latLng(lat1, lng1) : { lat: lat1, lng: lng1 };
    const latLng2 = L?.latLng ? L.latLng(lat2, lng2) : { lat: lat2, lng: lng2 };
    
    const distance = latLng1.distanceTo ? latLng1.distanceTo(latLng2) : 
                     Math.sqrt(Math.pow(lat2 - lat1, 2) + Math.pow(lng2 - lng1, 2)) * 111319; // rough conversion
    
    totalDistance += distance;
  }

  return totalDistance;
}

export default {
  findShortestPath,
  findNearestNode,
  findPathAcrossBuildings,
  pathToCoordinates,
  calculatePathDistance
};
