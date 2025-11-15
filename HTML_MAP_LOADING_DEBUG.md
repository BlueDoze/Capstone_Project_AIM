# HTML Map Loading - Debug Guide

## 📍 WHERE THE MAP IS LOADED

The map is now loaded **directly in `templates/index.html`** instead of in an iframe.

### **File Structure:**
```
templates/
└── index.html
    ├── CSS Links (Leaflet styles)
    ├── HTML Structure
    │   ├── <div id="chat-container"> ... chat interface
    │   └── <div id="map-container">
    │       ├── <div id="map"></div> ← MAP GOES HERE
    │       └── <div id="map-mode-indicator"> ← Status messages
    │
    └── Scripts (in order):
        ├── Leaflet JS library
        ├── Leaflet plugins
        ├── /static/../LeafletJS/floorPlansScript.js ← Building data
        ├── /static/map-controller.js ← Map initialization (FIXED)
        └── /static/script.js ← Chat logic
```

---

## 🗺️ WHAT SHOULD LOAD

When you visit http://localhost:8081, you should see:

### **Left Side (Chat Interface):**
- Fanshawe College Logo in red header
- Chat message area (white text on dark)
- Input box with "Send" button
- Initial message: "Welcome! How can I help you navigate Fanshawe College today?"

### **Right Side (Map):**
- **MapTiler base map** (streets, buildings, roads)
- **Building M** shown as blue polygon outline
- **SVG floor plan overlay** on Building M showing:
  - Room layouts and IDs (1003, 1004, 1018, etc.)
  - Navigation nodes (circles representing path waypoints)
  - Doors/exits marked on the plan

---

## 🔍 HOW TO DEBUG (Browser Console F12)

### **Step 1: Open Browser Console**
```
Windows/Linux: Press F12
Mac: Press Cmd + Option + J
```

### **Step 2: Expected Console Messages**

You should see these log messages (in order):

```javascript
✅ Map initialized
✅ Building M room configuration loaded
✅ Automatic monitoring started for: images/
🔄 System will automatically detect new images and update embeddings

// Then when map loads:
✅ Building M Floor 1 loaded successfully
✅ Navigation graph built!
✅ Highlighted [X] nodes
...
```

---

## ❌ TROUBLESHOOTING - COMMON ERRORS

### **Error 1: "Response is not JSON"**
```
❌ Error loading GeoJSON: TypeError: response.json is not a function
```

**Cause:** campus.geojson file not found or wrong path

**Fix:** Check Network tab (F12) → check if `/LeafletJS/campus.geojson` returns 200 OK
- If 404: File doesn't exist or path is wrong
- If CORS error: Flask route not working

**Solution:** Verify `/LeafletJS/campus.geojson` is accessible:
```bash
curl http://localhost:8081/LeafletJS/campus.geojson | head -20
```

---

### **Error 2: "Error loading SVG"**
```
❌ Error loading SVG: NetworkError
```

**Cause:** SVG floor plan file not found

**Fix:** Check Network tab for `/LeafletJS/Floorplans/Building%20M/M1_official.svg`
- URL must have `%20` for the space in "Building M"
- Must return 200 OK

**Solution:** Verify file exists and is accessible:
```bash
curl 'http://localhost:8081/LeafletJS/Floorplans/Building%20M/M1_official.svg' | head -20
```

---

### **Error 3: Map is blank gray"**
```
// No errors, but map shows nothing
```

**Cause:** JavaScript error or floorPlans data not loaded

**Fix:**
1. Check console for JavaScript errors (red text)
2. Type in console: `window.floorPlans`
   - Should show building data object
   - If `undefined`: floorPlansScript.js didn't load
3. Type in console: `window.map`
   - Should show Leaflet map object
   - If `null` or `undefined`: map initialization failed

**Solution:**
- Verify floorPlansScript.js script tag in index.html
- Check Network tab to see if `/static/../LeafletJS/floorPlansScript.js` loads (should be 200 OK)
- Check if Leaflet libraries loaded correctly

