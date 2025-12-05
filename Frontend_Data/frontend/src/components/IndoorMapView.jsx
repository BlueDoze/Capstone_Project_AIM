import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, ImageOverlay, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import GPSAccuracyCircle from './GPSAccuracyCircle';
import NavigationNodesOverlay from './NavigationNodesOverlay';
import PathOverlay from './PathOverlay';

// Custom hook for map rotation (if using leaflet-rotate)
function useMapRotation(map, bearing) {
  useEffect(() => {
    if (map && typeof map.setBearing === 'function') {
      map.setBearing(bearing || 0);
    }
  }, [map, bearing]);
}

// Custom SVG Overlay component with rotated bounds support
function SVGFloorPlanOverlay({ imageUrl, rotatedCorners, opacity = 0.7 }) {
  const map = useMap();
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!imageUrl || !rotatedCorners || rotatedCorners.length !== 4) {
      return;
    }

    // Remove existing overlay
    if (overlayRef.current) {
      map.removeLayer(overlayRef.current);
      overlayRef.current = null;
    }

    // Fetch and create SVG overlay
    fetch(imageUrl)
      .then(response => response.text())
      .then(svgText => {
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
        const svgElement = svgDoc.documentElement;

        // Convert rotated corners to Leaflet LatLngBounds format
        const bounds = L.latLngBounds(rotatedCorners.map(c => [c.lat, c.lng]));

        // Create SVG overlay with rotated bounds
        const overlay = L.svgOverlay(svgElement, bounds, {
          interactive: true,
          opacity: opacity
        });

        overlay.addTo(map);
        overlayRef.current = overlay;
        
        console.log('✅ SVG overlay added with rotated corners:', rotatedCorners);
      })
      .catch(err => {
        console.error('❌ Error loading SVG floor plan:', err);
      });

    // Cleanup on unmount
    return () => {
      if (overlayRef.current) {
        map.removeLayer(overlayRef.current);
      }
    };
  }, [imageUrl, rotatedCorners, opacity, map]);

  return null;
}

// Component to handle image overlay bounds (legacy fallback)
function FloorPlanOverlay({ imageUrl, bounds, opacity = 1.0 }) {
  return imageUrl ? (
    <ImageOverlay url={imageUrl} bounds={bounds} opacity={opacity} />
  ) : null;
}

// Component for navigation nodes (pathfinding)
function NavigationNodes({ nodes, onNodeClick, highlightedNodes = [] }) {
  if (!nodes || nodes.length === 0) return null;

  const [hoveredNode, setHoveredNode] = useState(null);

  return nodes.map((node, idx) => {
    const isHighlighted = highlightedNodes.includes(node.id);
    const isHovered = hoveredNode === node.id;
    
    // Determine node color based on type
    let nodeColor = '#3498db'; // default blue
    if (isHighlighted) nodeColor = '#e74c3c'; // red for highlighted
    else if (node.type === 'room') nodeColor = '#27ae60'; // green for rooms
    else if (node.type === 'stairs') nodeColor = '#f39c12'; // orange for stairs
    else if (node.type === 'elevator') nodeColor = '#9b59b6'; // purple for elevators
    else if (node.type === 'entrance') nodeColor = '#16a085'; // teal for entrances
    
    const nodeSize = isHighlighted ? 12 : (isHovered ? 10 : 8);
    
    const icon = L.divIcon({
      className: 'navigation-node',
      html: `<div style="
        width: ${nodeSize}px;
        height: ${nodeSize}px;
        background: ${nodeColor};
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        cursor: pointer;
        transition: all 0.2s ease;
        ${isHovered ? 'transform: scale(1.3);' : ''}
      "></div>`,
      iconSize: [nodeSize, nodeSize],
      iconAnchor: [nodeSize / 2, nodeSize / 2],
    });

    return (
      <Marker
        key={node.id || idx}
        position={node.position}
        icon={icon}
        eventHandlers={{
          click: () => onNodeClick && onNodeClick(node),
          mouseover: () => setHoveredNode(node.id),
          mouseout: () => setHoveredNode(null),
        }}
      >
        {/* Tooltip for node information */}
        {isHovered && (
          <Popup>
            <div className="text-sm">
              <strong>{node.name || node.id}</strong>
              {node.type && <div className="text-xs text-gray-600">Type: {node.type}</div>}
              {node.represents && <div className="text-xs text-gray-600">Room: {node.represents}</div>}
              <div className="mt-2 text-xs text-blue-600 cursor-pointer">
                Click to navigate here →
              </div>
            </div>
          </Popup>
        )}
      </Marker>
    );
  });
}

// Component for drawing the navigation path
function NavigationPath({ path, color = '#2ecc71', weight = 4 }) {
  if (!path || path.length < 2) return null;

  return (
    <Polyline
      positions={path}
      pathOptions={{
        color: color,
        weight: weight,
        opacity: 0.8,
        dashArray: '10, 10',
        lineCap: 'round',
        lineJoin: 'round',
      }}
    />
  );
}

// Map controller component
function MapController({ center, zoom, bounds, onMapClick }) {
  const map = useMap();

  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, zoom || 18);
    }
  }, [center, zoom, bounds, map]);

  // Handle map clicks
  useEffect(() => {
    if (onMapClick) {
      const handleClick = (e) => {
        onMapClick(e.latlng);
      };
      
      map.on('click', handleClick);
      
      return () => {
        map.off('click', handleClick);
      };
    }
  }, [map, onMapClick]);

  return null;
}

