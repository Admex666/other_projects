// lib/services/analytics_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user_health.dart';
import 'package:frontend/config/config.dart';
import '../models/admin_models.dart';

class AnalyticsService {
  static const _storage = FlutterSecureStorage();

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  /// Health Score lekérése
  Future<UserHealthScore> getHealthScore() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/analytics/health-score'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return UserHealthScore.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        throw Exception('Failed to load health score: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching health score: $e');
      throw Exception('Hiba a health score betöltése során: $e');
    }
  }

  /// Session tracking
  Future<void> trackSession() async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/analytics/track-session'),
        headers: headers,
      );

      if (response.statusCode != 200) {
        print('Session tracking failed: ${response.statusCode}');
      }
    } catch (e) {
      print('Error tracking session: $e');
      // Ne dobjunk exception-t, mert ez nem kritikus funkció
    }
  }

  /// Feature usage tracking
  Future<void> trackFeatureUsage(String featureName) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/analytics/track-feature/$featureName'),
        headers: headers,
      );

      if (response.statusCode != 200) {
        print('Feature tracking failed for $featureName: ${response.statusCode}');
      }
    } catch (e) {
      print('Error tracking feature usage for $featureName: $e');
      // Ne dobjunk exception-t, mert ez nem kritikus funkció
    }
  }

  /// Bulk feature tracking (több feature egyszerre)
  Future<void> trackMultipleFeatures(List<String> featureNames) async {
    for (final feature in featureNames) {
      await trackFeatureUsage(feature);
      // Kis késleltetés a spam elkerülésére
      await Future.delayed(Duration(milliseconds: 100));
    }
  }

  /// Admin - összes felhasználó health score-ja
  Future<List<AdminUserHealthScore>> getAllHealthScores() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/analytics/admin/all-health-scores'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((item) => AdminUserHealthScore.fromJson(item)).toList();
      } else if (response.statusCode == 403) {
        throw Exception('403: Admin access required');
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        throw Exception('Failed to load admin health scores: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching admin health scores: $e');
      throw Exception('Hiba az admin health score-ok betöltése során: $e');
    }
  }

  /// Admin - általános statisztikák
  Future<AdminStats> getAdminStats() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/analytics/admin/stats'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return AdminStats.fromJson(data);
      } else if (response.statusCode == 403) {
        throw Exception('403: Admin access required');
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        throw Exception('Failed to load admin stats: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching admin stats: $e');
      throw Exception('Hiba az admin statisztikák betöltése során: $e');
    }
  }

  /// Helper method - auth hibák ellenőrzése
  bool isAuthError(dynamic error) {
    final errorStr = error.toString().toLowerCase();
    return errorStr.contains('401') || 
           errorStr.contains('unauthorized') || 
           errorStr.contains('not authenticated') ||
           (errorStr.contains('token') && (errorStr.contains('invalid') || errorStr.contains('expired')));
  }
}