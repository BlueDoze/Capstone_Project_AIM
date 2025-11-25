# Building Info Hover Tooltips - Implementation Proposal

## 🎯 Objective

Display building information from `predios_info_english.json` when users hover their mouse over buildings on the campus map.

---

## 📊 Current State Analysis

### What Already Works

**Frontend** ([App.jsx:193-226](Fanshawe_Navigator-main/frontend/src/App.jsx#L193-L226)):
- ✅ Click on building → Fetches info from `/api/predios/${ref}/info`
- ✅ Hover effects → Changes building styling (weight, opacity)
- ✅ Building info popup component → Displays detailed info (lines 424-435)
- ✅ GeoJSON data with 22 buildings loaded

**Backend** ([app.py:1060-1099](src/api/app.py#L1060-L1099)):
- ⚠️ Endpoint `/api/predios/<ref>/info` exists but returns **mock data**
- ❌ Not connected to `predios_info_english.json` file

**Data** ([predios_info_english.json](Fanshawe_Navigator-main/backend/dados/predios_info_english.json)):
- ✅ 13 buildings with complete information
- ✅ Structure: nome, ref, andares, descricao, facilidades, salas_principais, horario_funcionamento

### What Needs Implementation

1. **Backend**: Connect endpoint to real JSON data
2. **Frontend**: Add hover tooltip functionality (currently only click works)

---

## 🏗️ Implementation Options

### Option A: Hover Tooltip + Click Popup (Recommended)

**UX Flow**:
- **Hover** → Small tooltip with basic info (nome, ref, descricao)
- **Click** → Full popup with detailed info (andares, facilidades, salas_principais, horario)

**Pros**:
- ✅ Best UX - quick preview on hover, details on click
- ✅ Keeps existing click functionality
- ✅ No accidental information overload
- ✅ Mobile-friendly (click still works on touch devices)

**Cons**:
- ⚠️ Two API calls (one on hover, one on click)
- ⚠️ Slightly more complex code

**Visual Example**:
```
Hover:
┌─────────────────────┐
│ Building A          │
│ Main administration │
└─────────────────────┘

Click:
┌───────────────────────────────────┐
│ Building A                    [X] │
├───────────────────────────────────┤
│ Main administration and classroom │
│ building                          │
│                                   │
│ Floors: 1, 2, 3                   │
│                                   │
│ Facilities:                       │
│ • Classrooms                      │
│ • Administrative Offices          │
│ • Restrooms                       │
│ • Elevators                       │
│                                   │
│ Hours: Mon-Fri 7am - 10pm        │
└───────────────────────────────────┘
```

---

### Option B: Hover Tooltip Only (Simple)

**UX Flow**:
- **Hover** → Full tooltip with all building info
- **Click** → No action (or same as hover)

**Pros**:
- ✅ Simplest implementation
- ✅ Single API call
- ✅ Immediate information access

**Cons**:
- ❌ Tooltip can be too large and cover map
- ❌ Harder to read while mouse is moving
- ❌ Accidentally triggers on map navigation
- ❌ Less mobile-friendly

---

### Option C: Hybrid with Caching

**UX Flow**:
- **First hover** → Fetch data from API, show basic tooltip, cache data
- **Subsequent hovers** → Use cached data instantly
- **Click** → Show detailed popup with cached data (no API call)

**Pros**:
- ✅ Best performance after first load
- ✅ Reduces server load
- ✅ Instant response on subsequent interactions
- ✅ Can prefetch all building data on map load

**Cons**:
- ⚠️ More complex state management
- ⚠️ Need cache invalidation strategy
- ⚠️ Initial load slower if prefetching all buildings

---

## 🛠️ Recommended Implementation (Option A)

### Step 1: Backend - Load Real JSON Data

**File**: `src/api/app.py`

**Add global variable** (near line 50-100 where other globals are):
```python
# Building info cache
building_info_data = None

def load_building_info():
    """Load building information from JSON file"""
    global building_info_data

    if building_info_data is not None:
        return building_info_data

    possible_paths = [
        project_root / 'Fanshawe_Navigator-main' / 'backend' / 'dados' / 'predios_info_english.json',
        project_root / 'src' / 'config' / 'predios_info_english.json',
    ]

    for json_path in possible_paths:
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                building_info_data = json.load(f)
                print(f"✅ Building info loaded from {json_path}")
                return building_info_data

    print("⚠️ Building info JSON not found")
    return {}
```

**Update endpoint** (replace mock data around line 1060-1099):
```python
@app.route("/api/predios/<ref>/info", methods=['GET'])
def get_building_info(ref):
    """Retorna informações detalhadas de um prédio"""
    try:
        # Load building data
        building_data = load_building_info()

        # Get info for specific building
        if ref.upper() in building_data:
            info = building_data[ref.upper()]

            return jsonify({
                "success": True,
                "info": info
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Building {ref} not found"
            }), 404

    except Exception as e:
        print(f"❌ Error getting building info: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

**Call on startup** (in the initialization section):
```python
# Around line 1200-1300 where app starts
if __name__ == '__main__':
    initialize_models()
    initialize_image_cache()
    load_building_info()  # ← Add this

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
```

---

### Step 2: Frontend - Add Hover Tooltip

**File**: `Fanshawe_Navigator-main/frontend/src/App.jsx`

**Import Leaflet Tooltip** (if not already imported, around line 1-10):
```javascript
import { MapContainer, TileLayer, GeoJSON, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet'; // Make sure this is imported
```

**Update `onEachFeature` function** (replace lines 193-226):
```javascript
const onEachFeature = (feature, layer) => {
  if (feature.properties) {
    const props = feature.properties;
    const nome = props.name || props.nome || 'Building';
    const ref = props.ref;

    // HOVER TOOLTIP - Basic info
    if (ref) {
      layer.on('mouseover', async function(e) {
        // Visual feedback
        this.setStyle({
          weight: 5,
          fillOpacity: 0.5
        });

        // Fetch building info for tooltip
        try {
          const response = await fetch(`${API_URL}/api/predios/${ref}/info`);
          const data = await response.json();

          if (data.success && data.info) {
            const tooltipContent = `
              <div style="min-width: 200px;">
                <strong style="font-size: 14px; color: #1e40af;">${data.info.nome}</strong><br/>
                <span style="font-size: 12px; color: #6b7280;">${data.info.descricao || ''}</span>
              </div>
            `;

            layer.bindTooltip(tooltipContent, {
              permanent: false,
              sticky: true,
              className: 'building-tooltip',
              opacity: 0.95
            }).openTooltip();
          }
        } catch (error) {
          console.error('Error fetching building info for tooltip:', error);
        }
      });

      layer.on('mouseout', function() {
        // Reset visual style
        this.setStyle(getFeatureStyle(feature));

        // Close tooltip
        layer.unbindTooltip();
      });
    }

    // CLICK POPUP - Detailed info (keep existing functionality)
    layer.on('click', async () => {
      if (ref) {
        try {
          const response = await fetch(`${API_URL}/api/predios/${ref}/info`);
          const data = await response.json();

          if (data.success && data.info) {
            setBuildingInfo(data);
          }
        } catch (error) {
          console.error('Error fetching building info:', error);
        }
      }
    });
  }
};
```

**Add CSS for tooltip styling** (create or update CSS file):
```css
/* Add to src/index.css or App.css */
.building-tooltip {
  background: white !important;
  border: 2px solid #BE1E2D !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
  padding: 8px 12px !important;
}

.building-tooltip::before {
  border-top-color: #BE1E2D !important;
}
```

**Update Building Info Popup** (enhance existing popup at lines 424-435):
```javascript
{buildingInfo && buildingInfo.info && (
  <div className="absolute top-4 right-4 bg-white rounded-lg shadow-2xl p-6 max-w-md z-10 border-2 border-fanshawe-red">
    <div className="flex justify-between items-start mb-4">
      <h4 className="text-xl font-bold text-gray-800">
        {buildingInfo.info.nome}
      </h4>
      <button
        onClick={() => setBuildingInfo(null)}
        className="text-gray-500 hover:text-fanshawe-red transition-colors"
      >
        <X size={20} />
      </button>
    </div>

    {/* Description */}
    {buildingInfo.info.descricao && (
      <p className="text-gray-600 mb-4">{buildingInfo.info.descricao}</p>
    )}

    {/* Floors */}
    {buildingInfo.info.andares && buildingInfo.info.andares.length > 0 && (
      <div className="mb-4">
        <h5 className="font-semibold text-gray-700 mb-2">Floors:</h5>
        <p className="text-gray-600">{buildingInfo.info.andares.join(', ')}</p>
      </div>
    )}

    {/* Facilities */}
    {buildingInfo.info.facilidades && buildingInfo.info.facilidades.length > 0 && (
      <div className="mb-4">
        <h5 className="font-semibold text-gray-700 mb-2">Facilities:</h5>
        <ul className="list-disc list-inside text-gray-600">
          {buildingInfo.info.facilidades.map((facility, idx) => (
            <li key={idx}>{facility}</li>
          ))}
        </ul>
      </div>
    )}

    {/* Main Rooms */}
    {buildingInfo.info.salas_principais && buildingInfo.info.salas_principais.length > 0 && (
      <div className="mb-4">
        <h5 className="font-semibold text-gray-700 mb-2">Main Rooms:</h5>
        <div className="space-y-1">
          {buildingInfo.info.salas_principais.slice(0, 5).map((sala, idx) => (
            <div key={idx} className="text-sm text-gray-600">
              <span className="font-medium">{sala.numero}</span> - {sala.tipo} (Floor {sala.andar})
            </div>
          ))}
          {buildingInfo.info.salas_principais.length > 5 && (
            <p className="text-xs text-gray-500 italic">
              + {buildingInfo.info.salas_principais.length - 5} more rooms
            </p>
          )}
        </div>
      </div>
    )}

    {/* Operating Hours */}
    {buildingInfo.info.horario_funcionamento && (
      <div className="mb-2">
        <h5 className="font-semibold text-gray-700 mb-2">Operating Hours:</h5>
        <p className="text-gray-600">{buildingInfo.info.horario_funcionamento}</p>
      </div>
    )}
  </div>
)}
```

---

## 🧪 Testing Plan

### Backend Testing

```bash
# Test endpoint with real data
curl http://localhost:5000/api/predios/A/info | jq

# Expected response:
{
  "success": true,
  "info": {
    "nome": "Building A",
    "ref": "A",
    "andares": [1, 2, 3],
    "descricao": "Main administration and classroom building",
    "facilidades": ["Classrooms", "Administrative Offices", ...],
    "salas_principais": [...],
    "horario_funcionamento": "Monday to Friday: 7am - 10pm"
  }
}
```

### Frontend Testing

1. **Hover Test**:
   - Open map
   - Hover over Building A
   - Should see small tooltip with name and description
   - Tooltip should follow mouse cursor

2. **Click Test**:
   - Click on Building A
   - Should see detailed popup with all information
   - Popup should stay open until X is clicked

3. **Multiple Buildings**:
   - Hover over different buildings (A, B, C, F, G)
   - Each should show correct information
   - No data mixing between buildings

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Hovers Mouse Over Building                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: onEachFeature → mouseover event                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Change building style (visual feedback)          │  │
│  │  2. Extract building ref (e.g., "A")                 │  │
│  │  3. fetch(`/api/predios/A/info`)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Flask Backend: /api/predios/<ref>/info                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Call load_building_info()                        │  │
│  │  2. Load predios_info_english.json (cached)         │  │
│  │  3. Look up building by ref                          │  │
│  │  4. Return JSON with building data                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Response Handler                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Parse JSON response                              │  │
│  │  2. Create tooltip HTML content                      │  │
│  │  3. Bind tooltip to layer                            │  │
│  │  4. Open tooltip at cursor position                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                 │
                 ▼
         🏢 TOOLTIP APPEARS!
```

---

## 🔄 Alternative: Prefetch All Data (Performance Optimization)

For even better performance, prefetch all building data when map loads:

```javascript
// In App.jsx, add useEffect when map opens
useEffect(() => {
  if (showMap && !buildingDataCache) {
    // Prefetch all building info
    const buildings = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'SC', 'T'];

    Promise.all(
      buildings.map(ref =>
        fetch(`${API_URL}/api/predios/${ref}/info`)
          .then(r => r.json())
          .then(data => ({ ref, data }))
      )
    ).then(results => {
      const cache = {};
      results.forEach(({ ref, data }) => {
        if (data.success) {
          cache[ref] = data.info;
        }
      });
      setBuildingDataCache(cache);
      console.log('✅ Building data prefetched:', Object.keys(cache).length);
    });
  }
}, [showMap]);

// Then use cache in onEachFeature instead of fetching
layer.on('mouseover', function() {
  if (buildingDataCache && buildingDataCache[ref]) {
    const info = buildingDataCache[ref];
    const tooltipContent = `...`;
    layer.bindTooltip(tooltipContent).openTooltip();
  }
});
```

---

## ✅ Implementation Checklist

### Backend
- [ ] Add `load_building_info()` function
- [ ] Update `/api/predios/<ref>/info` endpoint to use real data
- [ ] Call `load_building_info()` on server startup
- [ ] Test endpoint returns correct data for all buildings (A-T)

### Frontend
- [ ] Update `onEachFeature` to add mouseover event
- [ ] Create tooltip with basic info (nome, descricao)
- [ ] Keep click event for detailed popup
- [ ] Add CSS styling for tooltip
- [ ] Enhance popup component with all fields
- [ ] Test hover on multiple buildings
- [ ] Test click functionality still works
- [ ] Rebuild frontend: `bash build_frontend.sh`

### Testing
- [ ] Backend returns real data (not mock)
- [ ] Tooltip appears on hover with correct info
- [ ] Tooltip follows cursor
- [ ] Tooltip closes on mouseout
- [ ] Click popup shows detailed info
- [ ] No console errors
- [ ] Works on all 13 buildings

---

## 📝 Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| [src/api/app.py](src/api/app.py) | Add `load_building_info()`, update endpoint | ~50 new lines |
| [App.jsx](Fanshawe_Navigator-main/frontend/src/App.jsx) | Update `onEachFeature`, enhance popup | Lines 193-226, 424-435 |
| CSS file | Add tooltip styling | ~15 new lines |

---

## 🚀 Estimated Implementation Time

- **Backend**: 15 minutes
- **Frontend**: 30 minutes
- **Testing**: 15 minutes
- **Total**: ~1 hour

---

## 💡 Recommendation

**Use Option A (Hover Tooltip + Click Popup)** because:

1. ✅ Best user experience (quick preview + detailed view)
2. ✅ Leverages existing click functionality
3. ✅ Mobile-friendly (tooltips don't work well on touch, click still works)
4. ✅ Performance is good (backend caches JSON, one load at startup)
5. ✅ Matches common mapping UX patterns (Google Maps, etc.)

**Next Steps**:
1. Get user approval on approach
2. Implement backend changes
3. Implement frontend changes
4. Test thoroughly
5. Commit and push

---

**Status**: ⏳ **AWAITING USER APPROVAL**

**Question for User**: Should I proceed with implementing Option A (Hover Tooltip + Click Popup)?
