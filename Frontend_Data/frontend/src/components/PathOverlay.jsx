/**
 * PathOverlay.jsx
 * 
 * Visual path overlay with turn-by-turn directions
 * Shows navigation route with styled polyline and waypoint markers
 */

import React from 'react';
import { Polyline, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

/**
 * Path Overlay Component
 * Renders navigation path with animated polyline
 * 
 * @param {Array} pathCoordinates - Array of [lat, lng] coordinate pairs
 * @param {String} pathColor - Color of the path line (default: #2ecc71)
 * @param {Number} pathWeight - Width of the path line (default: 5)
 * @param {Boolean} animated - Whether to animate the path (default: true)
 * @param {Object} startMarker - Start position {lat, lng, label}
 * @param {Object} endMarker - End position {lat, lng, label}
 * @param {Array} waypoints - Array of waypoint objects {lat, lng, label}
 */
export default function PathOverlay({
  pathCoordinates = [],
  pathColor = '#2ecc71',
  pathWeight = 5,
  animated = true,
  startMarker = null,
  endMarker = null,
  waypoints = []
}) {
  if (!pathCoordinates || pathCoordinates.length < 2) {
    return null;
  }

  return (
    <>
      {/* Main path line */}
      <Polyline
        positions={pathCoordinates}
        pathOptions={{
          color: pathColor,
          weight: pathWeight,
          opacity: 0.8,
          dashArray: animated ? '10, 10' : null,
          lineCap: 'round',
          lineJoin: 'round'
        }}
        className={animated ? 'animate-dash' : ''}
      />

      {/* Start marker */}
      {startMarker && (
        <Marker
          position={[startMarker.lat, startMarker.lng]}
          icon={createCustomIcon('🟢', '#27ae60')}
        >
          <Popup>
            <div className="text-sm font-semibold">
              🟢 Start
              {startMarker.label && <div className="text-xs">{startMarker.label}</div>}
            </div>
          </Popup>
        </Marker>
      )}

      {/* End marker */}
      {endMarker && (
        <Marker
          position={[endMarker.lat, endMarker.lng]}
          icon={createCustomIcon('🔴', '#e74c3c')}
        >
          <Popup>
            <div className="text-sm font-semibold">
              🔴 Destination
              {endMarker.label && <div className="text-xs">{endMarker.label}</div>}
            </div>
          </Popup>
        </Marker>
      )}

      {/* Waypoint markers */}
      {waypoints && waypoints.map((waypoint, index) => (
        <Marker
          key={`waypoint-${index}`}
          position={[waypoint.lat, waypoint.lng]}
          icon={createCustomIcon(`${index + 1}`, '#f39c12')}
        >
          <Popup>
            <div className="text-sm">
              <strong>Waypoint {index + 1}</strong>
              {waypoint.label && <div className="text-xs">{waypoint.label}</div>}
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
}

/**
 * Create custom marker icon
 */
function createCustomIcon(text, color) {
  return L.divIcon({
    className: 'custom-nav-marker',
    html: `
      <div style="
        width: 30px;
        height: 30px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      ">
        ${text}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15]
  });
}

/**
 * Multi-Building Path Overlay
 * Renders path segments across multiple buildings with building transitions
 */
export function MultiBuildingPathOverlay({ segments = [] }) {
  if (!segments || segments.length === 0) {
    return null;
  }

  const colors = ['#2ecc71', '#3498db', '#9b59b6', '#e67e22'];

  return (
    <>
      {segments.map((segment, index) => (
        <React.Fragment key={`segment-${index}`}>
          <PathOverlay
            pathCoordinates={segment.coordinates}
            pathColor={colors[index % colors.length]}
            pathWeight={5}
            animated={true}
          />
          {segment.buildingTransition && (
            <Marker
              position={segment.transitionPoint}
              icon={createCustomIcon('🚪', '#34495e')}
            >
              <Popup>
                <div className="text-sm font-semibold">
                  Building Transition
                  <div className="text-xs">
                    {segment.fromBuilding} → {segment.toBuilding}
                  </div>
                </div>
              </Popup>
            </Marker>
          )}
        </React.Fragment>
      ))}
    </>
  );
}

/**
 * Turn-by-Turn Direction Marker
 */
export function DirectionMarker({ position, direction, instruction }) {
  let icon = '➡️';
  if (direction === 'left') icon = '⬅️';
  if (direction === 'right') icon = '➡️';
  if (direction === 'straight') icon = '⬆️';
  if (direction === 'stairs') icon = '🪜';
  if (direction === 'elevator') icon = '🛗';

  return (
    <Marker
      position={[position.lat, position.lng]}
      icon={createCustomIcon(icon, '#3498db')}
    >
      <Popup>
        <div className="text-sm">
          <strong>{instruction}</strong>
        </div>
      </Popup>
    </Marker>
  );
}
