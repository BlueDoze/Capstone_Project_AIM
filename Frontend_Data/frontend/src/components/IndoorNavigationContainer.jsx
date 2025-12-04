import React, { useState, useEffect } from 'react';
import IndoorMapView from './IndoorMapView';
import FloorSelector, { BuildingInfo, NavigationControls } from './FloorSelector';
import {
  loadFloorPlanData,
  loadNavigationNodes,
  findPath,
  nodePathToCoordinates,
  findNearestNode,
  generateDirections,
  getAvailableFloors,
} from '../utils/navigationUtils';

/**
 * IndoorNavigationContainer Component
 * 
 * Complete indoor navigation system integrating:
 * - Floor plan display
 * - Floor selection
 * - Pathfinding and navigation
 * - Turn-by-turn directions
 * 
 * This component demonstrates how to use the LeafletJS assets
 * for indoor navigation in the React app.
 */
export default function IndoorNavigationContainer({
  building = 'M',
  initialFloor = '1',
  startRoom = null,
  endRoom = null,
  className = '',
}) {
  // State management
  const [currentFloor, setCurrentFloor] = useState(initialFloor);
  const [floorPlanUrl, setFloorPlanUrl] = useState(null);
  const [navigationNodes, setNavigationNodes] = useState({});
  const [currentPath, setCurrentPath] = useState([]);
  const [isNavigating, setIsNavigating] = useState(false);
  const [currentInstruction, setCurrentInstruction] = useState('');
  const [userPosition, setUserPosition] = useState(null);
  const [availableFloors] = useState(getAvailableFloors(building));
  const [highlightedNodes, setHighlightedNodes] = useState([]);

  // Building-specific configuration
  const buildingConfig = {
    M: {
      name: 'Main Building',
      description: 'London Campus - Information Technology and Media',
      // Bounds for Building M floor plans (adjust based on your coordinate system)
      bounds: [
        [43.0125, -81.2005], // Southwest
        [43.0135, -81.1995], // Northeast
      ],
      center: [43.013, -81.2],
    },
    // Add other buildings as needed
  };

  const config = buildingConfig[building] || buildingConfig.M;

  // Load floor plan when building or floor changes
  useEffect(() => {
    loadFloorPlan();
  }, [building, currentFloor]);

  // Load navigation nodes when building changes
  useEffect(() => {
    loadNodes();
  }, [building]);

  // Calculate path when start/end rooms change
  useEffect(() => {
    if (startRoom && endRoom) {
      calculatePath(startRoom, endRoom);
    }
  }, [startRoom, endRoom, navigationNodes]);

  const loadFloorPlan = async () => {
    const url = await loadFloorPlanData(building, currentFloor);
    setFloorPlanUrl(url);
  };

  const loadNodes = async () => {
    const nodes = await loadNavigationNodes(building);
    setNavigationNodes(nodes);
  };

  const calculatePath = (start, end) => {
    // Find nearest nodes to start and end points
    const startNode = findNearestNode(start, navigationNodes);
    const endNode = findNearestNode(end, navigationNodes);

    if (!startNode || !endNode) {
      console.error('Could not find start or end nodes');
      return;
    }

    // Find path using Dijkstra's algorithm
    const graph = { nodes: navigationNodes };
    const nodePath = findPath(graph, startNode, endNode);

    if (nodePath.length === 0) {
      console.error('No path found');
      return;
    }

    // Convert to coordinates
    const coordinatePath = nodePathToCoordinates(nodePath, navigationNodes);
    setCurrentPath(coordinatePath);
    setHighlightedNodes(nodePath);

    // Generate directions
    const directions = generateDirections(nodePath, navigationNodes);
    if (directions.length > 0) {
      setCurrentInstruction(directions[0].instruction);
    }
  };

  const handleFloorChange = (newFloor) => {
    setCurrentFloor(newFloor);
  };

  const handleNodeClick = (node) => {
    console.log('Node clicked:', node);
    // You can implement custom logic here, e.g., set as destination
  };

  const handleStartNavigation = () => {
    setIsNavigating(true);
    // You could start tracking user position here
  };

  const handleStopNavigation = () => {
    setIsNavigating(false);
    setCurrentPath([]);
    setCurrentInstruction('');
    setHighlightedNodes([]);
  };

  const handleRecenter = () => {
    // Recenter map on user position
    if (userPosition) {
      // This would trigger the map to recenter
      console.log('Recentering on user position:', userPosition);
    }
  };

  // Convert nodes object to array for rendering
  const nodesArray = Object.entries(navigationNodes)
    .filter(([id, node]) => node.floor === currentFloor)
    .map(([id, node]) => ({
      id,
      ...node,
    }));

  return (
    <div className={`indoor-navigation-container ${className}`}>
      {/* Controls overlay */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          maxWidth: '300px',
        }}
      >
        {/* Building info */}
        <BuildingInfo
          building={building}
          info={{
            name: config.name,
            description: config.description,
          }}
        />

        {/* Floor selector */}
        <FloorSelector
          building={building}
          currentFloor={currentFloor}
          availableFloors={availableFloors}
          onFloorChange={handleFloorChange}
        />

        {/* Navigation controls */}
        {(startRoom || endRoom) && (
          <NavigationControls
            isNavigating={isNavigating}
            currentInstruction={currentInstruction}
            onStartNavigation={handleStartNavigation}
            onStopNavigation={handleStopNavigation}
            onRecenter={handleRecenter}
          />
        )}
      </div>

      {/* Map view */}
      <IndoorMapView
        building={building}
        floor={currentFloor}
        floorPlanUrl={floorPlanUrl}
        bounds={config.bounds}
        nodes={nodesArray}
        path={currentPath}
        userPosition={userPosition}
        onNodeClick={handleNodeClick}
        center={config.center}
        zoom={18}
        highlightedNodes={highlightedNodes}
      />
    </div>
  );
}
