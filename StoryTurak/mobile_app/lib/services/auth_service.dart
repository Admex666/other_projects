import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'geolixo_service.dart'; // For baseUrl connection

class AuthService extends ChangeNotifier {
  final _storage = const FlutterSecureStorage();
  String? _accessToken;
  
  bool get isAuthenticated => _accessToken != null;
  String? get token => _accessToken;

  // Key for storage
  static const _tokenKey = 'jwt_token';
  static const _usernameKey = 'username';

  Future<void> tryAutoLogin() async {
    final token = await _storage.read(key: _tokenKey);
    if (token != null) {
      _accessToken = token;
      notifyListeners();
    }
  }

  Future<String?> login(String username, String password) async {
    final url = Uri.parse('${GeolixoService.baseUrl}/auth/token');
    
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
    final url = Uri.parse('${GeolixoService.baseUrl}/auth/register');
    
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
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _usernameKey);
    notifyListeners();
  }
}
