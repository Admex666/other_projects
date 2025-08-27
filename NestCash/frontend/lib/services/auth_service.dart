import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/config/config.dart';
import 'dart:async';
import '../services/analytics_service.dart';
import '../services/http_service.dart';

class AuthService {
  // Secure storage instance
  static const _storage = FlutterSecureStorage();

  /// Regisztráció + automatikus bejelentkezés
  Future<bool> register(String username, String email, String password, {String? mobile,}) async {
    final resp = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'email': email,
        if (mobile != null && mobile.isNotEmpty) 'mobile': mobile,
        'password': password,
      }),
    );

    // Ha sikeres a regisztráció
    if (resp.statusCode == 201 || resp.statusCode == 200) {
      // Automatikus bejelentkezés
      final loginSuccess = await login(username, password);
      return loginSuccess;
    }
    
    return false;
  }

  /// Bejelentkezés
  Future<bool> login(String usernameOrEmail, String password) async {
    print('🔐 Starting login process...');
    
    try {
      // Egyszerű GET teszt előbb
      print('🧪 Testing simple GET request...');
      final getResponse = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/health'),
      ).timeout(const Duration(seconds: 15));
      
      print('✅ GET test successful: ${getResponse.statusCode}');
      
      // Most a POST kérés
      print('🚀 Sending POST request...');
      
      final postData = 'username=$usernameOrEmail&password=$password&grant_type=password';
      print('📤 POST data: $postData');
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/token'),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
        },
        body: postData,
      ).timeout(const Duration(seconds: 30));

      print('📬 POST Response received!');
      print('📊 Status: ${response.statusCode}');
      print('📝 Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['access_token'] as String?;
        final refreshToken = data['refresh_token'] as String?;
        final userId = data['user_id'] as String?;
        final username = data['username'] as String?;

        if (token != null && refreshToken != null) {
          await _storage.write(key: 'token', value: token);
          await _storage.write(key: 'refresh_token', value: refreshToken);
          if (userId != null) {
            await _storage.write(key: 'user_id', value: userId);
          }
          if (username != null) {
            await _storage.write(key: 'username', value: username);
          }

          // JAVÍTÁS: Session tracking minden bejelentkezésnél
          try {
            final analyticsService = AnalyticsService();
            await analyticsService.trackSession();
            print('✅ Login successful with session tracking');
          } catch (e) {
            print('⚠️ Session tracking failed, but login successful: $e');
          }

          return true;
        }
      }
    } catch (e) {
      print('🚨 Exception caught: $e');
      print('🚨 Exception type: ${e.runtimeType}');
    }
    
    return false;
  }

  Future<String?> getRefreshToken() async {
    return _storage.read(key: 'refresh_token');
  }

  Future<bool> refreshToken() async {
    final refreshToken = await getRefreshToken();
    if (refreshToken == null) return false;

    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final newAccessToken = data['access_token'] as String?;
        final newRefreshToken = data['refresh_token'] as String?;

        if (newAccessToken != null && newRefreshToken != null) {
          await _storage.write(key: 'token', value: newAccessToken);
          await _storage.write(key: 'refresh_token', value: newRefreshToken);
          return true;
        }
      }
    } catch (e) {
      print('Refresh token error: $e');
    }
    
    return false;
  }

  // ÚJ: Session tracking indítása app induláskor
  Future<void> initializeSessionTracking() async {
    final token = await getToken();
    if (token != null) {
      try {
        final analyticsService = AnalyticsService();
        await analyticsService.trackSession();
        print('✅ Session initialized successfully');
      } catch (e) {
        print('⚠️ Session initialization failed: $e');
      }
    }
  }


  Future<void> logout() async {
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'refresh_token');
    await _storage.delete(key: 'user_id');
    await _storage.delete(key: 'username');
  }

  Future<String?> getToken() async {
    return _storage.read(key: 'token');
  }

  Future<String?> getCurrentUsername() async {
    return _storage.read(key: 'username');
  }

  Future<String?> getUserId() async {
    return _storage.read(key: 'user_id');
  }

  Future<Map<String, dynamic>?> getUserProfile() async {
    try {
      final response = await HttpService.authenticatedRequest(
        method: 'GET',
        url: '${ApiConfig.baseUrl}/auth/me',
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else if (response.statusCode == 401) {
        // Ha még mindig 401, akkor kijelentkeztetjük
        await logout();
        throw Exception('401: Unauthorized');
      }
      
      throw Exception('HTTP ${response.statusCode}: ${response.body}');
    } catch (e) {
      print('Error getting user profile: $e');
      return null;
    }
  }

  Future<bool> updateProfile({
    String? username,
    String? email,
    String? mobile,
    String? password,
  }) async {
    try {
      final token = await getToken(); // A tárolt token lekérése
      
      Map<String, dynamic> updateData = {};
      if (username != null && username.isNotEmpty) updateData['username'] = username;
      if (email != null && email.isNotEmpty) updateData['email'] = email;
      if (mobile != null) updateData['mobile'] = mobile;
      if (password != null && password.isNotEmpty) updateData['password'] = password;
      
      final response = await http.put(
        Uri.parse('${ApiConfig.baseUrl}/auth/update-profile'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(updateData), // This is correctly encoding the map to JSON
      );
      
      if (response.statusCode == 200) {
        return true;
      } else {
        print('Profile update failed: ${response.body}'); // This line is crucial for debugging
        return false;
      }
    } catch (e) {
      print('Error updating profile: $e');
      return false;
    }
  }
}
