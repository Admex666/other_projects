// lib/services/analysis_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/models/analysis.dart';
import 'package:frontend/services/auth_service.dart'; 
import 'package:frontend/config/config.dart';

class AnalysisService {
  
  // AuthService instance létrehozása
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
    };
  }

  // Átfogó elemzés lekérése
  Future<FinancialAnalysis> getComprehensiveAnalysis({int monthsBack = 12}) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/comprehensive?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return FinancialAnalysis.fromJson(data);
    } else {
      throw Exception('Sikertelen elemzés lekérés: ${response.body}');
    }
  }

  // Alapvető statisztikák lekérése
  Future<BasicStats> getBasicStats({int monthsBack = 6}) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/basic-stats?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return BasicStats.fromJson(data);
    } else {
      throw Exception('Sikertelen alapstatisztika lekérés: ${response.body}');
    }
  }

  // Kockázatelemzés lekérése
  Future<RiskAnalysis> getRiskAnalysis({int monthsBack = 12}) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/risk-analysis?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return RiskAnalysis.fromJson(data);
    } else {
      throw Exception('Sikertelen kockázatelemzés lekérés: ${response.body}');
    }
  }

  // Kategóriaelemzés lekérése
  Future<CategoryAnalysis> getCategoryAnalysis({int monthsBack = 6}) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/category-analysis?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return CategoryAnalysis.fromJson(data);
    } else {
      throw Exception('Sikertelen kategóriaelemzés lekérés: ${response.body}');
    }
  }

  // ÚJ METÓDUSOK hozzáadása a meglévő kódhoz

  // Költési előrejelzés
  Future<ForecastResponse> getSpendingForecast({
    String forecastType = 'monthly',
    int periodsAhead = 6,
    int monthsHistory = 12,
  }) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/forecast?forecast_type=$forecastType&periods_ahead=$periodsAhead&months_history=$monthsHistory'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return ForecastResponse.fromJson(data);
    } else {
      throw Exception('Sikertelen előrejelzés lekérés: ${response.body}');
    }
  }

  // Anomália detektálás
  Future<AnomalyResponse> getAnomalyDetection({
    int monthsBack = 6,
    double sensitivity = 0.1,
  }) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/anomaly-detection?months_back=$monthsBack&sensitivity=$sensitivity'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return AnomalyResponse.fromJson(data);
    } else {
      throw Exception('Sikertelen anomália detektálás: ${response.body}');
    }
  }

  // ML költségvetési javaslatok
  Future<MLBudgetResponse> getMLBudgetRecommendations({
    int monthsBack = 6,
  }) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/ml-budget-recommendations?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return MLBudgetResponse.fromJson(data);
    } else {
      throw Exception('Sikertelen ML költségvetési javaslat lekérés: ${response.body}');
    }
  }

  // What-If szimulációk
  Future<WhatIfResponse> getWhatIfScenarios({
    required double targetSavings,
    int monthsBack = 6,
  }) async {
    final headers = await _getHeaders();
    
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/analysis/what-if-scenarios?target_savings=$targetSavings&months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return WhatIfResponse.fromJson(data);
    } else {
      throw Exception('Sikertelen What-If szimuláció: ${response.body}');
    }
  }

  // Fejlett betekintések (kombinált)
  Future<Map<String, dynamic>> getAdvancedInsights({
    int monthsBack = 6,
  }) async {
    final headers = await _getHeaders();
    
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/analysis/spending-insights?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Sikertelen fejlett betekintések lekérés: ${response.body}');
    }
  }
}