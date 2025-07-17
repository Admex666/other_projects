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
  Future<bool> register(String username, String email, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'email': email,
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
      if (token != null) {
        await _storage.write(key: 'token', value: token);
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
}
