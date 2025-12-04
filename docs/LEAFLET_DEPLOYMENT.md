# LeafletJS Integration - Deployment & Setup Guide

## Overview of Changes

This integration adds comprehensive indoor navigation capabilities to the Fanshawe Navigator by incorporating the LeafletJS folder's advanced features into the React application.

## Files Modified

### 1. Docker Configuration
- **`Dockerfile`**: Added steps to copy LeafletJS assets to frontend public directory
- **`docker-compose.yml`**: Added read-only volume mount for LeafletJS directory

### 2. Frontend Configuration
- **`Frontend_Data/frontend/package.json`**: Added Leaflet dependencies
  - `leaflet@^1.9.4`
  - `react-leaflet@^4.2.1`
  - `leaflet-rotate@^0.2.8`

### 3. Backend Configuration
- **`src/api/app.py`**: Added Flask route to serve LeafletJS assets

### 4. New React Components (Frontend_Data/frontend/src/)
- **`components/IndoorMapView.jsx`**: Core indoor map display with floor plans
- **`components/FloorSelector.jsx`**: Floor selection and navigation controls
- **`components/IndoorNavigationContainer.jsx`**: Complete navigation system
- **`utils/navigationUtils.js`**: Pathfinding and navigation utilities

### 5. Documentation
- **`Frontend_Data/INDOOR_NAVIGATION_GUIDE.md`**: Comprehensive developer guide

## Deployment Steps

### Step 1: Stop Existing Containers
```powershell
docker-compose down
```

### Step 2: Clean Docker System (Optional but Recommended)
```powershell
docker system prune -f
```

### Step 3: Rebuild Docker Image
```powershell
docker-compose build --no-cache
```

This will:
1. Install Node.js dependencies including Leaflet packages
2. Copy LeafletJS assets to `/app/Frontend_Data/frontend/public/leaflet-assets/`
3. Build the React frontend with Vite
4. Copy the built frontend to the Flask static directory

### Step 4: Start Services
```powershell
docker-compose up -d
```

### Step 5: Verify Deployment

Check that assets are accessible:
```powershell
# Check if container is running
docker ps

# Check if LeafletJS assets were copied
docker exec fanshawe-navigator ls /app/Frontend_Data/frontend/public/leaflet-assets

# Verify Flask route
curl http://localhost:8081/leaflet-assets/campus.geojson
```

### Step 6: Test in Browser
1. Navigate to `http://localhost:8081`
2. Open browser DevTools (F12)
3. Test asset loading:
   ```javascript
   fetch('/leaflet-assets/campus.geojson').then(r => r.json()).then(console.log)
   ```

## Development Workflow

### Local Development (Without Docker)

1. **Install Frontend Dependencies**
   ```powershell
   cd Frontend_Data/frontend
   npm install
   ```

2. **Start Frontend Dev Server**
   ```powershell
   npm run dev
   ```

3. **Start Flask Backend (Separate Terminal)**
   ```powershell
   cd ../../
   python src/api/app.py
   ```

4. **Access Application**
   - Frontend: `http://localhost:5173` (Vite dev server)
   - Backend API: `http://localhost:8081`
   - LeafletJS Assets: `http://localhost:8081/leaflet-assets/...`

### Docker Development (Recommended)

1. **Build and Start**
   ```powershell
   docker-compose up --build
   ```

2. **View Logs**
   ```powershell
   docker-compose logs -f
   ```

3. **Access Container Shell**
   ```powershell
   docker exec -it fanshawe-navigator /bin/bash
   ```

4. **Hot Reload Changes**
   - Data changes: Automatically reflected (volume mounted)
   - Code changes: Rebuild required
   - Config changes: Restart container

## Asset Serving Configuration

### Production (Docker Build)
Assets are copied during build:
```
LeafletJS/ → /app/Frontend_Data/frontend/public/leaflet-assets/
```

Frontend can access as:
```javascript
const url = '/leaflet-assets/Floorplans/Building M/M1.svg';
```

### Development (Volume Mount)
Assets are accessible via Flask route:
```
./LeafletJS:/app/LeafletJS:ro (read-only mount)
```

Flask serves from:
```python
@app.route('/leaflet-assets/<path:path>')
def serve_leaflet_assets(path):
    return send_from_directory('/app/LeafletJS', path)
```

## Verifying the Integration

### 1. Check Package Installation
```powershell
docker exec fanshawe-navigator npm list leaflet
docker exec fanshawe-navigator npm list react-leaflet
docker exec fanshawe-navigator npm list leaflet-rotate
```

### 2. Check Asset Availability
```powershell
# Check floor plans
docker exec fanshawe-navigator ls /app/LeafletJS/Floorplans

# Check navigation data
docker exec fanshawe-navigator cat /app/LeafletJS/JSON/all_node_data.json
```

