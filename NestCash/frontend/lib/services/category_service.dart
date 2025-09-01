// lib/services/category_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/models/category.dart'; 
import 'package:frontend/config/config.dart'; 

class CategoryService {
  final _storage = const FlutterSecureStorage(); // Secure storage példány

  Future<String?> _getAccessToken() async {
    return await _storage.read(key: 'token'); // Token lekérése a secure storage-ból
  }

  Future<List<Category>> getCategories({String? type}) async {
    final token = await _getAccessToken();
    if (token == null) {
      throw Exception('Access token not found.');
    }

    String url = '${ApiConfig.baseUrl}/categories';
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
      Uri.parse('${ApiConfig.baseUrl}/categories'), // Javított URL
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
      if (response.body.isNotEmpty) {
        return Category.fromJson(json.decode(response.body));
      } else {
        throw Exception('Server returned 201 but with an empty response body.');
      }
    } else {
      if (response.body.isNotEmpty) {
        try {
          final errorData = json.decode(response.body);
          throw Exception('Failed to create category: ${errorData['detail'] ?? response.statusCode}');
        } catch (e) {
          throw Exception('Failed to create category (HTTP ${response.statusCode}): ${response.body}');
        }
      } else {
        throw Exception('Failed to create category: Server returned empty response with status ${response.statusCode}.');
      }
    }
  }

  Future<void> deleteCategory(String categoryId) async {
    final token = await _getAccessToken();
    if (token == null) {
      throw Exception('Access token not found.');
    }

    final response = await http.delete(
      Uri.parse('${ApiConfig.baseUrl}/categories/$categoryId'), // Javított URL
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 204) {
      if (response.body.isNotEmpty) {
        final errorData = json.decode(response.body);
        throw Exception('Failed to delete category: ${errorData['detail'] ?? response.statusCode}');
      } else {
        throw Exception('Failed to delete category: Server returned status ${response.statusCode} with no body.');
      }
    }
  }
}