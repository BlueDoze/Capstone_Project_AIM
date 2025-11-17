# Testing Guide - Chatbot ↔ Map Integration

## 🧪 TESTING PHASES

### **Phase 1: Basic Setup Verification**

**Checklist:**
- [ ] Application starts without errors
- [ ] Map loads with Building M visible
- [ ] Chat window is functional
- [ ] Both containers (chat and map) display properly

**Commands to test:**
```bash
python main.py
# Open browser: http://localhost:8081
```

**Expected:**
- Homepage loads with chat on left, map on right
- Building M should be visible on the map (blue polygon)
- Chat shows: "Welcome! How can I help you navigate Fanshawe College today?"

---

### **Phase 2: Feature 1 Testing (Chat → Map)**

**Test Case 1.1: Simple Room Navigation**

**Steps:**
1. Type in chat: `"How do I get from room 1003 to room 1018?"`
2. Send message

**Expected Results:**
- ✅ Chat displays Gemini response with directions
- ✅ Map automatically shows:
  - Green marker at Room 1003
  - Red marker at Room 1018
  - Yellow/orange path connecting them
  - Auto-zoomed to show full route
- ✅ Console shows: `"🗺️ Navigation detected: Room_1003 → Room_1018"`

---

**Test Case 1.2: Using Room Aliases**

**Steps:**
1. Type: `"How to get from 1003 to bathroom men?"`
2. Send message

**Expected Results:**
- ✅ System resolves "1003" to Room_1003
- ✅ System resolves "bathroom men" to Bathroom-Men
- ✅ Same route displayed as Test 1.1
- ✅ Chat response mentions: "Men's Restroom" (not "Bathroom-Men")

---

**Test Case 1.3: Using Friendly Names**

**Steps:**
1. Type: `"Navigate from the computer lab to the men's bathroom"`
2. Send message

**Expected Results:**
- ⚠️ May not work (depends on Gemini extraction)
- Fallback: Use numeric room numbers or exact names from config

---

**Test Case 1.4: Non-Navigation Request**

**Steps:**
1. Type: `"What is your name?"`
2. Send message

**Expected Results:**
- ✅ Chat responds normally
- ✅ No mapAction triggered
- ✅ Map unchanged
- ✅ Console shows no navigation detected

---

### **Phase 3: Feature 2 Testing (Map → Chat)**

**Test Case 2.1: Start Map Navigation Mode**
*(Feature 2 requires UI button - not yet implemented)*

**When implemented, test:**
```javascript
// In browser console, manually start navigation mode
window.startMapNavigation()
```

**Expected:**
- ✅ Mode indicator shows: "Click on your starting location"
- ✅ Yellow indicator box pulses at top-left of map
- ✅ Map is interactive and clickable

---

**Test Case 2.2: Click Selection** *(Manual)*

**Steps:**
```javascript
// Step 1: Start navigation
window.startMapNavigation()

// Step 2: Click on Room 1003 in map
// (Click on the Room_1003 SVG element)

// Step 3: Mode indicator changes to "Click your destination"
// Step 4: Click on Bathroom-Men

// Step 5: Wait for chat response
```

**Expected:**
- ✅ Green marker appears at Room 1003
- ✅ Red marker appears at Bathroom-Men
- ✅ Yellow path shows route between them
- ✅ Chat automatically shows walking directions
- ✅ Console logs: `"✅ Route cleared"`, `"🗺️ Showing route..."`

---

### **Phase 4: API Testing**

**Test Case 4.1: Test /api/navigation/parse**

```bash
curl -X POST http://localhost:8081/api/navigation/parse \
  -H "Content-Type: application/json" \
  -d '{"message": "How to get from room 1003 to bathroom men?"}'
```

**Expected Response:**
```json
{
  "is_navigation": true,
  "start": "Room_1003",
  "end": "Bathroom-Men",
  "startNode": "M1_6",
  "endNode": "M1_9",
  "building": "M",
  "floor": 1,
  "start_original": "1003",
  "end_original": "bathroom men"
}
```

---

**Test Case 4.2: Test /api/navigation/from-clicks**

