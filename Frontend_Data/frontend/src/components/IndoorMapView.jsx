import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, ImageOverlay, Marker, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Custom hook for map rotation (if using leaflet-rotate)
function useMapRotation(map, bearing) {
  useEffect(() => {
    if (map && typeof map.setBearing === 'function') {
      map.setBearing(bearing || 0);
    }
  }, [map, bearing]);
}

// Component to handle image overlay bounds
function FloorPlanOverlay({ imageUrl, bounds, opacity = 1.0 }) {
  return imageUrl ? (
    <ImageOverlay url={imageUrl} bounds={bounds} opacity={opacity} />
  ) : null;
}

// Component for navigation nodes (pathfinding)
function NavigationNodes({ nodes, onNodeClick, highlightedNodes = [] }) {
  if (!nodes || nodes.length === 0) return null;

  return nodes.map((node, idx) => {
    const isHighlighted = highlightedNodes.includes(node.id);
    const icon = L.divIcon({
      className: 'navigation-node',
      html: `<div style="
        width: ${isHighlighted ? '12px' : '8px'};
        height: ${isHighlighted ? '12px' : '8px'};
        background: ${isHighlighted ? '#e74c3c' : '#3498db'};
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      "></div>`,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });

    return (
      <Marker
        key={node.id || idx}
        position={node.position}
        icon={icon}
        eventHandlers={{
          click: () => onNodeClick && onNodeClick(node),
        }}
      />
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
function MapController({ center, zoom, bounds }) {
  const map = useMap();

  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, zoom || 18);
    }
  }, [center, zoom, bounds, map]);

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
 * - center: Map center [lat, lng]
 * - zoom: Initial zoom level
 * - rotation: Map rotation in degrees (requires leaflet-rotate)
 */
export default function IndoorMapView({
  building,
  floor,
  floorPlanUrl,
  bounds,
  nodes = [],
  path = [],
  userPosition = null,
  onNodeClick,
  center = [0, 0],
  zoom = 18,
  rotation = 0,
  highlightedNodes = [],
  className = '',
}) {
  const mapRef = useRef(null);
  const [mapInstance, setMapInstance] = useState(null);

  // Use map rotation if available
  useMapRotation(mapInstance, rotation);

  // Custom user position marker
  const userIcon = L.divIcon({
    className: 'user-position-marker',
    html: `<div style="
      width: 16px;
      height: 16px;
      background: #3498db;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 10px rgba(52, 152, 219, 0.5);
      animation: pulse 2s infinite;
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

  return (
    <div className={`indoor-map-container ${className}`} style={{ width: '100%', height: '100%' }}>
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
        <MapController center={center} zoom={zoom} bounds={bounds} />

        {/* Floor plan overlay */}
        {floorPlanUrl && bounds && (
          <FloorPlanOverlay imageUrl={floorPlanUrl} bounds={bounds} opacity={0.9} />
        )}

        {/* Navigation nodes */}
        <NavigationNodes
          nodes={nodes}
          onNodeClick={onNodeClick}
          highlightedNodes={highlightedNodes}
        />

        {/* Navigation path */}
        {path && path.length > 0 && <NavigationPath path={path} />}

        {/* User position marker */}
        {userPosition && (
          <Marker position={userPosition} icon={userIcon} />
        )}
      </MapContainer>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.2);
            opacity: 0.7;
          }
        }
      `}</style>
    </div>
  );
}
