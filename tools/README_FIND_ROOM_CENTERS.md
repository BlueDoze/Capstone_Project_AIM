# 🗺️ Room Center Finder Tools

## Overview

There are **two versions** of the room center finder tool, depending on your workflow:

---

## Option 1: `find_room_centers.html` (Original)

**Status**: SVG coordinates captured WITHOUT rotation

**When to use**:
- You want pure SVG coordinates
- You will manually transform them afterward
- You understand the coordinate mismatch

**Workflow**:
1. Open: `http://localhost:8081/tools/find_room_centers.html`
2. Select a room
3. Click on SVG to capture coordinates (e.g., `X: 402.13, Y: 514.13`)
4. **Copy coordinates manually**
5. **You must transform them yourself** before using

**Note**: ⚠️ Coordinates are pure SVG without any transformation

---

## Option 2: `find_room_centers_no_rotation.html` (NEW - RECOMMENDED)

**Status**: SVG coordinates captured WITHOUT rotation + Clear guidance

**When to use**:
- You want a guided workflow
- You want explicit warnings NOT to use raw coordinates
- You want direct integration with the Coordinate Compensator

**Workflow**:
1. Open: `http://localhost:8081/tools/find_room_centers_no_rotation.html`
2. Select a room
3. Click on SVG to capture coordinates (e.g., `X: 402.13, Y: 514.13`)
4. Copy the JSON
5. **Automatically directed to use Coordinate Compensator**:
   - Go to: `http://localhost:8081/tools/coordinate_compensator.html`
   - Paste coordinates
   - Get transformed result
   - Copy to `building_m_rooms.json`

**Features**:
- ✅ Orange badge showing "NO ROTATION"
- ✅ Prominent warnings about not using raw coordinates
- ✅ Step-by-step next steps guidance
- ✅ Clear information about rotation difference

---

## Comparison

| Feature | Version 1 | Version 2 |
|---------|-----------|----------|
| **Tool Name** | `find_room_centers.html` | `find_room_centers_no_rotation.html` |
| **Color Scheme** | Blue | Orange |
| **Warnings** | Minimal | Prominent |
| **Guidance** | Basic | Detailed with next steps |
| **Rotation Applied** | No | No |
| **Best For** | Manual workflow | Automated workflow |
| **URL** | `/tools/find_room_centers.html` | `/tools/find_room_centers_no_rotation.html` |

---

## Complete Workflow: From Capture to Application

### Using Version 2 (RECOMMENDED):

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Capture Raw Coordinates                         │
│ Tool: find_room_centers_no_rotation.html               │
│ Result: X=402.13, Y=514.13 (NO rotation)               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: Transform Coordinates                           │
│ Tool: coordinate_compensator.html                       │
│ Input: X=402.13, Y=514.13                              │
│ Output: X=365.45, Y=542.89 (WITH rotation compensation)│
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: Apply to Configuration                          │
│ File: config/building_m_rooms.json                      │
│ "Room_1003": { "x": 365.45, "y": 542.89 }             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: Test in Application                             │
│ URL: http://localhost:8081                              │
│ Result: Room 1003 appears at CORRECT position ✅         │
└─────────────────────────────────────────────────────────┘
```

---

## Understanding the Rotation Issue

### The Problem

The application uses a **21.3° rotated coordinate system** to align the map geographically:

```
find_room_centers.html captures:
  Room_1003: X=402.13, Y=514.13  (SVG pure, NO rotation)

But application expects:
  Room_1003: X=365.45, Y=542.89  (WITH 21.3° rotation + scale + offset)

Result: ❌ Room appears in WRONG position
```

### The Solution

Use the **Coordinate Compensator** to automatically:
- Calculate the transformation matrix
- Apply rotation, scaling, and offset
- Convert all coordinates at once

```
Input (pure SVG):     X=402.13, Y=514.13
                              ↓
                    [Transformation Matrix]
                    x' = a*x + b*y + e
                    y' = c*x + d*y + f
                              ↓
Output (rotated):     X=365.45, Y=542.89 ✅
```

---

## Key Differences Explained

### `find_room_centers.html`

✅ Simple interface
❌ No explicit warnings about rotation
❌ Users might paste raw coordinates into config (WRONG!)

### `find_room_centers_no_rotation.html`

✅ Clear "NO ROTATION" badge
✅ Multiple warnings about not using raw coordinates
✅ Built-in next steps to use Compensator
✅ Color-coded UI (orange = warning)
✅ Better for new users

---

## Migration Guide

If you were using Version 1:

### ❌ What you were probably doing (WRONG):
```
find_room_centers.html → Copy coordinates → Paste directly in building_m_rooms.json
                                           → Rooms in WRONG positions ❌
```

### ✅ What you should do now (CORRECT):
```
find_room_centers_no_rotation.html → Compensator → building_m_rooms.json
                                    → Rooms in RIGHT positions ✅
```

---

## Troubleshooting

### Q: Which version should I use?
**A**: Use `find_room_centers_no_rotation.html` - it's clearer and guides you through the compensation process.

### Q: Why are there two versions?
**A**: To provide flexibility. Version 1 is for users who understand the rotation issue. Version 2 is for everyone else.

### Q: What if I already have coordinates from Version 1?
**A**: No problem! Just paste them into the Coordinate Compensator and apply the transformation.

### Q: Can I use raw coordinates directly?
**A**: ❌ **NO!** The application uses a rotated coordinate system. Always use the Compensator first.

---

## Technical Details

### Coordinate System Explanation

```
find_room_centers tools:
  - ViewBox: 0 0 816 1056
  - Rotation: NONE (0°)
  - System: Pure SVG coordinates

Application map:
  - ViewBox: 0 0 816 1056 (same)
  - Rotation: 21.3° + bilinear interpolation
  - System: Rotated SVG with geo-alignment
  - Corner transformation: Applied
```

### Why Bilinear Interpolation?

The application uses **bilinear interpolation** to map SVG coordinates to geo-coordinates (lat/lng). But it applies this with **rotated corners**, not pure corners.

This is why simple rotation won't work - you need the **affine transformation matrix** which captures:
1. Rotation (21.3°)
2. Scaling (if any)
3. Offset (translation in X and Y)

---

## Quick Links

- **Room Finder (No Rotation)**: `http://localhost:8081/tools/find_room_centers_no_rotation.html`
- **Room Finder (Original)**: `http://localhost:8081/tools/find_room_centers.html`
- **Coordinate Compensator**: `http://localhost:8081/tools/coordinate_compensator.html`
- **Coordinate Diagnostic**: `http://localhost:8081/tools/coordinate_diagnostic.html`

---

## Summary

| Task | Tool |
|------|------|
| Capture raw SVG coordinates | `find_room_centers_no_rotation.html` |
| Transform coordinates | `coordinate_compensator.html` |
| Diagnose coordinate issues | `coordinate_diagnostic.html` |
| Verify embeddings quality | Run `validate_map_embeddings.py` |

**Recommended Flow**: Version 2 → Compensator → Config → Application

