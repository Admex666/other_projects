class PrivateMessage {
  final String id;
  final String senderId;
  final String receiverId;
  final String senderUsername;
  final String receiverUsername;
  final String content;
  final bool isRead;
  final DateTime createdAt;
  final bool isMyMessage;

  PrivateMessage({
    required this.id,
    required this.senderId,
    required this.receiverId,
    required this.senderUsername,
    required this.receiverUsername,
    required this.content,
    required this.isRead,
    required this.createdAt,
    required this.isMyMessage,
  });

  factory PrivateMessage.fromJson(Map<String, dynamic> json) {
    return PrivateMessage(
      id: json['id'],
      senderId: json['sender_id'],
      receiverId: json['receiver_id'],
      senderUsername: json['sender_username'],
      receiverUsername: json['receiver_username'],
      content: json['content'],
      isRead: json['is_read'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
      isMyMessage: json['is_my_message'] ?? false,
    );
  }
}

class Conversation {
  final String id;
  final String otherUserId;
  final String otherUsername;
  final String? lastMessageContent;
  final DateTime? lastMessageAt;
  final int unreadCount;

  Conversation({
    required this.id,
    required this.otherUserId,
    required this.otherUsername,
    this.lastMessageContent,
    this.lastMessageAt,
    required this.unreadCount,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id'],
      otherUserId: json['other_user_id'],
      otherUsername: json['other_username'],
      lastMessageContent: json['last_message_content'],
      lastMessageAt: json['last_message_at'] != null 
        ? DateTime.parse(json['last_message_at']) 
        : null,
      unreadCount: json['unread_count'] ?? 0,
    );
  }
}