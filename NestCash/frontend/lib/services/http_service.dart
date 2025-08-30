// http_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/config.dart';
import 'auth_service.dart';
import '../services/language_service.dart';

class HttpService {
  static final AuthService _authService = AuthService();
  static final LanguageService _languageService = LanguageService();
  
  /// Automatikus token refresh-sel ellátott HTTP kérés
  static Future<http.Response> authenticatedRequest({
    required String method,
    required String url,
    Map<String, String>? headers,
    dynamic body,
    int maxRetries = 1,
  }) async {
    
    try {
      // Alapértelmezett headers
      final defaultHeaders = <String, String>{
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      
      // Language service biztonságos használata
      try {
        final currentLanguage = _languageService.currentLanguage;
        if (currentLanguage.isNotEmpty) {
          defaultHeaders['Accept-Language'] = currentLanguage;
        }
      } catch (e) {
        print('⚠️ Language service error: $e');
        defaultHeaders['Accept-Language'] = 'hu'; // Alapértelmezett nyelv
      }
      
      if (headers != null) {
        defaultHeaders.addAll(headers);
      }
      
      // Token hozzáadása
      final token = await _authService.getToken();
      if (token != null && token.isNotEmpty) {
        defaultHeaders['Authorization'] = 'Bearer $token';
      }
      
      print('🔍 Making ${method.toUpperCase()} request to: $url');
      
      // Első próbálkozás
      http.Response response = await _makeRequest(method, url, defaultHeaders, body);
      
      print('📨 Response status: ${response.statusCode}');
      
      // Ha 401-es hibát kapunk és van refresh token, próbáljuk meg frissíteni
      if (response.statusCode == 401 && maxRetries > 0) {
        print('🔄 401 received, attempting token refresh...');
        
        final refreshSuccess = await _authService.refreshToken();
        if (refreshSuccess) {
          print('✅ Token refreshed successfully, retrying request...');
          
          // Frissített token hozzáadása
          final newToken = await _authService.getToken();
          if (newToken != null && newToken.isNotEmpty) {
            defaultHeaders['Authorization'] = 'Bearer $newToken';
          }
          
          // Újrapróbálkozás
          response = await _makeRequest(method, url, defaultHeaders, body);
          print('📨 Retry response status: ${response.statusCode}');
        } else {
          print('❌ Token refresh failed, logging out user...');
          await _authService.logout();
        }
      }
      
      return response;
      
    } catch (e) {
      print('🚨 HttpService error: $e');
      print('🚨 Error type: ${e.runtimeType}');
      
      // Ha null check error, akkor próbáljuk meg biztonságosan kezelni
      if (e.toString().contains('Null check operator used on a null value')) {
        print('⚠️ Null check error detected, creating fallback response');
        
        // Fallback response létrehozása
        return http.Response(
          jsonEncode({'error': 'Service temporarily unavailable'}),
          500,
          headers: {'content-type': 'application/json'},
        );
      }
      
      rethrow;
    }
  }
  
  /// Tényleges HTTP kérés végrehajtása
  static Future<http.Response> _makeRequest(
    String method, 
    String url, 
    Map<String, String> headers, 
    dynamic body
  ) async {
    try {
      final uri = Uri.parse(url);
      
      switch (method.toUpperCase()) {
        case 'GET':
          return await http.get(uri, headers: headers)
              .timeout(const Duration(seconds: 15));
        case 'POST':
          return await http.post(
            uri, 
            headers: headers, 
            body: body is String ? body : (body != null ? jsonEncode(body) : null)
          ).timeout(const Duration(seconds: 15));
        case 'PUT':
          return await http.put(
            uri, 
            headers: headers, 
            body: body is String ? body : (body != null ? jsonEncode(body) : null)
          ).timeout(const Duration(seconds: 15));
        case 'DELETE':
          return await http.delete(uri, headers: headers)
              .timeout(const Duration(seconds: 15));
        default:
          throw ArgumentError('Unsupported HTTP method: $method');
      }
    } catch (e) {
      print('🚨 _makeRequest error: $e');
      rethrow;
    }
  }
}