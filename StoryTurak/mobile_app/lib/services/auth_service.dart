import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class AuthService extends ChangeNotifier {
  final _storage = const FlutterSecureStorage();
  String? _username;
  String? _accessToken;
  bool get isAuthenticated => _accessToken != null;
  String? get token => _accessToken;
  String? get username => _username;

  // Key for storage
  static const _tokenKey = 'jwt_token';
  static const _usernameKey = 'username';

  Future<void> tryAutoLogin() async {
    final token = await _storage.read(key: _tokenKey);
    final user = await _storage.read(key: _usernameKey);
    if (token != null) {
      _accessToken = token;
      _username = user;
      notifyListeners();
    }
  }

  Future<String?> login(String username, String password) async {
    final baseUrl = await ApiService().getBaseUrl();
    final url = Uri.parse('$baseUrl/auth/token');
    
    try {
      final response = await http.post(
        url,
        body: {
          'username': username,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _accessToken = data['access_token'];
        _username = username;
        
        await _storage.write(key: _tokenKey, value: _accessToken);
        await _storage.write(key: _usernameKey, value: username);
        
        notifyListeners();
        return null; // Success
      } else {
        final data = json.decode(response.body);
        return data['detail'] ?? "Hibás felhasználónév vagy jelszó";
      }
    } catch (e) {
      return "Hálózati hiba: $e";
    }
  }

  Future<String?> register(String username, String password) async {
    final baseUrl = await ApiService().getBaseUrl();
    final url = Uri.parse('$baseUrl/auth/register');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _accessToken = data['access_token'];
        _username = username;
        
        await _storage.write(key: _tokenKey, value: _accessToken);
        await _storage.write(key: _usernameKey, value: username);

        notifyListeners();
        return null; // Success
      } else {
        final data = json.decode(response.body);
        return data['detail'] ?? "Hiba a regisztráció során";
      }
    } catch (e) {
      return "Hálózati hiba: $e";
    }
  }

  Future<void> logout() async {
    _accessToken = null;
    _username = null;
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _usernameKey);
    notifyListeners();
  }
}
