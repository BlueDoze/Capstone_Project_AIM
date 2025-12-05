/**
 * usePathfinding.js
 * 
 * Custom hook for pathfinding operations using NavigationEngine
 * Provides multi-building navigation and path management
 */

import { useState, useCallback } from 'react';
import { 
  findPathAcrossBuildings,
  pathToCoordinates,
  calculatePathDistance 
} from '../services/NavigationEngine';

/**
 * Hook for pathfinding and route management
 * @param {Object} buildingGraphs - Map of building IDs to graph data
 * @param {Object} buildingConnections - Building connection configuration
 */
export function usePathfinding(buildingGraphs, buildingConnections) {
  const [currentPath, setCurrentPath] = useState(null);
  const [pathCoordinates, setPathCoordinates] = useState([]);
  const [pathDistance, setPathDistance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Find path between two locations
   * @param {Object} params - Navigation parameters
   * @param {String} params.startBuilding - Starting building
   * @param {String} params.startFloor - Starting floor
   * @param {String} params.endBuilding - Destination building
   * @param {String} params.endFloor - Destination floor
   * @param {String} params.endNode - Destination node ID
   * @param {Object} params.userPosition - User's current position {lat, lng}
   */
  const findPath = useCallback(async ({
    startBuilding,
    startFloor,
    endBuilding,
    endFloor,
    endNode,
    userPosition
  }) => {
    if (!buildingGraphs || !buildingConnections) {
      setError('Building graphs or connections not loaded');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔍 Finding path...');
      console.log(`   From: Building ${startBuilding} Floor ${startFloor}`);
      console.log(`   To: Building ${endBuilding} Floor ${endFloor} Node ${endNode}`);

      const result = findPathAcrossBuildings({
        startBuilding,
        startFloor,
        endBuilding,
        endFloor,
        destinationNodeId: endNode,
        userPosition,
        buildingGraphs,
        buildingConnections
      });

      if (!result) {
        throw new Error('No path found');
      }

      setCurrentPath(result);

      // Convert path to coordinates for map display
      let coords = [];
      
      if (result.type === 'single-building') {
        const graphData = buildingGraphs[result.building];
        coords = pathToCoordinates(result.path, graphData.nodePositions);
      } else if (result.type === 'multi-building') {
        // Combine segments
        result.segments.forEach(segment => {
          const graphData = buildingGraphs[segment.building];
          const segmentCoords = pathToCoordinates(segment.path, graphData.nodePositions);
          coords = coords.concat(segmentCoords);
        });
      }

      setPathCoordinates(coords);

      // Calculate distance
      const distance = calculatePathDistance(coords);
      setPathDistance(distance);

      console.log(`✅ Path found: ${coords.length} waypoints, ${distance.toFixed(0)}m`);

      return result;
    } catch (err) {
      console.error('❌ Pathfinding error:', err);
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [buildingGraphs, buildingConnections]);

  /**
   * Clear current path
   */
  const clearPath = useCallback(() => {
    setCurrentPath(null);
    setPathCoordinates([]);
    setPathDistance(0);
    setError(null);
  }, []);

  /**
   * Get path segment for a specific building/floor
   * Useful for multi-building navigation
   */
  const getPathSegment = useCallback((building, floor) => {
    if (!currentPath) return null;

    if (currentPath.type === 'single-building') {
      if (currentPath.building === building && currentPath.floor === floor) {
        return currentPath.path;
      }
      return null;
    }

    if (currentPath.type === 'multi-building') {
      const segment = currentPath.segments.find(
        s => s.building === building && s.floor === floor
      );
      return segment ? segment.path : null;
    }

    return null;
  }, [currentPath]);

  return {
    currentPath,
    pathCoordinates,
    pathDistance,
    loading,
    error,
    findPath,
    clearPath,
    getPathSegment,
    hasPath: currentPath !== null,
    isMultiBuilding: currentPath?.type === 'multi-building'
  };
}

export default usePathfinding;
