// lib/services/limit_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/limit.dart';

class LimitService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const LimitService({this.baseUrl = 'http://10.0.2.2:8000'});

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

  // Limitek lekérdezése
  Future<List<Limit>> getLimits({bool activeOnly = true, LimitType? type}) async {
    try {
      final headers = await _getHeaders();
      final queryParams = <String, String>{};
      
      if (activeOnly) queryParams['active_only'] = 'true';
      if (type != null) queryParams['limit_type'] = type.value;
      
      final uri = Uri.parse('$baseUrl/limits').replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final limits = (data['limits'] as List)
            .map((json) => Limit.fromJson(json))
            .toList();
        return limits;
      } else {
        throw Exception('Failed to load limits: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching limits: $e');
      throw Exception('Hiba a limitek betöltése során: $e');
    }
  }

  // Limit létrehozása
  Future<Limit> createLimit(Map<String, dynamic> limitData) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/limits/'),
        headers: headers,
        body: jsonEncode(limitData),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return Limit.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Limit létrehozása sikertelen');
      }
    } catch (e) {
      print('Error creating limit: $e');
      throw Exception('Hiba a limit létrehozása során: $e');
    }
  }

  // Limit frissítése
  Future<Limit> updateLimit(String limitId, Map<String, dynamic> updateData) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/limits/$limitId'),
        headers: headers,
        body: jsonEncode(updateData),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return Limit.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Limit frissítése sikertelen');
      }
    } catch (e) {
      print('Error updating limit: $e');
      throw Exception('Hiba a limit frissítése során: $e');
    }
  }

  // Limit törlése
  Future<bool> deleteLimit(String limitId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.delete(
        Uri.parse('$baseUrl/limits/$limitId'),
        headers: headers,
      );

      return response.statusCode == 204;
    } catch (e) {
      print('Error deleting limit: $e');
      throw Exception('Hiba a limit törlése során: $e');
    }
  }

  // Limit ellenőrzése
  Future<LimitCheckResult> checkLimits({
    required double amount,
    String? category,
    String? mainAccount,
    String? subAccountName,
  }) async {
    try {
      final headers = await _getHeaders();
      final queryParams = {
        'amount': amount.toString(),
        if (category != null) 'category': category,
        if (mainAccount != null) 'main_account': mainAccount,
        if (subAccountName != null) 'sub_account_name': subAccountName,
      };

      final uri = Uri.parse('$baseUrl/limits/check').replace(queryParameters: queryParams);
      final response = await http.post(uri, headers: headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return LimitCheckResult.fromJson(data);
      } else {
        // Hiba esetén engedjük a tranzakciót
        return const LimitCheckResult(isAllowed: true);
      }
    } catch (e) {
      print('Error checking limits: $e');
      // Hiba esetén engedjük a tranzakciót
      return const LimitCheckResult(isAllowed: true);
    }
  }

  // Limit státusz lekérdezése
  Future<LimitStatus> getLimitStatus() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/limits/status/overview'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return LimitStatus.fromJson(data);
      } else {
        throw Exception('Failed to load limit status: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching limit status: $e');
      throw Exception('Hiba a limit státusz betöltése során: $e');
    }
  }

  // Egy konkrét limit lekérdezése
  Future<Limit> getLimit(String limitId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/limits/$limitId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return Limit.fromJson(data);
      } else {
        throw Exception('Failed to load limit: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching limit: $e');
      throw Exception('Hiba a limit betöltése során: $e');
    }
  }
}