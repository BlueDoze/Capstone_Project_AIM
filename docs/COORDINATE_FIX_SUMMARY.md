# Coordinate Fix Implementation Summary

## Date: November 14, 2025

## Problem Statement
The coordinates for origin and destination rooms were not matching the actual room locations on the map. Navigation markers were being placed at corridor nodes instead of room centers, causing visual misalignment.

## Root Causes Identified

1. **SVG-to-LatLng Transformation**: Coordinates were being transformed from SVG space to geographic coordinates, but the logic didn't distinguish between corridor nodes and room polygons.

2. **Node vs Room Position**: Navigation graph nodes (M1_6, M1_8, etc.) represent corridor positions NEAR rooms, not the actual room centers.

3. **Room-to-Node Mapping**: The system only mapped rooms to corridor nodes for navigation, without accounting for visual display accuracy.

4. **Second Door Reference**: Room_1003 had a reference to a second door at M1_Int_2 that was causing confusion.

## Changes Implemented

### 1. Enhanced Coordinate Transformation (`static/map-controller.js`)

#### Added `svgCoordsToLatLng()` Function
- Separated coordinate transformation logic into reusable function
- Accepts raw SVG coordinates (x, y) and transforms to LatLng
- Handles rotated building corners and bilinear interpolation
- Added debug logging for coordinate transformations

```javascript
function svgCoordsToLatLng(svgX, svgY, svgMap, corners) {
    // Normalizes SVG coordinates and interpolates across rotated building bounds
    // Returns accurate LatLng coordinates
}
```

#### Updated `nodeToLatLng()` Function
- Now uses `svgCoordsToLatLng()` for consistency
- Extracts cx, cy from circle elements and transforms them

### 2. Room Center Calculation (`static/map-controller.js`)

#### Added `getRoomCenterFromSVG()` Function
- Finds room polygon element in SVG by ID
- Calculates geometric center using `getBBox()`
- Transforms room center to LatLng coordinates
- Provides more accurate visual positioning for markers

```javascript
function getRoomCenterFromSVG(roomId, svgMap, corners) {
    // Gets room element by ID (e.g., "Room_1003")
    // Calculates center point of room polygon
    // Returns LatLng of room center
}
```

### 3. Enhanced `getCoordinatesForRoom()` Function (`static/map-controller.js`)

**Old Logic**: Always returned corridor node position
**New Logic**: 
1. First tries to get room center from SVG (more accurate for display)
2. Falls back to corridor node if room center unavailable
3. Returns null if neither available

```javascript
function getCoordinatesForRoom(roomId, graphData, svgMap) {
    // Priority 1: Room center (visual accuracy)
    const roomCenter = getRoomCenterFromSVG(roomId, svgMap, currentCorners);
    if (roomCenter) return roomCenter;
    
    // Priority 2: Corridor node (fallback)
    const nodeId = getRoomNodeId(roomId, graphData);
    if (nodeId && graphData.nodePositions[nodeId]) {
        return graphData.nodePositions[nodeId];
    }
    
    return null;
}
```

### 4. Updated `showRouteBuildingM()` Function (`static/map-controller.js`)

- Now retrieves room names from navigation nodes
- Places markers at room centers instead of corridor nodes
- Falls back to node positions for non-room nodes (intersections, turns, etc.)
- Adds descriptive labels to markers

**Key Changes**:
```javascript
// Get room name from node
const startRoomName = getRoomNameFromNode(startNode, currentGraphData.nodeMetadata);

// Use room center for marker placement
if (startRoomName) {
    startCoords = getCoordinatesForRoom(startRoomName, currentGraphData, currentSvgMap);
}
```

### 5. Navigation Graph Updates (`LeafletJS/floorPlansScript.js`)

#### Removed Second Door Reference for Room_1003
- **Before**: `M1_Int_2` had reference to `Room_1003` door 2
- **After**: `M1_Int_2` is just an intersection

```javascript
// BEFORE
"M1_Int_2": {
    "represents": [
        { type: "intersection" },
        { type: "room", id: "Room_1003", door: "Door_1003_2" }
    ]
}

// AFTER
"M1_Int_2": {
    "represents": { type: "intersection" }
}
```

#### Updated Room-to-Node Comment
- Changed comment from "Need to add second door at M1_Int_2" to "Main door entrance"

### 6. Debug Utilities (`static/map-controller.js`)

#### Added Debug Mode Flag
```javascript
const DEBUG_COORDINATES = true;
```

#### Added `debugLogCoordinates()` Function
- Logs detailed coordinate information during transformations
- Includes SVG coordinates, normalized coordinates, and LatLng results
- Can be toggled on/off with DEBUG_COORDINATES flag

## Technical Details

### Coordinate System Transformations

1. **SVG Coordinates**: Native coordinate system of the floor plan SVG
   - Origin: Top-left of SVG canvas
   - Units: SVG user units (typically pixels)

2. **Normalized Coordinates**: Relative position within SVG viewBox
   - Range: 0.0 to 1.0 in both X and Y
   - Formula: `normX = (cx - viewBox.x) / viewBox.width`

