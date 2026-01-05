import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';

class RoutingService {
  // Using BRouter public instance which is excellent for hiking/trekking
  static const String _baseUrl = 'https://brouter.de/brouter';

  Future<List<LatLng>> getRoute(LatLng start, LatLng destination) async {
    // BRouter expects longitude,latitude|longitude,latitude
    final lonLats = '${start.longitude},${start.latitude}|${destination.longitude},${destination.latitude}';
    final url = '$_baseUrl?lonlats=$lonLats&profile=hiking-mountain&alternativeidx=0&format=geojson';
    
    try {
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        // BRouter GeoJSON structure: features -> geometry -> coordinates
        final List coordinates = data['features'][0]['geometry']['coordinates'];
        
        return coordinates.map((coord) => LatLng(coord[1].toDouble(), coord[0].toDouble())).toList();
      } else {
        print('BRouter API Error: ${response.statusCode}');
        return [start, destination]; // Fallback to straight line
      }
    } catch (e) {
      print('BRouter Exception: $e');
      return [start, destination]; // Fallback
    }
  }
}
