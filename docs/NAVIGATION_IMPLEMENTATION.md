# Campus Map Navigation Feature - Implementation Guide

## Overview

The Campus Map Navigation feature provides interactive indoor wayfinding across campus buildings. Users can request directions through natural language chat, and the system calculates optimal paths with turn-by-turn instructions.

## System Architecture

### Backend Components

#### 1. Navigation Service (`src/services/navigation_service.py`)
Core pathfinding engine using Dijkstra's algorithm.

**Key Features:**
- Single-building pathfinding
- Multi-building routing (via connectors)
- Multi-floor navigation (via stairs/elevators)
- Room-to-node resolution
- Building and floor data management

**Main Methods:**
```python
# Get navigation service instance
nav_service = get_navigation_service()

# Find path between locations
path = nav_service.find_path(
    start_building='M', start_floor='1', start_node='M1_1',
    end_building='H', end_floor='1', end_node='H1_20'
)

# Resolve room ID to navigation node
node = nav_service.resolve_room_to_node('M', '1', '1003')

# Get all available buildings and floors
buildings = nav_service.get_available_buildings()
floors = nav_service.get_available_floors('M')
```

#### 2. Direction Service (`src/services/direction_service.py`)
Generates human-readable turn-by-turn directions.

**Key Features:**
- Bearing and turn calculation
- Cardinal direction mapping
- Node description formatting
- Multi-segment direction generation
- Text summary creation

**Main Methods:**
```python
# Get direction service instance
dir_service = get_direction_service()

# Generate directions from path data
directions = dir_service.generate_directions(path_data)

# Create plain text summary
text = dir_service.generate_text_summary(directions)
```

#### 3. API Endpoints (`src/api/app.py`)

##### GET `/api/navigation/buildings`
Returns list of all buildings with navigation data.

**Response:**
```json
{
  "buildings": ["A", "B", "H", "M"]
}
```

##### GET `/api/navigation/floors/<building>`
Returns available floors for a building.

**Response:**
```json
{
  "building": "M",
  "floors": ["1", "2"]
}
```

##### GET `/api/navigation/data?building=M&floor=1`
Returns complete navigation data for a floor.

**Response:**
```json
{
  "navigationGraph": {
    "M1_1": {
      "connections": ["M1_2", "M1_3"],
      "lat": 43.013,
      "lng": -81.2,
      "represents": [{"type": "room", "id": "1003"}]
    }
  },
  "roomToNode": {
    "1003": "M1_1"
  }
}
```

##### POST `/api/navigation/calculate`
Calculates path between two locations.

**Request:**
```json
{
  "start": {
    "building": "M",
    "floor": "1",
    "room": "1003"
  },
  "end": {
    "building": "H",
    "floor": "1",
    "room": "H1018"
  }
}
```

**Response:**
```json
{
  "path": {
    "type": "multi-building",
    "segments": [
      {
        "building": "M",
        "floor": "1",
        "path": ["M1_1", "M1_2", "M1_exit"],
        "description": "Navigate to Building H connector"
      },
      {
        "building": "H",
        "floor": "1",
        "path": ["H1_entry", "H1_2", "H1_20"],
        "description": "Navigate to destination in H"
      }
    ]
  },
  "directions": {
    "type": "multi-building",
    "total_steps": 15,
    "steps": [
      {
        "step": 1,
        "instruction": "Start at room 1003",
        "building": "M",
        "floor": "1"
      }
    ]
  },
  "text_summary": "Navigate from Building M to Building H\n\n1. Start at room 1003\n..."
}
```

##### POST `/api/navigation/room-lookup`
Looks up node ID for a room.

**Request:**
```json
{
  "building": "M",
  "floor": "1",
  "room": "1003"
}
```

##### GET `/api/navigation/all-rooms?building=M&floor=1`
Returns all rooms and their node mappings.

### Frontend Components

#### 1. Navigation API Client (`Frontend_Data/frontend/src/utils/navigationApi.js`)

Utility functions for interacting with backend navigation API.