```bash
curl -X POST http://localhost:8081/api/navigation/from-clicks \
  -H "Content-Type: application/json" \
  -d '{"startRoom": "Room_1003", "endRoom": "Bathroom-Men", "building": "M", "floor": 1}'
```

**Expected Response:**
```json
{
  "reply": "<p>Walking directions HTML...</p>",
  "startRoom": "Room_1003",
  "endRoom": "Bathroom-Men",
  "startNode": "M1_6",
  "endNode": "M1_9"
}
```

---

**Test Case 4.3: Test /api/navigation/rooms**

```bash
curl http://localhost:8081/api/navigation/rooms
```

**Expected Response:**
```json
{
  "Room_1003": {
    "node": "M1_6",
    "description": "Room 1003 - Computer Lab"
  },
  "Room_1004": {
    "node": "M1_4",
    "description": "Room 1004 - Classroom"
  },
  ...
}
```

---

### **Phase 5: Room Alias Testing**

Test all aliases in config/building_m_rooms.json:

**Numeric Aliases:**
- [ ] "1003" → Room_1003
- [ ] "1004" → Room_1004
- [ ] "1018" → Room_1018

**Bathroom Aliases:**
- [ ] "bathroom men" → Bathroom-Men
- [ ] "men's bathroom" → Bathroom-Men
- [ ] "men bathroom" → Bathroom-Men
- [ ] "bathroom women" → Bathroom-Women
- [ ] "women's bathroom" → Bathroom-Women

**Facility Aliases:**
- [ ] "elevator" → Elevator-M
- [ ] "stairs" → Stairs_1
- [ ] "stairwell" → Stairs_1
- [ ] "exit" → Outside-Exit_1

**Test Format:**
```
User: "How to get from [ALIAS_1] to [ALIAS_2]?"
Expected: Navigation successful with correct rooms
```

---

### **Phase 6: Error Handling**

**Test Case 6.1: Non-existent Room**

**Steps:**
1. Type: `"How to get to room 9999?"`
2. Send message

**Expected:**
- ✅ Chat responds (Gemini may give generic answer)
- ✅ No mapAction (room not found)
- ✅ No error in console

---

**Test Case 6.2: Invalid Room Names**

**Steps:**
1. Type: `"Navigate to xyz building?"`
2. Send message

**Expected:**
- ✅ Gemini may ask for clarification or respond generically
- ✅ No mapAction triggered
- ✅ System handles gracefully

---

**Test Case 6.3: Missing Start/End Points**

**Steps:**
1. Type: `"How to get to the cafeteria?"`
2. Send message

**Expected:**
- ✅ If "cafeteria" not in aliases: No mapAction
- ✅ Chat response still provided
- ✅ User can rephrase with correct room number

---

### **Phase 7: Visual Testing**

**Checklist:**
- [ ] Green markers display correctly
- [ ] Red markers display correctly
- [ ] Yellow path nodes appear on map
- [ ] Mode indicator box styles correctly
- [ ] Mode indicator pulses when active
- [ ] Map stays responsive after navigation
- [ ] Zoom automatically fits route
- [ ] Rotation display updates when map rotates

---

### **Phase 8: Performance Testing**

**Test Case 8.1: Multiple Rapid Requests**

**Steps:**
1. Send 5 navigation requests rapidly
2. Click clear route between requests
3. Monitor memory usage

**Expected:**
- ✅ No memory leaks
- ✅ Each request completes successfully
- ✅ Map remains responsive
- ✅ No JavaScript errors

---

**Test Case 8.2: Long Navigation Path**

**Steps:**
1. Request navigation from Room 1003 to Room 1049
2. This requires longest path through building

**Expected:**
- ✅ Route calculates in <500ms
- ✅ All nodes highlight correctly
- ✅ Path displays smoothly

---

### **Phase 9: Browser Compatibility**

**Browsers to test:**
- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

**Expected:** All features work identically

---

### **Phase 10: Mobile Testing**

**Test Case 10.1: Responsive Layout**

**Steps:**
1. Open on mobile device (width < 480px)
2. Type navigation request
3. Verify both chat and map visible

