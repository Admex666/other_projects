import { useState, useEffect, useCallback } from 'react';
import { Coordinates } from '../types/quest';

interface GeolocationState {
  coords: Coordinates | null;
  accuracy: number | null;
  error: string | null;
  isLoading: boolean;
  permissionGranted: boolean;
}

// Global in-memory cache so coords persist across stages with ZERO delay
let globalGeoState: GeolocationState = {
  coords: null,
  accuracy: null,
  error: null,
  isLoading: true,
  permissionGranted: false,
};

const listeners = new Set<(state: GeolocationState) => void>();

function updateGlobalGeo(next: Partial<GeolocationState>) {
  globalGeoState = { ...globalGeoState, ...next };
  listeners.forEach((listener) => listener(globalGeoState));
}

let isGlobalWatchInitialized = false;

function initGlobalWatch() {
  if (isGlobalWatchInitialized || typeof window === 'undefined' || !('geolocation' in navigator)) return;
  isGlobalWatchInitialized = true;

  const handleSuccess = (position: GeolocationPosition) => {
    updateGlobalGeo({
      coords: {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      },
      accuracy: position.coords.accuracy,
      error: null,
      isLoading: false,
      permissionGranted: true,
    });
  };

  // Immediate fast fetch
  navigator.geolocation.getCurrentPosition(
    handleSuccess,
    () => {
      // Fallback
      navigator.geolocation.getCurrentPosition(handleSuccess, () => {}, {
        enableHighAccuracy: false,
        timeout: 10000,
      });
    },
    { enableHighAccuracy: true, timeout: 5000, maximumAge: 30000 }
  );

  // Persistent continuous watch
  navigator.geolocation.watchPosition(
    handleSuccess,
    () => {},
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 2000 }
  );
}

// Auto-start watcher on load
if (typeof window !== 'undefined') {
  initGlobalWatch();
}

export function useGeolocation() {
  const [geoState, setGeoState] = useState<GeolocationState>(() => globalGeoState);

  useEffect(() => {
    listeners.add(setGeoState);
    if (!globalGeoState.coords) {
      initGlobalWatch();
    }
    return () => {
      listeners.delete(setGeoState);
    };
  }, []);

  const requestLocation = useCallback(() => {
    if (!('geolocation' in navigator)) {
      updateGlobalGeo({
        isLoading: false,
        error: 'A böngésződ nem támogatja a GPS helymeghatározást.',
      });
      return;
    }

    if (!globalGeoState.coords) {
      updateGlobalGeo({ isLoading: true, error: null });
    }

    const handleSuccess = (position: GeolocationPosition) => {
      updateGlobalGeo({
        coords: {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        },
        accuracy: position.coords.accuracy,
        error: null,
        isLoading: false,
        permissionGranted: true,
      });
    };

    navigator.geolocation.getCurrentPosition(
      handleSuccess,
      (err) => {
        navigator.geolocation.getCurrentPosition(
          handleSuccess,
          (err2) => {
            let msg = 'Nem sikerült lekérni a valós GPS pozíciót.';
            if (err2.code === err2.PERMISSION_DENIED || err.code === err.PERMISSION_DENIED) {
              msg = 'A böngészőben le van tiltva a helyhozzáférés. Kattints a címsorban lévő lakat ikonra és engedélyezd!';
            }
            updateGlobalGeo({
              error: msg,
              isLoading: false,
              permissionGranted: false,
            });
          },
          { enableHighAccuracy: false, timeout: 8000, maximumAge: 30000 }
        );
      },
      { enableHighAccuracy: true, timeout: 6000, maximumAge: 10000 }
    );
  }, []);

  return { ...geoState, requestLocation };
}
