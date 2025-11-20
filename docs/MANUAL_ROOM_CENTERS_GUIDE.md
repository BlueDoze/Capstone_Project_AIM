# Manual Room Center Configuration Guide

## 📍 Where to Edit Room Centers

You can edit room center coordinates in **TWO ways**:

### Method 1: Using the Visual Tool (RECOMMENDED) ✨

1. **Open the Visual Tool**:
   ```
   http://localhost:8081/tools/find_room_centers.html
   ```
   
2. **Follow the on-screen instructions**:
   - Click on a room name button (e.g., "Room_1003")
   - Click on the SVG map at the exact center point of that room
   - The tool will show you the SVG coordinates
   - Copy the JSON format provided

3. **Paste into Configuration File**:
   - Open: `config/building_m_rooms.json`
   - Find the `"roomCentersSVG"` section
   - Replace the empty `{}` with your coordinates

### Method 2: Manual Editing (ADVANCED) 📝

Edit the file directly: **`config/building_m_rooms.json`**

Location in file: Look for the `"roomCentersSVG"` section at the bottom

---

## 📋 Configuration File Format

### File: `config/building_m_rooms.json`

```json
{
  "Building M": {
    "aliases": { ... },
    "roomToNode": { ... },
    "roomDescriptions": { ... },
    "navigationInstructions": { ... },
    
    "roomCentersSVG": {
      "_comment": "Manual override for room center coordinates in SVG space",
      "_instructions": "Format: {x, y} in SVG units. Leave empty {} for auto-calculation",
      
      "Room_1003": { "x": 250.5, "y": 600.3 },
      "Room_1004": {},  // Empty = use automatic calculation
      "Room_1006": { "x": 180.2, "y": 615.8 },
      "Room_1018": {},
      "Room_1030": {},
      "Room_1033": {},
      "Room_1035": {},
      "Room_1037": {},
      "Room_1040": {},
      "Room_1041": {},
      "Room_1045": {},
      "Room_1049": {},
      "Bathroom-Men": {},
      "Bathroom-Women": {},
      "Bathroom-Accessible": {},
      "Elevator-M": {},
      "Stairs_1": {},
      "Stairs_2": {},
      "Stairs_3": {}
    }
  }
}
```

---

## 🎯 How It Works

### Priority System:

1. **Manual Override** (if coordinates are provided):
   ```json
   "Room_1003": { "x": 250.5, "y": 600.3 }
   ```
   ✅ Uses your precise coordinates

2. **Automatic Calculation** (if empty object or missing):
   ```json
   "Room_1004": {}
   ```
   ✅ Calculates center from room polygon using `getBBox()`

### Console Output:

- **Manual**: `📌 Using MANUAL center for Room_1003: (250.5, 600.3)`
- **Auto**: `🏢 Room Room_1004 AUTO center in SVG: (234.56, 567.89)`

---

## 🔧 Step-by-Step: Adding Manual Coordinates

### Example: Setting Room_1003 Center

1. **Find the SVG coordinates** (use visual tool or Inkscape):
   - Open M1_official.svg
   - Measure the center point of Room_1003
   - Note coordinates: `x: 250.5, y: 600.3`

2. **Edit the JSON file**:
   ```json
   "Room_1003": { "x": 250.5, "y": 600.3 }
   ```

3. **Save the file**

4. **Refresh your browser** (no server restart needed!)

5. **Test**: Navigate to Room_1003 and verify marker position

---

## 🖼️ Using the Visual Tool

### Quick Start:

1. **Start the server** (if not already running):
   ```bash
   cd /home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM
   bash devserver.sh
   ```

2. **Open the tool**:
   ```
   http://localhost:8081/tools/find_room_centers.html
   ```

3. **Select and Click**:
   - Click a room button (e.g., "Room_1003")
   - The room will be highlighted on the SVG
   - Click at the center of the highlighted room
   - A red dot appears where you clicked

4. **Copy the JSON**:
   ```
   "Room_1003": { "x": 250.5, "y": 600.3 }
   ```

5. **Repeat for all rooms** you want to adjust

6. **Click "Show All Coordinates"** to see all your selections

7. **Copy and paste into** `config/building_m_rooms.json`

---

## 📊 Coordinate System Reference

