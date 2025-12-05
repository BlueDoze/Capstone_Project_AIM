/**
 * useGPSAccuracy.js
 * 
 * Custom hook for GPS location tracking with accuracy monitoring
 * Ported from gps_toggle.html lines 100-180
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const GPS_ACCURACY_THRESHOLD = 20; // meters

/**
 * Hook for GPS location tracking with accuracy filtering
 * @param {Object} options - Configuration options
 * @param {Number} options.accuracyThreshold - Maximum acceptable accuracy in meters (default: 20)
 * @param {Boolean} options.enableHighAccuracy - Request high accuracy GPS (default: true)
 * @param {Number} options.maximumAge - Maximum age of cached position (default: 5000ms)
 * @param {Number} options.timeout - GPS timeout (default: 10000ms)
 */
export function useGPSAccuracy(options = {}) {
  const {
    accuracyThreshold = GPS_ACCURACY_THRESHOLD,
    enableHighAccuracy = true,
    maximumAge = 5000,
    timeout = 10000
  } = options;

  const [position, setPosition] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [altitude, setAltitude] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const [isPoorSignal, setIsPoorSignal] = useState(false);
  const [error, setError] = useState(null);
  const [lastGoodPosition, setLastGoodPosition] = useState(null);

  const watchIdRef = useRef(null);

  const handleGPSSuccess = useCallback((geoPosition) => {
    const lat = geoPosition.coords.latitude;
    const lng = geoPosition.coords.longitude;
    const acc = geoPosition.coords.accuracy;
    const alt = geoPosition.coords.altitude;

    console.log(`📍 GPS Update: [${lat}, ${lng}] Accuracy: ±${acc.toFixed(0)}m`);

    setAccuracy(acc);
    setAltitude(alt);

    // Check accuracy threshold
    if (acc > accuracyThreshold) {
      console.warn(`⚠️ GPS accuracy too low: ${acc.toFixed(0)}m (threshold: ${accuracyThreshold}m)`);
      setIsPoorSignal(true);
      // Don't update position, keep using last good position
      return;
    }

    // Good signal - update position
    const newPosition = { lat, lng };
    setPosition(newPosition);
    setLastGoodPosition(newPosition);
    setIsPoorSignal(false);
    setError(null);
  }, [accuracyThreshold]);

  const handleGPSError = useCallback((err) => {
    console.error('❌ GPS Error:', err.message);
    
    let errorMessage = 'GPS error';
    switch (err.code) {
      case err.PERMISSION_DENIED:
        errorMessage = 'GPS permission denied';
        break;
      case err.POSITION_UNAVAILABLE:
        errorMessage = 'GPS position unavailable';
        break;
      case err.TIMEOUT:
        errorMessage = 'GPS timeout';
        break;
      default:
        errorMessage = err.message;
    }

    setError(errorMessage);
    setIsPoorSignal(true);
  }, []);

  const startTracking = useCallback(() => {
    if (!navigator.geolocation) {
      setError('GPS not supported by this browser');
      return;
    }

    if (watchIdRef.current !== null) {
      console.log('⚠️ GPS tracking already active');
      return;
    }

    console.log('🛰️ Starting GPS tracking...');
    setIsTracking(true);
    setError(null);

    const geoOptions = {
      enableHighAccuracy,
      maximumAge,
      timeout
    };

    watchIdRef.current = navigator.geolocation.watchPosition(
      handleGPSSuccess,
      handleGPSError,
      geoOptions
    );

    console.log(`✅ GPS watch started (ID: ${watchIdRef.current})`);
  }, [enableHighAccuracy, maximumAge, timeout, handleGPSSuccess, handleGPSError]);

  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      console.log(`🛑 GPS tracking stopped (ID: ${watchIdRef.current})`);
      watchIdRef.current = null;
    }
    setIsTracking(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return {
    position: isPoorSignal ? lastGoodPosition : position,
    accuracy,
    altitude,
    isTracking,
    isPoorSignal,
    error,
    startTracking,
    stopTracking,
    hasGoodSignal: !isPoorSignal && accuracy !== null && accuracy <= accuracyThreshold
  };
}

/**
 * Hook for single GPS position request (not continuous tracking)
 */
export function useGPSPosition(options = {}) {
  const {
    accuracyThreshold = GPS_ACCURACY_THRESHOLD,
    enableHighAccuracy = true,
    maximumAge = 5000,
    timeout = 10000
  } = options;

  const [position, setPosition] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getPosition = useCallback(() => {
    if (!navigator.geolocation) {
      setError('GPS not supported by this browser');
      return Promise.reject(new Error('GPS not supported'));
    }

    setLoading(true);
    setError(null);

    const geoOptions = {
      enableHighAccuracy,
      maximumAge,
      timeout
    };

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (geoPosition) => {
          const lat = geoPosition.coords.latitude;
          const lng = geoPosition.coords.longitude;
          const acc = geoPosition.coords.accuracy;

          console.log(`📍 GPS Position: [${lat}, ${lng}] Accuracy: ±${acc.toFixed(0)}m`);

          setAccuracy(acc);

          if (acc > accuracyThreshold) {
            const msg = `GPS accuracy too low: ${acc.toFixed(0)}m`;
            setError(msg);
            reject(new Error(msg));
            return;
          }

          const pos = { lat, lng };
          setPosition(pos);
          setLoading(false);
          resolve(pos);
        },
        (err) => {
          console.error('❌ GPS Error:', err.message);
          setError(err.message);
          setLoading(false);
          reject(err);
        },
        geoOptions
      );
    });
  }, [accuracyThreshold, enableHighAccuracy, maximumAge, timeout]);

  return {
    position,
    accuracy,
    loading,
    error,
    getPosition
  };
}

export default {
  useGPSAccuracy,
  useGPSPosition
};
