import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart'; 
import '../services/map_config.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/keldor_service.dart';
import '../services/notification_service.dart';
import '../models/keldor_models.dart';
import '../theme.dart';
import 'encounter_screen.dart'; 
import 'package:flutter/services.dart'; 
import '../services/auth_service.dart';
import 'character_screen.dart'; 
import '../services/location_service.dart';
import '../services/routing_service.dart';
import '../services/settings_service.dart';

class ExploreScreen extends StatefulWidget {
  const ExploreScreen({Key? key}) : super(key: key);

  @override
  State<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends State<ExploreScreen> {
  final MapController _mapController = MapController();
  LatLng _userLocation = const LatLng(47.4979, 19.0402); // Budapest center
  final Set<String> _triggeredEncounters = {};
  Timer? _pollTimer;
  Zone? _currentZone;
  final LocationService _locationService = LocationService();
  final RoutingService _routingService = RoutingService();
  StreamSubscription? _positionSubscription;
  List<LatLng> _routePoints = [];
  LatLng? _lastRouteUpdatePos;

  @override
  void initState() {
    super.initState();
    // 1. Initial Fetch
    WidgetsBinding.instance.addPostFrameCallback((_) {
       final token = context.read<AuthService>().token;
       context.read<KeldorService>().fetchNearbyWorld(token, _userLocation);
       
       // Fetch Data sequentially to avoid race conditions
       if (token != null) {
          context.read<KeldorService>().fetchUserCharacter(token).then((_) {
              if (mounted) {
                  context.read<KeldorService>().fetchQuests(token);
              }
          });
       }
    });

    // 2. Start polling for updates (Every 30s)
    _pollTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
       _updateWorld();
    });

    // 2.5 Listen to KeldorService for quest changes
    context.read<KeldorService>().addListener(_updateRoute);

