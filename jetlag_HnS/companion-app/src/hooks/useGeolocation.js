import { useState, useEffect } from 'react';

export const useGeolocation = (enabled = true) => {
    const [location, setLocation] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!enabled || !navigator.geolocation) {
            if (!navigator.geolocation) setError('Geolocation not supported');
            return;
        }

        const handleSuccess = (pos) => {
            const { latitude, longitude, accuracy, heading, speed } = pos.coords;
            setLocation({
                lat: latitude,
                lng: longitude,
                accuracy,
                heading,
                speed,
                timestamp: pos.timestamp
            });
        };

        const handleError = (err) => {
            setError(err.message);
        };

        const watcher = navigator.geolocation.watchPosition(
            handleSuccess,
            handleError,
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );

        return () => navigator.geolocation.clearWatch(watcher);
    }, [enabled]);

    return { location, error };
};
