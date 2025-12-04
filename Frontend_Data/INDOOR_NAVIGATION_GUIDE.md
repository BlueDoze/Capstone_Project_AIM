# Indoor Navigation Components - LeafletJS Integration

This document explains how to use the indoor navigation components that integrate the LeafletJS folder assets into the React application.

## Overview

The LeafletJS folder contains:
- **Floor Plans**: SVG/PDF/JPEG files for all campus buildings
- **Navigation Data**: JSON files with node-based pathfinding information
- **Campus GeoJSON**: Geographic data for outdoor mapping
- **Leaflet Plugins**: Custom plugins for map rotation and image manipulation

These assets are now integrated into the React app through new components.

## Components

### 1. IndoorMapView
Main component for displaying indoor floor plans with navigation overlays.

**Props:**
```jsx
<IndoorMapView
  building="M"                    // Building code
  floor="1"                       // Floor level
  floorPlanUrl="/path/to/plan.svg" // Floor plan image URL
  bounds={[[43.012, -81.200], [43.013, -81.199]]} // Map bounds
  nodes={[...]}                   // Navigation nodes
  path={[[lat1, lng1], ...]}     // Navigation path coordinates
  userPosition={[lat, lng]}       // User's current position
  onNodeClick={(node) => {}}     // Node click handler
  center={[43.013, -81.2]}       // Map center
  zoom={18}                       // Initial zoom level
  rotation={0}                    // Map rotation (requires leaflet-rotate)
  highlightedNodes={['node1']}   // Nodes to highlight
/>
```

### 2. FloorSelector
UI component for selecting different floors within a building.

**Props:**
```jsx
<FloorSelector
  building="M"
  currentFloor="1"
  availableFloors={[
    { level: '1', name: 'Ground Floor' },
    { level: '2', name: 'Second Floor' }
  ]}
  onFloorChange={(floor) => setCurrentFloor(floor)}
/>
```

### 3. BuildingInfo
Displays building information and metadata.

**Props:**
```jsx
<BuildingInfo
  building="M"
  info={{
    name: 'Main Building',
    description: 'Information Technology and Media'
  }}
/>
```

### 4. NavigationControls
Controls for starting/stopping navigation and displaying directions.

**Props:**
```jsx
<NavigationControls
  isNavigating={true}
  currentInstruction="Take the stairs to Floor 2"
  onStartNavigation={() => {}}
  onStopNavigation={() => {}}
  onRecenter={() => {}}
/>
```

### 5. IndoorNavigationContainer
Complete indoor navigation system (recommended for most use cases).

**Props:**
```jsx
<IndoorNavigationContainer
  building="M"
  initialFloor="1"
  startRoom={[43.0130, -81.2000]}  // Starting coordinates
  endRoom={[43.0132, -81.1998]}    // Destination coordinates
/>
```

## Utility Functions

All navigation utilities are in `src/utils/navigationUtils.js`:

### Pathfinding
```javascript
import { findPath, nodePathToCoordinates } from '../utils/navigationUtils';

// Find path between two nodes
const graph = { nodes: navigationNodes };
const nodePath = findPath(graph, 'startNodeId', 'endNodeId');
const coordinates = nodePathToCoordinates(nodePath, navigationNodes);
```

### Loading Assets
```javascript
import { loadFloorPlanData, loadNavigationNodes } from '../utils/navigationUtils';

// Load floor plan SVG
const floorPlanUrl = await loadFloorPlanData('M', '1'); // Building M, Floor 1

// Load navigation nodes for a building
const nodes = await loadNavigationNodes('M');
```

### Directions
```javascript
import { generateDirections } from '../utils/navigationUtils';

const directions = generateDirections(nodePath, navigationNodes);
// Returns: [{ nodeId, instruction, position, distance }, ...]
```

## Usage Examples

### Basic Indoor Map
```jsx
import IndoorMapView from './components/IndoorMapView';

function MyMap() {
  return (
    <IndoorMapView
      building="M"
      floor="1"
      floorPlanUrl="/leaflet-assets/Floorplans/Building M/M1.svg"
      bounds={[[43.0125, -81.2005], [43.0135, -81.1995]]}
      center={[43.013, -81.2]}
    />
  );
}
```

### Complete Navigation System
```jsx
import IndoorNavigationContainer from './components/IndoorNavigationContainer';

function RoomNavigation() {
  return (
    <IndoorNavigationContainer
      building="M"
      initialFloor="1"
      startRoom={[43.0130, -81.2000]}
      endRoom={[43.0132, -81.1998]}
    />
  );
}
```

