import { useState, useEffect, useCallback } from 'react';
import { Coordinates } from '../types/quest';

interface GeolocationState {
  coords: Coordinates | null;
  accuracy: number | null;
  error: string | null;
  isLoading: boolean;
  permissionGranted: boolean;
}

export function useGeolocation(options: PositionOptions = { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }) {
  const [geoState, setGeoState] = useState<GeolocationState>({
    coords: null,
    accuracy: null,
    error: null,
    isLoading: true,
    permissionGranted: false,
  });

  const requestLocation = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setGeoState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'A böngésződ nem támogatja a helymeghatározást.',
      }));
      return;
    }

    setGeoState((prev) => ({ ...prev, isLoading: true, error: null }));

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGeoState({
          coords: {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          },
          accuracy: position.coords.accuracy,
          error: null,
          isLoading: false,
          permissionGranted: true,
        });
      },
      (err) => {
        setGeoState({
          coords: null,
          accuracy: null,
          error: err.message || 'Nem sikerült lekérni a helyzetet.',
          isLoading: false,
          permissionGranted: false,
        });
      },
      options
    );
  }, [options]);

  useEffect(() => {
    if (!('geolocation' in navigator)) {
      setGeoState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'A böngésződ nem támogatja a helymeghatározást.',
      }));
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        setGeoState({
          coords: {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          },
          accuracy: position.coords.accuracy,
          error: null,
          isLoading: false,
          permissionGranted: true,
        });
      },
      (err) => {
        setGeoState((prev) => ({
          ...prev,
          isLoading: false,
          error: err.message,
        }));
      },
      options
    );

    return () => {
      navigator.geolocation.clearWatch(watchId);
    };
  }, []);

  return { ...geoState, requestLocation };
}
