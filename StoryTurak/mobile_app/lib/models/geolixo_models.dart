import 'package:latlong2/latlong.dart';

enum CharacterClass {
  soldier,
  poet,
  tax_collector,
  pilgrim,
}

enum EncounterType {
  fight,
  puzzle,
  narrative,
  shop,
}

class Zone {
  final String id;
  final String name;
  final String description;
  final List<LatLng> boundaryPoints;
  final int difficultyLevel;

  Zone({
    required this.id,
    required this.name,
    required this.description,
    required this.boundaryPoints,
    required this.difficultyLevel,
  });

  factory Zone.fromJson(Map<String, dynamic> json) {
    return Zone(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      boundaryPoints: (json['boundary_points'] as List)
          .map((p) => LatLng(p[0] as double, p[1] as double))
          .toList(),
      difficultyLevel: json['difficulty_level'] ?? 1,
    );
  }
}

class Encounter {
  final String id;
  final String title;
  final String description;
  final EncounterType type;
  final String zoneId;

  Encounter({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.zoneId,
  });

  factory Encounter.fromJson(Map<String, dynamic> json) {
    return Encounter(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      type: EncounterType.values.firstWhere(
        (e) => e.toString().split('.').last == json['type'],
        orElse: () => EncounterType.narrative,
      ),
      zoneId: json['zone_id'],
    );
  }
}
