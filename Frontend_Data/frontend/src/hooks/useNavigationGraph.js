/**
 * useNavigationGraph.js
 * 
 * Custom hook to load and manage navigation graph data from all_node_data.json
 * Provides caching and building/floor-specific data access
 */

import { useState, useEffect, useCallback } from 'react';
import { buildNavigationGraph } from '../services/SVGNodeParser';
import { fetchBuildingConnections } from '../services/BuildingConnectionService';

/**
 * Hook to load and manage complete navigation graph data
 */
export function useNavigationGraph() {
  const [allNodeData, setAllNodeData] = useState(null);
  const [buildingConnections, setBuildingConnections] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load all_node_data.json and building connections on mount
  useEffect(() => {
    loadNavigationData();
  }, []);

  const loadNavigationData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load all_node_data.json
      const nodeDataResponse = await fetch('/api/navigation/all-node-data');
      if (!nodeDataResponse.ok) {
        throw new Error('Failed to load navigation data');
      }
      const nodeData = await nodeDataResponse.json();

      // Load building connections
      const connections = await fetchBuildingConnections();

      setAllNodeData(nodeData);
      setBuildingConnections(connections);
      
      console.log('✅ Navigation graph data loaded');
      console.log(`   Buildings: ${Object.keys(nodeData).length}`);
      console.log(`   Connections: ${Object.keys(connections).length}`);
    } catch (err) {
      console.error('❌ Failed to load navigation data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    allNodeData,
    buildingConnections,
    loading,
    error,
    reload: loadNavigationData
  };
}

/**
 * Hook to load navigation data for a specific building and floor
 * @param {String} building - Building ID (e.g., "M", "H")
 * @param {String} floor - Floor number
 * @param {Object} overlayBounds - Leaflet bounds for coordinate conversion
 */
export function useFloorNavigation(building, floor, overlayBounds) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadFloorData = useCallback(async () => {
    if (!building || !floor || !overlayBounds) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch all_node_data.json
      const nodeDataResponse = await fetch('/api/navigation/all-node-data');
      if (!nodeDataResponse.ok) {
        throw new Error('Failed to load navigation data');
      }
      const allData = await nodeDataResponse.json();

      const buildingKey = `Building ${building}`;
      const buildingData = allData[buildingKey];

      if (!buildingData || !buildingData.floors || !buildingData.floors[floor]) {
        throw new Error(`No data for Building ${building} Floor ${floor}`);
      }

      const floorData = buildingData.floors[floor];

      // Fetch SVG content
      const svgResponse = await fetch(`/api/navigation/svg-content/${building}/${floor}`);
      if (!svgResponse.ok) {
        throw new Error('Failed to load SVG');
      }
      const { svgContent } = await svgResponse.json();

      // Build navigation graph with geographic coordinates
      const navGraph = buildNavigationGraph(
        svgContent,
        floorData.navigationGraph,
        overlayBounds
      );

      setGraphData({
        ...navGraph,
        building,
        floor,
        roomToNode: floorData.roomToNode || {},
        exitToNode: floorData.exitToNode || {},
        objects: floorData.objects || {},
        svgContent
      });

      console.log(`✅ Floor navigation loaded: Building ${building} Floor ${floor}`);
    } catch (err) {
      console.error('❌ Failed to load floor navigation:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [building, floor, overlayBounds]);

  useEffect(() => {
    loadFloorData();
  }, [loadFloorData]);

  return {
    graphData,
    loading,
    error,
    reload: loadFloorData
  };
}

/**
 * Hook to access building metadata from all_node_data.json
 * @param {String} building - Building ID
 */
export function useBuildingInfo(building) {
  const [buildingInfo, setBuildingInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!building) return;

    const loadBuildingInfo = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/navigation/all-node-data');
        if (!response.ok) {
          throw new Error('Failed to load navigation data');
        }
        const allData = await response.json();

        const buildingKey = `Building ${building}`;
        const data = allData[buildingKey];

        if (!data) {
          throw new Error(`Building ${building} not found`);
        }

        setBuildingInfo({
          path: data.path,
          floors: Object.keys(data.floors || {}),
          buildingKey
        });
      } catch (err) {
        console.error('❌ Failed to load building info:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadBuildingInfo();
  }, [building]);

  return { buildingInfo, loading, error };
}

export default {
  useNavigationGraph,
  useFloorNavigation,
  useBuildingInfo
};
