import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';

class RoutingService {
  // Using OSRM public instance which is reliable for walking routes
  static const String _baseUrl = 'https://router.project-osrm.org/route/v1/foot';

  Future<List<LatLng>> getRoute(LatLng start, LatLng destination) async {
    final url = '$_baseUrl/${start.longitude},${start.latitude};${destination.longitude},${destination.latitude}?overview=full&geometries=geojson';
    print('🚗 Fetching route: $url');
    
    try {
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['routes'] != null && data['routes'].isNotEmpty) {
          final List coordinates = data['routes'][0]['geometry']['coordinates'];
          print('✅ Route found with ${coordinates.length} points');
          return coordinates.map((coord) => LatLng(coord[1].toDouble(), coord[0].toDouble())).toList();
        }
        print('⚠️ OSRM: No routes found in response');
        return []; // Important to return empty list instead of fallback markers here
      } else {
        print('OSRM API Error: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('OSRM Exception: $e');
      return [];
    }
  }
}
