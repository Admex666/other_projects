import { useState, useEffect, useCallback } from 'react';

interface CompassState {
  heading: number | null; // 0 to 360 degrees
  error: string | null;
  needsPermission: boolean;
}

export function useCompass() {
  const [compassState, setCompassState] = useState<CompassState>({
    heading: null,
    error: null,
    needsPermission: false,
  });

  const handleOrientation = (e: DeviceOrientationEvent) => {
    let heading: number | null = null;

    // iOS WebKit compass heading
    if ('webkitCompassHeading' in e && typeof (e as unknown as { webkitCompassHeading: number }).webkitCompassHeading === 'number') {
      heading = (e as unknown as { webkitCompassHeading: number }).webkitCompassHeading;
    } else if (e.alpha !== null) {
      // Android / standard compass heading (alpha is 0..360)
      if (e.absolute || ('webkitCompassHeading' in e === false)) {
        heading = 360 - e.alpha;
      } else {
        heading = e.alpha;
      }
    }

    if (heading !== null) {
      heading = (heading + 360) % 360;
      setCompassState({
        heading: Math.round(heading),
        error: null,
        needsPermission: false,
      });
    }
  };

  const requestPermission = useCallback(async () => {
    if (
      typeof DeviceOrientationEvent !== 'undefined' &&
      typeof (DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> }).requestPermission === 'function'
    ) {
      try {
        const response = await (DeviceOrientationEvent as unknown as { requestPermission: () => Promise<string> }).requestPermission();
        if (response === 'granted') {
          window.addEventListener('deviceorientation', handleOrientation, true);
          setCompassState((prev) => ({ ...prev, needsPermission: false }));
        } else {
          setCompassState((prev) => ({
            ...prev,
            error: 'Iránytű hozzáférés elutasítva.',
            needsPermission: false,
          }));
        }
      } catch (err) {
        setCompassState((prev) => ({
          ...prev,
          error: 'Hiba az iránytű engedélykérésnél.',
          needsPermission: false,
        }));
      }
    }
  }, []);

  useEffect(() => {
    // Check if iOS permission is required
    if (
      typeof DeviceOrientationEvent !== 'undefined' &&
      typeof (DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> }).requestPermission === 'function'
    ) {
      setCompassState((prev) => ({ ...prev, needsPermission: true }));
    } else {
      window.addEventListener('deviceorientationabsolute' in window ? 'deviceorientationabsolute' : 'deviceorientation', handleOrientation, true);
    }

    return () => {
      window.removeEventListener('deviceorientation', handleOrientation, true);
      window.removeEventListener('deviceorientationabsolute', handleOrientation, true);
    };
  }, []);

  return { ...compassState, requestPermission };
}
