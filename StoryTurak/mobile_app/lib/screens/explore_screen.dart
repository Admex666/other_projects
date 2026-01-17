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

class ExploreScreen extends StatefulWidget {
  const ExploreScreen({Key? key}) : super(key: key);

  @override
  State<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends State<ExploreScreen> {
  final MapController _mapController = MapController();
  LatLng _userLocation = const LatLng(47.4979, 19.0402); // Budapest center
  Timer? _pollTimer;
  Zone? _currentZone;

  @override
  void initState() {
    super.initState();
    // 1. Initial Fetch
    WidgetsBinding.instance.addPostFrameCallback((_) {
       context.read<KeldorService>().fetchNearbyWorld(_userLocation);
       
       // Fetch Data sequentially to avoid race conditions
       final token = context.read<AuthService>().token;
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
  }

  Future<void> _updateWorld() async {
    if (mounted) {
       // Simulate movement or get real location
       // For MVP dev, we assume _userLocation is updated by map interaction or mocking
       
       context.read<KeldorService>().fetchNearbyWorld(_userLocation);
       
       final token = context.read<AuthService>().token;
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

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<KeldorService>();

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
                  if (service.activeQuests.isEmpty)
                    ...service.availableQuests.map((q) {
                        return Marker(
                            point: q.startLocation,
                            width: 60,
                            height: 60,
                            child: _buildQuestMarker(q, isActive: false),
                        );
                    }),

                  // Active Quest Stage Marker
                  ...service.activeQuests.map((uq) {
                      if (service.allQuests.isEmpty) return const Marker(point: LatLng(0,0), child: SizedBox.shrink());
                      
                      final qDef = service.allQuests.firstWhere(
                        (q) => q.id == uq.questId, 
                        orElse: () => service.allQuests.first
                      );
                      
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
                  // Encounter markers (only show if no active quest)
                  if (service.activeQuests.isEmpty)
                    ...service.nearbyEncounters.map((e) {
                        return Marker(
                            point: e.location,
                            width: 50,
                            height: 50,
                            child: _buildEncounterMarker(e),
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
                
                for (var e in service.nearbyEncounters) {
                    final d = distanceCalc.as(LengthUnit.Meter, _userLocation, e.location);
                    if (minDistance == null || d < minDistance) {
                        minDistance = d;
                        closestEncounter = e;
                    }
                }

                bool isNear = minDistance != null && minDistance <= 30;

                if (isNear && closestEncounter != null) {
                  return Positioned(
                    bottom: service.activeQuests.isNotEmpty ? 220 : 40, // Move up if HUD is present
                    right: 20,
                    child: FloatingActionButton.extended(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => EncounterScreen(
                              encounter: closestEncounter!,
                            ),
                          ),
                        );
                      },
                      backgroundColor: KeldorTheme.primary,
                      foregroundColor: KeldorTheme.background,
                      icon: const Icon(Icons.visibility),
                      label: Text("VIZSGÁLD MEG (${closestEncounter.title})"),
                    ),
                  );
                }
                return const SizedBox.shrink();
              },
            ),


           // Active Quest HUD
           if (service.activeQuests.isNotEmpty)
             _buildActiveQuestHud(service.activeQuests.first, service),
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

  void _showQuestCard(Quest quest) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black54,
      isScrollControlled: true,
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: KeldorTheme.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          border: Border.all(color: KeldorTheme.primary.withOpacity(0.2)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(quest.title, style: KeldorTheme.darkTheme.textTheme.displayMedium),
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.white54),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (quest.imageUrl != null) ...[
               ClipRRect(
                 borderRadius: BorderRadius.circular(12),
                 child: Stack(
                   children: [
                      Image.asset(
                        quest.imageUrl!,
                        height: 150,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Container(height: 150, color: Colors.white10),
                      ),
                      Positioned.fill(
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [Colors.transparent, Colors.black.withOpacity(0.8)],
                            ),
                          ),
                        ),
                      ),
                   ],
                 ),
               ),
               const SizedBox(height: 16),
            ],
            Text(
              quest.flavorText ?? quest.description,
              style: KeldorTheme.darkTheme.textTheme.bodyLarge?.copyWith(fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                const Icon(Icons.stars, color: KeldorTheme.primary, size: 20),
                const SizedBox(width: 8),
                Text("${quest.rewardsXp} XP Reward", style: const TextStyle(color: KeldorTheme.primary, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            ...quest.objectives.map((o) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                    children: [
                        const Icon(Icons.radio_button_unchecked, color: KeldorTheme.primary, size: 16),
                        const SizedBox(width: 12),
                        Text(o.description, style: const TextStyle(color: Colors.white70)),
                    ]
                ),
            )),
             const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () async {
                    final token = context.read<AuthService>().token;
                    if (token != null) {
                        final success = await context.read<KeldorService>().acceptQuest(token, quest.id);
                        if (success && mounted) {
                            Navigator.pop(context);
                            ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text("Küldetés elfogadva!"))
                            );
                        }
                    }
                },
                child: const Text("ELFOGADOM"),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
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
          } catch (e) {
              // Not found
          }
          
          if (targetLoc != null) {
              lines.add(Polyline(
                  points: [_userLocation, targetLoc],
                  strokeWidth: 4.5,
                  color: KeldorTheme.primary.withOpacity(0.8),
                  isDotted: false,
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
                        Navigator.pop(context);
                        final token = context.read<AuthService>().token;
                        if (token != null) {
                          // Accept the quest
                          await service.acceptQuest(token, quest.id);
                          
                          // Get the first stage's encounter
                          if (quest.stages.isNotEmpty) {
                            final firstStage = quest.stages[0];
                            final encounterId = firstStage.encounterId;
                            
                            if (encounterId == null) {
                              print('❌ No encounter ID for first stage');
                              return;
                            }
                            
                            print('🎯 Looking for encounter: $encounterId');
                            print('🎯 Nearby encounters: ${service.nearbyEncounters.map((e) => e.id).toList()}');
                            
                            // Find the encounter in nearby encounters or dynamic encounters
                            final encounter = service.nearbyEncounters.firstWhere(
                              (e) => e.id == encounterId,
                              orElse: () {
                                print('⚠️ Encounter not found in nearby, creating placeholder');
                                return Encounter(
                                  id: encounterId,
                                  title: firstStage.description,
                                  description: quest.description,
                                  type: EncounterType.story,
                                  location: firstStage.location,
                                  startNodeId: 'start',
                                  nodes: {}, // Will be loaded from backend
                                  zoneId: quest.starterZoneId ?? 'zone_nyolcker',
                                );
                              },
                            );
                            
                            print('✅ Opening encounter: ${encounter.id}');
                            
                            // Open the encounter screen
                            if (mounted) {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => EncounterScreen(encounter: encounter),
                                ),
                              );
                            }
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
}
