// lib/services/challenge_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/models/challenge.dart';

class ChallengeService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const ChallengeService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  /// Kihívások listázása
  Future<List<Challenge>> getChallenges({
    int limit = 20,
    int skip = 0,
    ChallengeType? challengeType,
    ChallengeDifficulty? difficulty,
    String? search,
    bool onlyAvailable = true,
    String sortBy = 'newest',
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final queryParams = <String, String>{
        'limit': limit.toString(),
        'skip': skip.toString(),
        'only_available': onlyAvailable.toString(),
        'sort_by': sortBy,
      };

      if (challengeType != null) {
        queryParams['challenge_type'] = challengeType.value;
      }
      if (difficulty != null) {
        queryParams['difficulty'] = difficulty.value;
      }
      if (search != null && search.isNotEmpty) {
        queryParams['search'] = search;
      }

      final uri = Uri.parse('$baseUrl/challenges/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final challenges = (data['challenges'] as List<dynamic>)
            .map((json) => Challenge.fromJson(json))
            .toList();
        return challenges;
      } else {
        throw Exception('Failed to load challenges: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting challenges: $e');
      throw Exception('Failed to load challenges: $e');
    }
  }

  /// Egy kihívás részletes adatai
  Future<Challenge> getChallenge(String challengeId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('$baseUrl/challenges/$challengeId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return Challenge.fromJson(data);
      } else {
        throw Exception('Failed to load challenge: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting challenge: $e');
      throw Exception('Failed to load challenge: $e');
    }
  }

  /// Kihíváshoz csatlakozás
  Future<UserChallenge> joinChallenge(
    String challengeId, {
    double? personalTarget,
    String? notes,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final body = <String, dynamic>{};
      if (personalTarget != null) body['personal_target'] = personalTarget;
      if (notes != null && notes.isNotEmpty) body['notes'] = notes;

      final response = await http.post(
        Uri.parse('$baseUrl/challenges/$challengeId/join'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return UserChallenge.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to join challenge');
      }
    } catch (e) {
      print('Error joining challenge: $e');
      if (e.toString().contains('Already participating')) {
        throw Exception('Már részt veszel ebben a kihívásban');
      }
      throw Exception('Nem sikerült csatlakozni a kihíváshoz: $e');
    }
  }

  /// Kihívás elhagyása
  Future<void> leaveChallenge(String challengeId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.delete(
        Uri.parse('$baseUrl/challenges/$challengeId/leave'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode != 204) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to leave challenge');
      }
    } catch (e) {
      print('Error leaving challenge: $e');
      throw Exception('Nem sikerült elhagyni a kihívást: $e');
    }
  }

  /// Saját kihívások listája
  Future<List<UserChallenge>> getMyParticipations({
    int limit = 20,
    int skip = 0,
    ParticipationStatus? status,
    ChallengeType? challengeType,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final queryParams = <String, String>{
        'limit': limit.toString(),
        'skip': skip.toString(),
      };

      if (status != null) {
        queryParams['status'] = status.value;
      }
      if (challengeType != null) {
        queryParams['challenge_type'] = challengeType.value;
      }

      final uri = Uri.parse('$baseUrl/challenges/my/participations').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final userChallenges = (data['user_challenges'] as List<dynamic>)
            .map((json) => UserChallenge.fromJson(json))
            .toList();
        return userChallenges;
      } else {
        throw Exception('Failed to load user challenges: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting user challenges: $e');
      throw Exception('Failed to load user challenges: $e');
    }
  }

  /// Ajánlott kihívások
  Future<List<Challenge>> getRecommendedChallenges({int limit = 5}) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final uri = Uri.parse('$baseUrl/challenges/recommendations/for-me').replace(
        queryParameters: {'limit': limit.toString()},
      );

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final challenges = (data['challenges'] as List<dynamic>)
            .map((json) => Challenge.fromJson(json))
            .toList();
        return challenges;
      } else {
        throw Exception('Failed to load recommended challenges: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting recommended challenges: $e');
      throw Exception('Failed to load recommended challenges: $e');
    }
  }

  /// Kihívás haladás frissítése
  Future<ChallengeProgress> updateChallengeProgress(String challengeId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.post(
        Uri.parse('$baseUrl/challenges/$challengeId/update-progress'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return ChallengeProgress.fromJson(data['progress']);
      } else {
        throw Exception('Failed to update progress: ${response.statusCode}');
      }
    } catch (e) {
      print('Error updating challenge progress: $e');
      throw Exception('Failed to update progress: $e');
    }
  }
}