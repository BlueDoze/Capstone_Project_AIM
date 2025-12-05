/**
 * BuildingConnectionService.js
 * 
 * Manages building-to-building connections for multi-building navigation
 * Loads and provides access to building_connections.JSON data
 */

/**
 * Building connections cache
 */
let buildingConnectionsCache = null;

/**
 * Fetch building connections from server
 * @returns {Promise<Object>} - Building connections data
 */
export async function fetchBuildingConnections() {
  if (buildingConnectionsCache) {
    console.log('✅ Using cached building connections');
    return buildingConnectionsCache;
  }

  try {
    const response = await fetch('/leaflet-assets/building_connections.JSON');
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const connections = await response.json();
    buildingConnectionsCache = connections;
    
    console.log('✅ Building connections loaded:', connections);
    return connections;
  } catch (error) {
    console.error('❌ Failed to fetch building connections:', error);
    return {};
  }
}

/**
 * Get connection between two buildings
 * @param {String} fromBuilding - Source building (e.g., "Building M")
 * @param {String} toBuilding - Destination building
 * @returns {Promise<Object|null>} - Connection object or null if not found
 */
export async function getConnection(fromBuilding, toBuilding) {
  const connections = await fetchBuildingConnections();
  
  const connection = connections?.[fromBuilding]?.[toBuilding];
  
  if (connection) {
    console.log(`✅ Found connection ${fromBuilding} → ${toBuilding}:`, connection);
  } else {
    console.warn(`⚠️ No connection found between ${fromBuilding} and ${toBuilding}`);
  }
  
  return connection || null;
}

/**
 * Get all connections from a specific building
 * @param {String} building - Building ID
 * @returns {Promise<Object>} - Map of destination buildings to connection objects
 */
export async function getConnectionsFrom(building) {
  const connections = await fetchBuildingConnections();
  return connections?.[building] || {};
}

/**
 * Check if two buildings are connected
 * @param {String} building1 - First building
 * @param {String} building2 - Second building
 * @returns {Promise<Boolean>} - True if connected (in either direction)
 */
export async function areConnected(building1, building2) {
  const connections = await fetchBuildingConnections();
  
  const forward = connections?.[building1]?.[building2];
  const reverse = connections?.[building2]?.[building1];
  
  return !!(forward || reverse);
}

/**
 * Get all buildings that have connections
 * @returns {Promise<Array<String>>} - Array of building IDs
 */
export async function getConnectedBuildings() {
  const connections = await fetchBuildingConnections();
  return Object.keys(connections);
}

/**
 * Clear the building connections cache
 */
export function clearCache() {
  buildingConnectionsCache = null;
  console.log('🗑️ Building connections cache cleared');
}

export default {
  fetchBuildingConnections,
  getConnection,
  getConnectionsFrom,
  areConnected,
  getConnectedBuildings,
  clearCache
};