3. **Geographic Coordinates (LatLng)**: Real-world map coordinates
   - Latitude and longitude values
   - Computed via bilinear interpolation across 4 building corners

4. **Rotation Handling**: Building M is rotated 21.3° on the map
   - Corners are pre-rotated before overlay placement
   - SVG nodes have `transform="rotate(-21.3)"` attribute
   - Transformation accounts for rotation automatically

### Navigation vs Display Separation

**Navigation Logic (Path Finding)**:
- Uses corridor nodes (M1_1, M1_2, etc.)
- Nodes represent walkable paths and intersections
- Dijkstra's algorithm finds shortest path between nodes

**Display Logic (Markers)**:
- Uses room centers for visual accuracy
- Calculated from actual room polygon geometry
- Provides better user experience

## Files Modified

1. ✅ `/static/map-controller.js`
   - Added: `svgCoordsToLatLng()`, `getRoomCenterFromSVG()`, `debugLogCoordinates()`
   - Enhanced: `getCoordinatesForRoom()`, `showRouteBuildingM()`
   - Modified: `nodeToLatLng()`

2. ✅ `/LeafletJS/floorPlansScript.js`
   - Removed: Second door reference for Room_1003 at M1_Int_2
   - Updated: Comment for Room_1003 in roomToNode mapping

## Expected Results

### Before Fix
- ❌ Markers appeared at corridor positions (outside rooms)
- ❌ Visual misalignment with room polygons
- ❌ Confusing user experience

### After Fix
- ✅ Markers appear at room centers (inside room polygons)
- ✅ Visual alignment with room geometry
- ✅ Accurate representation of start/end locations
- ✅ Path still uses corridor nodes (correct navigation logic)

## Testing Recommendations

### Manual Testing Steps

1. **Test Feature 1: Chat → Map**
   - Send message: "Navigate from Room 1003 to Room 1018"
   - Verify: Green marker appears inside Room_1003 (not in corridor)
   - Verify: Red marker appears inside Room_1018 (not in corridor)
   - Verify: Path highlights corridor nodes correctly

2. **Test Feature 2: Map → Chat**
   - Click "Start Navigation" button
   - Click on Room_1003 polygon
   - Click on Room_1018 polygon
   - Verify: Markers placed at room centers
   - Verify: Chat receives navigation request

3. **Test Multiple Rooms**
   - Test with: Room_1004, Room_1006, Room_1030, Room_1033, Room_1035, etc.
   - Verify: All markers appear at room centers

4. **Test Special Locations**
   - Test bathrooms: Bathroom-Men, Bathroom-Women, Bathroom-Accessible
   - Test elevator: Elevator-M
   - Test stairs: Stairs_1, Stairs_2, Stairs_3
   - Verify: Markers appear at logical positions

### Debug Console Output

With `DEBUG_COORDINATES = true`, you should see logs like:
```
🔍 [DEBUG] SVG→LatLng: {
  lat: "43.012543",
  lng: "-81.200234",
  svgX: "123.45",
  svgY: "456.78",
  normX: "0.1512",
  normY: "0.4327"
}

🏢 Room Room_1003 center in SVG: (234.56, 567.89)
✅ Using room center for Room_1003
```

## Known Limitations

1. **SVG Elements Must Exist**: Room IDs in configuration must match SVG element IDs
2. **BBox Accuracy**: `getBBox()` calculates axis-aligned bounding box (may not be perfect for rotated or complex shapes)
3. **Rotation Transform**: Assumes nodes have consistent rotation transform
4. **Single Door**: Currently uses only one door per room (ignored second door for Room_1003)

## Future Enhancements

1. **Multi-Door Support**: Handle rooms with multiple doors, selecting closest door based on path direction
2. **Custom Room Centers**: Add `roomCenters` configuration in JSON for manual overrides
3. **Visual Debug Mode**: Add UI toggle to show/hide node circles and room centers on map
4. **Coordinate Validation**: Add automated tests to verify coordinate accuracy
5. **Polygon Centroid**: Use actual geometric centroid instead of bounding box center for irregular shapes

## Verification Checklist

- ✅ Code changes implemented
- ✅ Navigation graph updated (removed second door)
- ✅ Debug logging added
- ✅ Functions properly separated (navigation vs display)
- ✅ Coordinate transformation enhanced
- ✅ Room center calculation added
- ⏳ Manual testing (pending user verification)
- ⏳ Browser console verification (pending user testing)

## Notes

- Server is running on port 8081
- Changes are client-side only (JavaScript) - no server restart needed
- Simply refresh browser to load updated map-controller.js
- Check browser console for debug output
- RAG system warnings in server log are not related to this fix

## How to Test Right Now

1. Open browser to: `http://localhost:8081`
2. Open Developer Console (F12)
3. Navigate map to Building M
4. Try navigation between rooms
5. Check console for debug logs showing coordinate transformations

---

**Implementation Status**: ✅ **COMPLETE**

All planned changes have been successfully implemented. The coordinate mismatch issue should now be resolved with markers accurately placed at room centers while maintaining correct navigation path logic through corridor nodes.