**Expected:**
- ✅ Chat shows above map (vertically stacked)
- ✅ Both containers visible
- ✅ Text readable
- ✅ Touch interactions work

---

**Test Case 10.2: Touch Interaction**

**Steps:**
1. Use touch to interact with map
2. Pinch-zoom on map
3. Drag map around
4. Type in chat on mobile

**Expected:**
- ✅ All touch gestures work
- ✅ Zoom works with pinch
- ✅ Map remains responsive
- ✅ Chat input accessible

---

## 🔍 DEBUGGING TIPS

### **Browser Console Debugging**

```javascript
// Check if map initialized
window.map
// Should return Leaflet map object

// Check current graph data
window.currentGraphData
// Should show graph, nodePositions, nodeMetadata

// Check navigation state
window.navigationState
// Should show current mode, rooms, coordinates

// Check floor plans loaded
window.floorPlans
// Should show all building data

// Manually trigger navigation (Feature 1)
window.showRouteBuildingM('M1_6', 'M1_9')

// Manually start click mode (Feature 2)
window.startMapNavigation()

// Clear route
window.clearRoute()
```

### **Flask Console Output**

Expected log messages:
```
✅ Building M room configuration loaded
✅ Map initialized
✅ Building M Floor 1 loaded successfully
🗺️ Navigation detected: Room_1003 → Room_1018
📝 Using only textual information for: How do I...
🎯 Showing route: M1_6 → M1_9
```

### **Network Debugging**

**Check requests:**
```
POST /chat - Chat message
POST /api/navigation/parse - Parsing endpoint
POST /api/navigation/from-clicks - Map clicks
GET /api/navigation/rooms - Room list
```

Use browser DevTools Network tab to verify all calls succeed (200 status).

---

## ✅ SIGN-OFF CHECKLIST

**Core Functionality:**
- [ ] Feature 1 (Chat → Map) fully functional
- [ ] Feature 2 (Map → Chat) can be triggered manually
- [ ] Room aliases work correctly
- [ ] Pathfinding algorithm works
- [ ] Visual display works (markers, path, zoom)

**API Integration:**
- [ ] `/chat` endpoint detects navigation
- [ ] `/api/navigation/parse` works
- [ ] `/api/navigation/from-clicks` works
- [ ] `/api/navigation/rooms` works

**UI/UX:**
- [ ] Mode indicator displays correctly
- [ ] Error messages are user-friendly
- [ ] Map is responsive
- [ ] Chat is responsive
- [ ] Responsive design works on mobile

**Error Handling:**
- [ ] Invalid rooms handled gracefully
- [ ] Missing coordinates handled
- [ ] Network errors caught
- [ ] Gemini API errors handled

**Performance:**
- [ ] Page loads in <3 seconds
- [ ] Navigation requests respond in <2 seconds
- [ ] Map remains smooth after navigation
- [ ] No memory leaks on repeated use

---

## 🎯 TEST SCENARIOS

### **Scenario A: First-Time User**
```
1. User opens app
2. Sees: Chat on left, map on right
3. Reads: "Welcome!" message
4. Types: "How do I get to the bathroom?"
5. System asks for clarification or shows directions
✓ Test passes if navigation occurs
```

### **Scenario B: Experienced User**
```
1. User knows room numbers
2. Types: "1003 to 1049"
3. System recognizes pattern
4. Shows full route immediately
✓ Test passes if route appears instantly
```

### **Scenario C: Visual User**
```
1. User prefers clicking
2. Triggers map navigation mode
3. Clicks start location
4. Clicks end location
5. Chatbot shows directions
✓ Test passes if all steps work smoothly
```

---

## 📊 EXPECTED TEST RESULTS

**Feature 1 Success Rate:** >95%
- Simple navigation: 100%
- With aliases: 90%+
- Complex queries: 80%+

**Feature 2 Success Rate:** >90%
- Click-based selection: 100%
- Route calculation: 100%
- Chat integration: 100%

**API Success Rate:** >98%
- Request validation: 100%
- Response formatting: 100%
- Error handling: 95%+

---

**Last Updated:** November 14, 2025
**Status:** Ready for manual testing
