/**
 * Navigation Utilities
 * 
 * Helper functions for pathfinding and navigation calculations
 * Based on the LeafletJS folder's navigation logic
 * Enhanced with GPS positioning and interactive node features
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
 * Calculate geographic distance between two lat/lng points using Haversine formula
 */
export function calculateGeoDistance(pos1, pos2) {
  const R = 6371e3; // Earth radius in meters
  const φ1 = (pos1.lat * Math.PI) / 180;
  const φ2 = (pos2.lat * Math.PI) / 180;
  const Δφ = ((pos2.lat - pos1.lat) * Math.PI) / 180;
  const Δλ = ((pos2.lng - pos1.lng) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
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

/**
 * Store user position in localStorage
 */
export function storeUserPosition(position, floor, building) {
  const data = {
    position,
    floor,
    building,
    timestamp: Date.now(),
  };
  localStorage.setItem('user_position', JSON.stringify(data));
}

/**
 * Retrieve user position from localStorage
 */
export function retrieveUserPosition(maxAge = 3600000) {
  try {
    const stored = localStorage.getItem('user_position');
    if (!stored) return null;

    const data = JSON.parse(stored);
    const age = Date.now() - data.timestamp;

    if (age > maxAge) {
      localStorage.removeItem('user_position');
      return null;
    }

    return {
      position: data.position,
      floor: data.floor,
      building: data.building,
    };
  } catch (error) {
    console.error('Error retrieving user position:', error);
    return null;
  }
}

/**
 * Format distance for display
 */
export function formatDistance(meters) {
  if (meters < 1) {
    return `${Math.round(meters * 100)} cm`;
  } else if (meters < 1000) {
    return `${Math.round(meters)} m`;
  } else {
    return `${(meters / 1000).toFixed(2)} km`;
  }
}

/**
 * Find nearest node to GPS position with floor filtering
 * Works with both {lat, lng} objects and [lat, lng] arrays
 */
export function findNearestNodeToGPS(gpsPosition, navigationData, floor = null) {
  if (!gpsPosition || !navigationData || !navigationData.nodes) {
    return null;
  }

  // Normalize position to {lat, lng} format
  let normalizedPos = gpsPosition;
  if (Array.isArray(gpsPosition)) {
    normalizedPos = { lat: gpsPosition[0], lng: gpsPosition[1] };
  } else if (gpsPosition.lat === undefined && gpsPosition.lng === undefined) {
    // Leaflet LatLng object - has lat() and lng() methods
    normalizedPos = { 
      lat: typeof gpsPosition.lat === 'function' ? gpsPosition.lat() : gpsPosition.lat,
      lng: typeof gpsPosition.lng === 'function' ? gpsPosition.lng() : gpsPosition.lng
    };
  }

  let nearestNode = null;
  let minDistance = Infinity;

  Object.entries(navigationData.nodes).forEach(([nodeId, node]) => {
    // Filter by floor if specified
    if (floor && node.floor !== floor) {
      return;
    }

    if (!node.position || node.position.length < 2) {
      return;
    }

    const nodeGeoPos = { 
      lat: node.position[0], 
      lng: node.position[1] 
    };

    const distance = calculateGeoDistance(normalizedPos, nodeGeoPos);
    
    if (distance < minDistance) {
      minDistance = distance;
      nearestNode = nodeId;
    }
  });

  if (nearestNode) {
    console.log(`📍 Nearest node to GPS: ${nearestNode} (${minDistance.toFixed(2)}m away)`);
  }

  return nearestNode;
}

/**
 * Find nearest node to a click position (simpler version for map interactions)
 * Specifically for handling Leaflet map click events
 */
export function findNearestNodeToClick(clickPosition, navigationGraph, floor = null) {
  if (!clickPosition || !navigationGraph) {
    return null;
  }

  // Extract lat/lng from Leaflet LatLng object or array
  const lat = typeof clickPosition.lat === 'function' ? clickPosition.lat() : clickPosition.lat || clickPosition[0];
  const lng = typeof clickPosition.lng === 'function' ? clickPosition.lng() : clickPosition.lng || clickPosition[1];
  
  const clickPos = { lat, lng };

  let nearestNode = null;
  let minDistance = Infinity;

  Object.entries(navigationGraph).forEach(([nodeId, node]) => {
    // Filter by floor if specified
    if (floor && node.floor && node.floor !== floor) {
      return;
    }

    if (!node.position || node.position.length < 2) {
      return;
    }

    const nodePos = { 
      lat: node.position[0], 
      lng: node.position[1] 
    };

    const distance = calculateGeoDistance(clickPos, nodePos);
    
    if (distance < minDistance) {
      minDistance = distance;
      nearestNode = nodeId;
    }
  });

  if (nearestNode) {
    console.log(`🎯 Nearest node to click: ${nearestNode} (${minDistance.toFixed(2)}m away)`);
  }

  return nearestNode;
}
