import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';
import '../models/keldor_models.dart';

class KeldorService extends ChangeNotifier {
  static const String baseUrl = 'http://192.168.31.86:8001'; // LAN IP for physical device
  // static const String baseUrl = 'http://10.0.2.2:8001'; // Android Emulator

  static void Function()? onUnauthorized;

  void _checkResponse(http.Response response) {
    if (response.statusCode == 401) {
      onUnauthorized?.call();
    }
  }

  // Fallback / Initial State (Budapest Pilot)
  List<Zone> activeZones = [
      // 1. Belváros
      Zone(
        id: "zone_belvaros",
        name: "Belváros - A Ködös Utcák",
        description: "A régi Pest szíve. Itt a legerősebb a Rend őreinek jelenléte, de a földalatti járatokban más világ uralkodik.",
        boundaryPoints: [
          const LatLng(47.498, 19.040),
          const LatLng(47.502, 19.050),
          const LatLng(47.495, 19.060),
          const LatLng(47.490, 19.045)
        ],
        difficultyLevel: 1,
      ),
      // 2. VIII. Kerület
      Zone(
        id: "zone_nyolcker",
        name: "VIII. Kerület - A Sötét Parkok",
        description: "A senki földje. Kereskedők, csempészek és bukott költők tanyája.",
        boundaryPoints: [
          const LatLng(47.495, 19.065), 
          const LatLng(47.498, 19.080),
          const LatLng(47.485, 19.085), 
          const LatLng(47.485, 19.070)
        ],
        difficultyLevel: 3,
      ),
  ];
  List<Encounter> nearbyEncounters = []; // Populated by fetch or fallback
  bool isLoading = false;

  Future<void> fetchNearbyWorld(String? token, LatLng location) async {
    isLoading = true;
    notifyListeners();

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/world/nearby?lat=${location.latitude}&lon=${location.longitude}'),
        headers: token != null ? {'Authorization': 'Bearer $token'} : {},
      );
      _checkResponse(response);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        activeZones = (data['zones'] as List)
            .map((z) => Zone.fromJson(z))
            .toList();
            
