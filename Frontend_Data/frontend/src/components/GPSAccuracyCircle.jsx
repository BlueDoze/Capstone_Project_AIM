/**
 * GPSAccuracyCircle.jsx
 * 
 * Visual indicator for GPS accuracy with color-coded feedback
 * Ported from gps_toggle.html GPS accuracy visualization
 */

import React from 'react';
import { Circle } from 'react-leaflet';

const GPS_ACCURACY_THRESHOLD = 20; // meters

/**
 * GPS Accuracy Circle Component
 * Shows a circle around GPS position indicating accuracy
 * Blue = good signal (< threshold), Red = poor signal (> threshold)
 * 
 * @param {Object} position - GPS position {lat, lng}
 * @param {Number} accuracy - Accuracy in meters
 * @param {Number} threshold - Accuracy threshold (default: 20m)
 * @param {Boolean} show - Whether to show the circle
 */
export default function GPSAccuracyCircle({
  position,
  accuracy,
  threshold = GPS_ACCURACY_THRESHOLD,
  show = true
}) {
  if (!show || !position || !accuracy) {
    return null;
  }

  const isPoorSignal = accuracy > threshold;

  return (
    <Circle
      center={[position.lat, position.lng]}
      radius={accuracy}
      pathOptions={{
        color: isPoorSignal ? '#ff4444' : '#0066cc',
        fillColor: isPoorSignal ? '#ff4444' : '#0066cc',
        fillOpacity: 0.15,
        weight: 2,
        dashArray: isPoorSignal ? '5, 5' : null
      }}
    />
  );
}

/**
 * GPS Status Display Component
 * Shows GPS status text with accuracy information
 */
export function GPSStatusDisplay({ 
  isTracking, 
  accuracy, 
  altitude, 
  isPoorSignal,
  error 
}) {
  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <strong>❌ GPS Error:</strong> {error}
      </div>
    );
  }

  if (!isTracking) {
    return (
      <div className="bg-gray-100 border border-gray-400 text-gray-700 px-4 py-3 rounded">
        📍 GPS Inactive
      </div>
    );
  }

  if (isPoorSignal) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded">
        <strong>⚠️ Poor GPS Signal</strong><br />
        Accuracy: ±{accuracy?.toFixed(0)}m<br />
        <small>(Threshold: {GPS_ACCURACY_THRESHOLD}m)</small><br />
        <strong>Using last known position</strong>
      </div>
    );
  }

  return (
    <div className="bg-green-100 border border-green-400 text-green-800 px-4 py-3 rounded">
      <strong>✅ GPS Active</strong><br />
      Accuracy: ±{accuracy?.toFixed(0)}m
      {altitude !== null && (
        <>
          <br />
          Altitude: {altitude.toFixed(1)}m
        </>
      )}
    </div>
  );
}