### SVG Coordinate Space:
- **Origin (0,0)**: Top-left corner of SVG canvas
- **X-axis**: Increases to the right
- **Y-axis**: Increases downward
- **Units**: SVG user units (typically pixels)
- **ViewBox**: Check `viewBox="0 0 816 1056"` in M1_official.svg

### Example Coordinates:
```json
{
  "Room_1003": { "x": 250.5, "y": 600.3 },
  "Room_1018": { "x": 180.2, "y": 450.8 },
  "Elevator-M": { "x": 300.0, "y": 620.0 }
}
```

---

## 🧪 Testing Your Changes

### 1. Check Console Output:
Open browser DevTools (F12) and look for:
```
📍 Loaded room centers: 3 manual overrides, 16 will use auto-calculation
📌 Using MANUAL center for Room_1003: (250.5, 600.3)
```

### 2. Test Navigation:
```
Chat: "Navigate from Room 1003 to Room 1018"
```
- Green marker should be at YOUR specified center for Room_1003
- If Room_1018 is empty `{}`, marker uses automatic calculation

### 3. Visual Verification:
- Marker should appear **inside** the room polygon
- Should be visually centered
- Should not be in the corridor

---

## 📝 Current Configuration Location

**File Path**: 
```
/home/luizeng/Documents/fanshawe_repo/Capstone_Project_AIM/config/building_m_rooms.json
```

**Section to Edit**:
```json
"roomCentersSVG": {
  // Add your coordinates here
}
```

---

## 💡 Tips for Finding Good Centers

1. **Visual Balance**: Choose a point that looks visually centered
2. **Avoid Walls**: Stay away from room boundaries
3. **Consider Shape**: For irregular rooms, find the "visual" center
4. **Test Multiple Points**: Click several times to find the best spot
5. **Use Gridlines**: If your SVG editor has gridlines, enable them

---

## 🔄 Updating Process

### When you change coordinates:

1. ✅ **Edit** `config/building_m_rooms.json`
2. ✅ **Save** the file
3. ✅ **Refresh** browser (Ctrl+F5 or Cmd+Shift+R)
4. ✅ **Test** navigation
5. ❌ **No server restart needed!**

### API Endpoint:
The configuration is served via:
```
http://localhost:8081/api/navigation/room-centers
```

---

## 🐛 Troubleshooting

### Coordinates not updating?
1. Check JSON syntax (no trailing commas!)
2. Verify file saved correctly
3. Hard refresh browser (Ctrl+F5)
4. Check browser console for errors

### Marker still in wrong place?
1. Verify room ID matches exactly
2. Check coordinates are not empty `{}`
3. Look for console logs showing manual vs auto
4. Test with visual tool to find better coordinates

### Tool not loading?
1. Check server is running on port 8081
2. Verify SVG path: `LeafletJS/Floorplans/Building M/M1_official.svg`
3. Check browser console for errors

---

## 📚 Complete Example

### Before (automatic calculation):
```json
"roomCentersSVG": {
  "Room_1003": {},
  "Room_1018": {},
  "Room_1030": {}
}
```

### After (with manual coordinates):
```json
"roomCentersSVG": {
  "Room_1003": { "x": 250.5, "y": 600.3 },
  "Room_1018": { "x": 180.2, "y": 450.8 },
  "Room_1030": { "x": 420.7, "y": 380.5 }
}
```

### Result:
- Room_1003: ✅ Uses manual center (250.5, 600.3)
- Room_1018: ✅ Uses manual center (180.2, 450.8)
- Room_1030: ✅ Uses manual center (420.7, 380.5)
- All other rooms: ✅ Use automatic calculation

---

## 🎯 Summary

| What | Where | How |
|------|-------|-----|
| **Edit Coordinates** | `config/building_m_rooms.json` | Add `{"x": X, "y": Y}` |
| **Visual Tool** | `http://localhost:8081/tools/find_room_centers.html` | Click and copy |
| **Test Changes** | Refresh browser | No server restart |
| **Check Logs** | Browser Console (F12) | See manual vs auto |

---

**Quick Access Links:**
- Config File: `config/building_m_rooms.json` → `roomCentersSVG` section
- Visual Tool: `http://localhost:8081/tools/find_room_centers.html`
- API Endpoint: `http://localhost:8081/api/navigation/room-centers`
