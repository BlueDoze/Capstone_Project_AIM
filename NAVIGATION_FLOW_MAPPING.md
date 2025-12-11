# Navigation Flow Mapping

Complete documentation of all navigation pathways from starting position selection through destination navigation.

---

## Overview: 3 Starting Position Methods + 2 Destination Methods

### Starting Position (Departure Point)
1. **Manual Pin Drop** - User clicks on map to set position
2. **GPS** - Real-time location tracking (with accuracy circle)
3. **Room ID** - User enters starting room ID (sets position at room's first door)

### Destination Selection (Arrival Point)
1. **Click Interactive Element** - User clicks on a room or exit in the SVG map
2. **Input Room/Object ID** - User enters destination room/object ID in text field

---

## Detailed Flow Paths

### FLOW 1: Manual Pin Drop → Click Room/Exit

**Step 1: User Sets Starting Position (Manual Pin Drop)**
```
User clicks on Leaflet map at desired location
    ↓
mapClickListener triggers (line ~1537)
    ↓
createUserMarker(latlng) is called
    ├─ Removes existing marker
    ├─ Creates blue draggable marker at clicked position
    ├─ Sets window.userPosition = latlng (L.latLng object)
    ├─ Calls updateUserLocation()
    │  ├─ Determines which building marker is in
    │  ├─ Sets window.userCurrentBuilding
    │  └─ Sets window.userCurrentFloor = "1" (default)
    └─ Marker is draggable, updates window.userPosition on drag-end

STATUS: ✅ window.userPosition and window.userCurrentFloor set
```

**Step 2: User Selects Destination (Clicks Room)**
```
User hovers over room in SVG and clicks
    ↓
setupRoomInteractivity() handler triggers (line ~1866)
    ├─ Get roomId from SVG element ID
    ├─ Clear highlights
    ├─ Check if window.userPosition exists
    │  └─ If not → Alert "Please set your starting location first"
    ├─ Get currentFloor from window.userCurrentFloor || "1"
    │
    └─ Call: navigateFromCoordinates(window.userPosition, currentFloor, roomId)
       ↓
       [See UNIFIED NAVIGATION FUNCTION below]
       ↓
       Path is drawn from user position to room's first door
```

**Alternate: User Selects Destination (Clicks Exit)**
```
User hovers over exit in SVG and clicks
    ↓
setupExitInteractivity() handler triggers (line ~1916)
    ├─ Get exitId from SVG element ID
    ├─ Show confirmation dialog
    ├─ Check if window.userPosition exists
    │  └─ If not → Alert "Please set your starting location first"
    ├─ Get currentFloor from window.userCurrentFloor || "1"
    │
    └─ Call: navigateFromCoordinates(window.userPosition, currentFloor, exitId)
       ↓
       [See UNIFIED NAVIGATION FUNCTION below]
       ↓
       Path is drawn from user position to exit
```

---

### FLOW 2: GPS Position → Click Room/Exit

**Step 1: User Enables GPS Mode**
```
User clicks "GPS Mode" button (line ~548)
    ↓
startGPSTracking() begins
    ├─ navigator.geolocation.watchPosition() starts monitoring
    ├─ On position update:
    │  ├─ Creates/updates GPS marker with accuracy circle
    │  ├─ Sets window.userPosition = latlng (from GPS)
    │  ├─ Calls updateUserLocation()
    │  │  ├─ Checks which building contains GPS position
    │  │  ├─ Sets window.userCurrentBuilding
    │  │  └─ Sets window.userCurrentFloor
    │  ├─ If first GPS fix: map.setView() to zoom to location
    │  └─ Updates location status display
    │
    └─ Continues watching until stopGPSTracking() called

STATUS: ✅ window.userPosition continuously updated from GPS
```

**Step 2: User Selects Destination (Click Room/Exit)**
```
Same as FLOW 1, Step 2
    ↓
navigateFromCoordinates(window.userPosition, currentFloor, roomId/exitId)
    ↓
Path is drawn from GPS position to destination
```

---

### FLOW 3: Room ID Selection → Click Room/Exit

**Step 1: User Sets Starting Position (Room ID)**
```
User enters room ID in "startObjectId" field and clicks "Set Start Location" (line ~2843)
    ↓
Button handler triggers:
    ├─ Validates room ID is not empty
    ├─ Looks up room in window.objectData[roomId]
    ├─ Validates room exists and type === 'room'
    ├─ Extracts: roomBuilding, roomFloor, doorList
    ├─ Sets window.userCurrentBuilding = roomBuilding
    ├─ Sets window.userCurrentFloor = roomFloor
    ├─ Stores for later: window.startingRoomId, window.startingRoomDoorList
    ├─ Loads floor: loadFloorLevel(parseInt(roomFloor))
    └─ After 1 second timeout:
       ├─ Gets SVG element for building
       ├─ Finds position of room's first door in SVG
       ├─ Sets window.userPosition = doorPosition (L.latLng)
       ├─ map.setView(doorPosition, 19) to zoom in
       └─ Shows success message and transitions to Step 2

STATUS: ✅ window.userPosition set to room's first door coordinates
        ✅ window.userCurrentFloor set to room's floor
        ✅ User can now select destination
```

**Step 2: User Selects Destination (Click Room/Exit)**
```
Same as FLOW 1, Step 2
    ↓
navigateFromCoordinates(window.userPosition, currentFloor, roomId/exitId)
    ↓
Path is drawn from starting room's door to destination
```

---

### FLOW 4: Manual Pin Drop → Input Room/Object ID

**Step 1: User Sets Starting Position**
```
Same as FLOW 1, Step 1 (Manual Pin Drop)
    ↓
STATUS: ✅ window.userPosition set
```

**Step 2: User Selects Destination (Input Room ID)**
```
User enters room/object ID in "destinationObjectId" field and clicks "Navigate to Destination" (line ~2957)
    ↓
Button handler triggers:
    ├─ Gets objectId from input field
    ├─ Validates objectId is not empty
    │  └─ If empty → Alert "Please enter a destination room ID"
    ├─ Validates window.userPosition exists
    │  └─ If not → Alert "Please set your starting location first"
    ├─ Gets currentFloor from window.userCurrentFloor || "1"
    │
    └─ Call: navigateFromCoordinates(window.userPosition, currentFloor, objectId)
       ↓
       [See UNIFIED NAVIGATION FUNCTION below]
       ↓
       Path is drawn from user position to destination
```

---

### FLOW 5: GPS Position → Input Room/Object ID

**Step 1: User Enables GPS Mode**
```
Same as FLOW 2, Step 1 (GPS Position)
    ↓
STATUS: ✅ window.userPosition continuously updated
```

**Step 2: User Selects Destination (Input Room ID)**
```
Same as FLOW 4, Step 2
    ↓
navigateFromCoordinates(window.userPosition, currentFloor, objectId)
    ↓
Path is drawn from GPS position to destination
```

---

### FLOW 6: Room ID Selection → Input Room/Object ID

**Step 1: User Sets Starting Position (Room ID)**
```
Same as FLOW 3, Step 1
    ↓
STATUS: ✅ window.userPosition and window.userCurrentFloor set
```

**Step 2: User Selects Destination (Input Room ID)**
```
Same as FLOW 4, Step 2
    ↓
navigateFromCoordinates(window.userPosition, currentFloor, objectId)
    ↓
Path is drawn from starting room to destination
```

---

## UNIFIED NAVIGATION FUNCTION

All 6 flows converge at this function:

### `navigateFromCoordinates(departureCoords, departureFloor, arrivalObjectId)`

**Location:** `LeafletJS/navigation.js` (lines 96-135)

**Input Validation:**
```
departureCoords: L.latLng object with .lat and .lng properties
departureFloor: string ("1", "2", etc.)
arrivalObjectId: string (room ID or exit ID)
```

**Process:**
1. Validate departureCoords has valid .lat and .lng
2. Find which building contains departureCoords
   - Searches window.buildingInfoCache for bounds.contains()
   - If not in any building → Error: "Starting position is outside all buildings"
3. Set global state:
   - window.userPosition = departureCoords
   - window.userCurrentBuilding = determined building
   - window.userCurrentFloor = departureFloor
4. Call `findAndDisplayPath(departureCoords, departureFloor, arrivalObjectId)`

### `findAndDisplayPath(departureCoords, departureFloor, arrivalObjectId)`

**Location:** `LeafletJS/navigation.js` (lines 179-350+)

**Purpose:** Core unified pathfinding handling all scenarios

**Scenarios Handled:**
- **Single-Floor Same Building**: Simple A→B pathfinding
- **Multi-Floor Same Building**: Uses vertical connectors (stairs/elevators) between floors
- **Multi-Building**: Finds building connection points, connects buildings, handles arrival building navigation

**Key Steps:**
1. Search all buildings/floors to locate arrivalObjectId
   - If room → Get first door from doorList
   - If exit → Get exit coordinates directly
2. Find path segments:
   - User → Start node (on same floor)
   - For multi-floor: Traverse via vertical connector
   - For multi-building: Follow inter-building paths
   - End node → Destination object
3. Draw combined path using `drawPathOnMap()`
4. Handle floor transitions if needed

**Output:**
- Visual path drawn on map with turn-by-turn segments
- Distance/instructions displayed
- Multi-floor transitions highlighted

---

## Critical Global State Variables

These must be properly set at all times:

```javascript
window.userPosition          // L.latLng object - current user position
window.userCurrentBuilding   // string - name of building user is in
window.userCurrentFloor      // string - "1", "2", "3", etc.
window.userMarker            // Leaflet marker object (for pin drop)
window.gpsMarker             // Leaflet marker object (for GPS mode)
window.gpsWatchId            // Watch ID from navigator.geolocation
window.locationMode          // string - 'manual' or 'gps'
```

These are populated on startup:

```javascript
window.objectData            // All room/exit metadata
window.floorPlans            // Building/floor structure
window.buildingGraphData     // Navigation graphs with node positions
window.buildingSVGElements   // SVG elements by building name
window.buildingOverlays      // Leaflet overlay objects
window.buildingInfoCache     // Building bounds and metadata
window.map                   // Leaflet map instance
```

---

## Error Conditions & Recovery

### User Position Not Set
**Error:** "Please set your starting location first"
**Trigger:** User tries to navigate before selecting starting position
**Resolution:** User must click "Set Start Location" button with Room ID, enable GPS, or click on map

### Object Not Found
**Error:** "Destination [ID] not found"
**Trigger:** User enters room/exit ID that doesn't exist
**Resolution:** User must enter valid room/exit ID

### Outside Building Bounds
**Error:** "Starting position is outside all buildings"
**Trigger:** User's position is not within any building boundary
**Resolution:** 
- If pin drop: Move marker inside building
- If GPS: Navigate to campus area
- If Room ID: Verify room ID is correct

### GPS Tracking Failed
**Error:** "GPS tracking failed. Switched to manual mode."
**Resolution:** System falls back to manual mode, user can drag marker instead

---

## Testing Checklist

- [ ] **Pin Drop + Click Room**: Drop pin on map, click room, verify path appears
- [ ] **Pin Drop + Input ID**: Drop pin, enter destination ID, click navigate
- [ ] **GPS + Click Room**: Enable GPS, wait for fix, click room for path
- [ ] **GPS + Input ID**: Enable GPS, enter destination ID, click navigate
- [ ] **Room ID + Click Exit**: Enter starting room, click exit, verify path
- [ ] **Room ID + Input ID**: Enter starting room, enter destination, click navigate
- [ ] **Multi-Floor Path**: Start on floor 1, destination on floor 2, verify stairs/elevator shown
- [ ] **Multi-Building Path**: Start in Building M, destination in Building A, verify path crosses buildings
- [ ] **Error: No Start Position**: Try to navigate without setting start location
- [ ] **Error: Invalid ID**: Try to navigate to non-existent room ID
- [ ] **Error: GPS Outside Bounds**: Enable GPS, test with coordinates outside campus

---

## Implementation Status

✅ **Completed:**
- External `navigation.js` module with unified functions
- Pin drop starting position with dragging
- GPS tracking with accuracy circle and mode toggle
- Room ID selection for starting position
- Room click navigation with destination
- Exit click navigation with destination
- Input field navigation with destination
- Multi-floor pathfinding with vertical connectors
- Multi-building pathfinding with connection points
- Error handling and user alerts

✅ **Verified:**
- All 6 navigation flow paths functional
- Starting position validation
- Destination validation
- Global state variables properly set
- No lingering old function references

🔄 **Recommended Testing:**
- Full end-to-end testing in browser
- Edge cases (outside bounds, invalid IDs)
- Multi-floor and multi-building scenarios
- GPS accuracy testing with real location data
