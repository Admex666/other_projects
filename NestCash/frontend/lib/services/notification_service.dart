import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class NotificationService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const NotificationService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Értesítések listázása
  Future<NotificationListResponse?> getNotifications({
    int skip = 0,
    int limit = 20,
    bool unreadOnly = false,
    String? notificationType,
    String? priority,
  }) async {
    try {
      final headers = await _getHeaders();
      
      final queryParams = <String, String>{
        'skip': skip.toString(),
        'limit': limit.toString(),
        'unread_only': unreadOnly.toString(),
      };
      
      if (notificationType != null) {
        queryParams['notification_type'] = notificationType;
      }
      if (priority != null) {
        queryParams['priority'] = priority;
      }
      
      final uri = Uri.parse('$baseUrl/notifications/').replace(
        queryParameters: queryParams,
      );
      
      final response = await http.get(uri, headers: headers);
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return NotificationListResponse.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error fetching notifications: $e');
      return null;
    }
  }

  /// Értesítési statisztikák
  Future<NotificationStats?> getNotificationStats() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/notifications/stats'),
        headers: headers,
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return NotificationStats.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error fetching notification stats: $e');
      return null;
    }
  }

  /// Értesítés olvasottnak jelölése
  Future<bool> markAsRead(String notificationId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/notifications/$notificationId/read'),
        headers: headers,
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Error marking notification as read: $e');
      return false;
    }
  }

  /// Összes értesítés olvasottnak jelölése
  Future<bool> markAllAsRead() async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/notifications/mark-all-read'),
        headers: headers,
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Error marking all notifications as read: $e');
      return false;
    }
  }

  /// Értesítés törlése
  Future<bool> deleteNotification(String notificationId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.delete(
        Uri.parse('$baseUrl/notifications/$notificationId'),
        headers: headers,
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Error deleting notification: $e');
      return false;
    }
  }

  /// Egy értesítés lekérése
  Future<NotificationItem?> getNotification(String notificationId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/notifications/$notificationId'),
        headers: headers,
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return NotificationItem.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error fetching notification: $e');
      return null;
    }
  }
}

// Model osztályok
class NotificationListResponse {
  final List<NotificationItem> notifications;
  final int totalCount;
  final int unreadCount;
  final int skip;
  final int limit;

  NotificationListResponse({
    required this.notifications,
    required this.totalCount,
    required this.unreadCount,
    required this.skip,
    required this.limit,
  });

  factory NotificationListResponse.fromJson(Map<String, dynamic> json) {
    return NotificationListResponse(
      notifications: (json['notifications'] as List)
          .map((item) => NotificationItem.fromJson(item))
          .toList(),
      totalCount: json['total_count'],
      unreadCount: json['unread_count'],
      skip: json['skip'],
      limit: json['limit'],
    );
  }
}

class NotificationItem {
  final String id;
  final String userId;
  final String type;
  final String title;
  final String message;
  final String priority;
  final bool isRead;
  final DateTime createdAt;
  final DateTime? readAt;
  final DateTime? expiresAt;
  final String? actionUrl;
  final String? actionText;
  final String? relatedTransactionId;
  final String? relatedForumPostId;
  final String? relatedUserId;

  NotificationItem({
    required this.id,
    required this.userId,
    required this.type,
    required this.title,
    required this.message,
    required this.priority,
    required this.isRead,
    required this.createdAt,
    this.readAt,
    this.expiresAt,
    this.actionUrl,
    this.actionText,
    this.relatedTransactionId,
    this.relatedForumPostId,
    this.relatedUserId,
  });

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    return NotificationItem(
      id: json['id'],
      userId: json['user_id'],
      type: json['type'],
      title: json['title'],
      message: json['message'],
      priority: json['priority'],
      isRead: json['is_read'],
      createdAt: DateTime.parse(json['created_at']),
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
      expiresAt: json['expires_at'] != null ? DateTime.parse(json['expires_at']) : null,
      actionUrl: json['action_url'],
      actionText: json['action_text'],
      relatedTransactionId: json['related_transaction_id'],
      relatedForumPostId: json['related_forum_post_id'],
      relatedUserId: json['related_user_id'],
    );
  }
}

class NotificationStats {
  final int totalCount;
  final int unreadCount;
  final Map<String, int> priorityCounts;
  final Map<String, int> typeCounts;

  NotificationStats({
    required this.totalCount,
    required this.unreadCount,
    required this.priorityCounts,
    required this.typeCounts,
  });

  factory NotificationStats.fromJson(Map<String, dynamic> json) {
    return NotificationStats(
      totalCount: json['total_count'],
      unreadCount: json['unread_count'],
      priorityCounts: Map<String, int>.from(json['priority_counts']),
      typeCounts: Map<String, int>.from(json['type_counts']),
    );
  }
}

// Enum-ok
enum NotificationType {
  transactionAdded,
  accountBalanceLow,
  monthlySummary,
  budgetExceeded,
  forumLike,
  forumComment,
  forumFollow,
  systemMessage,
  knowledgeProgress,
}

enum NotificationPriority {
  low,
  medium,
  high,
  urgent,
}