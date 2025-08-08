import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/models/message_models.dart';

class MessageService {
  final AuthService _authService = AuthService();
  final String baseUrl;

  MessageService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    if (token == null) {
      _authService.logout();
      throw Exception('Authentication token not found');
    }

    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  Future<List<Conversation>> getConversations({int skip = 0, int limit = 50}) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/messages/conversations').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final List<dynamic> conversationsJson = data['conversations'];
      return conversationsJson.map((json) => Conversation.fromJson(json)).toList();
    }
    throw Exception('Failed to load conversations: ${response.body}');
  }

  Future<List<PrivateMessage>> getMessages(String otherUserId, {int skip = 0, int limit = 50}) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/messages/conversations/$otherUserId').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final List<dynamic> messagesJson = data['messages'];
      return messagesJson.map((json) => PrivateMessage.fromJson(json)).toList();
    }
    throw Exception('Failed to load messages: ${response.body}');
  }

  Future<PrivateMessage> sendMessage(String otherUserId, String content) async {
    final response = await http.post(
      Uri.parse('$baseUrl/messages/conversations/$otherUserId'),
      headers: await _getHeaders(),
      body: jsonEncode({'content': content}),
    );

    if (response.statusCode == 201) {
      return PrivateMessage.fromJson(jsonDecode(response.body));
    }
    throw Exception('Failed to send message: ${response.body}');
  }

  Future<int> getUnreadMessageCount() async {
    final response = await http.get(
      Uri.parse('$baseUrl/messages/unread-count'),
      headers: await _getHeaders(),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['unread_count'] ?? 0;
    }
    throw Exception('Failed to get unread count: ${response.body}');
  }
}