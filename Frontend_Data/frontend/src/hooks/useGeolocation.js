import { useState, useEffect, useRef } from 'react';

/**
 * useGeolocation Hook
 * 
 * Manages GPS tracking with accuracy validation and error handling
 * Based on LeafletJS gps_toggle.html implementation
 * 
 * @param {Object} options - Configuration options
 * @param {number} options.accuracyThreshold - Maximum acceptable accuracy in meters (default: 20)
 * @param {boolean} options.enableHighAccuracy - Use high accuracy mode (default: true)
 * @param {number} options.timeout - Position timeout in ms (default: 10000)
 * @param {number} options.maximumAge - Max age of cached position (default: 5000)
 * 
 * @returns {Object} Geolocation state and controls
 */
export default function useGeolocation(options = {}) {
  const {
    accuracyThreshold = 20,
    enableHighAccuracy = true,
    timeout = 10000,
    maximumAge = 5000,
  } = options;

  const [position, setPosition] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [altitude, setAltitude] = useState(null);
  const [error, setError] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const [isPoorSignal, setIsPoorSignal] = useState(false);
  const watchIdRef = useRef(null);

  const startTracking = () => {
    if (!navigator.geolocation) {
      setError({ message: 'GPS not supported by your browser', code: 'NOT_SUPPORTED' });
      return false;
    }

    setIsTracking(true);
    setError(null);

    watchIdRef.current = navigator.geolocation.watchPosition(
      // Success callback
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const acc = pos.coords.accuracy;
        const alt = pos.coords.altitude;

        console.log(`📍 GPS Update: [${lat}, ${lng}] Accuracy: ±${acc.toFixed(0)}m`);

        setAccuracy(acc);
        setAltitude(alt);

        // Check accuracy threshold
        if (acc > accuracyThreshold) {
          console.warn(
            `⚠️ GPS accuracy too low: ${acc.toFixed(0)}m (threshold: ${accuracyThreshold}m)`
          );
          setIsPoorSignal(true);
          setError({
            message: `Poor GPS signal (±${acc.toFixed(0)}m)`,
            code: 'POOR_ACCURACY',
            accuracy: acc,
            threshold: accuracyThreshold,
          });
          // Don't update position if accuracy is too poor
          return;
        }

        // Good signal - update position
        setIsPoorSignal(false);
        setError(null);
        setPosition({ lat, lng });
      },
      // Error callback
      (err) => {
        console.error('GPS Error:', err);
        
        let errorMessage = 'GPS tracking failed';
        let errorCode = 'UNKNOWN';

        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMessage = 'Location permission denied';
            errorCode = 'PERMISSION_DENIED';
            break;
          case err.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable';
            errorCode = 'POSITION_UNAVAILABLE';
            break;
          case err.TIMEOUT:
            errorMessage = 'Location request timed out';
            errorCode = 'TIMEOUT';
            break;
          default:
            errorMessage = err.message || 'Unknown GPS error';
        }

        setError({ message: errorMessage, code: errorCode, original: err });
        setIsTracking(false);
      },
      // Options
      {
        enableHighAccuracy,
        timeout,
        maximumAge,
      }
    );

    return true;
  };

  const stopTracking = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsTracking(false);
    setIsPoorSignal(false);
    setError(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return {
    position,
    accuracy,
    altitude,
    error,
    isTracking,
    isPoorSignal,
    startTracking,
    stopTracking,
  };
}
