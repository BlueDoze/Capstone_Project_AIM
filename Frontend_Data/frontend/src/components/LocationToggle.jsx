import React from 'react';
import useGeolocation from '../hooks/useGeolocation';

/**
 * LocationToggle Component
 * 
 * GPS tracking toggle with visual feedback and accuracy monitoring
 * Based on LeafletJS gps_toggle.html implementation
 */
export default function LocationToggle({ 
  locationMode,
  onModeChange,
  onPositionUpdate,
  accuracyThreshold = 20,
  className = ''
}) {
  const {
    position,
    accuracy,
    altitude,
    error,
    isTracking,
    isPoorSignal,
    startTracking,
    stopTracking,
  } = useGeolocation({ accuracyThreshold });

  // Update parent component when GPS position changes
  React.useEffect(() => {
    if (position && !isPoorSignal) {
      onPositionUpdate(position, accuracy); // Pass accuracy to parent
    }
  }, [position, isPoorSignal, accuracy, onPositionUpdate]);

  const handleToggle = () => {
    if (locationMode === 'manual') {
      // Switch to GPS mode
      const started = startTracking();
      if (started) {
        onModeChange('gps');
      }
    } else {
      // Switch to manual mode
      stopTracking();
      onModeChange('manual');
    }
  };

  const getStatusText = () => {
    if (locationMode === 'manual') {
      return '📍 Manual Mode';
    }

    if (!isTracking) {
      return '🔄 Starting GPS...';
    }

    if (error) {
      if (error.code === 'POOR_ACCURACY') {
        return (
          <>
            ⚠️ Poor GPS Signal
            <br />
            Accuracy: ±{accuracy?.toFixed(0)}m
            <br />
            (Threshold: {accuracyThreshold}m)
            <br />
            <b>Using last known position</b>
          </>
        );
      }
      return `❌ ${error.message}`;
    }

    let statusText = `✅ GPS Active\nAccuracy: ±${accuracy?.toFixed(0)}m`;
    if (altitude !== null) {
      statusText += `\nAltitude: ${altitude.toFixed(1)}m`;
    }
    return statusText;
  };

  const getButtonStyle = () => {
    if (locationMode === 'gps') {
      return 'bg-red-500 hover:bg-red-600';
    }
    return 'bg-blue-600 hover:bg-blue-700';
  };

  const getButtonText = () => {
    return locationMode === 'manual' ? '🛰️ Switch to GPS' : '📍 Switch to Manual';
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-3 min-w-[200px] ${className}`}>
      <h4 className="text-sm font-semibold mb-2">📍 Location Mode</h4>
      
      <button
        onClick={handleToggle}
        className={`w-full ${getButtonStyle()} text-white font-medium py-2 px-4 rounded transition-colors text-sm mb-2`}
      >
        {getButtonText()}
      </button>

      <div className="text-xs text-gray-600 leading-relaxed whitespace-pre-line">
        {getStatusText()}
      </div>

      {/* Visual indicator for poor signal */}
      {isPoorSignal && (
        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-300 rounded text-xs text-yellow-800">
          ⚠️ Signal too weak for accurate positioning
        </div>
      )}

      {/* Position debug info (can be removed in production) */}
      {position && !isPoorSignal && (
        <div className="mt-2 p-2 bg-green-50 border border-green-300 rounded text-xs text-green-800">
          📍 {position.lat.toFixed(6)}, {position.lng.toFixed(6)}
        </div>
      )}
    </div>
  );
}
