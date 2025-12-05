import React, { useState, useEffect, useCallback } from 'react';
import IndoorMapView from './IndoorMapView';
import FloorSelector, { BuildingInfo, NavigationControls } from './FloorSelector';
import StartupModal from './StartupModal';
import LocationToggle from './LocationToggle';
import {
  getNavigationData,
  calculatePath,
  getFloorPlanUrl,
  formatPathForDisplay,
  getAllRooms,
  getAvailableFloors,
} from '../utils/navigationApi';
import {
  storeUserPosition,
  retrieveUserPosition,
  findNearestNodeToGPS,
} from '../utils/navigationUtils';

/**
 * MapNavigator Component
 * 
 * Enhanced indoor navigation component using backend API
 * Integrates with new navigation services for pathfinding
 */
export default function MapNavigator({
  building = 'M',
  initialFloor = '1',
  mapAction = null,
  onNavigationComplete = null,
  className = '',
}) {
  // State management
  const [currentFloor, setCurrentFloor] = useState(initialFloor);
  const [floorPlanUrl, setFloorPlanUrl] = useState(null);
  const [navigationData, setNavigationData] = useState(null);
  const [currentPath, setCurrentPath] = useState(null);
  const [pathCoordinates, setPathCoordinates] = useState([]);
  const [isNavigating, setIsNavigating] = useState(false);
  const [directions, setDirections] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [userPosition, setUserPosition] = useState(null);
  const [availableFloors, setAvailableFloors] = useState([]);
  const [availableRooms, setAvailableRooms] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // New: User positioning states
  const [showStartupModal, setShowStartupModal] = useState(false);
  const [locationMode, setLocationMode] = useState('manual'); // 'manual' or 'gps'
  const [userFloor, setUserFloor] = useState(initialFloor);
  const [isWaitingForMapClick, setIsWaitingForMapClick] = useState(false);

  // Load initial data
  useEffect(() => {
    loadFloorData();
  }, [building, currentFloor]);

  // Initialize user position
  useEffect(() => {
    const saved = retrieveUserPosition();
    if (saved && saved.building === building) {
      setUserPosition(saved.position);
      setUserFloor(saved.floor);
      if (saved.floor !== currentFloor) {
        setCurrentFloor(saved.floor);
      }
    } else {
      // Show startup modal if no saved position
      setShowStartupModal(true);
    }
  }, [building]);

  // Handle map action from chat
  useEffect(() => {
    if (mapAction && mapAction.type === 'SHOW_ROUTE') {
      handleMapAction(mapAction);
    }
  }, [mapAction]);

  const loadFloorData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load floor plan URL
      const planUrl = getFloorPlanUrl(building, currentFloor);
      setFloorPlanUrl(planUrl);

      // Load navigation data
      const navData = await getNavigationData(building, currentFloor);
      setNavigationData(navData);

      // Load available floors
      const floors = await getAvailableFloors(building);
      setAvailableFloors(floors);

      // Load available rooms
      const rooms = await getAllRooms(building, currentFloor);
      setAvailableRooms(rooms);

    } catch (err) {
      console.error('Error loading floor data:', err);
      setError('Failed to load floor data');
    } finally {
      setLoading(false);
    }
  };

  const handleMapAction = async (action) => {
    if (!action.path) {
      // Calculate path if not provided
      await handleNavigationRequest(action.start, action.end);
    } else {
      // Use provided path
      displayPath(action.path, action.directions);
    }
  };

  const handleNavigationRequest = async (start, end) => {
    setLoading(true);
    setError(null);

    try {
      const result = await calculatePath(start, end);

      if (!result) {
        setError('Could not calculate path');
        return;
      }

      displayPath(result.path, result.directions);

    } catch (err) {
      console.error('Error calculating navigation:', err);
      setError('Failed to calculate route');
    } finally {
      setLoading(false);
    }
  };

  const displayPath = (pathData, directionsData) => {
    const formatted = formatPathForDisplay({ path: pathData, directions: directionsData });

    if (!formatted) {
      setError('Invalid path data');
      return;
    }

    setCurrentPath(formatted);
    setDirections(directionsData?.steps || []);
    setIsNavigating(true);
    setCurrentStepIndex(0);

    // Extract coordinates for map display
    if (formatted.type === 'single') {
      setPathCoordinates(formatted.coordinates);
      // Switch to path floor if different
      if (formatted.floor !== currentFloor) {
        setCurrentFloor(formatted.floor);
      }
    } else if (formatted.type === 'multi-floor') {
      // Show first segment
      const firstSegment = formatted.segments[0];
      setPathCoordinates(firstSegment.coordinates);
      if (firstSegment.floor !== currentFloor) {
        setCurrentFloor(firstSegment.floor);
      }
    } else if (formatted.type === 'multi-building') {
      // Show first segment
      const firstSegment = formatted.segments[0];
      setPathCoordinates(firstSegment.coordinates);
      if (firstSegment.building !== building || firstSegment.floor !== currentFloor) {
        // Note: Would need to switch buildings - for now just show message
        console.warn('Multi-building navigation requires building switch');
      }
    }
  };

  const handleStopNavigation = () => {
    setIsNavigating(false);
    setCurrentPath(null);
    setPathCoordinates([]);
    setDirections([]);
    setCurrentStepIndex(0);

    if (onNavigationComplete) {
      onNavigationComplete();
    }
  };

  const handleNextStep = () => {
    if (currentStepIndex < directions.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const handlePreviousStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleFloorChange = (newFloor) => {
    setCurrentFloor(newFloor);

    // If navigating multi-floor, update path coordinates
    if (currentPath && currentPath.type === 'multi-floor') {
      const segment = currentPath.segments.find(s => s.floor === newFloor);
      if (segment) {
        setPathCoordinates(segment.coordinates);
      }
    }
  };

  const handleRecenter = () => {
    // Reset map to center position
    // This would trigger a map reset in the IndoorMapView component
    console.log('Recenter map');
  };

  // New: Handle startup modal completion
  const handleStartupComplete = useCallback((result) => {
    setShowStartupModal(false);
    
    if (result.method === 'gps') {
      setLocationMode('gps');
      setUserFloor(result.floor);
      if (result.floor !== currentFloor) {
        setCurrentFloor(result.floor);
      }
    } else if (result.method === 'manual' && result.waitingForClick) {
      setIsWaitingForMapClick(true);
      setUserFloor(result.floor);
      if (result.floor !== currentFloor) {
        setCurrentFloor(result.floor);
      }
    } else if (result.method === 'default') {
      setUserPosition(result.position);
      setUserFloor(result.floor);
      storeUserPosition(result.position, result.floor, building);
    }
  }, [building, currentFloor]);

  // New: Handle GPS position updates
  const handleGPSPositionUpdate = useCallback((position) => {
    setUserPosition(position);
    storeUserPosition(position, userFloor, building);
    
    // Find nearest node for more accurate navigation
    if (navigationData) {
      const nearestNode = findNearestNodeToGPS(position, navigationData, userFloor);
      if (nearestNode) {
        console.log('User is near node:', nearestNode);
      }
    }
  }, [building, userFloor, navigationData]);

  // New: Handle map click for manual position setting
  const handleMapClick = useCallback((latlng) => {
    if (isWaitingForMapClick) {
      setUserPosition(latlng);
      setIsWaitingForMapClick(false);
      storeUserPosition(latlng, userFloor, building);
      console.log('User position set manually:', latlng);
    }
  }, [isWaitingForMapClick, userFloor, building]);

  // New: Handle node click for navigation
  const handleNodeClick = useCallback(async (node) => {
    if (!userPosition) {
      alert('Please set your current position first');
      return;
    }
    
    console.log('Navigate to node:', node);
    
    // Determine start node from user position
    const startNode = findNearestNodeToGPS(userPosition, navigationData, userFloor);
    
    if (!startNode) {
      alert('Cannot determine starting position');
      return;
    }
    
    // Calculate path to clicked node
    const start = {
      building: building,
      floor: userFloor,
      node: startNode
    };
    
    const end = {
      building: node.building || building,
      floor: node.floor || currentFloor,
      node: node.id
    };
    
    await handleNavigationRequest(start, end);
  }, [userPosition, navigationData, userFloor, building, currentFloor]);

  // New: Handle location mode change
  const handleLocationModeChange = useCallback((mode) => {
    setLocationMode(mode);
  }, []);

  // Building configuration
  const buildingConfig = {
    M: {
      name: 'Main Building',
      description: 'London Campus - Information Technology and Media',
      bounds: [[43.0125, -81.2005], [43.0135, -81.1995]],
      center: [43.013, -81.2],
    },
    H: {
      name: 'H Building',
      description: 'London Campus',
      bounds: [[43.0128, -81.2003], [43.0138, -81.1993]],
      center: [43.0133, -81.1998],
    },
  };

  const config = buildingConfig[building] || buildingConfig.M;
  const currentDirection = directions[currentStepIndex];

  return (
    <div className={`map-navigator ${className}`}>
      {/* Startup Modal */}
      {showStartupModal && (
        <StartupModal
          building={building}
          availableFloors={availableFloors.map(f => f.level) || ['1', '2', '3']}
          onComplete={handleStartupComplete}
          onClose={() => setShowStartupModal(false)}
        />
      )}

      {/* Building Info Header */}
      <BuildingInfo
        building={building}
        floor={currentFloor}
        buildingName={config.name}
        description={config.description}
      />

      {/* Location Toggle */}
      <div style={{ position: 'absolute', top: '80px', right: '10px', zIndex: 1000 }}>
        <LocationToggle
          locationMode={locationMode}
          onModeChange={handleLocationModeChange}
          onPositionUpdate={handleGPSPositionUpdate}
          accuracyThreshold={20}
        />
      </div>

      {/* Floor Selector */}
      <FloorSelector
        building={building}
        currentFloor={currentFloor}
        availableFloors={availableFloors}
        onFloorChange={handleFloorChange}
      />

      {/* Map Display */}
      <div className="map-container" style={{ position: 'relative', height: '500px' }}>
        {loading && (
          <div className="map-loading">
            <p>Loading map data...</p>
          </div>
        )}

        {error && (
          <div className="map-error" style={{ color: 'red', padding: '10px' }}>
            <p>Error: {error}</p>
          </div>
        )}

        {floorPlanUrl && navigationData && (
          <IndoorMapView
            building={building}
            floor={currentFloor}
            floorPlanUrl={floorPlanUrl}
            bounds={config.bounds}
            center={config.center}
            nodes={navigationData.navigationGraph || {}}
            path={pathCoordinates}
            userPosition={userPosition}
            highlightedNodes={currentPath ? currentPath.nodes : []}
            onNodeClick={handleNodeClick}
            onMapClick={handleMapClick}
          />
        )}
      </div>

      {/* Navigation Controls */}
      {isNavigating && (
        <NavigationControls
          isNavigating={isNavigating}
          onStop={handleStopNavigation}
          onRecenter={handleRecenter}
        />
      )}

      {/* Turn-by-turn Directions */}
      {isNavigating && directions.length > 0 && (
        <div className="directions-panel" style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '8px' }}>
          <h3>Directions</h3>
          
          {/* Current Instruction */}
          <div className="current-instruction" style={{ 
            fontSize: '1.2em', 
            fontWeight: 'bold', 
            padding: '10px', 
            backgroundColor: '#f0f0f0', 
            borderRadius: '5px',
            marginBottom: '15px'
          }}>
            <span className="step-number">Step {currentStepIndex + 1} of {directions.length}:</span>
            <p>{currentDirection?.instruction || 'No instruction'}</p>
          </div>

          {/* Navigation Buttons */}
          <div className="direction-controls" style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <button
              onClick={handlePreviousStep}
              disabled={currentStepIndex === 0}
              style={{ padding: '8px 16px', cursor: currentStepIndex === 0 ? 'not-allowed' : 'pointer' }}
            >
              ← Previous
            </button>
            <button
              onClick={handleNextStep}
              disabled={currentStepIndex === directions.length - 1}
              style={{ padding: '8px 16px', cursor: currentStepIndex === directions.length - 1 ? 'not-allowed' : 'pointer' }}
            >
              Next →
            </button>
          </div>

          {/* All Steps List */}
          <div className="all-steps" style={{ maxHeight: '200px', overflowY: 'auto' }}>
            <h4>All Steps:</h4>
            <ol>
              {directions.map((step, idx) => (
                <li
                  key={idx}
                  className={idx === currentStepIndex ? 'current-step' : ''}
                  style={{
                    padding: '5px',
                    backgroundColor: idx === currentStepIndex ? '#e3f2fd' : 'transparent',
                    cursor: 'pointer',
                  }}
                  onClick={() => setCurrentStepIndex(idx)}
                >
                  {step.instruction}
                  {step.building && ` (Building ${step.building}, Floor ${step.floor})`}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}

      {/* Path Summary */}
      {currentPath && (
        <div className="path-summary" style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '5px' }}>
          <h4>Route Summary</h4>
          <p>
            <strong>Type:</strong> {currentPath.type === 'single' ? 'Single Floor' : 
                                    currentPath.type === 'multi-floor' ? 'Multi-Floor' : 'Multi-Building'}
          </p>
          {currentPath.type === 'single' && (
            <p>Building {currentPath.building}, Floor {currentPath.floor}</p>
          )}
          {currentPath.type === 'multi-floor' && (
            <p>Building {currentPath.building}, Floors: {currentPath.segments.map(s => s.floor).join(', ')}</p>
          )}
          {currentPath.type === 'multi-building' && (
            <p>Buildings: {currentPath.segments.map(s => s.building).join(' → ')}</p>
          )}
        </div>
      )}
    </div>
  );
}
