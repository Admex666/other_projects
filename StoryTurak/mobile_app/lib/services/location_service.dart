
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

import 'dart:async';
import 'package:flutter/foundation.dart';

class LocationService extends ChangeNotifier {
  StreamSubscription<Position>? _positionSubscription;
  LatLng? _lastPosition;
  LatLng? _lastTrackedPosition; // Anchor to filter drift
  double _accumulatedDistance = 0.0;
  int _sessionSteps = 0;
  
  // 1 Step ~= 0.72m (User Request)
  static const double stepLengthMeters = 0.72;
  static const double trackingThresholdMeters = 25.0; // Filter out drift < 25m

  int get sessionSteps => _sessionSteps;
  LatLng? get lastPosition => _lastPosition;
  
  // Debug Mode
  bool _isDebugMode = false;
  bool get isDebugMode => _isDebugMode;

  void setDebugMode(bool enabled) {
    _isDebugMode = enabled;
    notifyListeners();
  }

  void setMockLocation(LatLng location) {
    if (!_isDebugMode) return;
    
    // Simulate position update
    final mockPos = Position(
        longitude: location.longitude,
        latitude: location.latitude,
        timestamp: DateTime.now(),
        accuracy: 10,
        altitude: 0,
        heading: 0,
        speed: 0,
        speedAccuracy: 0, 
        altitudeAccuracy: 1, 
        headingAccuracy: 1
    );
    _onLocationUpdate(mockPos);
  }

  void startTracking() async {
    if (_positionSubscription != null) return;
    
    // Reset anchor on start
    _lastTrackedPosition = null;

    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return;

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 2, // Keep low for UI smoothness, we filter logic manually
      ),
    ).listen(_onLocationUpdate);
    
    print("📍 Location Tracking Started");
  }

  void stopTracking() {
    _positionSubscription?.cancel();
    _positionSubscription = null;
    _lastTrackedPosition = null;
    print("🛑 Location Tracking Stopped. Total Steps: $_sessionSteps");
  }

  void _onLocationUpdate(Position pos) {
    final newPos = LatLng(pos.latitude, pos.longitude);
    
    // Initialize start point
    if (_lastTrackedPosition == null) {
      _lastTrackedPosition = newPos;
    } else {
      // Check distance from last *tracked* position (anchor)
      final distance = getDistance(_lastTrackedPosition!, newPos);
      
      // Only count if user moved significantly (Anti-Drift)
      if (distance >= trackingThresholdMeters) {
         _accumulatedDistance += distance;
         
         // Convert accumulated distance to new steps
         int newSteps = (_accumulatedDistance / stepLengthMeters).floor();
         if (newSteps > 0) {
             _sessionSteps += newSteps;
             _accumulatedDistance -= (newSteps * stepLengthMeters); // Keep remainder
             print("🚶 Steps: +$newSteps (Total: $_sessionSteps)");
             
             // Update the anchor only when we confirmed real movement
             _lastTrackedPosition = newPos;
         }
      }
    }
    
    // Always update UI position for map rendering
    _lastPosition = newPos;
    notifyListeners(); 
  }
  Stream<LatLng> get positionStream {
    return Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 5,
      ),
    ).map((pos) => LatLng(pos.latitude, pos.longitude));
  }

  Future<LatLng> getCurrentLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return Future.error('Location services are disabled.');
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return Future.error('Location permissions are denied');
      }
    }
    
    if (permission == LocationPermission.deniedForever) {
      return Future.error('Location permissions are permanently denied.');
    }

    Position pos = await Geolocator.getCurrentPosition();
    return LatLng(pos.latitude, pos.longitude);
  }

  double getDistance(LatLng p1, LatLng p2) {
    return Geolocator.distanceBetween(
      p1.latitude, p1.longitude,
      p2.latitude, p2.longitude,
    );
  }
}
