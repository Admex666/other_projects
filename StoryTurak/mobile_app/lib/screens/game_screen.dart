
import 'dart:async';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/story.dart';
import '../services/story_engine.dart';
import '../services/location_service.dart';
import '../services/api_service.dart';
import '../services/socket_service.dart';
import '../services/asset_service.dart';
import 'package:flutter_compass/flutter_compass.dart';
import 'dart:convert';
import 'dart:math' as math;

import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/routing_service.dart';
import '../services/map_config.dart';

class GameScreen extends StatefulWidget {
  final String storyId;
  final String? initialNodeId;
  final Map<String, dynamic>? initialVars;
  final String? sessionId;
  final String? userId;

  const GameScreen({
    super.key, 
    required this.storyId, 
    this.initialNodeId,
    this.initialVars,
    this.sessionId,
    this.userId,
  });

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  late StoryEngine _engine;
  final LocationService _locationService = LocationService();
  final ApiService _api = ApiService();
  final SocketService _socket = SocketService();
  final RoutingService _routingService = RoutingService();
  final MapController _mapController = MapController();
  final DraggableScrollableController _sheetController = DraggableScrollableController();
  
  LatLng _currentPos = const LatLng(47.4979, 19.0402);
  List<LatLng> _routePoints = [];
  List<String> _currentOrder = [];
  Map<String, LatLng> _otherPlayers = {};
  bool _isLoading = true;
  double _distanceToTarget = 0.0;
  double _minDistanceWitnessed = double.infinity; // For rerouting
  bool _hasHapticTriggered = false;
  String? _errorMessage;
  double? _heading;
  DateTime? _lastPosTime; // For velocity check
  LatLng? _lastPos; // For velocity check
  StreamSubscription? _compassSubscription;
  StreamSubscription? _positionSubscription;
  bool _followUser = true;
  MapStyle _currentStyle = MapConfig.getStyle('dark');

  @override
  void initState() {
    super.initState();
    _engine = Provider.of<StoryEngine>(context, listen: false);
    _initGame();
    _initCompass();
    _loadMapStyle();
  }

  Future<void> _loadMapStyle() async {
    final prefs = await SharedPreferences.getInstance();
    final styleId = prefs.getString('map_style') ?? 'dark';
    if (mounted) {
      setState(() {
        _currentStyle = MapConfig.getStyle(styleId);
      });
    }
  }

  void _initCompass() {
    _compassSubscription = FlutterCompass.events?.listen((event) {
      if (mounted) {
        setState(() {
          _heading = event.heading;
        });
      }
    });
  }

