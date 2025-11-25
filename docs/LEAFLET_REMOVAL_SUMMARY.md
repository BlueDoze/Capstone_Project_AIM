# LeafletJS Removal Summary

**Date**: November 25, 2025  
**Branch**: feature/backend-parse-data

## Overview

Removed all LeafletJS dependencies and references from the Fanshawe Navigator project. The system now exclusively uses the React-based SVG mapping implementation from the `Fanshawe_Navigator-main` frontend.

## What Was Removed

### 1. Directories
- `/map/` - Entire directory containing:
  - GeoJSON files
  - Floor plan images  
  - PDFs
  - Leaflet-based HTML viewers

### 2. Scripts
- `scripts/generation/generate_route_viewer.py` - Script that generated standalone HTML visualizations using Leaflet CDN

### 3. Frontend Dependencies
- `leaflet` (^1.9.4) - Removed from `Fanshawe_Navigator-main/frontend/package.json`
- `react-leaflet` (^4.2.1) - Removed from `Fanshawe_Navigator-main/frontend/package.json`

### 4. Static Files
- `static/map-controller.js` - Old Leaflet map controller (no longer needed)

### 5. Backend References
- Removed `LeafletJS/campus.geojson` path from GeoJSON search in `src/api/app.py`
- Cleaned up old Flask route references to `/map/<path:path>`

## What Remains

### Current Mapping Implementation
The project now uses **only** the React-based SVG mapping system located in:
- `Fanshawe_Navigator-main/frontend/src/components/`
- Building M floor plan with SVG overlay
- Real-time path visualization
- Click-based navigation
- Manual room center coordinates

### Active Components
- React frontend with SVG-based mapping
- Flask backend API for navigation logic
- Building M room configuration (`config/building_m_rooms.json`)
- Navigation API endpoints (`/api/navigation/*`)
- Chat-to-Map and Map-to-Chat integration

## Documentation Updates

The following documentation files still reference LeafletJS but are marked as legacy/historical:
- `README.md` - Main project documentation
- `MAP_FIX.md` - Debugging guide
- `API_URL_FIX.md` - API configuration
- `BUILDING_HOVER_PROPOSAL.md` - Feature proposal

**Note**: These files are intentionally left as-is for historical reference. They document the evolution of the mapping system and may be useful for understanding past decisions.

## Migration Path

No migration is needed. The React SVG mapping system has been the primary implementation since its deployment. LeafletJS components were legacy artifacts that were no longer in use.

## Benefits of Removal

1. **Cleaner Dependencies**: Removed 2 npm packages (`leaflet`, `react-leaflet`)
2. **Reduced Confusion**: Single mapping implementation (SVG-based)
3. **Smaller Bundle**: Frontend build is now lighter
4. **Easier Maintenance**: No need to maintain dual mapping systems
5. **Better Performance**: SVG rendering is more efficient for floor plans

## Future Considerations

If outdoor campus mapping is needed in the future, consider:
- Mapbox GL JS (modern, WebGL-based)
- OpenLayers (open-source alternative)
- Google Maps API (if budget allows)

However, for indoor floor plan navigation, the current SVG approach is ideal and should be maintained.

## Commit Information

```bash
git add -A
git commit -m "Remove LeafletJS dependencies and legacy map components"
git push origin feature/backend-parse-data
```

## References

- Original Mapping System: `Fanshawe_Navigator-main/frontend/`
- Building M Config: `config/building_m_rooms.json`
- Navigation API: `src/api/app.py` (lines 1450-1600)
- SVG Map Implementation: React components in frontend

---

**Author**: GitHub Copilot  
**Reviewed**: Pending
