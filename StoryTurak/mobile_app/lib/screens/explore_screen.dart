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

import '../services/auth_service.dart'; // Add AuthService import
import 'character_screen.dart'; // Import CharacterScreen

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
       
       // Fetch Character Data
       final token = context.read<AuthService>().token;
       if (token != null) {
          context.read<GeolixoService>().fetchUserCharacter(token);
          context.read<GeolixoService>().fetchQuests(token); // Fetch Quests
       }
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
       
       final token = context.read<AuthService>().token;
       if (token != null) {
           context.read<GeolixoService>().fetchUserCharacter(token); // Update character state
       }
       
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
    
    // Check Active Quests Progress (Visit Zone)
    for (var uq in service.activeQuests) {
        if (uq.status != QuestStatus.active) continue;
        
        // Find basic data locally - simplified for MVP
        // In prod, logic would be more robust server-side on update
        // Here we trigger an update if we entered the target zone
        
        // Mock check: if current zone ID matches objective target
        // We'd need to know the quest definition. For MVP we trust server updates on location poll 
        // (but we haven't implemented server-side location pushing yet, so we could mock it)
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
        
        // Persist visit
        final token = context.read<AuthService>().token;
        final char = context.read<GeolixoService>().activeCharacter;
        if (token != null && char != null) {
            context.read<GeolixoService>().markZoneVisited(token, char.id, newZone.id);
        }
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
              // Navigation Line Layer
              PolylineLayer(
                  polylines: _buildNavigationLines(service),
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: _userLocation,
                    width: 40,
                    height: 40,
                    child: _buildPlayerIcon(),
                  ),
                  // Available Quests
                  ...service.availableQuests.map((q) {
                      // Find location (center of starter zone or user loc fallback)
                      LatLng qLoc = _userLocation;
                      try {
                          final zone = service.activeZones.firstWhere((z) => z.id == q.starterZoneId);
                          // Approximate center - simplified
                          qLoc = zone.boundaryPoints[0]; 
                      } catch (e) {
                          // Global quest, maybe put near user?
                          qLoc = const LatLng(47.498, 19.040); // Default Belvaros
                      }
                      
                      return Marker(
                          point: qLoc,
                          width: 40,
                          height: 40,
                          child: GestureDetector(
                            onTap: () => _showQuestDialog(q),
                            child: const Icon(Icons.priority_high, color: Colors.yellow, size: 36),
                          ),
                      );
                  }),
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
          
          // Character HUD (Top Right)
          if (service.activeCharacter != null)
            Positioned(
              top: 60,
              right: 20,
              child: GestureDetector(
                onTap: () {
                    Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const CharacterScreen()),
                    );
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Row(
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            service.activeCharacter!.name,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                          Text(
                            "LVL ${service.activeCharacter!.level} ${service.activeCharacter!.characterClass.toString().split('.').last.toUpperCase()}",
                            style: const TextStyle(color: Colors.grey, fontSize: 10),
                          ),
                        ],
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.person, color: GeolixoTheme.accent),
                    ],
                  ),
                ),
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

  List<Polyline> _buildNavigationLines(GeolixoService service) {
      List<Polyline> lines = [];
      
      for (var uq in service.activeQuests) {
          if (uq.status != QuestStatus.active) continue;
          
          // Simplified: Assume we want to go to the first objective's target
          // In a real app we'd fetch the specific quest definition to know the target ID
          // For MVP, we'll try to match specific known IDs or loop active zones
          
          Zone? targetZone;
          
          // Hardcheck for our known seed quest
          if (uq.questId == "quest_starter_01") {
               try {
                   targetZone = service.activeZones.firstWhere((z) => z.id == "zone_belvaros");
               } catch (e) {}
          }
          
          if (targetZone != null) {
              // Calculate center
              double latSum = 0;
              double lngSum = 0;
              for (var p in targetZone.boundaryPoints) {
                  latSum += p.latitude;
                  lngSum += p.longitude;
              }
              LatLng center = LatLng(latSum / targetZone.boundaryPoints.length, lngSum / targetZone.boundaryPoints.length);
              
              lines.add(Polyline(
                  points: [_userLocation, center],
                  strokeWidth: 4.0,
                  color: GeolixoTheme.accent.withOpacity(0.7),
                  isDotted: true,
              ));
          }
      }
      return lines;
  }

  void _showQuestDialog(Quest quest) {
      showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
              backgroundColor: GeolixoTheme.surface,
              title: Text(quest.title, style: GeolixoTheme.darkTheme.textTheme.displayMedium),
              content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                      Text(quest.description, style: const TextStyle(color: Colors.white70)),
                      const SizedBox(height: 16),
                      Text("Jutalom: ${quest.rewardsXp} XP", style: const TextStyle(color: GeolixoTheme.accent)),
                      const SizedBox(height: 8),
                      // List objectives
                      ...quest.objectives.map((o) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(children: [
                              const Icon(Icons.check_circle_outline, color: Colors.grey, size: 16),
                              const SizedBox(width: 8),
                              Expanded(child: Text(o.description, style: const TextStyle(color: Colors.white60))),
                          ]),
                      )),
                  ],
              ),
              actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text("Mégse"),
                  ),
                  ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: GeolixoTheme.accent),
                      onPressed: () async {
                          final token = context.read<AuthService>().token;
                          if (token != null) {
                              final success = await context.read<GeolixoService>().acceptQuest(token, quest.id);
                              if (success && mounted) {
                                  Navigator.pop(ctx);
                                  ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text("Küldetés felvéve!"), backgroundColor: Colors.green),
                                  );
                              }
                          }
                      },
                      child: const Text("Elfogadom"),
                  ),
              ],
          ),
      );
  }
}
