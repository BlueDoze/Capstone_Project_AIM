# Smart Door Selection - Quick Testing Guide

## What Changed

The system now intelligently selects the **closest door** to the user's starting position when navigating to rooms with multiple doors.

**Visual Example:**
```
User @ Position A
  |
  | 25m to Door_M1003_1
  |
  ├──────────────────────────────────┤ Room M1003
  |
  | 10m to Door_M1003_2 ← SELECTED (closer)
  
Path: User Position → Door_M1003_2 (shortest route)
```

---

## Test Cases

### TEST 1: Single-Door Room (Baseline)
**Room:** H1003
**Expected:** Navigate to H1003, path connects to Door_H1003
**Check Console For:**
```
🚪 Finding closest door for room H1003 from user position
   Available doors: {Door_H1003: "H1_5"}
✅ Selected closest door: Door_H1003 (Xm from user)
```

---

### TEST 2: Multi-Door Room - Same Floor
**Room:** M1003 (2 doors: Door_M1003_1, Door_M1003_2)
**Steps:**
1. Set start location to M1018 (or use pin drop in M building)
2. Click on M1003 room or enter "M1003" as destination
3. **Expected:** Path drawn to the closer of the two doors

**Console Output:**
```
🚪 Finding closest door for room M1003 from user position
   Available doors: {Door_M1003_1: "M1_Path1_6", Door_M1003_2: "M1_Int_2"}
   📏 Door_M1003_1 (node: M1_Path1_6): 25.34m from start
   📏 Door_M1003_2 (node: M1_Int_2): 10.21m from start
✅ Selected closest door: Door_M1003_2 (10.21m from user)
🔵 Drew blue line to destination door: Door_M1003_2
```

**Result:** Blue line should connect to the closer door ✅

---

### TEST 3: Multi-Door Room - Multi-Floor
**Room:** M2012 (2 doors on Floor 2)
**Steps:**
1. Set start location to M1040 (Floor 1)
2. Enter "M2012" as destination
3. Click "Take the stairs" button
4. Wait for Floor 2 to load
5. **Expected:** Path appears from stairs to the closer door of M2012

**Console Output (Floor 2 transition):**
```
🚪 Room M2012 contains 2 door(s)
   Door 1 (Door_M2012_1 → node M2_5): Distance 12.45m from final node
   Door 2 (Door_M2012_2 → node M2_12): Distance 8.67m from final node
✅ Selected closest door: Door_M2012_2 (8.67m from final node)
🟢 Drew green line from vertical connector Stairs_1_M2 to first node
🔵 Drew blue line to destination door: Door_M2012_2
```

---

### TEST 4: Multi-Door Room - Multi-Building  
**Room:** H1005 (2 doors in Building H)
**Steps:**
1. Set start location to M1049 (Building M)
2. Enter "H1005" as destination
3. **Expected:** Path crosses buildings and connects to closest door of H1005

**Console Output:**
```
🌉 Multi-building: Building M → Building H
✅ Path to exit (5 nodes)
✅ Path to destination (12 nodes)
🎨 Drawing multi-building path...
📍 Processing segment 2:
🎯 This is the final segment - adding final object connection
🚪 Room H1005 contains 2 door(s)
   Door 1 (Door_H1005_2 → node H1_13): Distance 9.23m from final node
   Door 2 (Door_H1005_1 → node H1_14): Distance 14.56m from final node
✅ Selected closest door: Door_H1005_2 (9.23m from final node)
🔵 Drew blue line to destination door: Door_H1005_2
```

---

### TEST 5: Cafeteria with 2 Doors
**Room:** Cafeteria_H1 (Door_Cafe_H1_1, Door_Cafe_H1_2)
**Steps:**
1. Set start location or use pin drop in H building
2. Click on Cafeteria or enter "Cafeteria_H1"
3. **Expected:** Path connects to closer of the two cafeteria doors

**Console Check:**
```
🚪 Finding closest door for room Cafeteria_H1 from user position
   Available doors: {Door_Cafe_H1_1: "H1_10", Door_Cafe_H1_2: "H1_22"}
   📏 Door_Cafe_H1_1 (node: H1_10): 18.45m from start
   📏 Door_Cafe_H1_2 (node: H1_22): 7.89m from start
✅ Selected closest door: Door_Cafe_H1_2 (7.89m from user)
```

---

## Data Verification

### Check object_data.json Structure
Open `LeafletJS/JSON/object_data.json` and search for "M1003":

```json
"M1003": {
    "building": "Building M",
    "floor": "1",
    "typeCategory": "room",
    "type": "classroom",
    "doors": {
        "Door_M1003_1": "M1_Path1_6",
        "Door_M1003_2": "M1_Int_2"
    }
}
```

✅ **Expected:** Doors are dictionaries (not arrays) mapping door ID → node ID

### Check Browser Console

1. Open DevTools (F12)
2. Go to Console tab
3. Perform navigation
4. Look for messages starting with:
   - 🚪 (Finding closest door)
   - 📏 (Door distance)
   - ✅ (Selected door)

---

## Common Issues & Fixes

### Issue: Doors appear as array [Door_1, Door_2]
**Cause:** object_data.json not regenerated
**Fix:** 
1. Open `LeafletJS/JSON/ExcelToJson.ipynb`
2. Run cell: "Generate object_data.json"
3. Restart application

### Issue: Path still goes to wrong door
**Cause:** Browser cache not cleared
**Fix:** 
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+R)
3. Close and reopen browser tab

### Issue: Console shows "Door not found in SVG"
**Cause:** SVG element IDs don't match data
**Fix:** Verify door IDs in CSV files match SVG element IDs

---

## Success Criteria

✅ All tests pass if:
1. Doors are shown as dictionaries in object_data.json
2. Console logs show distance calculations
3. Path connects to closest door (not random door)
4. Same behavior for single-door rooms (backward compatible)
5. Multi-floor and multi-building navigation work correctly

---

## Rooms With Multiple Doors

**Known Multi-Door Rooms:**
- M1003: 2 doors (Door_M1003_1, Door_M1003_2)
- M1005: 2 doors (Door_H1005_1, Door_H1005_2)
- M2012: 2 doors (Door_M2012_1, Door_M2012_2)
- M2017: 2 doors (Door_M2017_1, Door_M2017_2)
- M2018: 2 doors (Door_M2018_1, Door_M2018_2)
- M2041: 2 doors (Door_M2041_1, Door_M2041_2)
- M2047: 2 doors (Door_M2047_1, Door_M2047_2)
- Cafeteria_H1: 2 doors (Door_Cafe_H1_1, Door_Cafe_H1_2)

**Use these rooms for testing!**

---

## Questions?

Check the comprehensive guide: `SMART_DOOR_SELECTION_SYSTEM.md`
