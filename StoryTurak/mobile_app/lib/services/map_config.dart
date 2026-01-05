
class MapStyle {
  final String url;
  final List<String> subdomains;

  const MapStyle(this.url, this.subdomains);
}

class MapConfig {
  static const String darkUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png';
  static const String lightUrl = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png';
  static const String outdoorUrl = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  static const Map<String, MapStyle> styleDetails = {
    'dark': MapStyle(darkUrl, ['a', 'b', 'c', 'd']),
    'light': MapStyle(lightUrl, ['a', 'b', 'c', 'd']),
    'outdoor': MapStyle(outdoorUrl, []),
  };

  static const List<Map<String, String>> styles = [
    {'name': 'Sötét (Dark)', 'id': 'dark'},
    {'name': 'Világos (Light)', 'id': 'light'},
    {'name': 'Utcai (Outdoor)', 'id': 'outdoor'},
  ];

  static MapStyle getStyle(String? id) {
    return styleDetails[id] ?? styleDetails['dark']!;
  }
}
