
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/story.dart';
import '../models/session.dart';

class ApiService {
  static const String prodUrl = 'https://storyturak-backend.onrender.com';
  static const String localUrl = 'http://192.168.31.86:8001';

  Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final isLocal = prefs.getBool('use_local_backend') ?? false;
    return isLocal ? localUrl : prodUrl;
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
}
