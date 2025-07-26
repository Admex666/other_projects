// lib/services/badge_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class BadgeService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const BadgeService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<String?> getToken() async {
    return _storage.read(key: 'token');
  }

  // Felhasználó badge-einek lekérése
  Future<Map<String, dynamic>?> getUserBadges({String? category, bool favoriteOnly = false}) async {
    final token = await getToken();
    if (token == null) return null;

    String url = '$baseUrl/badges/my-badges';
    List<String> queryParams = [];
    
    if (category != null) queryParams.add('category=$category');
    if (favoriteOnly) queryParams.add('favorite_only=true');
    
    if (queryParams.isNotEmpty) {
      url += '?${queryParams.join('&')}';
    }

    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Error fetching user badges: $e');
      return null;
    }
  }

  // Badge haladás lekérése
  Future<Map<String, dynamic>?> getBadgeProgress() async {
    final token = await getToken();
    if (token == null) return null;

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/badges/progress'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Error fetching badge progress: $e');
      return null;
    }
  }

  // Badge statisztikák lekérése
  Future<Map<String, dynamic>?> getBadgeStats() async {
    final token = await getToken();
    if (token == null) return null;

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/badges/stats'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Error fetching badge stats: $e');
      return null;
    }
  }

  // Badge beállítások frissítése
  Future<bool> updateBadge(String badgeId, {bool? isFavorite, bool? isVisible}) async {
    final token = await getToken();
    if (token == null) return false;

    Map<String, dynamic> updateData = {};
    if (isFavorite != null) updateData['is_favorite'] = isFavorite;
    if (isVisible != null) updateData['is_visible'] = isVisible;

    try {
      final response = await http.put(
        Uri.parse('$baseUrl/badges/my-badges/$badgeId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(updateData),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error updating badge: $e');
      return false;
    }
  }

  // Kategória statisztikák lekérése
  Future<Map<String, dynamic>?> getCategoryStats(String category) async {
    final token = await getToken();
    if (token == null) return null;

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/badges/categories/$category/stats'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Error fetching category stats: $e');
      return null;
    }
  }

  // Badge leaderboard lekérése
  Future<Map<String, dynamic>?> getBadgeLeaderboard({int limit = 10}) async {
    final token = await getToken();
    if (token == null) return null;

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/badges/leaderboard?limit=$limit'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Error fetching badge leaderboard: $e');
      return null;
    }
  }
}