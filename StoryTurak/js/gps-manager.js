export class GpsManager {
    constructor() {
        this.watchId = null;
        this.currentPosition = null;
        this.listeners = [];
        this.mockMode = false; // For debugging
    }

    start() {
        if (!navigator.geolocation) {
            console.error('Geolocation is not supported');
            return;
        }

        const options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        };

        this.watchId = navigator.geolocation.watchPosition(
            (pos) => this.handleUpdate(pos),
            (err) => this.handleError(err),
            options
        );
        console.log('GPS tracking started');
    }

    stop() {
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
    }

    handleUpdate(position) {
        this.currentPosition = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy
        };

        // Notify listeners
        this.listeners.forEach(cb => cb(this.currentPosition));
    }

    handleError(error) {
        console.warn(`GPS Error: ${error.code} - ${error.message}`);
        // In a real app, we might want to notify the UI
    }

    subscribe(callback) {
        this.listeners.push(callback);
    }

    getDistance(lat1, lon1, lat2, lon2) {
        const R = 6371e3; // metres
        const φ1 = lat1 * Math.PI / 180; // φ, λ in radians
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lon2 - lon1) * Math.PI / 180;

        const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        return R * c; // in metres
    }
}

export const gpsManager = new GpsManager();