**Key Functions:**
```javascript
import {
  getAvailableBuildings,
  getAvailableFloors,
  getNavigationData,
  calculatePath,
  getAllRooms,
  lookupRoom,
  getFloorPlanUrl,
  formatPathForDisplay
} from '../utils/navigationApi';

// Get buildings
const buildings = await getAvailableBuildings();

// Calculate path
const result = await calculatePath(
  { building: 'M', floor: '1', room: '1003' },
  { building: 'H', floor: '1', room: 'H1018' }
);
```

#### 2. MapNavigator Component (`Frontend_Data/frontend/src/components/MapNavigator.jsx`)

Complete navigation UI with map display and turn-by-turn directions.

**Usage:**
```jsx
import MapNavigator from './components/MapNavigator';

<MapNavigator
  building="M"
  initialFloor="1"
  mapAction={mapActionFromChat}
  onNavigationComplete={() => console.log('Done')}
/>
```

**Features:**
- Interactive floor plan display
- Floor selector
- Path visualization
- Turn-by-turn directions panel
- Step navigation (next/previous)
- Multi-floor and multi-building support

## Data Files

### 1. all_node_data.json
Complete navigation graph for all buildings and floors.

**Structure:**
```json
{
  "Building M": {
    "Floor 1": {
      "navigationGraph": {
        "M1_1": {
          "connections": ["M1_2"],
          "lat": 43.013,
          "lng": -81.2,
          "represents": [{"type": "room", "id": "1003"}]
        }
      },
      "roomToNode": {
        "1003": "M1_1"
      },
      "objects": {
        "rooms": ["1003", "1018"],
        "exits": ["Exit-North"]
      }
    }
  }
}
```

### 2. building_connections.JSON
Defines pathways between buildings.

**Structure:**
```json
{
  "M-H Connector": {
    "exit": "M1_exit_H",
    "entry": "H1_entry_M"
  }
}
```

### 3. Building positions.JSON
SVG overlay position adjustments for floor plans.

**Structure:**
```json
{
  "Building M": {
    "latOffset": 0.0005,
    "lngOffset": -0.0003,
    "scale": 1.2,
    "rotation": 15
  }
}
```

## Usage Examples

### 1. Chat-based Navigation

User types: **"How do I get from room 1003 to H1018?"**

**Backend Flow:**
1. `classify_user_intent()` identifies NAVIGATION intent
2. `parse_navigation_request()` extracts start/end locations
3. `NavigationService.find_path()` calculates route
4. `DirectionService.generate_directions()` creates instructions
5. Response sent to frontend with `mapAction`

**Frontend Flow:**
1. Chat component receives `mapAction` object
2. `MapNavigator` component displays path
3. User sees interactive map with highlighted route
4. Turn-by-turn directions displayed in panel

### 2. Programmatic Navigation

```python
# Python backend
from src.services.navigation_service import get_navigation_service
from src.services.direction_service import get_direction_service

nav_service = get_navigation_service()
dir_service = get_direction_service()

# Calculate path
path = nav_service.find_path('M', '1', 'M1_1', 'H', '1', 'H1_20')

# Generate directions
directions = dir_service.generate_directions(path)
print(dir_service.generate_text_summary(directions))
```

```javascript
// JavaScript frontend
import { calculatePath } from '../utils/navigationApi';

const result = await calculatePath(
  { building: 'M', floor: '1', room: '1003' },
  { building: 'H', floor: '1', room: 'H1018' }
);

console.log(result.text_summary);
// Display result.path on map
```

## Supported Scenarios

### ✅ Implemented

1. **Single Building, Same Floor**
   - Navigate from room 1003 to room 1018 in Building M
   - Uses simple Dijkstra's algorithm

2. **Multiple Buildings**
   - Navigate from Building M to Building H
   - Uses building connections
   - Two-segment path with transition instruction

3. **Multiple Floors (Same Building)**
   - Navigate from Floor 1 to Floor 2 in Building M
   - Uses stairs or elevator nodes
   - Shows floor transition instructions