/**
 * IndoorMapView Component
 * 
 * Displays indoor floor plans with SVG overlays, navigation nodes, and pathfinding
 * 
 * Props:
 * - building: Building code (e.g., 'A', 'B', 'M')
 * - floor: Floor level (e.g., '1', '2', '3')
 * - floorPlanUrl: URL to the SVG/image floor plan
 * - bounds: [[south, west], [north, east]] coordinates for image overlay
 * - nodes: Array of navigation nodes { id, position: [lat, lng], type, connections }
 * - path: Array of [lat, lng] coordinates for the current route
 * - userPosition: Current user position [lat, lng]
 * - onNodeClick: Callback when a node is clicked
 * - onMapClick: Callback when map is clicked (for manual position setting)
 * - center: Map center [lat, lng]
 * - zoom: Initial zoom level
 * - rotation: Map rotation in degrees (requires leaflet-rotate)
 */
export default function IndoorMapView({
  building,
  floor,
  floorPlanUrl,
  bounds,
  rotatedCorners,
  nodes = [],
  path = [],
  userPosition = null,
  onNodeClick,
  onMapClick,
  center = [0, 0],
  zoom = 18,
  rotation = 0,
  highlightedNodes = [],
  className = '',
  gpsAccuracy = null, // New: GPS accuracy in meters
  showGPSCircle = false, // New: Toggle GPS accuracy circle
  enableNodeInteraction = true, // New: Enable/disable node clicking
  startPoint = null, // Start point for route selection
  endPoint = null, // End point for route selection
}) {
  const mapRef = useRef(null);
  const [mapInstance, setMapInstance] = useState(null);

  // Use map rotation if available
  useMapRotation(mapInstance, rotation);

  // Custom user position marker
  const userIcon = L.divIcon({
    className: 'user-position-marker',
    html: `<div style="
      width: 20px;
      height: 20px;
      background: #3498db;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 15px rgba(52, 152, 219, 0.6);
    ">
      <div style="
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 10px;
        height: 10px;
        background: white;
        border-radius: 50%;
      "></div>
    </div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
  
  // Start point marker (green A)
  const startIcon = L.divIcon({
    className: 'start-point-marker',
    html: `<div style="
      width: 32px;
      height: 32px;
      background: #27ae60;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 15px rgba(39, 174, 96, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      color: white;
      font-size: 18px;
    ">A</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
  
  // End point marker (red B)
  const endIcon = L.divIcon({
    className: 'end-point-marker',
    html: `<div style="
      width: 32px;
      height: 32px;
      background: #e74c3c;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 15px rgba(231, 76, 60, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      color: white;
      font-size: 18px;
    ">B</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });

  return (
    <div className={`indoor-map-container ${className}`} style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
        attributionControl={false}
        ref={mapRef}
        whenCreated={setMapInstance}
      >
        {/* Map controller */}
        <MapController center={center} zoom={zoom} bounds={bounds} onMapClick={onMapClick} />

        {/* Base map tiles - OpenStreetMap */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={22}
        />

        {/* Floor plan overlay - SVG with rotated corners */}
        {floorPlanUrl && rotatedCorners && (
          <SVGFloorPlanOverlay 
            imageUrl={floorPlanUrl} 
            rotatedCorners={rotatedCorners} 
            opacity={0.7} 
          />
        )}

        {/* GPS Accuracy Circle - New Component */}
        {showGPSCircle && userPosition && gpsAccuracy && (
          <GPSAccuracyCircle 
            position={userPosition} 
            accuracy={gpsAccuracy} 
          />
        )}

        {/* Navigation nodes - Using new NavigationNodesOverlay */}
        {enableNodeInteraction && nodes && nodes.length > 0 && (
          <NavigationNodesOverlay
            nodes={nodes}
            onNodeClick={onNodeClick}
            highlightedNodes={highlightedNodes}
          />
        )}

        {/* Navigation path - Using new PathOverlay */}
        {path && path.length > 0 && (
          <PathOverlay 
            path={path}
            startPosition={path[0]}
            endPosition={path[path.length - 1]}
          />
        )}

        {/* User position marker */}
        {userPosition && !startPoint && (
          <Marker 
            position={userPosition} 
            icon={userIcon}
            draggable={true}
            eventHandlers={{
              dragend: (e) => {
                const newPos = e.target.getLatLng();
                console.log('User position updated:', newPos);
              }
            }}
          >
            <Popup>
              <div className="text-sm">
                <strong>📍 Your Location</strong>
                <div className="text-xs text-gray-600 mt-1">
                  Drag to adjust position
                </div>
              </div>
            </Popup>
          </Marker>
        )}
        
        {/* Start point marker (green A) */}
        {startPoint && startPoint.position && (
          <Marker 
            position={startPoint.position} 
            icon={startIcon}
          >
            <Popup>
              <div className="text-sm">
                <strong>🟢 Start Point</strong>
              </div>
            </Popup>
          </Marker>
        )}
        
        {/* End point marker (red B) */}
        {endPoint && endPoint.position && (
          <Marker 
            position={endPoint.position} 
            icon={endIcon}
          >
            <Popup>
              <div className="text-sm">
                <strong>🔴 Destination</strong>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Info overlay for interactive hints */}
      {nodes && nodes.length > 0 && (
        <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 rounded-lg shadow-lg p-3 text-xs max-w-xs z-[1000]">
          <div className="font-semibold mb-1">💡 Interactive Map Tips:</div>
          <ul className="space-y-1 text-gray-700">
            <li>• Hover over nodes to see details</li>
            <li>• Click any node to navigate there</li>
            <li>• Drag your position marker to adjust location</li>
            <li>• Use mouse wheel to zoom</li>
          </ul>
        </div>
      )}

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            box-shadow: 0 0 15px rgba(52, 152, 219, 0.6);
          }
          50% {
            box-shadow: 0 0 25px rgba(52, 152, 219, 0.9);
          }
        }
        .user-position-marker > div {
          animation: pulse 2s infinite;
        }
      `}</style>
    </div>
  );
}
