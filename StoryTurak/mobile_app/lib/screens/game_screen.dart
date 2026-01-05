
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

import 'package:shared_preferences/shared_preferences.dart';
import '../services/map_config.dart';

class GameScreen extends StatefulWidget {
  final String storyId;
  final String? initialNodeId;
  final String? sessionId;
  final String? userId;

  const GameScreen({
    super.key, 
    required this.storyId, 
    this.initialNodeId,
    this.sessionId,
    this.userId,
  });

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  final StoryEngine _engine = StoryEngine();
  final LocationService _locationService = LocationService();
  final ApiService _api = ApiService();
  final SocketService _socket = SocketService();
  final MapController _mapController = MapController();
  final DraggableScrollableController _sheetController = DraggableScrollableController();
  
  LatLng _currentPos = const LatLng(47.4979, 19.0402);
  Map<String, LatLng> _otherPlayers = {};
  bool _isLoading = true;
  double _distanceToTarget = 0.0;
  bool _hasHapticTriggered = false;
  String? _errorMessage;
  double? _heading;
  StreamSubscription? _compassSubscription;
  StreamSubscription? _positionSubscription;
  bool _followUser = true;
  MapStyle _currentStyle = MapConfig.getStyle('dark');

  @override
  void initState() {
    super.initState();
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
      _engine.loadStory(story, startAtNodeId: widget.initialNodeId);
      
      _engine.addListener(() {
        if (mounted) {
          setState(() { _hasHapticTriggered = false; });
          if (widget.sessionId != null) {
            _socket.sendAdvance(_engine.currentNode!.id);
          }
        }
      });

      if (widget.sessionId != null && widget.userId != null) {
        await _socket.connect(widget.sessionId!, widget.userId!);
        _socket.stream.listen(_handleSocketMessage);
      }

      _positionSubscription = _locationService.positionStream.listen((pos) {
        if (!mounted) return;
        setState(() {
          _currentPos = pos;
          if (widget.sessionId != null) _socket.sendPosition(pos);
          
          if (_followUser) {
            _mapController.move(pos, _mapController.camera.zoom);
          }
          
          final node = _engine.currentNode;
          if (node?.targetLocation != null) {
            _distanceToTarget = const Distance().as(LengthUnit.Meter, _currentPos, node!.targetLocation!);
            if (_distanceToTarget < 20 && !_hasHapticTriggered) {
              HapticFeedback.heavyImpact();
              _hasHapticTriggered = true;
            }
          }
        });
      });
      
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

  void _handleSocketMessage(dynamic data) {
    if (data is String) {
      final msg = jsonDecode(data);
      if (msg['userId'] == widget.userId) return;

      setState(() {
        if (msg['type'] == 'POSITION') {
          _otherPlayers[msg['userId']] = LatLng(msg['lat'], msg['lng']);
        } else if (msg['type'] == 'USER_LEFT') {
          _otherPlayers.remove(msg['userId']);
        }
      });
    }
  }

  @override
  void dispose() {
    _compassSubscription?.cancel();
    _positionSubscription?.cancel();
    _socket.disconnect();
    _engine.dispose();
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
            ),
            children: [
              TileLayer(
                urlTemplate: _currentStyle.url,
                subdomains: _currentStyle.subdomains,
              ),
              if (node.targetLocation != null)
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

  Widget _buildTravelView(StoryNode node) {
    return Column(
      children: [
        Text("CÉLPONT", style: TextStyle(fontSize: 10, color: Colors.amber.withOpacity(0.8), letterSpacing: 2)),
        Text(node.text.split('.').first, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
        const SizedBox(height: 12),
        Text("${_distanceToTarget.toInt()} m", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
        const SizedBox(height: 20),
        ElevatedButton(onPressed: () => _engine.next(), child: const Text("MEGÉRKEZTEM (SZIMULÁCIÓ)")),
      ],
    );
  }

  Widget _buildNarrativeView(StoryNode node) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (node.image != null) ClipRRect(borderRadius: BorderRadius.circular(16), child: Image.asset(node.image!, height: 200, fit: BoxFit.cover)),
        const SizedBox(height: 24),
        Text(node.text, style: const TextStyle(fontSize: 16, height: 1.6)),
        const SizedBox(height: 32),
        if (node.type == NodeType.narrative)
          ElevatedButton(onPressed: () => node.next == null ? Navigator.pop(context) : _engine.next(), child: Text(node.buttonText ?? 'TOVÁBB')),
        if (node.type == NodeType.input)
          TextField(decoration: InputDecoration(hintText: 'Válasz...', filled: true, fillColor: Colors.white10, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))), onSubmitted: (v) => _engine.handleInput(v)),
        if (node.type == NodeType.choice)
          ...node.choices!.asMap().entries.map((e) => Padding(padding: const EdgeInsets.only(bottom: 12), child: OutlinedButton(onPressed: () => _engine.makeChoice(e.key), child: Text(e.value.text)))),
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
