/**
 * Navigation API Client
 * 
 * Frontend client for interacting with the backend navigation API
 */

const API_BASE = '/api/navigation';

/**
 * Get complete all_node_data.json with all buildings and floors
 */
export async function getAllNodeData() {
  try {
    const response = await fetch('/leaflet-assets/all_node_data.json');
    if (!response.ok) throw new Error('Failed to fetch all_node_data.json');
    const data = await response.json();
    console.log('✅ Loaded all_node_data.json');
    return data;
  } catch (error) {
    console.error('Error fetching all_node_data:', error);
    return null;
  }
}

/**
 * Get list of all buildings with navigation data
 */
export async function getAvailableBuildings() {
  try {
    const response = await fetch(`${API_BASE}/buildings`);
    if (!response.ok) throw new Error('Failed to fetch buildings');
    const data = await response.json();
    return data.buildings || [];
  } catch (error) {
    console.error('Error fetching buildings:', error);
    return [];
  }
}

/**
 * Get list of floors for a building
 */
export async function getAvailableFloors(building) {
  try {
    const response = await fetch(`${API_BASE}/floors/${building}`);
    if (!response.ok) throw new Error(`Failed to fetch floors for building ${building}`);
    const data = await response.json();
    return data.floors || [];
  } catch (error) {
    console.error(`Error fetching floors for building ${building}:`, error);
    return [];
  }
}

/**
 * Get navigation data for a specific building and floor
 */
export async function getNavigationData(building, floor) {
  try {
    const response = await fetch(`${API_BASE}/data?building=${building}&floor=${floor}`);
    if (!response.ok) throw new Error(`Failed to fetch navigation data for ${building}-${floor}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching navigation data for ${building}-${floor}:`, error);
    return null;
  }
}

/**
 * Get all rooms for a building and floor
 */
export async function getAllRooms(building, floor) {
  try {
    const response = await fetch(`${API_BASE}/all-rooms?building=${building}&floor=${floor}`);
    if (!response.ok) throw new Error(`Failed to fetch rooms for ${building}-${floor}`);
    const data = await response.json();
    return data.rooms || {};
  } catch (error) {
    console.error(`Error fetching rooms for ${building}-${floor}:`, error);
    return {};
  }
}

/**
 * Look up node for a room ID
 */
export async function lookupRoom(building, floor, room) {
  try {
    const response = await fetch(`${API_BASE}/room-lookup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ building, floor, room }),
    });
    if (!response.ok) throw new Error(`Room ${room} not found`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error looking up room ${room}:`, error);
    return null;
  }
}

/**
 * Calculate navigation path between two locations
 * 
 * @param {Object} start - {building, floor, node or room}
 * @param {Object} end - {building, floor, node or room}
 * @returns {Object} - {path, directions, text_summary}
 */
export async function calculatePath(start, end) {
  try {
    const response = await fetch(`${API_BASE}/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ start, end }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to calculate path');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error calculating path:', error);
    return null;
  }
}

/**
 * Parse navigation intent from user message
 */
export async function parseNavigationIntent(message) {
  try {
    const response = await fetch(`${API_BASE}/parse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) throw new Error('Failed to parse navigation intent');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error parsing navigation intent:', error);
    return { is_navigation: false };
  }
}

/**
 * Get floor plan URL for a building and floor
 */
export function getFloorPlanUrl(building, floor) {
  // Floor plan files are named like M1.svg, M2.svg in Building M folder
  return `/leaflet-assets/Floorplans/Building ${building}/${building}${floor}.svg`;
}

/**
 * Get building position adjustments
 */
export async function getBuildingPositions() {
  try {
    const response = await fetch('/leaflet-assets/building_positions.json');
    if (!response.ok) throw new Error('Failed to fetch building positions');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching building positions:', error);
    return null;
  }
}

/**
 * Rotate a point around a center by an angle (in degrees)
 * Matches the coordinate_system.html implementation
 */
export function rotatePoint(point, center, angleDeg) {
  const angleRad = (angleDeg * Math.PI) / 180;
  const cos = Math.cos(angleRad);
  const sin = Math.sin(angleRad);

  const dx = point.lng - center.lng;
  const dy = point.lat - center.lat;

  return {
    lat: center.lat + (dy * cos - dx * sin),
    lng: center.lng + (dx * cos + dy * sin)
  };
}

/**
 * Calculate rotated bounds for SVG overlay
 * Based on coordinate_system.html approach
 */
export function calculateRotatedBounds(bounds, rotationDeg) {
  // bounds format: [[south, west], [north, east]]
  const south = bounds[0][0];
  const west = bounds[0][1];
  const north = bounds[1][0];
  const east = bounds[1][1];
  
  const center = {
    lat: (south + north) / 2,
    lng: (west + east) / 2
  };
  
  // Calculate corners: NW, NE, SE, SW
  const corners = [
    { lat: north, lng: west },  // NW
    { lat: north, lng: east },  // NE
    { lat: south, lng: east },  // SE
    { lat: south, lng: west }   // SW
  ];
  
  // Rotate each corner around center
  return corners.map(corner => rotatePoint(corner, center, rotationDeg));
}

/**
 * Format path data for map display
 */
export function formatPathForDisplay(pathData) {
  if (!pathData || !pathData.path) return null;

  const { path, directions } = pathData;
  const pathType = path.type;

  if (pathType === 'single-building') {
    return {
      type: 'single',
      building: path.building,
      floor: path.floor,
      nodes: path.path,
      coordinates: path.nodes.map(node => [node.lat, node.lng]),
      directions: directions.steps,
    };
  } else if (pathType === 'multi-building') {
    return {
      type: 'multi-building',
      segments: path.segments.map((segment, idx) => ({
        building: segment.building,
        floor: segment.floor,
        nodes: segment.path,
        coordinates: segment.nodes.map(node => [node.lat, node.lng]),
        description: segment.description,
      })),
      directions: directions.steps,
    };
  } else if (pathType === 'multi-floor') {
    return {
      type: 'multi-floor',
      building: path.building,
      segments: path.segments.map((segment, idx) => ({
        floor: segment.floor,
        nodes: segment.path,
        coordinates: segment.nodes.map(node => [node.lat, node.lng]),
        description: segment.description,
      })),
      transition: path.transition,
      directions: directions.steps,
    };
  }

  return null;
}

/**
 * Extract node coordinates from path data
 */
export function extractPathCoordinates(pathData) {
  if (!pathData) return [];

  const formatted = formatPathForDisplay(pathData);
  if (!formatted) return [];

  if (formatted.type === 'single') {
    return formatted.coordinates;
  } else if (formatted.type === 'multi-building' || formatted.type === 'multi-floor') {
    // Concatenate all segment coordinates
    return formatted.segments.reduce((acc, segment) => {
      return [...acc, ...segment.coordinates];
    }, []);
  }

  return [];
}

/**
 * Get building bounds for map display
 */
export function getBuildingBounds(building) {
  const bounds = {
    M: {
      center: [43.013, -81.2],
      bounds: [[43.0125, -81.2005], [43.0135, -81.1995]],
    },
    H: {
      center: [43.0133, -81.1998],
      bounds: [[43.0128, -81.2003], [43.0138, -81.1993]],
    },
    // Add other buildings as needed
  };

  return bounds[building] || bounds.M;
}
