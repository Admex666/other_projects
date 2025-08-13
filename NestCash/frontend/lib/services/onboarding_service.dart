// lib/services/onboarding_service.dart - Frissített verzió

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/onboarding_model.dart';
import 'package:frontend/config/config.dart';

class OnboardingService {
  static const _storage = FlutterSecureStorage();

  const OnboardingService();

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

  // Onboarding állapot lekérdezése
  Future<OnboardingStatusResponse> getOnboardingStatus() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/status'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return OnboardingStatusResponse.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        throw Exception('Failed to load onboarding status: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching onboarding status: $e');
      rethrow;
    }
  }

  // Onboarding lépés frissítése
  Future<Map<String, dynamic>> updateOnboardingStep(int stepNumber, Map<String, dynamic>? data) async {
    try {
      final headers = await _getHeaders();
      final request = UpdateOnboardingStepRequest(step: stepNumber, data: data);
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/step/$stepNumber'),
        headers: headers,
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to update onboarding step');
      }
    } catch (e) {
      print('Error updating onboarding step: $e');
      rethrow;
    }
  }

  // User szándékok mentése
  Future<Map<String, dynamic>> saveUserIntents(List<UserIntent> intents) async {
    try {
      final headers = await _getHeaders();
      final request = UserIntentSelection(intents: intents);
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/intents'),
        headers: headers,
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to save user intents');
      }
    } catch (e) {
      print('Error saving user intents: $e');
      rethrow;
    }
  }

  // Alapbeállítások mentése
  Future<Map<String, dynamic>> saveBasicSetup(BasicSetupData setupData) async {
    try {
      final headers = await _getHeaders();
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/basic-setup'),
        headers: headers,
        body: jsonEncode(setupData.toJson()),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to save basic setup');
      }
    } catch (e) {
      print('Error saving basic setup: $e');
      rethrow;
    }
  }

  // Tutorial tartalom lekérdezése - ÚJ!
  Future<TutorialContent> getTutorialContent(UserType userType) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/tutorial/${userType.value}'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return TutorialContent.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        throw Exception('Failed to load tutorial content: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching tutorial content: $e');
      rethrow;
    }
  }

  // Onboarding befejezése
  Future<Map<String, dynamic>> completeOnboarding() async {
    try {
      final headers = await _getHeaders();
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/complete'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to complete onboarding');
      }
    } catch (e) {
      print('Error completing onboarding: $e');
      rethrow;
    }
  }

  // Onboarding újraindítása
  Future<Map<String, dynamic>> restartOnboarding() async {
    try {
      final headers = await _getHeaders();
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/restart'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to restart onboarding');
      }
    } catch (e) {
      print('Error restarting onboarding: $e');
      rethrow;
    }
  }

  // Elérhető user típusok lekérdezése
  Future<Map<String, dynamic>> getAvailableUserTypes() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/onboarding/user-types'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('401: Unauthorized');
      } else {
        throw Exception('Failed to load user types: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching user types: $e');
      rethrow;
    }
  }

  // Helper metódus auth hibák kezelésére
  bool isAuthError(dynamic error) {
    final errorStr = error.toString().toLowerCase();
    return errorStr.contains('401') || 
           errorStr.contains('unauthorized') || 
           errorStr.contains('not authenticated') ||
           (errorStr.contains('token') && (errorStr.contains('invalid') || errorStr.contains('expired')));
  }
}