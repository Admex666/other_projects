// lib/services/category_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/models/category.dart'; // Importáljuk az imént létrehozott kategória modellt

class CategoryService {
  final String _baseUrl = 'http://10.0.2.2:8000/categories'; // Cserélje le a saját API URL-jére
  final _storage = const FlutterSecureStorage(); // Secure storage példány

  Future<String?> _getAccessToken() async {
    return await _storage.read(key: 'token'); // Token lekérése a secure storage-ból
  }

  Future<List<Category>> getCategories({String? type}) async {
    final token = await _getAccessToken();
    if (token == null) {
      throw Exception('Access token not found.');
    }

    String url = _baseUrl;
    if (type != null) {
      url += '?category_type=$type';
    }

    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      List<dynamic> categoryList = data['categories'];
      return categoryList.map((json) => Category.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load categories: ${response.body}');
    }
  }

  Future<Category> createCategory(String name, String type) async {
    final token = await _getAccessToken();
    if (token == null) {
      throw Exception('Access token not found.');
    }

    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: json.encode({
        'name': name,
        'type': type,
      }),
    );

    if (response.statusCode == 201) {
      return Category.fromJson(json.decode(response.body));
    } else {
      final errorData = json.decode(response.body);
      throw Exception('Failed to create category: ${errorData['detail'] ?? response.statusCode}');
    }
  }

  Future<void> deleteCategory(String categoryId) async {
    final token = await _getAccessToken();
    if (token == null) {
      throw Exception('Access token not found.');
    }

    final response = await http.delete(
      Uri.parse('$_baseUrl/$categoryId'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 204) {
      final errorData = json.decode(response.body);
      throw Exception('Failed to delete category: ${errorData['detail'] ?? response.statusCode}');
    }
  }
}