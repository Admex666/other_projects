// lib/services/analysis_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/models/analysis.dart';
import 'package:frontend/services/auth_service.dart'; // AuthService import hozzáadása

class AnalysisService {
  static const String baseUrl = 'http://10.0.2.2:8000';
  
  // AuthService instance létrehozása
  final AuthService _authService = const AuthService();

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
      Uri.parse('$baseUrl/analysis/comprehensive?months_back=$monthsBack'),
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
      Uri.parse('$baseUrl/analysis/basic-stats?months_back=$monthsBack'),
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
      Uri.parse('$baseUrl/analysis/risk-analysis?months_back=$monthsBack'),
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
      Uri.parse('$baseUrl/analysis/category-analysis?months_back=$monthsBack'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return CategoryAnalysis.fromJson(data);
    } else {
      throw Exception('Sikertelen kategóriaelemzés lekérés: ${response.body}');
    }
  }
}