### 3. Test Flask Route
```powershell
curl http://localhost:8081/leaflet-assets/campus.geojson
curl http://localhost:8081/leaflet-assets/JSON/building_connections.JSON
```

### 4. Test Frontend Build
```powershell
docker exec fanshawe-navigator ls /app/Frontend_Data/frontend/dist/leaflet-assets
```

## Common Issues & Solutions

### Issue: "Cannot find module 'leaflet'"
**Solution:** Rebuild Docker image to install npm packages
```powershell
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Issue: Floor plans not loading (404 errors)
**Solution:** Verify assets were copied during build
```powershell
docker exec fanshawe-navigator ls /app/Frontend_Data/frontend/public/leaflet-assets/Floorplans
```

### Issue: "Module not found: Can't resolve 'react-leaflet'"
**Solution:** Check package.json has correct dependencies
```powershell
docker exec fanshawe-navigator cat /app/Frontend_Data/frontend/package.json
```

### Issue: Map not displaying
**Solution:** Import Leaflet CSS in your component
```javascript
import 'leaflet/dist/leaflet.css';
```

### Issue: Navigation data not found
**Solution:** Check Flask route is working
```powershell
curl http://localhost:8081/leaflet-assets/JSON/all_node_data.json
```

## Performance Optimization

### 1. Asset Caching
Configure Flask to cache static assets:
```python
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year
```

### 2. Compress Assets
Enable gzip compression for SVG files:
```python
from flask_compress import Compress
Compress(app)
```

### 3. Lazy Load Floor Plans
Load floor plans only when user navigates to indoor view:
```javascript
const [floorPlan, setFloorPlan] = useState(null);

useEffect(() => {
  if (showIndoorMap) {
    loadFloorPlanData(building, floor).then(setFloorPlan);
  }
}, [showIndoorMap, building, floor]);
```

## Environment Variables

Add to `.env` file if needed:
```env
GEMINI_API_KEY=your_api_key_here
FLASK_ENV=production
PORT=8081

# Optional: Configure asset paths
LEAFLET_ASSETS_PATH=/app/LeafletJS
```

## Security Considerations

1. **Read-Only Mount**: LeafletJS volume is mounted as read-only (`:ro`)
2. **Asset Validation**: Flask serves only from designated directory
3. **CORS**: Configure if frontend is on different domain
4. **File Types**: Only serve expected file types (SVG, JSON, GeoJSON)

## Monitoring & Debugging

### Enable Debug Mode
```python
# In src/api/app.py
app.config['DEBUG'] = True  # Only for development!
```

### Check Container Logs
```powershell
docker-compose logs -f web
```

### Monitor Network Requests
Use browser DevTools Network tab to verify:
- Leaflet CSS/JS loading
- Floor plan SVG requests
- Navigation JSON data requests

### Verify Build Output
```powershell
# Check Vite build output
docker-compose logs | Select-String "vite"

# Check for npm errors
docker-compose logs | Select-String "npm ERR"
```

## Rollback Procedure

If issues occur, rollback to previous version:

1. **Restore Previous Image**
   ```powershell
   docker images  # Find previous image ID
   docker tag <previous-image-id> your-image-name
   docker-compose up
   ```

2. **Git Revert Changes**
   ```powershell
   git revert HEAD
   docker-compose build
   docker-compose up
   ```

## Next Steps

1. **Test Indoor Navigation**: Use IndoorNavigationContainer component
2. **Integrate with UI**: Add to your main App.jsx
3. **Add Room Search**: Connect room database to navigation
4. **User Positioning**: Implement indoor positioning system
5. **Multi-Building Routes**: Add building-to-building navigation

## Support & Resources

- **Leaflet Documentation**: https://leafletjs.com/reference.html
- **React Leaflet**: https://react-leaflet.js.org/docs/start-introduction
- **Docker Compose**: https://docs.docker.com/compose/

## Checklist

- [ ] Docker image built successfully
- [ ] Leaflet packages installed (`npm list` shows leaflet)
- [ ] LeafletJS assets accessible via Flask route
- [ ] Floor plans visible in browser
- [ ] Navigation data loads correctly
- [ ] No console errors in browser
- [ ] Container health check passing
- [ ] Components render without errors
- [ ] Documentation reviewed
- [ ] Team trained on new components

## Version Information

- **Leaflet**: 1.9.4
- **React Leaflet**: 4.2.1
- **Leaflet Rotate**: 0.2.8
- **React**: 18.3.1
- **Vite**: 5.3.1
- **Flask**: (check requirements.txt)
- **Python**: 3.11

---

**Date Created**: December 4, 2025  
**Last Updated**: December 4, 2025  
**Maintainer**: Development Team
