import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';

class RoutingService {
  // Primary: OSRM DE (More stable for Europe)
  static const String _baseUrlPrimary = 'https://routing.openstreetmap.de/routed-foot/route/v1/foot';
  // Fallback: Project OSRM Demo
  static const String _baseUrlFallback = 'https://router.project-osrm.org/route/v1/foot';

  Future<List<LatLng>?> getRoute(LatLng start, LatLng destination) async {
    // Try Primary
    var route = await _fetchRoute(_baseUrlPrimary, start, destination);
    if (route != null && route.isNotEmpty) return route;

    print('⚠️ Primary routing failed, trying fallback...');
    // Try Fallback
    return await _fetchRoute(_baseUrlFallback, start, destination);
  }

  Future<List<LatLng>?> _fetchRoute(String baseUrl, LatLng start, LatLng destination) async {
    final url = '$baseUrl/${start.longitude},${start.latitude};${destination.longitude},${destination.latitude}?overview=full&geometries=geojson';
    
    try {
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['routes'] != null && data['routes'].isNotEmpty) {
          final List coordinates = data['routes'][0]['geometry']['coordinates'];
          return coordinates.map((coord) => LatLng(coord[1].toDouble(), coord[0].toDouble())).toList();
        }
      }
      return null;
    } catch (e) {
      print('Routing Exception ($baseUrl): $e');
      return null;
    }
  }
}