---

### **Error 4: No rooms visible on map**
```
// Map shows, building outline visible, but no SVG overlay
```

**Cause:** SVG file didn't load or didn't parse correctly

**Fix:**
1. Check console for "Error loading SVG" message
2. Check Network tab for SVG file request
3. Try fetching SVG manually:
```bash
curl 'http://localhost:8081/LeafletJS/Floorplans/Building%20M/M1_official.svg'
```

**Solution:** Make sure file path in map-controller.js uses `%20` for spaces:
```javascript
// CORRECT:
const svgPath = '/LeafletJS/Floorplans/Building%20M/M1_official.svg?ts=' + ...

// WRONG:
const svgPath = '/LeafletJS/Floorplans/Building M/M1_official.svg?ts=' + ...
```

---

## 🧪 MANUAL TESTS IN CONSOLE

### **Test 1: Check if floorPlans loaded**
```javascript
// In browser console, type:
window.floorPlans['Building M']['floors']['floor1']

// Should show object with:
// - navigationGraph: {...}
// - roomToNode: {...}
// - objects: {...}
```

### **Test 2: Check if map initialized**
```javascript
window.map

// Should show L.Map object with properties
// If null: Map didn't initialize
```

### **Test 3: Check current graph data**
```javascript
window.currentGraphData

// Should show:
// - graph: {...}
// - nodePositions: {...}
// - nodeMetadata: {...}
```

### **Test 4: Test Feature 1 manually (Chat → Map)**
```javascript
// This will show a route from Room_1003 to Room_1018
window.showRouteBuildingM('M1_6', 'M1_8')

// Check map for:
// - Green marker at Room 1003
// - Red marker at Room 1018
// - Yellow path between them
```

### **Test 5: Test Feature 2 manually (Map → Chat)**
```javascript
// Start click-selection mode
window.startMapNavigation()

// Then click on rooms in the map
// You should see:
// - Green marker after first click
// - Red marker after second click
// - Path drawn between them
```

---

## 🔧 CURRENT FIXES APPLIED

### **Fixed Paths in map-controller.js:**

**Before:**
```javascript
fetch('campus.geojson?ts=' + ...)  // ❌ Wrong - relative path
const svgPath = prePath + '/M1_official.svg?ts=' + ...  // ❌ Wrong - dynamic path
```

**After:**
```javascript
fetch('/LeafletJS/campus.geojson?ts=' + ...)  // ✅ Correct - absolute path
const svgPath = '/LeafletJS/Floorplans/Building%20M/M1_official.svg?ts=' + ...  // ✅ Correct
```

---

## ✅ VERIFICATION CHECKLIST

When you load http://localhost:8081:

- [ ] **Chat interface appears** on the left
- [ ] **Map appears** on the right
- [ ] **MapTiler base map visible** (street map background)
- [ ] **Building M outline visible** (blue polygon)
- [ ] **Browser console shows** `✅ Building M Floor 1 loaded successfully`
- [ ] **Right-click on map** → Building M → Click → Shows SVG floor plan overlay
- [ ] **Console messages show** no errors (only warnings about RAG system are OK)

If all checks pass → **Map is working correctly!**

---

## 📱 RESPONSIVE LAYOUT

**Desktop (1920x1080):**
- Chat: 400px width (left)
- Map: 800px width (right)
- Both: 600px height

**Tablet (768px):**
- Stacked vertically
- Chat: 45vh height
- Map: 50vh height

**Mobile (<480px):**
- Stacked vertically
- Chat: 40vh height
- Map: 55vh height

---

## 🎯 NEXT STEPS

Once map loads successfully:

1. **Test Feature 1:** Type navigation request in chat
2. **Test Feature 2:** Use browser console to test click-based navigation
3. **Test Room Aliases:** Try "bathroom men", "elevator", "1003", etc.
4. **Test Error Handling:** Try non-existent rooms and invalid requests

---

**Last Updated:** November 14, 2025
**Status:** Ready for browser testing