    // 3. Listen to real-time location
    _positionSubscription = _locationService.positionStream.listen((pos) {
      if (mounted) {
        setState(() {
          _userLocation = pos;
        });
        _checkGeofences();
        _maybeUpdateRoute();
      }
    });
  }

  Future<void> _updateWorld() async {
    if (mounted) {
       // Simulate movement or get real location
       // For MVP dev, we assume _userLocation is updated by map interaction or mocking
       
       final token = context.read<AuthService>().token;
       context.read<KeldorService>().fetchNearbyWorld(token, _userLocation);
       
       if (token != null) {
           context.read<KeldorService>().fetchUserCharacter(token); // Update character state
       }
       
       _checkGeofences();
    }
  }

  void _checkGeofences() {
    final service = context.read<KeldorService>();
    Zone? newZone;
    
    for (var zone in service.activeZones) {
       if (service.isPointInZone(_userLocation, zone)) {
         newZone = zone;
         break;
       }
    }

    if (_currentZone?.id != newZone?.id) {
      _handleZoneTransition(newZone);
    }
  }

  void _handleZoneTransition(Zone? newZone) {
    setState(() {
      _currentZone = newZone;
    });

    if (newZone != null) {
      HapticFeedback.heavyImpact(); // Vibrate on entry
      NotificationService().showZoneNotification(newZone.name); // System Notification
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Beléptél: ${newZone.name}"),
          backgroundColor: KeldorTheme.primary,
          duration: const Duration(seconds: 3),
        ),
      );
      
      // Persist visit
      final token = context.read<AuthService>().token;
      final char = context.read<KeldorService>().activeCharacter;
      if (token != null && char != null) {
        context.read<KeldorService>().markZoneVisited(token, char.id, newZone.id);
      }
    }
  }
  
  void _maybeUpdateRoute() {
    if (_lastRouteUpdatePos == null || _routePoints.isEmpty) {
      _updateRoute();
      return;
    }
    
    final dist = const Distance().as(LengthUnit.Meter, _userLocation, _lastRouteUpdatePos!);
    if (dist > 50) {
      _updateRoute();
    }
  }

  Future<void> _updateRoute() async {
    final service = context.read<KeldorService>();
    final activeQuests = service.activeQuests.where((q) => q.status == QuestStatus.active).toList();
    
    if (activeQuests.isEmpty) {
      if (mounted) setState(() => _routePoints = []);
      return;
    }

    final uq = activeQuests.first;
    LatLng? target;
    try {
      final qDef = service.allQuests.firstWhere((q) => q.id == uq.questId);
      if (qDef.stages.isNotEmpty && uq.currentStageIndex < qDef.stages.length) {
        target = qDef.stages[uq.currentStageIndex].location;
      } else {
        target = qDef.startLocation;
      }
    } catch (e) {
      return;
    }

    if (target != null) {
      debugPrint('🚀 [Explore] Fetching walking route from $_userLocation to $target');
      final points = await _routingService.getRoute(_userLocation, target);
      if (mounted && points != null && points.isNotEmpty) {
        setState(() {
          _routePoints = points;
          _lastRouteUpdatePos = _userLocation;
        });
        debugPrint('✅ [Explore] Got ${points.length} route points');
      }
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _positionSubscription?.cancel();
    try {
      context.read<KeldorService>().removeListener(_updateRoute);
    } catch (_) {}
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<KeldorService>();
    final activeUserQuests = service.activeQuests.where((q) => q.status == QuestStatus.active).toList();

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
                urlTemplate: MapConfig.getStyle(context.watch<SettingsService>().mapStyle).url,
                subdomains: MapConfig.getStyle(context.watch<SettingsService>().mapStyle).subdomains,
                userAgentPackageName: 'com.storyturak.keldor',
              ),
              PolygonLayer(
                polygons: service.activeZones.map((zone) {
                  bool isInside = _currentZone?.id == zone.id;
                  return Polygon(
                    points: zone.boundaryPoints,
                    color: isInside 
                        ? KeldorTheme.primary.withOpacity(0.3) // Green inside
                        : Colors.white10, // Dim outside
                    borderColor: isInside 
                        ? KeldorTheme.primary 
                        : Colors.white24,
                    borderStrokeWidth: 3,
                    isFilled: true,
                    label: zone.name,
                    labelStyle: GoogleFonts.cinzel(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10),
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
                  // Available Quests (Only show start location if not already on an active quest)
                  if (activeUserQuests.isEmpty)
                    ...service.availableQuests.map((q) {
                        return Marker(
                            point: q.startLocation,
                            width: 60,
                            height: 60,
                            child: _buildQuestMarker(q, isActive: false),
                        );
                    }),

                  // Active Quest Stage Marker
                  ...activeUserQuests.map((uq) {
                      if (service.allQuests.isEmpty) return const Marker(point: LatLng(0,0), child: SizedBox.shrink());
                      
                      Quest? qDef;
                      try {
                          qDef = service.allQuests.firstWhere((q) => q.id == uq.questId);
                      } catch (e) {
                          return const Marker(point: LatLng(0,0), child: SizedBox.shrink());
                      }
                      
                      LatLng target;
                      if (qDef.stages.isNotEmpty && uq.currentStageIndex < qDef.stages.length) {
                          target = qDef.stages[uq.currentStageIndex].location;
                      } else {
                          target = qDef.startLocation;
                      }

                      return Marker(
                          point: target,
                          width: 60,
                          height: 60,
                          child: _buildQuestMarker(qDef, isActive: true),
                      );
                  }),
                ],
              ),
            ],
          ),
          
          Builder(
            builder: (context) {
              final service = context.watch<KeldorService>();
              Encounter? closestEncounter;
              double? minDistance;
              
              const distanceCalc = Distance();
              
              // Determine target encounter for active quest
              String? activeBountyEncounterId;
              if (activeUserQuests.isNotEmpty) {
                  final uq = activeUserQuests.first;
                  final qDef = service.allQuests.firstWhere((q) => q.id == uq.questId, orElse: () => service.allQuests.first);
                  if (qDef.stages.isNotEmpty && uq.currentStageIndex < qDef.stages.length) {
                      activeBountyEncounterId = qDef.stages[uq.currentStageIndex].encounterId;
                  }
              }

              for (var e in service.nearbyEncounters) {
                  final d = distanceCalc.as(LengthUnit.Meter, _userLocation, e.location);
                  if (minDistance == null || d < minDistance) {
                      minDistance = d;
                      closestEncounter = e;
                  }
              }

              bool isNear = minDistance != null && minDistance <= 30;

              // Auto-trigger if it's the active quest target
              if (isNear && closestEncounter != null && activeBountyEncounterId != null && closestEncounter.id == activeBountyEncounterId) {
                   if (!_triggeredEncounters.contains(closestEncounter.id)) {
                       WidgetsBinding.instance.addPostFrameCallback((_) {
                           _navigateToEncounter(closestEncounter!);
                       });
                   }
                   return const SizedBox.shrink();
              }
              
              return const SizedBox.shrink();
            },
          ),

          // Active Quest HUD
          if (activeUserQuests.isNotEmpty)
            _buildActiveQuestHud(activeUserQuests.first, service),
          
          // Minimalist Header
          Positioned(
            top: 60,
            left: 20,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "HELYZET (N:${service.activeZones.length})", // Debug count
                  style: KeldorTheme.darkTheme.textTheme.labelLarge?.copyWith(
                    color: Colors.white54,
                    letterSpacing: 2,
                  ),
                ),
                Text(
                  _currentZone?.name ?? "Ismeretlen Terület",
                  style: KeldorTheme.darkTheme.textTheme.displayMedium?.copyWith(
                    fontSize: 20,
                    color: _currentZone != null ? KeldorTheme.primary : Colors.white,
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
                    color: Colors.black,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: KeldorTheme.primary.withOpacity(0.3)),
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
                            style: TextStyle(color: KeldorTheme.primary.withOpacity(0.7), fontSize: 10),
                          ),
                        ],
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.person, color: KeldorTheme.primary),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }


  Widget _buildActiveQuestHud(UserQuest uq, KeldorService service) {
    Quest? qDef;
    try {
        qDef = service.allQuests.firstWhere((q) => q.id == uq.questId);
    } catch (e) {
        return const SizedBox.shrink();
    }

    final currentStage = (qDef.stages.isNotEmpty && uq.currentStageIndex < qDef.stages.length) 
        ? qDef.stages[uq.currentStageIndex] 
        : null;
    
    // Progress Calculation
    double progress = 0;
    if (qDef.stages.isNotEmpty) {
        progress = (uq.currentStageIndex) / qDef.stages.length;
    }

    return Positioned(
      bottom: 20,
      left: 20,
      right: 20,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: KeldorTheme.surface.withOpacity(0.95),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: KeldorTheme.primary.withOpacity(0.3)),
          boxShadow: [
              BoxShadow(color: Colors.black45, blurRadius: 10, offset: const Offset(0, 4))
          ]
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(qDef.title, style: GoogleFonts.cinzel(color: KeldorTheme.primary, fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 4),
                      Text(currentStage?.description ?? "Cél elérése...", style: const TextStyle(color: Colors.white, fontSize: 14), overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.redAccent),
                  tooltip: "Abandon Quest",
                  onPressed: () async {
                    final confirmed = await showDialog<bool>(
                      context: context,
                      builder: (context) => AlertDialog(
                        backgroundColor: KeldorTheme.surface,
                        title: Text('Abandon Quest?', style: GoogleFonts.cinzel(color: KeldorTheme.primary)),
                        content: Text('Are you sure you want to abandon "${qDef!.title}"?', style: const TextStyle(color: Colors.white70)),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context, false),
                            child: const Text('Cancel'),
                          ),
                          TextButton(
                            onPressed: () => Navigator.pop(context, true),
                            child: const Text('Abandon', style: TextStyle(color: Colors.redAccent)),
                          ),
                        ],
                      ),
                    );
                    
                      if (confirmed == true) {
                        final token = context.read<AuthService>().token;
                        if (token != null) {
                          // Call abandon quest endpoint
                          await service.abandonQuest(token, uq.id);
                          
                          // Clear triggers and refresh map so first stage can re-trigger later
                          setState(() {
                            _triggeredEncounters.clear();
                          });
                          _updateWorld();
                        }
                      }
                  },
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Progress Bar
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                backgroundColor: Colors.white10,
                color: KeldorTheme.primary,
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStatItem(Icons.timer_outlined, "12:45"), // Mock time
                _buildStatItem(Icons.directions_walk, "${qDef.estimatedDistanceKm} KM"),
                _buildStatItem(Icons.flag, "${uq.currentStageIndex + 1} / ${qDef.stages.length}"),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(IconData icon, String value) {
      return Row(
          children: [
              Icon(icon, size: 14, color: Colors.white70),
              const SizedBox(width: 4),
              Text(value, style: const TextStyle(color: Colors.white70, fontSize: 12)),
          ],
      );
  }


  Widget _buildQuestMarker(Quest quest, {required bool isActive}) {
    return GestureDetector(
      onTap: () => _showQuestDetail(quest, isActive),
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0.0, end: 1.0),
        duration: const Duration(milliseconds: 1500),
        curve: Curves.easeInOut,
        builder: (context, value, child) {
          return Stack(
            alignment: Alignment.center,
            children: [
              // Pulse effect for available quests
              if (!isActive)
                Opacity(
                  opacity: 1.0 - value,
                  child: Transform.scale(
                    scale: 1.0 + (value * 0.5),
                    child: Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.amber, width: 2),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                ),
              // Main marker
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: isActive ? KeldorTheme.primary : Colors.amber,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 3),
                  boxShadow: [
                    BoxShadow(
                      color: (isActive ? KeldorTheme.primary : Colors.amber).withOpacity(0.5),
                      blurRadius: 10,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: Icon(
                  isActive ? Icons.stars : Icons.flag,
                  color: Colors.white,
                  size: 28,
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPlayerIcon() {
    return Container(
      decoration: BoxDecoration(
        color: KeldorTheme.primary,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: KeldorTheme.primary.withOpacity(0.5),
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

  List<Polyline> _buildNavigationLines(KeldorService service) {
      if (_routePoints.isNotEmpty) {
          return [
              Polyline(
                  points: _routePoints,
                  strokeWidth: 5,
                  color: KeldorTheme.primary.withOpacity(0.8),
              )
          ];
      }

      // Fallback to straight lines if route not yet fetched
      List<Polyline> lines = [];
      
      for (var uq in service.activeQuests) {
          if (uq.status != QuestStatus.active) continue;
          
          LatLng? targetLoc;
          
          try {
              final qDef = service.allQuests.firstWhere((q) => q.id == uq.questId);
              if (qDef.stages.isNotEmpty && uq.currentStageIndex < qDef.stages.length) {
                  targetLoc = qDef.stages[uq.currentStageIndex].location;
              } else {
                  targetLoc = qDef.startLocation;
              }
          } catch (e) {}
          
          if (targetLoc != null) {
              lines.add(Polyline(
                  points: [_userLocation, targetLoc],
                  strokeWidth: 4,
                  color: KeldorTheme.primary.withOpacity(0.4),
                  isDotted: true,
              ));
          }
      }
      return lines;
  }

  Widget _buildEncounterMarker(Encounter encounter) {
      return TweenAnimationBuilder<double>(
        tween: Tween(begin: 0.0, end: 1.0),
        duration: const Duration(seconds: 2),
        curve: Curves.easeInOut,
        builder: (context, value, child) {
            return Stack(
                alignment: Alignment.center,
                children: [
                    // Outer pulse ring
                    Opacity(
                        opacity: 1.0 - value,
                        child: Transform.scale(
                            scale: 1.0 + (value * 1.5),
                            child: Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                    border: Border.all(color: KeldorTheme.primary, width: 2),
                                    shape: BoxShape.circle,
                                ),
                            ),
                        ),
                    ),
                    child!,
                ],
            );
        },
        child: Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
                color: Colors.black,
                shape: BoxShape.circle,
                border: Border.all(color: KeldorTheme.primary.withOpacity(0.8), width: 2),
                boxShadow: [
                    BoxShadow(color: KeldorTheme.primary.withOpacity(0.3), blurRadius: 8)
                ],
            ),
            child: const Icon(Icons.auto_stories, color: KeldorTheme.primary, size: 16),
        ),
      );
  }

  void _showQuestDetail(Quest quest, bool isActive) {
    final service = context.read<KeldorService>();
    final distanceCalc = Distance();
    final distanceToQuest = distanceCalc.as(
      LengthUnit.Meter,
      _userLocation,
      quest.startLocation,
    );
    final isNearby = distanceToQuest <= 30;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.95),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          border: Border.all(color: KeldorTheme.primary.withOpacity(0.3), width: 1),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title
            Text(
              quest.title,
              style: GoogleFonts.cinzel(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: KeldorTheme.primary,
              ),
            ),
            const SizedBox(height: 12),
            // Description
            Text(
              quest.description,
              style: GoogleFonts.merriweather(
                fontSize: 14,
                color: Colors.white70,
              ),
            ),
            const SizedBox(height: 16),
            // Stats
            Row(
              children: [
                Icon(Icons.route, color: KeldorTheme.primary, size: 16),
                const SizedBox(width: 8),
                Text(
                  '${quest.estimatedDistanceKm.toStringAsFixed(1)} km',
                  style: GoogleFonts.merriweather(color: Colors.white),
                ),
                const SizedBox(width: 24),
                Icon(Icons.star, color: Colors.amber, size: 16),
                const SizedBox(width: 8),
                Text(
                  '${quest.rewardsXp} XP',
                  style: GoogleFonts.merriweather(color: Colors.white),
                ),
              ],
            ),
            const SizedBox(height: 24),
            // Action Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: isNearby && !isActive
                    ? () async {
                        final token = context.read<AuthService>().token;
                        if (token == null) return;
                        
                        Navigator.pop(context);
                        // Accept the quest
                        final success = await service.acceptQuest(token, quest.id);
                        
                        if (success) {
                          // IMPORTANT: Clear triggers so if they abandoned/restarted, the first one fires
                          // And refresh world so the encounter is available in nearbyEncounters
                          setState(() {
                            _triggeredEncounters.clear();
                          });
                          _updateWorld();
                        } else {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text("Hiba a küldetés indításakor. Kérlek próbáld újra!"),
                                backgroundColor: Colors.redAccent,
                              ),
                            );
                          }
                        }
                      }
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: KeldorTheme.primary,
                  disabledBackgroundColor: Colors.grey.shade800,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: Text(
                  isActive
                      ? 'Quest Active'
                      : isNearby
                          ? 'Start Quest'
                          : 'Get Closer (${distanceToQuest.toStringAsFixed(0)}m away)',
                  style: GoogleFonts.cinzel(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: isActive || !isNearby ? Colors.white54 : Colors.black,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  Future<void> _navigateToEncounter(Encounter encounter) async {
    if (!_triggeredEncounters.contains(encounter.id)) {
      setState(() {
        _triggeredEncounters.add(encounter.id);
      });
      
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => EncounterScreen(encounter: encounter),
        ),
      );
      
      // Refresh world data when returning from encounter to show next checkpoint
      _updateWorld();
    }
  }
}
