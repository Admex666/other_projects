
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/story.dart';
import '../models/session.dart';

class ApiService {
  // Check emulator vs real device IP. For Windows executable use localhost.
  static const String baseUrl = 'http://192.168.31.86:8001';

  Future<Story> fetchStory(String storyId) async {
    final response = await http.get(Uri.parse('$baseUrl/stories/$storyId'));

    if (response.statusCode == 200) {
      return Story.fromJson(json.decode(utf8.decode(response.bodyBytes)));
    } else {
      throw Exception('Failed to load story: ${response.statusCode}');
    }
  }

  Future<Session> createSession(String campaignId, Player host) async {
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

