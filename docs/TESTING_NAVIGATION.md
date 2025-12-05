# Testing Indoor Navigation Feature

## Quick Start

### 1. Start the Flask Backend

```bash
cd C:\Users\pedri\OneDrive\Desktop\Projeto_Final\Capstone_Project_AIM
python run_app.py
```

The server should start on `http://localhost:8081`

### 2. Build and Start the React Frontend (if not built)

```bash
cd Frontend_Data/frontend
npm install
npm run build
```

Note: The Flask server serves the built React app from `Frontend_Data/frontend/dist`

### 3. Open the Application

Navigate to: `http://localhost:8081`

## Testing Navigation Requests

### Example User Queries

Try these queries in the chat interface:

#### Single Room Navigation
- **"How do I get to room 1003?"**
- **"Show me the way to room 1018"**
- **"Navigate to room 1003 in building M"**

#### Room-to-Room Navigation
- **"How do I get from room 1003 to room 1018?"**
- **"Navigate from 1003 to 1018"**
- **"Take me from room 1003 to H1018"** (multi-building)

#### Expected Behavior

1. **Chat Response**: Text-based turn-by-turn directions
2. **Map Display**: Automatic popup with indoor map
3. **Route Visualization**: Highlighted path on floor plan
4. **Step-by-Step**: Navigate through directions with next/previous buttons

## Backend API Testing

### Test Navigation Endpoints Directly

```bash
# Get available buildings
curl http://localhost:8081/api/navigation/buildings

# Get floors for Building M
curl http://localhost:8081/api/navigation/floors/M

# Get navigation data
curl "http://localhost:8081/api/navigation/data?building=M&floor=1"

# Calculate path
curl -X POST http://localhost:8081/api/navigation/calculate \
  -H "Content-Type: application/json" \
  -d "{\"start\": {\"building\": \"M\", \"floor\": \"1\", \"room\": \"1003\"}, \"end\": {\"building\": \"M\", \"floor\": \"1\", \"room\": \"1018\"}}"
```

### Or use Python test script

```bash
python tests/test_navigation_integration.py
```

## Verification Checklist

### Backend ✓
- [ ] Flask server starts without errors
- [ ] Navigation services load successfully
- [ ] `/api/navigation/buildings` returns building list
- [ ] `/api/navigation/calculate` returns path and directions
- [ ] Chat endpoint recognizes navigation intent
- [ ] Response includes `mapAction` object

### Frontend ✓
- [ ] App loads in browser
- [ ] Chat interface is responsive
- [ ] Sending navigation query works
- [ ] Indoor map modal opens automatically
- [ ] Floor plan displays correctly
- [ ] Route is highlighted on map
- [ ] Directions panel shows steps
- [ ] Next/Previous buttons work
- [ ] Can close map and return to chat

## Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
netstat -ano | findstr :8081

# Kill process if needed
taskkill /PID <PID> /F

# Restart server
python run_app.py
```

### "No module named 'src.services.navigation_service'"
```bash
# Make sure you're in project root
cd C:\Users\pedri\OneDrive\Desktop\Projeto_Final\Capstone_Project_AIM

# Check file exists
dir src\services\navigation_service.py
```

### Map Doesn't Display
- Check browser console (F12) for errors
- Verify `MapNavigator.jsx` exists in `Frontend_Data/frontend/src/components/`
- Verify `navigationApi.js` exists in `Frontend_Data/frontend/src/utils/`
- Rebuild frontend: `cd Frontend_Data/frontend && npm run build`

### No Path Found
- Verify room exists: `curl "http://localhost:8081/api/navigation/all-rooms?building=M&floor=1"`
- Check `LeafletJS/all_node_data.json` has room-to-node mapping
- Verify nodes are connected in navigation graph

### Floor Plan Not Showing
- Check SVG file exists: `LeafletJS/Floorplans/M/M_building_floor_1.svg`
- Verify building positions data: `LeafletJS/Building positions.JSON`

## Sample Working Request/Response

### Request
```json
{
  "message": "How do I get to room 1003?"
}
```

### Response
```json
{
  "reply": "Navigate to room 1003 in Building M\n\n1. Start at your location\n2. Turn left at hallway intersection\n3. Continue straight\n4. Room 1003 is on your left",
  "mapAction": {
    "type": "SHOW_ROUTE",
    "start": {
      "location": "current",
      "building": "M",
      "floor": "1",
      "node": "M1_entrance"
    },
    "end": {
      "location": "1003",
      "building": "M",
      "floor": "1",
      "node": "M1_1"
    },
    "path": {
      "type": "single-building",
      "building": "M",
      "floor": "1",
      "path": ["M1_entrance", "M1_int_1", "M1_1"]
    },
    "directions": {
      "total_steps": 4,
      "steps": [...]
    }
  }
}
```

## Available Test Rooms

### Building M - Floor 1
- 1003, 1018, 1063, 1074, 1089
- Elevator, Stairs, Bathrooms
- M-H Connector

### Building H - Floor 1
- H1018, H1025, H1042
- Cafeteria, Elevator
- H-M Connector, H-F Connector

## Performance Expectations

- **Path Calculation**: < 100ms
- **Direction Generation**: < 50ms
- **Total API Response**: < 200ms
- **Map Load Time**: < 2s
- **Route Display**: Immediate

## Success Criteria

✅ User asks "How do I get to room 1003?"
✅ Backend calculates path using navigation graph
✅ Turn-by-turn directions generated
✅ Chat shows text directions
✅ Map modal opens automatically
✅ Floor plan displays with highlighted route
✅ User can navigate step-by-step
✅ All transitions are smooth

## Next Steps

Once basic navigation works:
1. Test multi-building routes (M to H)
2. Test multi-floor routes (Floor 1 to Floor 2)
3. Add more buildings to navigation data
4. Implement real-time position tracking
5. Add accessibility routing options

---

**Date**: December 4, 2025
**Status**: Ready for Testing
