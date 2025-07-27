// lib/services/pti_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/models/pti_models.dart';

class PTIService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const PTIService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// PTI Dashboard adatok lekérése
  Future<PTIDashboardResponse?> getDashboard() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/pti/dashboard'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PTIDashboardResponse.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error getting PTI dashboard: $e');
      return null;
    }
  }

  /// PTI pontszám lekérése
  Future<PTIScoreResponse?> getPTIScore({
    PTIPeriod period = PTIPeriod.weekly,
    bool calculate = false,
  }) async {
    try {
      final headers = await _getHeaders();
      final queryParams = {
        'period': period.value,
        'calculate': calculate.toString(),
      };
      
      final uri = Uri.parse('$baseUrl/pti/score').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PTIScoreResponse.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error getting PTI score: $e');
      return null;
    }
  }

  /// PTI számítás indítása
  Future<bool> calculatePTI({
    PTIPeriod period = PTIPeriod.weekly,
    bool forceRecalculate = false,
  }) async {
    try {
      final headers = await _getHeaders();
      final body = jsonEncode({
        'period': period.value,
        'force_recalculate': forceRecalculate,
      });

      final response = await http.post(
        Uri.parse('$baseUrl/pti/calculate'),
        headers: headers,
        body: body,
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error calculating PTI: $e');
      return false;
    }
  }

  /// Ranglista lekérése
  Future<PTIRankingResponse?> getRanking({
    PTIPeriod period = PTIPeriod.weekly,
    RankingScope scope = RankingScope.global,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final headers = await _getHeaders();
      final queryParams = {
        'period': period.value,
        'scope': scope.value,
        'limit': limit.toString(),
        'offset': offset.toString(),
      };
      
      final uri = Uri.parse('$baseUrl/pti/ranking').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PTIRankingResponse.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error getting PTI ranking: $e');
      return null;
    }
  }

  /// PTI beállítások lekérése
  Future<PTIUserSettings?> getSettings() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/pti/settings'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PTIUserSettings.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error getting PTI settings: $e');
      return null;
    }
  }

  /// PTI beállítások frissítése
  Future<PTIUserSettings?> updateSettings(PTIUserSettings settings) async {
    try {
      final headers = await _getHeaders();
      final body = jsonEncode(settings.toJson());

      final response = await http.put(
        Uri.parse('$baseUrl/pti/settings'),
        headers: headers,
        body: body,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PTIUserSettings.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error updating PTI settings: $e');
      return null;
    }
  }

  /// PTI összehasonlítás lekérése
  Future<PTIComparisonResponse?> getComparison({
    PTIPeriod period = PTIPeriod.weekly,
  }) async {
    try {
      final headers = await _getHeaders();
      final queryParams = {
        'period': period.value,
      };
      
      final uri = Uri.parse('$baseUrl/pti/comparison').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PTIComparisonResponse.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error getting PTI comparison: $e');
      return null;
    }
  }

  /// Fejlesztési javaslatok lekérése
  Future<List<String>> getImprovementSuggestions() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/pti/suggestions'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<String>.from(data['suggestions'] ?? []);
      }
      return [];
    } catch (e) {
      print('Error getting PTI suggestions: $e');
      return [];
    }
  }

  /// Ranglista statisztikák
  Future<Map<String, dynamic>?> getLeaderboardStats({
    PTIPeriod period = PTIPeriod.weekly,
  }) async {
    try {
      final headers = await _getHeaders();
      final queryParams = {
        'period': period.value,
      };
      
      final uri = Uri.parse('$baseUrl/pti/leaderboard/stats').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (e) {
      print('Error getting leaderboard stats: $e');
      return null;
    }
  }
}