### Custom Implementation
```jsx
import { useState, useEffect } from 'react';
import IndoorMapView from './components/IndoorMapView';
import FloorSelector from './components/FloorSelector';
import { loadFloorPlanData, loadNavigationNodes, findPath } from './utils/navigationUtils';

function CustomNavigation() {
  const [floor, setFloor] = useState('1');
  const [floorPlan, setFloorPlan] = useState(null);
  const [nodes, setNodes] = useState({});
  const [path, setPath] = useState([]);

  useEffect(() => {
    // Load floor plan
    loadFloorPlanData('M', floor).then(setFloorPlan);
    
    // Load navigation nodes
    loadNavigationNodes('M').then(setNodes);
  }, [floor]);

  const navigateToRoom = (roomId) => {
    const graph = { nodes };
    const nodePath = findPath(graph, 'current', roomId);
    // ... convert to coordinates and set path
  };

  return (
    <div>
      <FloorSelector
        building="M"
        currentFloor={floor}
        availableFloors={[
          { level: '1', name: 'Ground' },
          { level: '2', name: 'Second' }
        ]}
        onFloorChange={setFloor}
      />
      <IndoorMapView
        building="M"
        floor={floor}
        floorPlanUrl={floorPlan}
        bounds={[[43.0125, -81.2005], [43.0135, -81.1995]]}
        nodes={Object.values(nodes)}
        path={path}
      />
    </div>
  );
}
```

## Accessing LeafletJS Assets

Assets are served through two methods:

### 1. Via Flask Route (Development)
```javascript
// Access floor plans
const url = '/leaflet-assets/Floorplans/Building M/M1.svg';

// Access navigation data
const response = await fetch('/leaflet-assets/JSON/all_node_data.json');
const nodes = await response.json();

// Access campus GeoJSON
const geoJson = await fetch('/leaflet-assets/campus.geojson');
```

### 2. Via React Public Directory (Production)
After Docker build, assets are copied to `/leaflet-assets/` in the public directory:
```javascript
const url = '/leaflet-assets/Floorplans/Building M/M1.svg';
```

## Available Floor Plans

All buildings with floor plans:
- **Building A**: Floors 1, 2, 3
- **Building B**: Floors 1, 2
- **Building C**: Floors 1, 2
- **Building D**: Floors 1, 2
- **Building E**: Floors 1, 2
- **Building F**: Floor plans available
- **Building G**: Floor 1
- **Building H**: Floor 1
- **Building J**: Floor 1
- **Building K**: Floor 1
- **Building M**: Floors 1, 2
- **Building T**: Floor 1

All floor plans are available in SVG, PDF, and JPEG formats.

## Navigation Data Structure

The `all_node_data.json` file contains nodes in this format:
```json
{
  "nodeId": {
    "id": "nodeId",
    "position": [lat, lng],
    "floor": "1",
    "building": "M",
    "type": "hallway|stairs|elevator|door|room",
    "name": "Room M1234",
    "connections": ["nodeId2", "nodeId3"],
    "direction": "up|down"
  }
}
```

## Coordinate Systems

The LeafletJS folder uses SVG coordinates that need to be converted to Leaflet lat/lng:

```javascript
import { svgToLatLng } from '../utils/navigationUtils';

const latLng = svgToLatLng([svgX, svgY], bounds);
```

## Styling Navigation Elements

All components use inline styles for maximum portability, but you can override with custom CSS:

```css
/* Custom node styling */
.navigation-node {
  /* Override default node appearance */
}

/* Custom path styling */
.leaflet-interactive.leaflet-polyline {
  /* Override path appearance */
}

/* User position marker */
.user-position-marker {
  /* Override user marker */
}
```

## Integration with Existing MapView

To add indoor navigation to your existing outdoor map:

```jsx
import { useState } from 'react';
import MapView from './components/MapView'; // Your existing outdoor map
import IndoorNavigationContainer from './components/IndoorNavigationContainer';

function HybridMap() {
  const [mode, setMode] = useState('outdoor'); // 'outdoor' or 'indoor'
  const [selectedBuilding, setSelectedBuilding] = useState(null);

  return (
    <div>
      {mode === 'outdoor' ? (
        <MapView
          onBuildingClick={(building) => {
            setSelectedBuilding(building);
            setMode('indoor');
          }}
        />
      ) : (
        <IndoorNavigationContainer
          building={selectedBuilding}
          onBack={() => setMode('outdoor')}
        />
      )}
    </div>
  );
}
```

## Performance Considerations

1. **Lazy Loading**: Load floor plans only when needed
2. **Asset Optimization**: SVG files are preferred over large JPEGs
3. **Node Filtering**: Filter nodes by floor to reduce rendering load
4. **Pathfinding Cache**: Cache calculated paths for common routes

## Next Steps

1. Integrate with your room search/selection UI
2. Add real-time user positioning (using device sensors or indoor positioning)
3. Implement multi-floor routing (e.g., stairs/elevators between floors)
4. Add accessibility features (wheelchair-accessible routes)
5. Integrate with your chatbot for natural language navigation

## Troubleshooting

**Floor plans not loading:**
- Check that Docker copied assets correctly: `docker exec <container> ls /app/Frontend_Data/frontend/public/leaflet-assets/Floorplans`
- Verify Flask route is working: `curl http://localhost:8081/leaflet-assets/campus.geojson`

**Navigation nodes not found:**
- Ensure `all_node_data.json` is accessible
- Check building codes match (case-sensitive)
- Verify floor numbers are strings ('1', not 1)

**Path not rendering:**
- Check that coordinates are in [lat, lng] format
- Verify bounds are correctly set for the building
- Ensure nodes have valid position arrays

## Resources

- Leaflet Documentation: https://leafletjs.com/
- React Leaflet: https://react-leaflet.js.org/
- Leaflet Rotate Plugin: https://github.com/fnicollet/Leaflet.Rotate
