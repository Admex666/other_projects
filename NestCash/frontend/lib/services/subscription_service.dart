// lib/services/subscription_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/subscription.dart';
import 'auth_service.dart';

class SubscriptionService {
  final AuthService _authService;
  final String baseUrl;

  SubscriptionService({
    required AuthService authService,
    this.baseUrl = 'http://10.0.2.2:8000',
  }) : _authService = authService;

  /// Általános HTTP kérés wrapper auth kezeléssel
  Future<http.Response> _makeRequest(
    String method,
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    final token = await _authService.getToken();
    
    if (token == null) {
      throw Exception('Nincs érvényes token - bejelentkezés szükséges');
    }

    final headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };

    final uri = Uri.parse('$baseUrl$endpoint');

    switch (method.toUpperCase()) {
      case 'GET':
        return await http.get(uri, headers: headers);
      case 'POST':
        return await http.post(
          uri,
          headers: headers,
          body: body != null ? jsonEncode(body) : null,
        );
      case 'PUT':
        return await http.put(
          uri,
          headers: headers,
          body: body != null ? jsonEncode(body) : null,
        );
      default:
        throw Exception('Nem támogatott HTTP metódus: $method');
    }
  }

  /// Jelenlegi felhasználó előfizetésének lekérése
  Future<UserSubscription> getMySubscription() async {
    try {
      final response = await _makeRequest('GET', '/subscription/me');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return UserSubscription.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else {
        throw Exception('Előfizetés lekérése sikertelen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Előfizetés lekérése sikertelen: $e');
    }
  }

  /// Elérhető előfizetési tervek lekérése
  Future<List<SubscriptionPlan>> getAvailablePlans() async {
    try {
      final response = await _makeRequest('GET', '/subscription/plans');

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => SubscriptionPlan.fromJson(json)).toList();
      } else {
        throw Exception('Tervek lekérése sikertelen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Tervek lekérése sikertelen: $e');
    }
  }

  /// Felhasználó funkciói és korlátai
  Future<FeaturesSummary> getMyFeatures() async {
    try {
      final response = await _makeRequest('GET', '/subscription/features');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return FeaturesSummary.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else {
        throw Exception('Funkciók lekérése sikertelen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Funkciók lekérése sikertelen: $e');
    }
  }

  /// Konkrét funkció hozzáférésének ellenőrzése
  Future<FeatureAccess> checkFeatureAccess(
    String feature, {
    int? currentUsageCount,
    int? currentActiveChallenges,
    int? currentHabitCount,
    int? dailyLessonCount,
    int? currentPartnerCount,
    String? analysisType,
  }) async {
    try {
      final body = <String, dynamic>{
        'feature': feature,
        if (currentUsageCount != null) 'current_usage_count': currentUsageCount,
        if (currentActiveChallenges != null) 'current_active_challenges': currentActiveChallenges,
        if (currentHabitCount != null) 'current_habit_count': currentHabitCount,
        if (dailyLessonCount != null) 'daily_lesson_count': dailyLessonCount,
        if (currentPartnerCount != null) 'current_partner_count': currentPartnerCount,
        if (analysisType != null) 'analysis_type': analysisType,
      };

      final response = await _makeRequest('POST', '/subscription/check-feature', body: body);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return FeatureAccess.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else {
        throw Exception('Funkció ellenőrzés sikertelen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Funkció ellenőrzés sikertelen: $e');
    }
  }

  /// Előfizetés frissítése
  /// FONTOS: Ez csak a belső állapot frissítése! 
  /// A tényleges fizetés külön payment service-n keresztül történik
  Future<bool> upgradeSubscription(
    SubscriptionTier newTier, {
    String? paymentProvider,
    String? externalSubscriptionId,
  }) async {
    try {
      final body = <String, dynamic>{
        'tier': newTier.value,
        if (paymentProvider != null) 'payment_provider': paymentProvider,
        if (externalSubscriptionId != null) 'external_subscription_id': externalSubscriptionId,
      };

      final response = await _makeRequest('POST', '/subscription/upgrade', body: body);

      if (response.statusCode == 200) {
        return true;
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else if (response.statusCode == 402) {
        throw Exception('Fizetés szükséges');
      } else {
        final data = jsonDecode(response.body);
        throw Exception(data['detail'] ?? 'Előfizetés frissítés sikertelen');
      }
    } catch (e) {
      throw Exception('Előfizetés frissítés sikertelen: $e');
    }
  }

  /// Előfizetés lemondása (FREE tier-re visszaállítás)
  Future<bool> cancelSubscription({String reason = 'user_request'}) async {
    try {
      final body = {'reason': reason};
      final response = await _makeRequest('POST', '/subscription/cancel', body: body);

      if (response.statusCode == 200) {
        return true;
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else {
        final data = jsonDecode(response.body);
        throw Exception(data['detail'] ?? 'Előfizetés lemondás sikertelen');
      }
    } catch (e) {
      throw Exception('Előfizetés lemondás sikertelen: $e');
    }
  }

  /// Konkrét funkció használati statisztikáinak lekérése
  Future<FeatureAccess> getFeatureUsage(String feature) async {
    try {
      final response = await _makeRequest('GET', '/subscription/usage/$feature');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return FeatureAccess.fromJson(data);
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else {
        throw Exception('Használati adatok lekérése sikertelen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Használati adatok lekérése sikertelen: $e');
    }
  }

  /// Előfizetési történet lekérése
  Future<Map<String, dynamic>> getSubscriptionHistory() async {
    try {
      final response = await _makeRequest('GET', '/subscription/history');

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw Exception('Nincs jogosultság - bejelentkezés szükséges');
      } else {
        throw Exception('Történet lekérése sikertelen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Történet lekérése sikertelen: $e');
    }
  }

  // Utility metódusok gyakran használt ellenőrzésekhez

  /// Ellenőrzi, hogy lehet-e új challenge-t létrehozni
  Future<FeatureAccess> canCreateChallenge(int currentActiveChallenges) async {
    return await checkFeatureAccess(
      'challenges',
      currentActiveChallenges: currentActiveChallenges,
    );
  }

  /// Ellenőrzi, hogy lehet-e új habit-ot létrehozni
  Future<FeatureAccess> canCreateHabit(int currentHabitCount) async {
    return await checkFeatureAccess(
      'habit_streak',
      currentHabitCount: currentHabitCount,
    );
  }

  /// Ellenőrzi, hogy lehet-e knowledge base-t használni (lecke nézése)
  Future<FeatureAccess> canAccessKnowledge(int dailyLessonCount) async {
    return await checkFeatureAccess(
      'knowledge_base',
      dailyLessonCount: dailyLessonCount,
    );
  }

  /// Ellenőrzi, hogy lehet-e advanced analytics-ot használni
  Future<FeatureAccess> canAccessAnalytics(String analysisType) async {
    return await checkFeatureAccess(
      'analysis_insights',
      analysisType: analysisType,
    );
  }

  /// Ellenőrzi, hogy lehet-e új accountability partner-t hozzáadni
  Future<FeatureAccess> canAddPartner(int currentPartnerCount) async {
    return await checkFeatureAccess(
      'accountability_partner',
      currentPartnerCount: currentPartnerCount,
    );
  }
}