        nearbyEncounters = (data['encounters'] as List)
            .map((e) => Encounter.fromJson(e))
            .toList();
      } else {
        print("Failed to load world data: ${response.statusCode}");
      }
    } catch (e) {
      print("Error fetching world data: $e");
      print("Error fetching world data: $e");
      // Fallback for demo/offline/network issues
      print("⚠️ TRIGGERING FALLBACK DATA (Offline Mode) ⚠️");
      // Zones are already initialized in constructor for immediate map render, 
      // but if list is empty for some reason, restore them:
      if (activeZones.isEmpty) {
         activeZones = [
            Zone(
              id: "zone_belvaros",
              name: "Belváros - A Ködös Utcák",
              description: "A régi Pest szíve.",
              boundaryPoints: [
                const LatLng(47.498, 19.040),
                const LatLng(47.502, 19.050),
                const LatLng(47.495, 19.060),
                const LatLng(47.490, 19.045)
              ],
              difficultyLevel: 1,
            ),
             Zone(
              id: "zone_nyolcker",
              name: "VIII. Kerület",
              description: "A senki földje.",
              boundaryPoints: [
                const LatLng(47.495, 19.065), 
                const LatLng(47.498, 19.080),
                const LatLng(47.485, 19.085), 
                const LatLng(47.485, 19.070)
              ],
              difficultyLevel: 3,
            ),
         ];
      }

      // Add offline encounters matching the zones
      nearbyEncounters = [
        Encounter(
          id: "enc_poet_ghost",
          title: "Az Elfeledett Költő Szelleme",
          description: "Egy halvány alak szaval a lámpaoszlop alatt.",
          type: EncounterType.story,
          startNodeId: "start",
          nodes: {
            "start": EncounterNode(
                id: "start",
                type: EncounterNodeType.narrative,
                text: "A szellem feléd fordul. 'Emlékszel még?'",
                nextNodeId: "end"
            ),
            "end": EncounterNode(
                id: "end",
                type: EncounterNodeType.narrative,
                text: "A köd eloszlik."
            )
          },
          location: const LatLng(47.498, 19.040),
          zoneId: "zone_belvaros",
        ),
      ];
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  // --- Character Management ---
  Character? activeCharacter;
  List<Character> userCharacters = [];

  void setActiveCharacter(Character char) {
      activeCharacter = char;
      notifyListeners();
  }

  void clearActiveCharacter() {
      activeCharacter = null;
      notifyListeners();
  }
  
  Future<void> fetchUserCharacters(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/characters'),
        headers: {'Authorization': 'Bearer $token'},
      );
      _checkResponse(response);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        userCharacters = data.map((d) => Character.fromJson(d)).toList();
        
        // If we have an active character, update its data from the list
        if (activeCharacter != null) {
            try {
                activeCharacter = userCharacters.firstWhere((c) => c.id == activeCharacter!.id);
            } catch (e) {
                // Keep old one or clear? Let's keep for now or clear if not found at all
            }
        }
        notifyListeners();
      } else {
        print("Failed to fetch characters: ${response.statusCode}");
      }
    } catch (e) {
      print("Error fetching characters: $e");
    }
  }

  // Backward compatibility alias
  Future<void> fetchUserCharacter(String token) => fetchUserCharacters(token);

  Future<void> markZoneVisited(String token, String charId, String zoneId) async {
    try {
        await http.post(
            Uri.parse('$baseUrl/characters/$charId/visit-zone?zone_id=$zoneId'),
            headers: {'Authorization': 'Bearer $token'},
        );
    } catch (e) {
        print("Error marking zone visited: $e");
    }
  }

  // --- Quest Management ---
  List<Quest> allQuests = [];
  List<Quest> availableQuests = [];
  List<UserQuest> activeQuests = [];

  Future<void> fetchQuests(String token) async {
    try {
        // 1. Fetch Active Quests for Character
        if (activeCharacter != null) {
            final activeResp = await http.get(
                Uri.parse('$baseUrl/characters/${activeCharacter!.id}/quests'),
                headers: {'Authorization': 'Bearer $token'},
            );
            _checkResponse(activeResp);
            if (activeResp.statusCode == 200) {
                final List<dynamic> data = json.decode(activeResp.body);
                activeQuests = data.map((q) => UserQuest.fromJson(q)).toList();
            }
        }

        // 2. Fetch All Quests
        final availResp = await http.get(
            Uri.parse('$baseUrl/test/quests'),  // TEMP: Using test endpoint
            headers: {'Authorization': 'Bearer $token'},
        );
        _checkResponse(availResp);
        print('🔍 Quest fetch status: ${availResp.statusCode}');
        if (availResp.statusCode == 200) {
            final Map<String, dynamic> data = json.decode(availResp.body);
            final List<dynamic> questList = data['quests'];
            allQuests = questList.map((q) => Quest.fromJson(q)).toList();
            
            // Filter out quests already active (ignore completed/failed for availability)
            final activeIds = activeQuests
                .where((aq) => aq.status == QuestStatus.active)
                .map((aq) => aq.questId)
                .toSet();
            availableQuests = allQuests
                .where((q) => !activeIds.contains(q.id))
                .toList();
            
            print('📋 Total quests: ${allQuests.length}, Active: ${activeQuests.length}, Available: ${availableQuests.length}');
            for (var q in availableQuests) {
                print('   📍 ${q.title} at ${q.startLocation}');
            }
        } else {
            print('❌ Quest fetch failed: ${availResp.statusCode} - ${availResp.body}');
        }
        
        notifyListeners();
        
    } catch (e) {
        print("Error fetching quests: $e");
    }
  }

  Future<bool> acceptQuest(String token, String questId) async {
      try {
          final response = await http.post(
              Uri.parse('$baseUrl/quests/$questId/accept'),
              headers: {'Authorization': 'Bearer $token'},
          );
          
          _checkResponse(response);
          if (response.statusCode == 200) {
              await fetchQuests(token); // Refresh state
              return true;
          }
          return false;
      } catch (e) {
          print("Error accepting quest: $e");
          return false;
      }
  }

  Future<bool> abandonQuest(String token, String userQuestId) async {
      try {
          final response = await http.delete(
              Uri.parse('$baseUrl/user-quests/$userQuestId'),
              headers: {'Authorization': 'Bearer $token'},
          );
          
          _checkResponse(response);
          if (response.statusCode == 200) {
              await fetchQuests(token); // Refresh state
              return true;
          }
          return false;
      } catch (e) {
          print("Error abandoning quest: $e");
          return false;
      }
  }

  Future<Map<String, dynamic>?> resolveEncounter(String token, String encounterId, String outcome) async {
      try {
          final response = await http.post(
              Uri.parse('$baseUrl/encounters/resolve'),
              headers: {
                  'Authorization': 'Bearer $token',
                  'Content-Type': 'application/json',
              },
              body: json.encode({
                  "encounter_id": encounterId,
                  "outcome": outcome
              }),
          );
          
          _checkResponse(response);
          if (response.statusCode == 200) {
              final data = json.decode(response.body);
              // Refresh character and quests to show new state immediately
              await fetchUserCharacter(token);
              await fetchQuests(token);
              return data;
          }
          print("Resolve failed: ${response.body}");
          return null;
      } catch (e) {
          print("Error resolving encounter: $e");
          return null;
      }
  }

  // Ray-casting algorithm to check if point is inside polygon
  bool isPointInZone(LatLng point, Zone zone) {
    int intersectCount = 0;
    List<LatLng> polygon = zone.boundaryPoints;
    
    for (int j = 0; j < polygon.length - 1; j++) {
      if (_rayCastIntersect(point, polygon[j], polygon[j + 1])) {
        intersectCount++;
      }
    }
    // Check last segment connection
    if (_rayCastIntersect(point, polygon.last, polygon.first)) {
      intersectCount++;
    }

    return (intersectCount % 2) == 1; // Odd = inside, Even = outside
  }

  bool _rayCastIntersect(LatLng point, LatLng vertA, LatLng vertB) {
    double aY = vertA.latitude;
    double bY = vertB.latitude;
    double pY = point.latitude;
    double aX = vertA.longitude;
    double bX = vertB.longitude;
    double pX = point.longitude;

    if ((aY > pY && bY > pY) || (aY < pY && bY < pY) || (aX < pX && bX < pX)) {
      return false; 
    }

    double m = (aY - bY) / (aX - bX); // Slope
    double bee = (-aX) * m + aY; // Y-intercept
    double x = (pY - bee) / m; // X-coordinate of intersection

    return x > pX;
  }
}