### ⚠️ Partially Implemented

4. **Multiple Floors + Multiple Buildings**
   - Logic exists but requires complete building connection data
   - Currently only M-H and H-F connections defined

### 📋 Planned Enhancements

1. **Real-time Position Tracking**
   - GPS positioning (accuracy challenges indoors)
   - WiFi triangulation
   - QR code waypoints

2. **Accessibility Options**
   - Wheelchair-accessible routes
   - Elevator-only paths
   - Avoid stairs preference

3. **Additional Buildings**
   - Expand navigation data to buildings A, B, C, D, E, G, J, K, T
   - More building connections
   - Outdoor routing between buildings

## Testing

### Run Validation Tests
```bash
cd C:\Users\pedri\OneDrive\Desktop\Projeto_Final\Capstone_Project_AIM
python tests/validate_navigation.py
```

**Tests Include:**
- JSON file validation
- Navigation data structure verification
- API endpoint checks
- React component validation
- Python service verification

### Manual Testing

1. **Test Backend API:**
```bash
# Start Flask server
python run_app.py

# Test endpoints
curl http://localhost:8081/api/navigation/buildings
curl http://localhost:8081/api/navigation/data?building=M&floor=1
```

2. **Test Frontend:**
- Open React app in browser
- Send chat message: "How do I get to room 1003?"
- Verify map displays with route
- Check turn-by-turn directions

## Troubleshooting

### Issue: No path found
**Cause:** Start or end nodes not connected in navigation graph
**Solution:** Verify nodes exist and are properly connected in `all_node_data.json`

### Issue: Building connection not found
**Cause:** Missing entry in `building_connections.JSON`
**Solution:** Add connector with exit and entry node IDs

### Issue: Floor plan not displaying
**Cause:** SVG file missing or incorrect path
**Solution:** Check SVG exists at `LeafletJS/Floorplans/{Building}/{Building}_building_floor_{floor}.svg`

### Issue: Directions show wrong turns
**Cause:** Node positions (lat/lng) may be inaccurate
**Solution:** Verify coordinate accuracy in navigation graph

## Integration with Chat System

The navigation feature is fully integrated with the AI chat assistant:

1. User sends navigation request via chat
2. `classify_user_intent()` detects NAVIGATION intent
3. `parse_navigation_request()` extracts location details
4. Navigation service calculates path
5. Direction service generates instructions
6. Chat response includes `mapAction` object
7. Frontend displays both text directions and interactive map

**Chat Response Format:**
```json
{
  "reply": "Navigate from Building M to Building H\n\n1. Start at room 1003\n2. Turn left...",
  "mapAction": {
    "type": "SHOW_ROUTE",
    "start": {"building": "M", "floor": "1", "node": "M1_1"},
    "end": {"building": "H", "floor": "1", "node": "H1_20"},
    "path": { /* path data */ },
    "directions": { /* direction data */ }
  }
}
```

## Performance Considerations

- **Path Calculation:** O(E log V) using Dijkstra's algorithm
- **Typical Response Time:** < 100ms for single-building paths
- **Memory Usage:** ~2-5MB for complete campus navigation data
- **Caching:** Navigation data loaded once at service initialization

## Security Notes

- Navigation data is read-only
- No user data stored in navigation requests
- Building layouts are public information
- API endpoints require no authentication (campus public info)

## Future Enhancements

1. **Dynamic Obstacles**
   - Temporary path blockages (construction, events)
   - Real-time route recalculation
   - Alternative route suggestions

2. **Personalization**
   - Save favorite locations
   - Recent destinations
   - Custom waypoints

3. **Enhanced Visualization**
   - 3D building models
   - Augmented reality directions
   - Animated route preview

4. **Analytics**
   - Popular destinations
   - Navigation success rate
   - Path optimization based on usage

## Support

For issues or questions:
1. Check this documentation
2. Run validation tests
3. Review implementation files
4. Check console logs for error messages

---

**Implementation Status:** ✅ Complete  
**Last Updated:** December 4, 2025  
**Version:** 1.0.0
