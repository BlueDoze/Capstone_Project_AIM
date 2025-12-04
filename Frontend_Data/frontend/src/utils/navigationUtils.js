/**
 * Navigation Utilities
 * 
 * Helper functions for pathfinding and navigation calculations
 * Based on the LeafletJS folder's navigation logic
 */

/**
 * Calculate distance between two points using Euclidean distance
 */
export function calculateDistance(point1, point2) {
  const dx = point2[0] - point1[0];
  const dy = point2[1] - point1[1];
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Dijkstra's algorithm for pathfinding
 * 
 * @param {Object} graph - Graph with nodes and connections
 * @param {string} startId - Starting node ID
 * @param {string} endId - Ending node ID
 * @returns {Array} - Array of node IDs representing the path
 */
export function findPath(graph, startId, endId) {
  if (!graph || !graph.nodes || !startId || !endId) {
    console.error('Invalid graph or node IDs');
    return [];
  }

  const nodes = graph.nodes;
  const distances = {};
  const previous = {};
  const unvisited = new Set();

  // Initialize distances
  Object.keys(nodes).forEach((nodeId) => {
    distances[nodeId] = Infinity;
    previous[nodeId] = null;
    unvisited.add(nodeId);
  });

  distances[startId] = 0;

  while (unvisited.size > 0) {
    // Find node with minimum distance
    let currentId = null;
    let minDistance = Infinity;

    unvisited.forEach((nodeId) => {
      if (distances[nodeId] < minDistance) {
        minDistance = distances[nodeId];
        currentId = nodeId;
      }
    });

    if (currentId === null || currentId === endId) {
      break;
    }

    unvisited.delete(currentId);
    const currentNode = nodes[currentId];

    if (!currentNode || !currentNode.connections) {
      continue;
    }

    // Check all neighbors
    currentNode.connections.forEach((neighborId) => {
      if (!unvisited.has(neighborId)) {
        return;
      }

      const neighbor = nodes[neighborId];
      if (!neighbor) {
        return;
      }

      const distance = calculateDistance(
        currentNode.position,
        neighbor.position
      );
      const altDistance = distances[currentId] + distance;

      if (altDistance < distances[neighborId]) {
        distances[neighborId] = altDistance;
        previous[neighborId] = currentId;
      }
    });
  }

  // Reconstruct path
  const path = [];
  let current = endId;

  while (current !== null) {
    path.unshift(current);
    current = previous[current];
  }

  // Return empty array if no path found
  if (path.length === 0 || path[0] !== startId) {
    return [];
  }

  return path;
}

/**
 * Convert node IDs to coordinate positions
 */
export function nodePathToCoordinates(nodePath, nodes) {
  return nodePath.map((nodeId) => {
    const node = nodes[nodeId];
    return node ? node.position : null;
  }).filter(Boolean);
}

/**
 * Find the nearest node to a given position
 */
export function findNearestNode(position, nodes) {
  if (!position || !nodes) {
    return null;
  }

  let nearestId = null;
  let minDistance = Infinity;

  Object.entries(nodes).forEach(([nodeId, node]) => {
    if (!node.position) {
      return;
    }

    const distance = calculateDistance(position, node.position);
    if (distance < minDistance) {
      minDistance = distance;
      nearestId = nodeId;
    }
  });

  return nearestId;
}

/**
 * Generate turn-by-turn directions from a path
 */
export function generateDirections(path, nodes) {
  if (!path || path.length < 2) {
    return [];
  }

  const directions = [];

  for (let i = 0; i < path.length - 1; i++) {
    const currentNode = nodes[path[i]];
    const nextNode = nodes[path[i + 1]];

    if (!currentNode || !nextNode) {
      continue;
    }

    let instruction = '';

    // Determine instruction based on node types
    if (nextNode.type === 'stairs') {
      instruction = `Take the stairs ${nextNode.direction || ''}`;
    } else if (nextNode.type === 'elevator') {
      instruction = 'Take the elevator';
    } else if (nextNode.type === 'door') {
      instruction = `Go through the ${nextNode.name || 'door'}`;
    } else if (nextNode.type === 'hallway') {
      instruction = 'Continue down the hallway';
    } else if (nextNode.type === 'room') {
      instruction = `Arrive at ${nextNode.name || 'destination'}`;
    } else {
      // Calculate direction
      const angle = calculateBearing(currentNode.position, nextNode.position);
      const direction = bearingToDirection(angle);
      instruction = `Head ${direction}`;
    }

    directions.push({
      nodeId: nextNode.id,
      instruction,
      position: nextNode.position,
      distance: calculateDistance(currentNode.position, nextNode.position),
    });
  }

  return directions;
}

/**
 * Calculate bearing between two points
 */
export function calculateBearing(point1, point2) {
  const dx = point2[0] - point1[0];
  const dy = point2[1] - point1[1];
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);
  return (angle + 360) % 360;
}

