# Door Selection Fix for Multi-Door Rooms

## Issue Summary

When navigating to a room with multiple doors, the system was selecting the closest door to the **user's starting position** instead of the closest door to the **final navigation node** (the point where the user exits the hallway and enters the room).

### Example Problem
- User starts at position [43.01, -81.19] on Floor 1
- Room H1003 has 2 doors: Door_H1003_A and Door_H1003_B
- Door_H1003_A is 30m from user's start position
- Door_H1003_B is 5m from the final navigation node (user's destination)
- **Bug**: System selected Door_H1003_A (closest to start)
- **Expected**: Should select Door_H1003_B (closest to destination)

---

## Root Cause

In `LeafletJS/navigation.js`, the closest door selection was using `departureCoords.distanceTo(doorCenter)`:

```javascript
// WRONG - uses starting position
const distance = departureCoords.distanceTo(doorCenter);
```

This calculates distance from the user's starting position, not from where they'll actually be arriving at the room.

---

## Solution Implemented

Changed the logic to use the **last node in the path** (final navigation point) instead:

```javascript
// CORRECT - uses the final node in the navigation path
const lastNodeId = path[path.length - 1];
const lastNodePosition = graphData.nodePositions[lastNodeId];
const distance = lastNodePosition.distanceTo(doorCenter);
```

### Changes Made

**File:** `LeafletJS/navigation.js` (lines 471-502)

**Before:**
```javascript
let finalObjectId = null;
if (objectType === 'room' && doorList && doorList.length > 0) {
    let closestDoorId = null;
    let minDistance = Infinity;
    
    doorList.forEach((doorId) => {
        const doorElement = svgMap.getElementById(doorId);
        if (doorElement) {
            const doorCenter = objectToLatLng(doorElement, svgMap, buildingOverlay);
            if (doorCenter) {
                const distance = departureCoords.distanceTo(doorCenter);  // ❌ WRONG
                if (distance < minDistance) {
                    minDistance = distance;
                    closestDoorId = doorId;
                }
            }
        }
    });
    
    finalObjectId = closestDoorId || doorList[0];
    console.log(`✅ Selected closest door: ${finalObjectId}`);
}
```

**After:**
```javascript
let finalObjectId = null;
if (objectType === 'room' && doorList && doorList.length > 0) {
    let closestDoorId = null;
    let minDistance = Infinity;
    
    // Get the position of the last node in the path (nearest to destination)
    const lastNodeId = path[path.length - 1];
    const lastNodePosition = graphData.nodePositions[lastNodeId];
    
    console.log(`🚪 Finding closest door for room ${arrivalObjectId} from last node ${lastNodeId}`);
    
    doorList.forEach((doorId) => {
        const doorElement = svgMap.getElementById(doorId);
        if (doorElement) {
            const doorCenter = objectToLatLng(doorElement, svgMap, buildingOverlay);
            if (doorCenter && lastNodePosition) {
                // Calculate distance from the last node to each door
                const distance = lastNodePosition.distanceTo(doorCenter);  // ✅ CORRECT
                console.log(`   📏 ${doorId}: ${distance.toFixed(2)}m`);
                if (distance < minDistance) {
                    minDistance = distance;
                    closestDoorId = doorId;
                }
            }
        }
    });
    
    finalObjectId = closestDoorId || doorList[0];
    console.log(`✅ Selected closest door: ${finalObjectId} (${minDistance.toFixed(2)}m from node)`);
}
```

---

## Navigation Path Flow Verification

### Single-Floor, Same Building Navigation
```
User Position → [Find nearest node] → Path calculation → Last node in path → [FIND CLOSEST DOOR] → Room door → Final path line drawn
```

✅ **Fixed** - Now uses last node position for door selection

### Multi-Floor Navigation (Same Building)
```
User → Stairs/Elevator (on Floor 1) → [User advances to Floor 2] → Nearest connector node → Path to destination → [FIND CLOSEST DOOR via continueToNextFloor()] → Room door
```

✅ **Already Working** - `continueToNextFloor()` uses `findClosestDoorToPosition()` helper function (line 2697 in interactiveMap.html)

### Multi-Building Navigation
```
User → Building A path → Exit node → [Jump to Building B] → Entry node → Path to destination → [FIND CLOSEST DOOR via drawMultiBuildingPath()] → Room door
```

✅ **Already Working** - `drawMultiBuildingPath()` calculates closest door from last node (lines 1435-1462 in interactiveMap.html)

---

## Console Logging Added

For debugging, the updated code now logs:
```
🚪 Finding closest door for room H1003 from last node H1_5
   📏 Door_H1003: 5.23m
   📏 Door_H1003_2: 12.41m
✅ Selected closest door: Door_H1003 (5.23m from node)
```

This makes it easy to verify the correct door is being selected.

---

## Testing Checklist

- [ ] **Single-Floor Room Navigation**: Navigate to room with multiple doors, verify closest door to path endpoint is selected
  - Example: M1001 (2 doors) from M-Building M1
  - Expected: Closest door to final node selected
  
- [ ] **Multi-Floor Room Navigation**: Navigate to room on different floor with multiple doors
  - Example: Start Floor 1 → Climb stairs → Room on Floor 2 with multiple doors
  - Expected: Closest door to final node on Floor 2 is selected
  
- [ ] **Multi-Building Room Navigation**: Navigate across buildings to room with multiple doors
  - Example: Building M → Building H → Room with multiple doors
  - Expected: Closest door to final node in Building H is selected
  
- [ ] **Single-Door Rooms**: Navigate to rooms with only one door (sanity check)
  - Expected: Single door is used (fallback: `doorList[0]`)
  
- [ ] **Exits**: Navigate to stairs/elevators/outside exits
  - Expected: Exit itself is final object (not a door)
  - All scenarios: click, input ID, multi-floor, multi-building

---

## Impact

This fix ensures that when users arrive at a room via navigation, the path connects to the most logical entry point (closest to their actual approach), providing:
- More intuitive navigation paths
- Shorter final segment distances
- Better user experience for multi-door rooms

---

## Files Modified

- `LeafletJS/navigation.js` - Lines 471-502

---

## Compatibility

This change is **backward compatible**:
- If a room has only 1 door: fallback uses `doorList[0]` (same as before)
- If path/node data is missing: fallback uses first door in list
- No changes to function signatures or public APIs
