import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  // Secure storage instance
  static const _storage = FlutterSecureStorage();

  // TODO: állítsd be a backend URL-t (emulátor vs. device!)
  // Android emulatorról: http://10.0.2.2:8000
  // iOS simulatorról:   http://localhost:8000
  final String baseUrl;

  const AuthService({this.baseUrl = 'http://10.0.2.2:8000'});

  /// Regisztráció
  Future<bool> register(String username, String email, String password, {String? mobile,}) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'email': email,
        if (mobile != null && mobile.isNotEmpty) 'mobile': mobile,
        'password': password,
      }),
    );

    // Backend implementációtól függ – igazítsd ha más kódot ad vissza
    return resp.statusCode == 201 || resp.statusCode == 200;
  }

  /// Bejelentkezés
  Future<bool> login(String usernameOrEmail, String password) async {
    // Ha a backend az OAuth2 form-data sémát várja (/auth/token),
    // akkor urlencoded body kell. Ha JSON-t vár, igazítsd!
    final resp = await http.post(
      Uri.parse('$baseUrl/auth/token'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'username': usernameOrEmail,
        'password': password,
      },
    );

    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      final token = data['access_token'] as String?;
      final userId = data['user_id'] as String?;
      final username = data['username'] as String?;

      if (token != null) {
            await _storage.write(key: 'token', value: token);
            if (userId != null) {
                await _storage.write(key: 'user_id', value: userId);
            }
            if (username != null) {
                await _storage.write(key: 'username', value: username);
            }
            return true;
        }
    }
    return false;
  }

  Future<void> logout() async {
    await _storage.delete(key: 'token');
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
    final token = await getToken();
    if (token == null) return null;

    final resp = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (resp.statusCode == 200) {
      return jsonDecode(resp.body) as Map<String, dynamic>;
    }
    return null;
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
        Uri.parse('$baseUrl/auth/update-profile'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(updateData),
      );
      
      if (response.statusCode == 200) {
        return true;
      } else {
        print('Profile update failed: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error updating profile: $e');
      return false;
    }
  }
}
