
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/story.dart';
import '../models/session.dart';

class ApiService {
  static const String prodUrl = 'https://storyturak-backend.onrender.com';
  static const String localUrl = 'http://10.0.2.2:8001';

  Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final isLocal = prefs.getBool('use_local_backend') ?? false;
    final localIp = prefs.getString('local_ip') ?? '10.0.2.2';
    return isLocal ? 'http://$localIp:8001' : prodUrl;
  }

  Future<Story> fetchStory(String storyId) async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/stories/$storyId'));

    if (response.statusCode == 200) {
      return Story.fromJson(json.decode(utf8.decode(response.bodyBytes)));
    } else {
      throw Exception('Failed to load story: ${response.statusCode}');
    }
  }

  Future<List<Story>> fetchStories() async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/stories'));

    if (response.statusCode == 200) {
      Iterable l = json.decode(utf8.decode(response.bodyBytes));
      return List<Story>.from(l.map((model) => Story.fromJson(model)));
    } else {
      throw Exception('Failed to load stories');
    }
  }

  Future<Session> createSession(String campaignId, Player host) async {
    final baseUrl = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/session/create?campaign_id=$campaignId'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(host.toJson()),
    );

    if (response.statusCode == 200) {
      return Session.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create session');
    }
  }

  Future<Session> joinSession(String code, Player user) async {
    final baseUrl = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/session/join'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'code': code, 'user': user.toJson()}),
    );

    if (response.statusCode == 200) {
      return Session.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to join session');
    }
  }

  Future<Session> getSession(String code) async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/session/$code'));
    if (response.statusCode == 200) {
      return Session.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to fetch session');
    }
  }

  // --- Auth & Progress ---

  Future<Player> register(String username, String password) async {
    final baseUrl = await getBaseUrl();
    print("📡 Registering user at $baseUrl...");
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'username': username, 'password': password}),
      ).timeout(const Duration(seconds: 10));

      print("📡 Response status: ${response.statusCode}");
      if (response.statusCode == 200) {
        return Player.fromJson(json.decode(response.body));
      } else {
        try {
          final error = json.decode(response.body);
          throw Exception(error['detail'] ?? 'Registration failed');
        } catch (_) {
          throw Exception('Hiba történt (${response.statusCode})');
        }
      }
    } catch (e) {
      print("❌ Registration error: $e");
      rethrow;
    }
  }

  Future<Player> login(String username, String password) async {
    final baseUrl = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'username': username, 'password': password}),
    );

    if (response.statusCode == 200) {
      return Player.fromJson(json.decode(response.body));
    } else {
      final error = json.decode(response.body);
      throw Exception(error['detail'] ?? 'Login failed');
    }
  }

  Future<void> saveProgress(String userId, String storyId, String nodeId, Map<String, dynamic> variables) async {
    final baseUrl = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/progress/$userId/$storyId'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'nodeId': nodeId, 'variables': variables}),
    );
    if (response.statusCode != 200) throw Exception('Failed to save progress');
  }

  Future<Map<String, dynamic>?> getProgress(String userId, String storyId) async {
    final baseUrl = await getBaseUrl();
    final response = await http.get(Uri.parse('$baseUrl/progress/$userId/$storyId'));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['nodeId'] == null) return null;
      return data;
    }
    return null;
  }

  Future<void> addXp(String userId, int amount) async {
    final baseUrl = await getBaseUrl();
    final response = await http.post(
      Uri.parse('$baseUrl/progress/$userId/any/xp?amount=$amount'),
      headers: {'Content-Type': 'application/json'},
    );
    if (response.statusCode != 200) throw Exception('Failed to add XP');
  }

  Future<void> logEvent(String? userId, String type, Map<String, dynamic> payload) async {
    final baseUrl = await getBaseUrl();
    await http.post(
      Uri.parse('$baseUrl/analytics/log'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'userId': userId,
        'type': type,
        'payload': payload,
      }),
    );
  }
}
