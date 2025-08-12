// lib/services/accountability_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/accountability_models.dart';
import 'package:frontend/config/config.dart';

class AccountabilityService {
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

  // === PROFILE MANAGEMENT ===

  /// Create accountability profile
  Future<AccountabilityProfile> createProfile(AccountabilityProfile profile) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/accountability/profile'),
        headers: headers,
        body: jsonEncode(profile.toJson()),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return AccountabilityProfile.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Profil létrehozása sikertelen');
      }
    } catch (e) {
      print('Error creating accountability profile: $e');
      throw Exception('Hiba a profil létrehozása során: $e');
    }
  }

  /// Get my accountability profile
  Future<AccountabilityProfile?> getMyProfile() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/accountability/profile'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return AccountabilityProfile.fromJson(data);
      } else if (response.statusCode == 404) {
        return null; // No profile exists
      } else {
        throw Exception('Failed to load profile: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching accountability profile: $e');
      throw Exception('Hiba a profil betöltése során: $e');
    }
  }

  /// Update accountability profile
  Future<AccountabilityProfile> updateProfile(Map<String, dynamic> updates) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('${ApiConfig.baseUrl}/accountability/profile'),
        headers: headers,
        body: jsonEncode(updates),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return AccountabilityProfile.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Profil frissítése sikertelen');
      }
    } catch (e) {
      print('Error updating accountability profile: $e');
      throw Exception('Hiba a profil frissítése során: $e');
    }
  }

  // === MATCHING ===

  /// Get partner suggestions (Plus/Pro only)
  Future<List<PartnerSuggestion>> getPartnerSuggestions({int limit = 10}) async {
    try {
      final headers = await _getHeaders();
      final uri = Uri.parse('${ApiConfig.baseUrl}/accountability/suggestions').replace(
        queryParameters: {'limit': limit.toString()},
      );
      
      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        return data.map((json) => PartnerSuggestion.fromJson(json)).toList();
      } else if (response.statusCode == 403) {
        throw Exception('Matching funkció csak Plus és Pro előfizetőknek elérhető');
      } else {
        throw Exception('Failed to load suggestions: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching partner suggestions: $e');
      throw Exception('Hiba a partner javaslatok betöltése során: $e');
    }
  }

  // === PARTNERSHIPS ===

  /// Get my partnerships
  Future<List<Partnership>> getMyPartnerships({PartnershipStatus? status}) async {
    try {
      final headers = await _getHeaders();
      final queryParams = <String, String>{};
      if (status != null) {
        queryParams['status'] = status.value;
      }

      final uri = Uri.parse('${ApiConfig.baseUrl}/accountability/partnerships').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );
      
      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        return data.map((json) => Partnership.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load partnerships: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching partnerships: $e');
      throw Exception('Hiba a partnerkapcsolatok betöltése során: $e');
    }
  }

  /// Send partnership request
  Future<String> sendPartnershipRequest(PartnershipRequest request) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/accountability/partnerships/request'),
        headers: headers,
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return data['partnership_id'];
      } else if (response.statusCode == 403) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Partnerlimit elérve');
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Partnership kérelem sikertelen');
      }
    } catch (e) {
      print('Error sending partnership request: $e');
      throw Exception('Hiba a partnership kérelem küldése során: $e');
    }
  }

  /// Respond to partnership request
  Future<bool> respondToPartnership(String partnershipId, bool accept, {String? message}) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/accountability/partnerships/$partnershipId/respond'),
        headers: headers,
        body: jsonEncode({
          'accept': accept,
          if (message != null) 'message': message,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error responding to partnership: $e');
      return false;
    }
  }

  /// End partnership
  Future<bool> endPartnership(String partnershipId, {String? reason}) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/accountability/partnerships/$partnershipId/end'),
        headers: headers,
        body: jsonEncode({
          if (reason != null) 'reason': reason,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error ending partnership: $e');
      return false;
    }
  }

  // === CHECK-INS ===

  /// Create check-in
  Future<CheckIn> createCheckIn(String partnershipId, CheckIn checkIn) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/accountability/partnerships/$partnershipId/checkins'),
        headers: headers,
        body: jsonEncode(checkIn.toJson()),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return CheckIn.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Check-in létrehozása sikertelen');
      }
    } catch (e) {
      print('Error creating check-in: $e');
      throw Exception('Hiba a check-in létrehozása során: $e');
    }
  }

  /// Get check-ins for partnership
  Future<List<CheckIn>> getCheckIns(String partnershipId, {int? limit, String? userId}) async {
    try {
      final headers = await _getHeaders();
      final queryParams = <String, String>{};
      if (limit != null) queryParams['limit'] = limit.toString();
      if (userId != null) queryParams['user_id'] = userId;

      final uri = Uri.parse('${ApiConfig.baseUrl}/accountability/partnerships/$partnershipId/checkins').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );
      
      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        return data.map((json) => CheckIn.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load check-ins: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching check-ins: $e');
      throw Exception('Hiba a check-in-ek betöltése során: $e');
    }
  }

  /// Get today's check-in status
  Future<bool> getTodayCheckInStatus(String partnershipId, String userId) async {
    try {
      final today = DateTime.now().toIso8601String().split('T')[0];
      final checkIns = await getCheckIns(partnershipId, userId: userId);
      
      return checkIns.any((checkIn) => checkIn.date == today);
    } catch (e) {
      print('Error checking today check-in status: $e');
      return false;
    }
  }

  // === SEARCH ===

  /// Search users for partnerships (Free users)
  Future<List<PartnerSuggestion>> searchUsers(String query, {int limit = 20}) async {
    try {
      final headers = await _getHeaders();
      final uri = Uri.parse('${ApiConfig.baseUrl}/accountability/search').replace(
        queryParameters: {
          'q': query,
          'limit': limit.toString(),
        },
      );
      
      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        return data.map((json) => PartnerSuggestion.fromJson(json)).toList();
      } else {
        throw Exception('Failed to search users: ${response.statusCode}');
      }
    } catch (e) {
      print('Error searching users: $e');
      throw Exception('Hiba a felhasználók keresése során: $e');
    }
  }
}