  Future<void> _initGame() async {
    try {
      final story = await _api.fetchStory(widget.storyId);
      if (mounted) await AssetService.preloadStoryAssets(context, story);
      _engine.loadStory(story, 
          startAtNodeId: widget.initialNodeId, 
          initialVars: widget.initialVars);
      
      _engine.addListener(_onEngineChange);
      
      if (mounted) {
        setState(() { 
          _hasHapticTriggered = false;
          if (_engine.currentNode?.orderAnswer != null) {
            _currentOrder = List<String>.from(_engine.currentNode!.orderAnswer!)..shuffle();
          }
        });
        _updateRoute();
        if (widget.sessionId != null) {
          _socket.sendAdvance(_engine.storyId!, _engine.currentNode!.id, _engine.variables);
        }
      }

      if (widget.sessionId != null && widget.userId != null) {
        await _socket.connect(widget.sessionId!, widget.userId!);
        _socket.stream.listen(_handleSocketMessage);
      }

      _positionSubscription = _locationService.positionStream.listen((pos) {
        if (!mounted) return;
        
        final now = DateTime.now();
        if (_lastPos != null && _lastPosTime != null) {
          final dist = const Distance().as(LengthUnit.Meter, _lastPos!, pos);
          final timeDiff = now.difference(_lastPosTime!).inSeconds;
          if (timeDiff > 0) {
            final speed = dist / timeDiff;
            if (speed > 15) { // 54 km/h - suspicious for walking
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("⚠️ Túl gyorsan haladsz!"), duration: Duration(seconds: 2))
              );
            }
          }
        }
        _lastPos = pos;
        _lastPosTime = now;

        setState(() {
          _currentPos = pos;
          if (widget.sessionId != null) _socket.sendPosition(pos);
          
          if (_followUser) {
            _mapController.move(pos, _mapController.camera.zoom);
          }
          
          final node = _engine.currentNode;
          if (node?.targetLocation != null) {
            _distanceToTarget = const Distance().as(LengthUnit.Meter, _currentPos, node!.targetLocation!);
            
            // Intelligent Rerouting Logic
            if (_distanceToTarget < _minDistanceWitnessed) {
              _minDistanceWitnessed = _distanceToTarget;
            } else if (_distanceToTarget > _minDistanceWitnessed + 50) {
              // User has deviated 50m from their closest approach
              _minDistanceWitnessed = _distanceToTarget; // Reset to avoid constant spam
              _updateRoute();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("🔄 Útvonal újratervezése..."), duration: Duration(seconds: 1))
              );
            }

            if (_distanceToTarget < 20 && !_hasHapticTriggered) {
              HapticFeedback.heavyImpact();
              _hasHapticTriggered = true;
            }
          }
        });
      });
      
      await _updateRoute();
      setState(() => _isLoading = false);
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e.toString();
        });
      }
    }
  }

  Future<void> _updateRoute() async {
    final node = _engine.currentNode;
    if (node?.targetLocation == null) {
      if (mounted) setState(() => _routePoints = []);
      return;
    }

    final points = await _routingService.getRoute(_currentPos, node!.targetLocation!);
    if (mounted) {
      setState(() {
        _routePoints = points;
      });
    }
  }

  void _handleSocketMessage(dynamic data) {
    if (data is String) {
      final msg = jsonDecode(data);
      if (msg['userId'] == widget.userId) return;

      setState(() {
        if (msg['type'] == 'POSITION') {
          _otherPlayers[msg['userId']] = LatLng(msg['lat'], msg['lng']);
        } else if (msg['type'] == 'STORY_ADVANCE') {
          // Sync engine state if another player advanced
          final newNodeId = msg['nodeId'];
          if (_engine.currentNode?.id != newNodeId && _engine.story != null) {
            _engine.loadStory(_engine.story!, 
                startAtNodeId: newNodeId, 
                initialVars: msg['variables']);
          }
        } else if (msg['type'] == 'USER_LEFT') {
          _otherPlayers.remove(msg['userId']);
        }
      });
    }
  }

  void _onEngineChange() {
    if (mounted) {
      setState(() { 
        _hasHapticTriggered = false;
        _minDistanceWitnessed = double.infinity; // Reset for new node
        if (_engine.currentNode?.orderAnswer != null) {
          _currentOrder = List<String>.from(_engine.currentNode!.orderAnswer!)..shuffle();
        }
      });
      _updateRoute();
      if (widget.sessionId != null) {
        _socket.sendAdvance(_engine.storyId!, _engine.currentNode!.id, _engine.variables);
      }
    }
  }

  @override
  void dispose() {
    _engine.removeListener(_onEngineChange);
    _compassSubscription?.cancel();
    _positionSubscription?.cancel();
    _socket.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    
    if (_errorMessage != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, color: Colors.red, size: 60),
                const SizedBox(height: 16),
                Text("Hiba történt:\n\n$_errorMessage", textAlign: TextAlign.center),
                const SizedBox(height: 24),
                ElevatedButton(onPressed: () => Navigator.pop(context), child: const Text("Vissza"))
              ],
            ),
          ),
        ),
      );
    }

    final node = _engine.currentNode;
    if (node == null) return const Scaffold(body: Center(child: Text("Üres történet")));
    
    return Scaffold(
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: node.targetLocation ?? _currentPos,
              initialZoom: 16.0,
              interactionOptions: const InteractionOptions(
                flags: InteractiveFlag.all,
                enableMultiFingerGestureRace: true,
              ),
            ),
            children: [
              TileLayer(
                urlTemplate: _currentStyle.url,
                subdomains: _currentStyle.subdomains,
              ),
              if (_routePoints.isNotEmpty)
                PolylineLayer(
                  polylines: [
                    Polyline(
                      points: _routePoints,
                      color: Colors.blueAccent.withAlpha(180),
                      strokeWidth: 5,
                    ),
                  ],
                ),
                if (_routePoints.isEmpty && node.targetLocation != null)
                PolylineLayer(
                  polylines: [
                    Polyline(
                      points: [_currentPos, node.targetLocation!],
                      color: Colors.blueAccent.withOpacity(0.5),
                      strokeWidth: 4,
                      isDotted: true,
                    ),
                  ],
                ),
              MarkerLayer(
                markers: [
                  ..._otherPlayers.entries.map((e) => Marker(
                    point: e.value,
                    width: 30, height: 30,
                    child: _buildGhostMarker(e.key),
                  )),
                  Marker(
                    point: _currentPos,
                    width: 60, height: 60,
                    child: _buildPlayerMarker(_heading),
                  ),
                  if (node.targetLocation != null)
                     Marker(
                      point: node.targetLocation!,
                      width: 40, height: 40,
                      child: const Icon(Icons.location_on, color: Colors.amber, size: 30),
                    ),
                ],
              ),
            ],
          ),

          Positioned(
            top: 0, left: 0, right: 0,
            child: SafeArea(
              child: LinearProgressIndicator(
                value: _engine.progress,
                backgroundColor: Colors.white10,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.blueAccent.withOpacity(0.8)),
                minHeight: 3,
              ),
            ),
          ),

          DraggableScrollableSheet(
            controller: _sheetController,
            initialChildSize: 0.15,
            minChildSize: 0.1,
            maxChildSize: 0.85,
            builder: (context, scrollController) {
              return ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                child: BackdropFilter(
                  filter: ui.ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                  child: Container(
                    decoration: BoxDecoration(color: const Color(0xFF0F172A).withOpacity(0.85), borderRadius: const BorderRadius.vertical(top: Radius.circular(24))),
                    child: SingleChildScrollView(
                      controller: scrollController,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      child: AnimatedSwitcher(duration: const Duration(milliseconds: 500), child: _buildStoryContent(node)),
                    ),
                  ),
                ),
              );
            },
          ),

          Positioned(
            top: 40, right: 20,
            child: Column(
              children: [
                FloatingActionButton.small(
                  heroTag: "closeBtn",
                  backgroundColor: Colors.black54,
                  child: const Icon(Icons.close, color: Colors.white),
                  onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                ),
                const SizedBox(height: 12),
                FloatingActionButton.small(
                  heroTag: "followBtn",
                  backgroundColor: _followUser ? Colors.blueAccent : Colors.black54,
                  child: Icon(
                    _followUser ? Icons.gps_fixed : Icons.gps_not_fixed, 
                    color: Colors.white
                  ),
                  onPressed: () {
                    setState(() {
                      _followUser = !_followUser;
                      if (_followUser) {
                        _mapController.move(_currentPos, _mapController.camera.zoom);
                      }
                    });
                  },
                ),
                const SizedBox(height: 12),
                FloatingActionButton.small(
                  heroTag: "northBtn",
                  backgroundColor: Colors.black54,
                  child: const Icon(Icons.explore, color: Colors.white),
                  onPressed: () {
                    _mapController.rotate(0);
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayerMarker(double? heading) {
    return Stack(
      alignment: Alignment.center,
      children: [
        if (heading != null)
          Transform.rotate(
            angle: (heading * (math.pi / 180)),
            child: Container(
              width: 50, height: 50,
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  colors: [Colors.blueAccent.withOpacity(0.4), Colors.transparent],
                  center: const Alignment(0, -0.8),
                  radius: 0.8,
                ),
              ),
              child: CustomPaint(
                painter: DirectionPainter(),
              ),
            ),
          ),
        Container(
          width: 15, height: 15,
          decoration: BoxDecoration(
            color: Colors.blueAccent,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: const [BoxShadow(color: Colors.blueAccent, blurRadius: 10, spreadRadius: 2)],
          ),
        ),
      ],
    );
  }

  Widget _buildGhostMarker(String id) {
    return Opacity(
      opacity: 0.6,
      child: Container(
        decoration: BoxDecoration(color: Colors.purpleAccent, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2)),
        child: const Center(child: Icon(Icons.person, size: 12, color: Colors.white)),
      ),
    );
  }

  Widget _buildStoryContent(StoryNode node) {
    return Column(
      key: ValueKey(node.id),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Center(child: Container(width: 40, height: 4, margin: const EdgeInsets.only(bottom: 20), decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)))),
        if (node.type == NodeType.location_wait)
          _buildTravelView(node)
        else
          _buildNarrativeView(node),
      ],
    );
  }

  double _calculateTotalRouteDistance() {
    if (_routePoints.isEmpty) return _distanceToTarget;
    double dist = 0.0;
    for (int i = 0; i < _routePoints.length - 1; i++) {
      dist += const Distance().as(LengthUnit.Meter, _routePoints[i], _routePoints[i+1]);
    }
    return dist;
  }

  Widget _buildTravelView(StoryNode node) {
    final totalDist = _calculateTotalRouteDistance();
    final minutes = (totalDist / 80).ceil(); // ~4.8 km/h walking speed

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildQuickStat(Icons.directions_walk, "${totalDist.toInt()} m"),
            const SizedBox(width: 24),
            _buildQuickStat(Icons.timer_outlined, "$minutes perc"),
          ],
        ),
        const SizedBox(height: 24),
        Text((node.text ?? "Utazás").split('.').first, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
        const SizedBox(height: 20),
        ElevatedButton(onPressed: () => _engine.next(), child: const Text("MEGÉRKEZTEM (SZIMULÁCIÓ)")),
      ],
    );
  }

  Widget _buildQuickStat(IconData icon, String text) {
    return Column(
      children: [
        Icon(icon, color: Colors.amber, size: 20),
        const SizedBox(height: 4),
        Text(text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white)),
      ],
    );
  }

  Widget _buildNarrativeView(StoryNode node) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (node.image != null) ClipRRect(borderRadius: BorderRadius.circular(16), child: Image.asset(node.image!, height: 200, fit: BoxFit.cover)),
        const SizedBox(height: 24),
        Text(node.text ?? "", style: const TextStyle(fontSize: 16, height: 1.6)),
        const SizedBox(height: 32),
        if (node.type == NodeType.narrative)
          ElevatedButton(onPressed: () => node.next == null ? Navigator.pop(context) : _engine.next(), child: Text(node.buttonText ?? 'TOVÁBB')),
        
        if (node.type == NodeType.input && node.orderAnswer != null)
          _buildOrderInput(node)
        else if (node.type == NodeType.input)
          TextField(decoration: InputDecoration(hintText: 'Válasz...', filled: true, fillColor: Colors.white10, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))), onSubmitted: (v) => _engine.handleInput(v)),
        
        if (node.type == NodeType.choice)
          ...node.choices!.asMap().entries.map((e) => Padding(padding: const EdgeInsets.only(bottom: 12), child: OutlinedButton(onPressed: () => _engine.makeChoice(e.key), child: Text(e.value.text)))),
      ],
    );
  }

  Widget _buildOrderInput(StoryNode node) {
    return Column(
      children: [
        const Text("Húzd a megfelelő sorrendbe:", style: TextStyle(color: Colors.white70, fontSize: 13)),
        const SizedBox(height: 16),
        ReorderableListView(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          onReorder: (oldIndex, newIndex) {
            setState(() {
              if (newIndex > oldIndex) newIndex -= 1;
              final item = _currentOrder.removeAt(oldIndex);
              _currentOrder.insert(newIndex, item);
            });
          },
          children: _currentOrder.asMap().entries.map((e) {
            return Card(
              key: ValueKey(e.value),
              color: Colors.white.withOpacity(0.05),
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: const Icon(Icons.drag_handle, color: Colors.white38),
                title: Text(e.value, style: const TextStyle(color: Colors.white)),
                trailing: Text("${e.key + 1}.", style: const TextStyle(color: Colors.blueAccent)),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: () => _engine.checkOrder(_currentOrder),
          style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
          child: const Text("BEKÜLDÉS"),
        ),
      ],
    );
  }
}

class DirectionPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    var paint = Paint()
      ..color = Colors.blueAccent.withOpacity(0.3)
      ..style = PaintingStyle.fill;

    var path = ui.Path();
    path.moveTo(size.width / 2, size.height / 2);
    path.relativeLineTo(-15, -30);
    path.relativeLineTo(30, 0);
    path.close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
