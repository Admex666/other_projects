import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart'; // Add Geolocation
import '../services/map_config.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart'; // Add Geolocation
import '../services/map_config.dart';
import '../services/geolixo_service.dart';
import '../services/notification_service.dart'; // System Notifications
import '../models/geolixo_models.dart';
import '../theme.dart';
import 'encounter_screen.dart'; // Import EncounterScreen
import 'package:flutter/services.dart'; // For HapticFeedback

class ExploreScreen extends StatefulWidget {
  const ExploreScreen({Key? key}) : super(key: key);

  @override
  State<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends State<ExploreScreen> {
  final MapController _mapController = MapController();
  LatLng _userLocation = const LatLng(47.498, 19.050); // Default to Budapest
  Zone? _currentZone;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    // 1. Initial Fetch
    WidgetsBinding.instance.addPostFrameCallback((_) {
       context.read<GeolixoService>().fetchNearbyWorld(_userLocation);
    });

    // 2. Start location stream and polling
    _startLocationUpdates();
  }

  void _startLocationUpdates() {
    // Basic polling mock for loop (replace with real Geolocator.getPositionStream in prod)
    _pollTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
       // Simulate movement or get real location
       // For MVP dev, we assume _userLocation is updated by map interaction or mocking
       
       context.read<GeolixoService>().fetchNearbyWorld(_userLocation);
       _checkGeofences();
    });
  }

  void _checkGeofences() {
    final service = context.read<GeolixoService>();
    Zone? newZone;
    
    for (var zone in service.activeZones) {
      if (service.isPointInZone(_userLocation, zone)) {
        newZone = zone;
        break;
      }
    }

    // Check if ID changed (to avoid repeated triggers on polling updates)
    if (newZone?.id != _currentZone?.id) {
      setState(() {
        _currentZone = newZone;
      });

      if (newZone != null) {
        HapticFeedback.heavyImpact(); // Vibrate on entry
        NotificationService().showZoneNotification(newZone.name); // System Notification
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Beléptél: ${newZone.name}"),
            backgroundColor: GeolixoTheme.accent,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<GeolixoService>();

    return Scaffold(
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _userLocation,
              initialZoom: 14.5,
              minZoom: 12,
              maxZoom: 18,
              onTap: (tapPosition, point) {
                // DEBUG: Teleport user on tap to test geofencing
                setState(() {
                  _userLocation = point;
                });
                _checkGeofences();
              },
            ),
            children: [
              TileLayer(
                urlTemplate: MapConfig.darkUrl,
                subdomains: const ['a', 'b', 'c', 'd'],
                userAgentPackageName: 'com.storyturak.geolixo',
              ),
              PolygonLayer(
                polygons: service.activeZones.map((zone) {
                  bool isInside = _currentZone?.id == zone.id;
                  return Polygon(
                    points: zone.boundaryPoints,
                    color: isInside 
                        ? Colors.redAccent.withOpacity(0.4) // High vis inside
                        : Colors.blueAccent.withOpacity(0.4), // High vis outside
                    borderColor: isInside 
                        ? Colors.red 
                        : Colors.blue,
                    borderStrokeWidth: 4,
                    isFilled: true,
                    label: zone.name,
                    labelStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  );
                }).toList(),
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: _userLocation,
                    width: 40,
                    height: 40,
                    child: _buildPlayerIcon(),
                  ),
                ],
              ),
            ],
          ),
          
          
            if (_currentZone != null)
              Positioned(
                bottom: 40,
              right: 20,
              child: FloatingActionButton.extended(
                onPressed: () {
                   final service = context.read<GeolixoService>();
                   // Find an encounter for this zone
                   Encounter? targetEncounter;
                   
                   try {
                     targetEncounter = service.nearbyEncounters.firstWhere(
                       (e) => e.zoneId == _currentZone!.id
                     );
                   } catch (e) {
                     // No specific encounter found
                   }
                   
                   // Fallback generic encounter if list is empty or no match
                   targetEncounter ??= Encounter(
                        id: "generic_explore",
                        title: "Üres Utca",
                        description: "Nincs itt semmi érdekes jelenleg. A szelek halkan fújnak.",
                        type: EncounterType.narrative,
                        zoneId: _currentZone!.id,
                   );

                   Navigator.push(
                     context,
                     MaterialPageRoute(
                       builder: (context) => EncounterScreen(
                         encounter: targetEncounter!,
                       ),
                     ),
                   );
                },
                backgroundColor: GeolixoTheme.accent,
                foregroundColor: GeolixoTheme.background,
                icon: const Icon(Icons.visibility),
                label: Text("VIZSGÁLD MEG (${_currentZone!.difficultyLevel})"),
              ),
            ),

          // Minimalist Header
          Positioned(
            top: 60,
            left: 20,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "HELYZET (N:${service.activeZones.length})", // Debug count
                  style: GeolixoTheme.darkTheme.textTheme.labelLarge?.copyWith(
                    color: Colors.white54,
                    letterSpacing: 2,
                  ),
                ),
                Text(
                  _currentZone?.name ?? "Ismeretlen Terület",
                  style: GeolixoTheme.darkTheme.textTheme.displayMedium?.copyWith(
                    fontSize: 20,
                    color: _currentZone != null ? GeolixoTheme.accent : Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayerIcon() {
    return Container(
      decoration: BoxDecoration(
        color: GeolixoTheme.primary,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: GeolixoTheme.primary.withOpacity(0.5),
            blurRadius: 10,
            spreadRadius: 2,
          )
        ],
      ),
      child: const Icon(
        Icons.navigation,
        color: Colors.black,
        size: 20,
      ),
    );
  }
}