/**
 * Convert bearing to cardinal direction
 */
export function bearingToDirection(bearing) {
  const directions = [
    'north',
    'northeast',
    'east',
    'southeast',
    'south',
    'southwest',
    'west',
    'northwest',
  ];
  const index = Math.round(bearing / 45) % 8;
  return directions[index];
}

/**
 * Load floor plan data from the LeafletJS assets
 */
export async function loadFloorPlanData(building, floor) {
  try {
    const response = await fetch(
      `/leaflet-assets/Floorplans/Building ${building}/${building}${floor}.svg`
    );
    if (!response.ok) {
      throw new Error(`Floor plan not found: ${building}${floor}`);
    }
    return `/leaflet-assets/Floorplans/Building ${building}/${building}${floor}.svg`;
  } catch (error) {
    console.error('Error loading floor plan:', error);
    return null;
  }
}

/**
 * Load navigation nodes for a building
 */
export async function loadNavigationNodes(building) {
  try {
    const response = await fetch('/leaflet-assets/JSON/all_node_data.json');
    if (!response.ok) {
      throw new Error('Failed to load navigation nodes');
    }
    const data = await response.json();
    
    // Filter nodes for the specific building
    const buildingNodes = {};
    Object.entries(data).forEach(([nodeId, node]) => {
      if (node.building === building) {
        buildingNodes[nodeId] = node;
      }
    });
    
    return buildingNodes;
  } catch (error) {
    console.error('Error loading navigation nodes:', error);
    return {};
  }
}

/**
 * Load building positions and connections
 */
export async function loadBuildingConnections() {
  try {
    const response = await fetch('/leaflet-assets/JSON/building_connections.JSON');
    if (!response.ok) {
      throw new Error('Failed to load building connections');
    }
    return await response.json();
  } catch (error) {
    console.error('Error loading building connections:', error);
    return {};
  }
}

/**
 * Convert SVG coordinates to Leaflet lat/lng
 * (This depends on your specific coordinate system - adjust as needed)
 */
export function svgToLatLng(svgPoint, bounds) {
  if (!bounds || !svgPoint) {
    return null;
  }

  // Assuming bounds is [[south, west], [north, east]]
  const [[south, west], [north, east]] = bounds;
  
  // This is a simplified conversion - adjust based on your actual coordinate system
  const lat = south + (svgPoint[1] / 1000) * (north - south);
  const lng = west + (svgPoint[0] / 1000) * (east - west);
  
  return [lat, lng];
}

/**
 * Get available floors for a building
 */
export function getAvailableFloors(building) {
  // This should be loaded from your building data
  // For now, return a common configuration
  const floorConfigs = {
    A: [{ level: '1', name: 'Ground Floor' }, { level: '2', name: 'Second Floor' }, { level: '3', name: 'Third Floor' }],
    B: [{ level: '1', name: 'Ground Floor' }, { level: '2', name: 'Second Floor' }],
    C: [{ level: '1', name: 'Ground Floor' }, { level: '2', name: 'Second Floor' }],
    D: [{ level: '1', name: 'Ground Floor' }, { level: '2', name: 'Second Floor' }],
    E: [{ level: '1', name: 'Ground Floor' }, { level: '2', name: 'Second Floor' }],
    G: [{ level: '1', name: 'Ground Floor' }],
    H: [{ level: '1', name: 'Ground Floor' }],
    J: [{ level: '1', name: 'Ground Floor' }],
    K: [{ level: '1', name: 'Ground Floor' }],
    M: [{ level: '1', name: 'Ground Floor' }, { level: '2', name: 'Second Floor' }],
    T: [{ level: '1', name: 'Ground Floor' }],
  };

  return floorConfigs[building] || [];
}
