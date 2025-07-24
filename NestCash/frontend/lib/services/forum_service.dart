// lib/services/forum_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:frontend/services/auth_service.dart';

class ForumService {
  final AuthService _authService = AuthService();
  final String baseUrl;

  ForumService({this.baseUrl = 'http://10.0.2.2:8000'});

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

  // === POSTS ===
  Future<Map<String, dynamic>> getPosts({
    int skip = 0,
    int limit = 20,
    String? category,
    String feedType = 'all',
    String sortBy = 'newest',
  }) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
      'feed_type': feedType,
      'sort_by': sortBy,
      if (category != null) 'category': category,
    };

    final uri = Uri.parse('$baseUrl/forum/posts/').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load posts: ${response.body}');
  }

  Future<Map<String, dynamic>> createPost({
    required String title,
    required String content,
    required String category,
    String privacyLevel = 'public',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/forum/posts/'),
      headers: await _getHeaders(),
      body: jsonEncode({
        'title': title,
        'content': content,
        'category': category,
        'privacy_level': privacyLevel,
      }),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to create post: ${response.body}');
  }

  Future<Map<String, dynamic>> getPost(String postId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/forum/posts/$postId'),
      headers: await _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load post: ${response.body}');
  }

  Future<void> deletePost(String postId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/forum/posts/$postId'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 204) {
      throw Exception('Failed to delete post: ${response.body}');
    }
  }

  // === LIKES ===
  Future<void> toggleLike(String postId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/forum/posts/$postId/like'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to toggle like: ${response.body}');
    }
  }

  // === COMMENTS ===
  Future<Map<String, dynamic>> getComments(String postId, {int skip = 0, int limit = 50}) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/forum/posts/$postId/comments').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load comments: ${response.body}');
  }

  Future<Map<String, dynamic>> createComment(String postId, String content) async {
    final response = await http.post(
      Uri.parse('$baseUrl/forum/posts/$postId/comments'),
      headers: await _getHeaders(),
      body: jsonEncode({'content': content}),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to create comment: ${response.body}');
  }

  Future<void> deleteComment(String commentId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/forum/comments/$commentId'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 204) {
      throw Exception('Failed to delete comment: ${response.body}');
    }
  }

  // === FOLLOW ===
  Future<Map<String, dynamic>> searchUsers(String query, {int skip = 0, int limit = 20}) async {
    final queryParams = {
      'q': query,
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/forum/follow/search').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to search users: ${response.body}');
  }

  Future<void> followUser(String userId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/forum/follow/users/$userId'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to follow user: ${response.body}');
    }
  }

  Future<void> unfollowUser(String userId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/forum/follow/users/$userId'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 204) {
      throw Exception('Failed to unfollow user: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getFollowing({int skip = 0, int limit = 50}) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/forum/follow/following').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load following: ${response.body}');
  }

  Future<Map<String, dynamic>> getFollowers({int skip = 0, int limit = 50}) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/forum/follow/followers').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load followers: ${response.body}');
  }

  // === NOTIFICATIONS ===
  Future<Map<String, dynamic>> getNotifications({int skip = 0, int limit = 50}) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };

    final uri = Uri.parse('$baseUrl/forum/notifications/').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: await _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load notifications: ${response.body}');
  }

  Future<void> markNotificationAsRead(String notificationId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/forum/notifications/$notificationId/read'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to mark notification as read: ${response.body}');
    }
  }

  Future<void> markAllNotificationsAsRead() async {
    final response = await http.put(
      Uri.parse('$baseUrl/forum/notifications/mark-all-read'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to mark all notifications as read: ${response.body}');
    }
  }

  Future<void> deleteNotification(String notificationId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/forum/notifications/$notificationId'),
      headers: await _getHeaders(),
    );

    if (response.statusCode != 204) {
      throw Exception('Failed to delete notification: ${response.body}');
    }
  }

  Future<int> getUnreadNotificationCount() async {
    final response = await http.get(
      Uri.parse('$baseUrl/forum/notifications/unread-count'),
      headers: await _getHeaders(),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['unread_count'] ?? 0;
    }
    throw Exception('Failed to get unread count: ${response.body}');
  }

  // === SETTINGS ===
  Future<Map<String, dynamic>> getForumSettings() async {
    final response = await http.get(
      Uri.parse('$baseUrl/forum/settings/'),
      headers: await _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load forum settings: ${response.body}');
  }

  Future<Map<String, dynamic>> getForumStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/forum/settings/stats'),
      headers: await _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load forum stats: ${response.body}');
  }

  Future<void> updateForumSettings({
    String? defaultPrivacyLevel,
    Map<String, bool>? notificationsEnabled,
  }) async {
    final body = <String, dynamic>{};
    if (defaultPrivacyLevel != null) body['default_privacy_level'] = defaultPrivacyLevel;
    if (notificationsEnabled != null) body['notifications_enabled'] = notificationsEnabled;

    final response = await http.put(
      Uri.parse('$baseUrl/forum/settings/'),
      headers: await _getHeaders(),
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to update forum settings: ${response.body}');
    }
  }
}