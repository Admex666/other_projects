// lib/services/category_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/models/category.dart'; // Importáljuk az imént létrehozott kategória modellt

class CategoryService {
  final String _baseUrl = 'http://10.0.2.2:8000/categories/'; // Cserélje le a saját API URL-jére, hozzáadva a perjelet
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
      // Existing error handling, still good
      throw Exception('Failed to load categories: ${response.body}');
    }
  }

  Future<Category> createCategory(String name, String type) async {
    final token = await _getAccessToken();
    if (token == null) {
      throw Exception('Access token not found.');
    }

    final response = await http.post(
      Uri.parse(_baseUrl), // Base URL already includes the trailing slash
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
      // Check if the body is not empty before decoding
      if (response.body.isNotEmpty) {
        return Category.fromJson(json.decode(response.body));
      } else {
        throw Exception('Server returned 201 but with an empty response body.');
      }
    } else {
      // Handle other status codes, especially if the server sends error details
      if (response.body.isNotEmpty) {
        try {
          final errorData = json.decode(response.body);
          throw Exception('Failed to create category: ${errorData['detail'] ?? response.statusCode}');
        } catch (e) {
          // If the error body is not valid JSON
          throw Exception('Failed to create category (HTTP ${response.statusCode}): ${response.body}');
        }
      } else {
        // If the server returned an error status code with an empty body
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
      Uri.parse('$_baseUrl$categoryId'), // Base URL already includes the trailing slash
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 204) { // 204 No Content means successful deletion with no body
      if (response.body.isNotEmpty) {
        final errorData = json.decode(response.body);
        throw Exception('Failed to delete category: ${errorData['detail'] ?? response.statusCode}');
      } else {
        throw Exception('Failed to delete category: Server returned status ${response.statusCode} with no body.');
      }
    }
  }
}