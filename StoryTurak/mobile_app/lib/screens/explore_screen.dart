import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../models/story.dart';
import 'game_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/map_config.dart';

class ExploreScreen extends StatefulWidget {
  const ExploreScreen({super.key});

  @override
  State<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends State<ExploreScreen> {
  final ApiService _api = ApiService();
  List<Story> _stories = [];
  bool _isLoading = true;
  String? _errorMessage;
  final MapController _mapController = MapController();
  MapStyle _currentStyle = MapConfig.getStyle('dark');

  @override
  void initState() {
    super.initState();
    _loadStories();
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

  Future<void> _loadStories() async {
    try {
      final stories = await _api.fetchStories();
      if (mounted) {
        setState(() {
          _stories = stories;
          _isLoading = false;
        });
        _fitBounds();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _fitBounds() {
    if (_stories.isEmpty) return;
    
    final points = <LatLng>[];
    for (var story in _stories) {
      final startPos = _findFirstLocation(story);
      if (startPos != null) points.add(startPos);
    }

    if (points.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final bounds = LatLngBounds.fromPoints(points);
        _mapController.fitCamera(
          CameraFit.bounds(
            bounds: bounds,
            padding: const EdgeInsets.all(50),
          ),
        );
      });
    }
  }

  LatLng? _findFirstLocation(Story story) {
    // Basic search: return first node that has targetLocation
    for (var node in story.nodes.values) {
      if (node.targetLocation != null) return node.targetLocation;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_errorMessage != null) return Scaffold(body: Center(child: Text("Hiba: $_errorMessage")));

    final markers = _stories.map((story) {
      final pos = _findFirstLocation(story);
      if (pos == null) return null;
      return Marker(
        point: pos,
        width: 45,
        height: 45,
        child: GestureDetector(
          onTap: () => _showStoryPreview(story),
          child: _buildPin(),
        ),
      );
    }).whereType<Marker>().toList();

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: const MapOptions(
              initialCenter: LatLng(47.4979, 19.0402),
              initialZoom: 13,
            ),
            children: [
              TileLayer(
                urlTemplate: _currentStyle.url,
                subdomains: _currentStyle.subdomains,
              ),
              MarkerLayer(markers: markers),
            ],
          ),
          
          Positioned(
            top: 60,
            left: 20,
            child: Text(
              "KALANDOK A KÖZELBEN",
              style: GoogleFonts.outfit(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
                shadows: [const Shadow(color: Colors.black, blurRadius: 10)],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPin() {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 35,
          height: 35,
          decoration: BoxDecoration(
            color: Colors.blueAccent.withOpacity(0.3),
            shape: BoxShape.circle,
          ),
        ),
        const Icon(Icons.location_on, color: Colors.blueAccent, size: 35),
        const Positioned(
          top: 8,
          child: Icon(Icons.circle, color: Colors.white, size: 8),
        ),
      ],
    );
  }

  void _showStoryPreview(Story story) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
          color: Color(0xFF1E293B),
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              story.title,
              style: GoogleFonts.outfit(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              "Kezdd el ezt a kalandot a helyszínen!",
              style: TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => GameScreen(storyId: story.id)),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blueAccent,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text("MEGTEKINTÉS", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}
