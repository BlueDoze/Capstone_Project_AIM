# Campus Navigation - Quick Start Guide

## For Users

### How to Get Directions

1. **Via Chat (Recommended)**
   - Type: "How do I get to room 1003?"
   - Type: "Navigate from room 1003 to H1018"
   - Type: "Show me the way to the cafeteria in Building H"

2. **Via Map Interface**
   - Click on starting room/location
   - Click on destination room/location
   - Path automatically displays with directions

### Understanding Directions

**Direction Types:**
- **Single Floor:** Navigate within one building floor
- **Multi-Floor:** Use stairs/elevator to change floors
- **Multi-Building:** Travel between different buildings

**Turn Instructions:**
- "Turn left/right" - 90° turns
- "Bear left/right" - Slight turns (<45°)
- "Sharp left/right" - Acute turns (>120°)
- "Continue straight" - No turn needed
- "U-turn" - 180° reversal

---

## For Developers

### Quick Implementation

#### 1. Backend - Calculate Path

```python
from src.services.navigation_service import get_navigation_service
from src.services.direction_service import get_direction_service

nav = get_navigation_service()
dirs = get_direction_service()

# Find path
path = nav.find_path('M', '1', 'M1_1', 'H', '1', 'H1_20')

# Generate directions
directions = dirs.generate_directions(path)
print(dirs.generate_text_summary(directions))
```

#### 2. Frontend - Display Path

```javascript
import { calculatePath } from '../utils/navigationApi';
import MapNavigator from './components/MapNavigator';

// Calculate path
const result = await calculatePath(
  { building: 'M', floor: '1', room: '1003' },
  { building: 'H', floor: '1', room: 'H1018' }
);

// Display with MapNavigator
<MapNavigator
  building="M"
  initialFloor="1"
  mapAction={{
    type: 'SHOW_ROUTE',
    path: result.path,
    directions: result.directions
  }}
/>
```

#### 3. API Usage

```bash
# Get buildings
curl http://localhost:8081/api/navigation/buildings

# Get navigation data
curl http://localhost:8081/api/navigation/data?building=M&floor=1

# Calculate path
curl -X POST http://localhost:8081/api/navigation/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"building": "M", "floor": "1", "room": "1003"},
    "end": {"building": "H", "floor": "1", "room": "H1018"}
  }'
```

### File Locations

**Backend:**
- Navigation Service: `src/services/navigation_service.py`
- Direction Service: `src/services/direction_service.py`
- API Endpoints: `src/api/app.py` (lines 830-1000+)

**Frontend:**
- API Client: `Frontend_Data/frontend/src/utils/navigationApi.js`
- Map Component: `Frontend_Data/frontend/src/components/MapNavigator.jsx`
- Indoor Map View: `Frontend_Data/frontend/src/components/IndoorMapView.jsx`

**Data:**
- Navigation Graph: `LeafletJS/all_node_data.json`
- Building Connections: `LeafletJS/building_connections.JSON`
- Position Adjustments: `LeafletJS/Building positions.JSON`
- Floor Plans: `LeafletJS/Floorplans/{Building}/`

### Testing

```bash
# Validate implementation
python tests/validate_navigation.py

# Run full tests (requires pytest)
python -m pytest tests/test_navigation.py -v
```

### Common Tasks

#### Add New Building

1. Add navigation data to `all_node_data.json`:
```json
{
  "Building X": {
    "Floor 1": {
      "navigationGraph": { /* nodes */ },
      "roomToNode": { /* mappings */ }
    }
  }
}
```

2. Add floor plan SVG to `LeafletJS/Floorplans/X/`

3. Add position data to `Building positions.JSON` (if needed)

#### Add Building Connection

Edit `building_connections.JSON`:
```json
{
  "X-Y Connector": {
    "exit": "X1_exit_Y",
    "entry": "Y1_entry_X"
  }
}
```

#### Add Room Alias

Edit `config/building_m_rooms.json`:
```json
{
  "aliases": {
    "cafe": "1001",
    "computer lab": "1015"
  }
}
```

### API Response Formats

**Path Types:**
- `single-building` - Same building, same floor
- `multi-floor` - Same building, different floors
- `multi-building` - Different buildings

**Direction Step:**
```json
{
  "step": 1,
  "instruction": "Turn left at hallway intersection",
  "building": "M",
  "floor": "1",
  "node": { /* node data */ }
}
```

### Debugging

**Enable Logging:**
```python
# In navigation_service.py
print(f"Finding path from {start_node} to {end_node}")
print(f"Path found: {path}")
```

**Check Console:**
- Backend: Flask server console
- Frontend: Browser developer tools console

**Common Issues:**
- No path found → Check node connections
- Wrong building → Verify building letter case
- Missing floor plan → Check SVG file path

---

## Available Buildings & Floors

### Buildings with Full Navigation Data
- **Building M:** Floors 1, 2 (Main Building)
- **Building H:** Floor 1

### Buildings with Floor Plans Only
- A, B, C, D, E, F, G, J, K, T

### Building Connections
- M ↔ H (M-H Connector)
- H ↔ F (H-F Connector)

---

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/navigation/buildings` | GET | List all buildings |
| `/api/navigation/floors/<building>` | GET | List floors for building |
| `/api/navigation/data` | GET | Get floor navigation data |
| `/api/navigation/calculate` | POST | Calculate path |
| `/api/navigation/room-lookup` | POST | Find node for room |
| `/api/navigation/all-rooms` | GET | List all rooms |
| `/api/navigation/parse` | POST | Parse navigation intent |

---

## Example User Queries

### Supported
✅ "How do I get to room 1003?"  
✅ "Navigate from 1003 to 1018"  
✅ "Show me the way to Building H"  
✅ "Directions to the cafeteria"  
✅ "Where is the elevator in Building M?"  
✅ "Take me to H1018 from room 1003"  

### Requires More Context
⚠️ "Where is room 1003?" (shows location, not route)  
⚠️ "How long to walk to H1018?" (not yet implemented)  
⚠️ "Wheelchair accessible route?" (not yet implemented)  

---

## Performance Metrics

- **Path Calculation:** < 100ms (typical)
- **Direction Generation:** < 50ms
- **API Response:** < 200ms (total)
- **Graph Size:** ~1500 nodes (Building M+H)
- **Memory:** ~3MB (loaded data)

---

## Resources

- Full Documentation: `docs/NAVIGATION_IMPLEMENTATION.md`
- Validation Tests: `tests/validate_navigation.py`
- LeafletJS Guides: `docs/LEAFLET_IMPLEMENTATION_SUMMARY.md`

**Version:** 1.0.0  
**Updated:** December 4, 2025
