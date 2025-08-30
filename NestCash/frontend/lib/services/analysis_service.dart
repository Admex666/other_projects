// lib/services/analysis_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/models/analysis.dart';
import 'package:frontend/services/auth_service.dart'; 
import 'package:frontend/config/config.dart';
import '../services/language_service.dart';
import 'package:frontend/services/http_service.dart';

class AnalysisService {
  final LanguageService _languageService = LanguageService();
  final AuthService _authService = AuthService();

  // Token lekérése az AuthService-ből
  Future<String?> _getToken() async {
    return await _authService.getToken();
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
      'Accept-Language': _languageService.currentLanguage,
    };
  }

  // Átfogó elemzés lekérése
  Future<FinancialAnalysis> getComprehensiveAnalysis({int monthsBack = 12}) async {
    try {
      // Biztonságos nyelv lekérés
      String currentLang;
      try {
        currentLang = _languageService.currentLanguage;
        if (currentLang.isEmpty) {
          currentLang = 'hu';
        }
      } catch (e) {
        print('⚠️ Error getting language, using default: $e');
        currentLang = 'hu';
      }
      
      print('🔍 Getting comprehensive analysis for $monthsBack months, lang: $currentLang');
      
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/comprehensive?months_back=$monthsBack&lang=$currentLang',
      );

    print('📊 Comprehensive analysis response: ${response.statusCode}');

    if (response.statusCode == 200) {
      final responseBody = response.body;
      print('📊 Raw response body length: ${responseBody.length}');
      print('📊 First 500 chars of response: ${responseBody.length > 500 ? responseBody.substring(0, 500) : responseBody}');
      
      try {
        final Map<String, dynamic> data = json.decode(responseBody);
        print('📊 JSON parsed successfully, keys: ${data.keys.toList()}');
        
        // Ellenőrizzük a főbb mezőket null értékekre
        data.forEach((key, value) {
          if (value == null) {
            print('⚠️ NULL value found for key: $key');
          }
        });
        
        return FinancialAnalysis.fromJson(data);
      } catch (jsonError) {
        print('🚨 JSON parsing error: $jsonError');
        print('🚨 JSON parsing error type: ${jsonError.runtimeType}');
        rethrow;
      }
    } else {
      print('📊 Comprehensive analysis error: ${response.body}');
      throw Exception('Sikertelen elemzés lekérés: ${response.body}');
    }
  } catch (e) {
    print('🚨 AnalysisService.getComprehensiveAnalysis error: $e');
    print('🚨 Error type: ${e.runtimeType}');
    print('🚨 Stack trace: ${StackTrace.current}');
    rethrow;
  }
}

  // Alapvető statisztikák lekérése
  Future<BasicStats> getBasicStats({int monthsBack = 6}) async {
    try {
      print('📊 Loading basic stats for $monthsBack months...');
      
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/basic-stats?months_back=$monthsBack',
      );

      print('📊 Basic stats response: ${response.statusCode}');

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        print('📊 Basic stats data received successfully');
        return BasicStats.fromJson(data);
      } else {
        print('📊 Basic stats error: ${response.body}');
        throw Exception('Sikertelen alapstatisztika lekérés: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getBasicStats error: $e');
      print('🚨 Error type: ${e.runtimeType}');
      rethrow;
    }
  }

  // Kockázatelemzés lekérése
  Future<RiskAnalysis> getRiskAnalysis({int monthsBack = 12}) async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/risk-analysis?months_back=$monthsBack',
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return RiskAnalysis.fromJson(data);
      } else {
        throw Exception('Sikertelen kockázatelemzés lekérés: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getRiskAnalysis error: $e');
      rethrow;
    }
  }

  // Kategóriaelemzés lekérése
  Future<CategoryAnalysis> getCategoryAnalysis({int monthsBack = 6}) async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/category-analysis?months_back=$monthsBack',
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return CategoryAnalysis.fromJson(data);
      } else {
        throw Exception('Sikertelen kategóriaelemzés lekérés: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getCategoryAnalysis error: $e');
      rethrow;
    }
  }

  // Költési előrejelzés
  Future<ForecastResponse> getSpendingForecast({
    String forecastType = 'monthly',
    int periodsAhead = 6,
    int monthsHistory = 12,
  }) async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/forecast?forecast_type=$forecastType&periods_ahead=$periodsAhead&months_history=$monthsHistory',
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return ForecastResponse.fromJson(data);
      } else {
        throw Exception('Sikertelen előrejelzés lekérés: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getSpendingForecast error: $e');
      rethrow;
    }
  }

  // Anomália detektálás
  Future<AnomalyResponse> getAnomalyDetection({
    int monthsBack = 6,
    double sensitivity = 0.1,
  }) async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/anomaly-detection?months_back=$monthsBack&sensitivity=$sensitivity',
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return AnomalyResponse.fromJson(data);
      } else {
        throw Exception('Sikertelen anomália detektálás: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getAnomalyDetection error: $e');
      rethrow;
    }
  }

  // ML költségvetési javaslatok
  Future<MLBudgetResponse> getMLBudgetRecommendations({
    int monthsBack = 6,
  }) async {
    try {
      final currentLang = _languageService.currentLanguage;
      
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/ml-budget-recommendations?months_back=$monthsBack&lang=$currentLang',
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return MLBudgetResponse.fromJson(data);
      } else {
        throw Exception('Sikertelen ML költségvetési javaslat lekérés: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getMLBudgetRecommendations error: $e');
      rethrow;
    }
  }

  // What-If szimulációk
  Future<WhatIfResponse> getWhatIfScenarios({
    required double targetSavings,
    int monthsBack = 6,
  }) async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'POST',
        url: '${ApiConfig.baseUrl}/analysis/what-if-scenarios?target_savings=$targetSavings&months_back=$monthsBack',
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return WhatIfResponse.fromJson(data);
      } else {
        throw Exception('Sikertelen What-If szimuláció: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getWhatIfScenarios error: $e');
      rethrow;
    }
  }

  // Fejlett betekintések (kombinált)
  Future<Map<String, dynamic>> getAdvancedInsights({
    int monthsBack = 6,
  }) async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/analysis/spending-insights?months_back=$monthsBack',
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Sikertelen fejlett betekintések lekérés: ${response.body}');
      }
    } catch (e) {
      print('🚨 AnalysisService.getAdvancedInsights error: $e');
      rethrow;
    }
  }
}