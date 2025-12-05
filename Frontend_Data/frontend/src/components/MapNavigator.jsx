import React, { useState, useEffect, useCallback } from 'react';
import IndoorMapView from './IndoorMapView';
import FloorSelector, { BuildingInfo, NavigationControls } from './FloorSelector';
import StartupModal from './StartupModal';
import LocationToggle from './LocationToggle';
import SelectionModeGuide from './SelectionModeGuide';
import {
  getNavigationData,
  calculatePath,
  getFloorPlanUrl,
  formatPathForDisplay,
  getAllRooms,
  getAvailableFloors,
  getAllNodeData,
  getBuildingPositions,
  calculateRotatedBounds,
} from '../utils/navigationApi';
import {
  storeUserPosition,
  retrieveUserPosition,
  findNearestNodeToGPS,
} from '../utils/navigationUtils';
import { parseSVGNodes, mergeNavigationData } from '../utils/svgParser';

// Building configuration with actual GeoJSON coordinates
const BUILDING_CONFIG = {
  M: {
    name: 'Main Building',
    description: 'London Campus - Information Technology and Media',
    bounds: [[43.0139203, -81.1989228], [43.0147647, -81.1982043]],
    center: [43.0143425, -81.19856355],
  },
  H: {
    name: 'H Building',
    description: 'London Campus',
    bounds: [[43.0139261, -81.1993256], [43.0143793, -81.1988453]],
    center: [43.0141527, -81.19908545],
  },
};

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
  
  // New: GPS accuracy tracking
  const [gpsAccuracy, setGpsAccuracy] = useState(null);
  const [showGPSCircle, setShowGPSCircle] = useState(false);
  
  // New: Selection mode for interactive position setting (single-click)
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectionStep, setSelectionStep] = useState('start'); // 'start' or 'end'
  const [startPoint, setStartPoint] = useState(null);
  const [endPoint, setEndPoint] = useState(null);
  const [instructionText, setInstructionText] = useState('');
  const [showTutorial, setShowTutorial] = useState(false);
  
  // New: Rotated bounds for SVG overlay (matching coordinate_system.html approach)
  const [rotatedCorners, setRotatedCorners] = useState(null);
  const [buildingPositions, setBuildingPositions] = useState(null);

  // Load initial data
  useEffect(() => {
    loadFloorData();
  }, [building, currentFloor]);
  
  // Load building positions and calculate rotated corners
  useEffect(() => {
    const loadBuildingPositions = async () => {
      try {
        const positions = await getBuildingPositions();
        setBuildingPositions(positions);
        console.log('✅ Building positions loaded:', positions);
      } catch (error) {
        console.error('❌ Error loading building positions:', error);
      }
    };
    
    loadBuildingPositions();
  }, []);
  
  // Calculate rotated corners when building, floor, or positions change
  useEffect(() => {
    if (!buildingPositions) return;
    
    const buildingKey = `Building ${building}`;
    const floorPositions = buildingPositions[buildingKey]?.[currentFloor];
    
    if (!floorPositions) {
      console.warn(`No position adjustments for ${buildingKey} floor ${currentFloor}`);
      return;
    }
    
    const config = BUILDING_CONFIG[building];
    if (!config) return;
    
    // Calculate rotated corners using rotation from Building positions.JSON
    const rotation = floorPositions.positionAdjustments.rotation;
    const corners = calculateRotatedBounds(config.bounds, rotation);
    
    setRotatedCorners(corners);
    console.log(`🔄 Calculated rotated corners for Building ${building} floor ${currentFloor}:`, corners);
    console.log(`   Rotation: ${rotation}°`);
  }, [building, currentFloor, buildingPositions]);

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
    } else if (mapAction && mapAction.type === 'INTERACTIVE_MODE') {
      // Enable selection mode for one-click start and one-click end
      setSelectionMode(true);
      setSelectionStep('start');
      setStartPoint(null);
      setEndPoint(null);
      setInstructionText('Tap to set START point (1/2)');
      setCurrentPath(null);
      setIsNavigating(false);
      
      // Show tutorial on first use
      const hasSeenTutorial = localStorage.getItem('indoor_nav_tutorial_seen');
      if (!hasSeenTutorial) {
        setShowTutorial(true);
      }
    }
  }, [mapAction]);

  const loadFloorData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load complete all_node_data.json
      const allNodeData = await getAllNodeData();
      if (!allNodeData) {
        throw new Error('Failed to load navigation data');
      }

      // Get building and floor data
      const buildingKey = `Building ${building}`;
      const buildingData = allNodeData[buildingKey];
      
      if (!buildingData || !buildingData.floors || !buildingData.floors[currentFloor]) {
        throw new Error(`No data for Building ${building}, Floor ${currentFloor}`);
      }

      const floorData = buildingData.floors[currentFloor];
      const planUrl = getFloorPlanUrl(building, currentFloor);
      setFloorPlanUrl(planUrl);

      // Parse SVG to get node positions
      console.log('🔍 Parsing SVG for node positions...');
      const config = BUILDING_CONFIG[building] || BUILDING_CONFIG.M;
      const svgParsedData = await parseSVGNodes(
        planUrl,
        floorData.navigationGraph,
        config.bounds
      );

      // Merge navigation graph with positions
      const enhancedNavData = mergeNavigationData(
        floorData.navigationGraph,
        svgParsedData
      );

      // Set enhanced navigation data
      setNavigationData({
        ...floorData,
        ...enhancedNavData,
        nodePositions: svgParsedData.nodePositions
      });

      console.log('✅ Navigation data loaded with positions:', enhancedNavData);

      // Load available floors from building data
      const floors = Object.keys(buildingData.floors).map(f => ({ level: f }));
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
  const handleGPSPositionUpdate = useCallback((position, accuracy = null) => {
    setUserPosition(position);
    storeUserPosition(position, userFloor, building);
    
    // Update GPS accuracy and show circle if GPS mode
    if (accuracy !== null) {
      setGpsAccuracy(accuracy);
      setShowGPSCircle(locationMode === 'gps');
    }
    
    // Find nearest node for more accurate navigation
    if (navigationData) {
      const nearestNode = findNearestNodeToGPS(position, navigationData, userFloor);
      if (nearestNode) {
        console.log('User is near node:', nearestNode);
      }
    }
  }, [building, userFloor, navigationData, locationMode]);

  // New: Handle map click for manual position setting (single click for start, then single click for end)
  const handleMapClick = useCallback(async (latlng) => {
    console.log('🖱️ Map clicked:', latlng, '| Selection mode:', selectionMode, '| Step:', selectionStep, '| Floor:', currentFloor);
    
    // Handle manual position setting (startup modal workflow)
    if (isWaitingForMapClick) {
      setUserPosition(latlng);
      setIsWaitingForMapClick(false);
      storeUserPosition(latlng, userFloor, building);
      console.log('User position set manually:', latlng);
      return;
    }
    
    // Handle selection mode (one-click start, one-click end)
    if (selectionMode && navigationData) {
      console.log('🔍 Finding nearest node to:', latlng);
      const nearestNode = findNearestNodeToGPS(latlng, navigationData, currentFloor);
      
      if (!nearestNode) {
        console.warn('No node found near clicked position');
        setInstructionText('No navigation point found. Try clicking closer to a hallway.');
        return;
      }
      
      if (selectionStep === 'start') {
        // First click - set start point
        setStartPoint({ node: nearestNode, position: latlng, floor: currentFloor });
        setSelectionStep('end');
        setInstructionText('Tap to set END point (2/2)');
        console.log('Start point set:', nearestNode);
      } else if (selectionStep === 'end') {
        // Second click - set end point and calculate route
        setEndPoint({ node: nearestNode, position: latlng, floor: currentFloor });
        setInstructionText('Calculating route...');
        console.log('End point set:', nearestNode);
        
        // Calculate path
        await calculateRouteFromSelection(
          { node: startPoint.node, position: startPoint.position, floor: startPoint.floor },
          { node: nearestNode, position: latlng, floor: currentFloor }
        );
      }
    }
  }, [isWaitingForMapClick, userFloor, building, selectionMode, navigationData, currentFloor, selectionStep, startPoint]);

  // Calculate route from selection mode
  const calculateRouteFromSelection = useCallback(async (start, end) => {
    if (!start || !end) {
      console.error('Missing start or end point');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await calculatePath(
        {
          building: building,
          floor: start.floor,
          node: start.node
        },
        {
          building: building,
          floor: end.floor,
          node: end.node
        }
      );
      
      if (!result) {
        setError('Could not calculate path');
        setInstructionText('Failed to find route. Try different locations.');
        return;
      }
      
      displayPath(result.path, result.directions);
      setInstructionText('Route found! Follow the path.');
      
      // Keep markers visible but exit selection mode
      setSelectionMode(false);
      
    } catch (err) {
      console.error('Error calculating route from selection:', err);
      setError('Failed to calculate route');
      setInstructionText('Error calculating route. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [building]);

  // New: Reset selection mode
  const handleResetSelection = useCallback(() => {
    setSelectionMode(false);
    setSelectionStep('start');
    setStartPoint(null);
    setEndPoint(null);
    setInstructionText('');
    setCurrentPath(null);
    setIsNavigating(false);
    setPathCoordinates([]);
    setDirections([]);
  }, []);
  
  // Restart selection from beginning
  const handleRestartSelection = useCallback(() => {
    setSelectionStep('start');
    setStartPoint(null);
    setEndPoint(null);
    setInstructionText('Tap to set START point (1/2)');
    setCurrentPath(null);
    setPathCoordinates([]);
  }, []);

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
    setShowGPSCircle(mode === 'gps'); // Show GPS circle only in GPS mode
  }, []);

  const config = BUILDING_CONFIG[building] || BUILDING_CONFIG.M;
  const currentDirection = directions[currentStepIndex];

  return (
    <div className={`map-navigator ${className}`} style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
      {/* Tutorial Guide Modal */}
      {showTutorial && (
        <SelectionModeGuide
          onClose={() => {
            setShowTutorial(false);
            localStorage.setItem('indoor_nav_tutorial_seen', 'true');
          }}
          onSkip={() => {
            setShowTutorial(false);
            localStorage.setItem('indoor_nav_tutorial_seen', 'true');
          }}
        />
      )}
      
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
      <div style={{ position: 'relative', zIndex: 100, flexShrink: 0 }}>
        <BuildingInfo
          building={building}
          floor={currentFloor}
          buildingName={config.name}
          description={config.description}
        />
      </div>

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
      <div style={{ position: 'absolute', top: '140px', left: '10px', zIndex: 1000 }}>
        <FloorSelector
          building={building}
          currentFloor={currentFloor}
          availableFloors={availableFloors}
          onFloorChange={handleFloorChange}
        />
      </div>

      {/* Map Display */}
      <div className="map-container" style={{ position: 'relative', flex: 1, minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
        {loading && (
          <div className="map-loading" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 1001 }}>
            <p>Loading map data...</p>
          </div>
        )}

        {error && (
          <div className="map-error" style={{ color: 'red', padding: '10px' }}>
            <p>Error: {error}</p>
          </div>
        )}
        
        {/* Selection Mode Instruction Overlay */}
        {selectionMode && instructionText && (
          <div style={{
            position: 'absolute',
            top: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            backgroundColor: '#3498db',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '25px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            fontSize: '16px',
            fontWeight: '500',
            maxWidth: '90%',
            textAlign: 'center',
            animation: 'slideDown 0.3s ease-out'
          }}>
            {instructionText}
          </div>
        )}
        
        {/* Selection Mode Control Buttons */}
        {selectionMode && (
          <div style={{
            position: 'absolute',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: '90%'
          }}>
            <button
              onClick={() => setShowTutorial(true)}
              style={{
                backgroundColor: '#9b59b6',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '25px',
                border: 'none',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                minWidth: '120px',
                touchAction: 'manipulation'
              }}
            >
              ❓ Help
            </button>
            {startPoint && (
              <button
                onClick={handleRestartSelection}
                style={{
                  backgroundColor: '#f39c12',
                  color: 'white',
                  padding: '12px 24px',
                  borderRadius: '25px',
                  border: 'none',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                  minWidth: '120px',
                  touchAction: 'manipulation'
                }}
              >
                🔄 Restart
              </button>
            )}
            <button
              onClick={handleResetSelection}
              style={{
                backgroundColor: '#e74c3c',
                color: 'white',
                padding: '12px 24px',
                borderRadius: '25px',
                border: 'none',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                minWidth: '120px',
                touchAction: 'manipulation'
              }}
            >
              ✕ Cancel
            </button>
          </div>
        )}

        {floorPlanUrl && navigationData && (
          <div style={{ flex: 1, position: 'relative', width: '100%', height: '100%' }}>
            <IndoorMapView
              building={building}
              floor={currentFloor}
              floorPlanUrl={floorPlanUrl}
              bounds={config.bounds}
              rotatedCorners={rotatedCorners}
              center={config.center}
              nodes={navigationData.navigationGraph || {}}
              path={pathCoordinates}
              userPosition={userPosition}
              highlightedNodes={currentPath ? currentPath.nodes : []}
              onNodeClick={handleNodeClick}
              onMapClick={handleMapClick}
              gpsAccuracy={gpsAccuracy}
              showGPSCircle={showGPSCircle}
              enableNodeInteraction={!isWaitingForMapClick}
              startPoint={startPoint}
              endPoint={endPoint}
            />
          </div>
        )}
        
        {/* CSS Animations */}
        <style>{`
          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateX(-50%) translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateX(-50%) translateY(0);
            }
          }
          
          /* Mobile touch target optimization */
          @media (max-width: 768px) {
            button {
              min-height: 44px;
              min-width: 44px;
            }
          }
        `}</style>
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
