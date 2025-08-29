// http_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/config.dart';
import 'auth_service.dart';

class HttpService {
  static final AuthService _authService = AuthService();
  
  /// Automatikus token refresh-sel ellátott HTTP kérés
  static Future<http.Response> authenticatedRequest({
    required String method,
    required String url,
    Map<String, String>? headers,
    dynamic body,
    int maxRetries = 1,
  }) async {
    
    // Alapértelmezett headers
    final defaultHeaders = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    if (headers != null) {
      defaultHeaders.addAll(headers);
    }
    
    // Token hozzáadása
    final token = await _authService.getToken();
    if (token != null) {
      defaultHeaders['Authorization'] = 'Bearer $token';
    }
    
    // Első próbálkozás
    http.Response response = await _makeRequest(method, url, defaultHeaders, body);
    
    // Ha 401-es hibát kapunk és van refresh token, próbáljuk meg frissíteni
    if (response.statusCode == 401 && maxRetries > 0) {
      print('🔄 401 received, attempting token refresh...');
      
      final refreshSuccess = await _authService.refreshToken();
      if (refreshSuccess) {
        print('✅ Token refreshed successfully, retrying request...');
        
        // Frissített token hozzáadása
        final newToken = await _authService.getToken();
        if (newToken != null) {
          defaultHeaders['Authorization'] = 'Bearer $newToken';
        }
        
        // Újrapróbálkozás
        response = await _makeRequest(method, url, defaultHeaders, body);
      } else {
        print('❌ Token refresh failed, logging out user...');
        await _authService.logout();
      }
    }
    
    return response;
  }
  
  /// Tényleges HTTP kérés végrehajtása
  static Future<http.Response> _makeRequest(
    String method, 
    String url, 
    Map<String, String> headers, 
    dynamic body
  ) async {
    final uri = Uri.parse(url);
    
    switch (method.toUpperCase()) {
      case 'GET':
        return await http.get(uri, headers: headers);
      case 'POST':
        return await http.post(
          uri, 
          headers: headers, 
          body: body is String ? body : jsonEncode(body)
        );
      case 'PUT':
        return await http.put(
          uri, 
          headers: headers, 
          body: body is String ? body : jsonEncode(body)
        );
      case 'DELETE':
        return await http.delete(uri, headers: headers);
      default:
        throw ArgumentError('Unsupported HTTP method: $method');
    }
  }
}