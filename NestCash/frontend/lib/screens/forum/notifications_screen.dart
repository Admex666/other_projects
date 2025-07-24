// lib/screens/forum/notifications_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/forum_service.dart';
import 'package:frontend/models/forum_models.dart';
import 'package:frontend/screens/forum/post_detail_screen.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({Key? key}) : super(key: key);

  @override
  _NotificationsScreenState createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final ForumService _forumService = ForumService();
  final ScrollController _scrollController = ScrollController();
  
  List<ForumNotification> _notifications = [];
  bool _isLoading = false;
  bool _hasMore = true;
  int _skip = 0;
  final int _limit = 20;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 500) {
      if (!_isLoading && _hasMore) {
        _loadMoreNotifications();
      }
    }
  }

  Future<void> _loadNotifications() async {
    if (_isLoading) return;
    
    setState(() {
      _isLoading = true;
      _skip = 0;
      _notifications.clear();
      _hasMore = true;
    });

    try {
      final response = await _forumService.getNotifications(
        skip: _skip,
        limit: _limit,
      );

      final List<dynamic> notificationsJson = response['notifications'];
      final List<ForumNotification> newNotifications = notificationsJson
          .map((json) => ForumNotification.fromJson(json))
          .toList();

      setState(() {
        _notifications = newNotifications;
        _skip += _limit;
        _hasMore = newNotifications.length == _limit;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba az értesítések betöltésekor: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadMoreNotifications() async {
    if (_isLoading || !_hasMore) return;
    
    setState(() {
      _isLoading = true;
    });

    try {
      final response = await _forumService.getNotifications(
        skip: _skip,
        limit: _limit,
      );

      final List<dynamic> notificationsJson = response['notifications'];
      final List<ForumNotification> newNotifications = notificationsJson
          .map((json) => ForumNotification.fromJson(json))
          .toList();

      setState(() {
        _notifications.addAll(newNotifications);
        _skip += _limit;
        _hasMore = newNotifications.length == _limit;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba az értesítések betöltésekor: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _markAsRead(ForumNotification notification) async {
    if (notification.isRead) return;

    try {
      await _forumService.markNotificationAsRead(notification.id);
      
      setState(() {
        final index = _notifications.indexWhere((n) => n.id == notification.id);
        if (index != -1) {
          _notifications[index] = ForumNotification(
            id: notification.id,
            type: notification.type,
            message: notification.message,
            postId: notification.postId,
            fromUserId: notification.fromUserId,
            fromUsername: notification.fromUsername,
            isRead: true,
            createdAt: notification.createdAt,
          );
        }
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba az értesítés olvasottá jelölésekor: $e')),
      );
    }
  }

  Future<void> _markAllAsRead() async {
    try {
      await _forumService.markAllNotificationsAsRead();
      
      setState(() {
        _notifications = _notifications.map((notification) => 
          ForumNotification(
            id: notification.id,
            type: notification.type,
            message: notification.message,
            postId: notification.postId,
            fromUserId: notification.fromUserId,
            fromUsername: notification.fromUsername,
            isRead: true,
            createdAt: notification.createdAt,
          )
        ).toList();
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Minden értesítés olvasottá jelölve!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba az értesítések olvasottá jelölésekor: $e')),
      );
    }
  }

  Future<void> _deleteNotification(ForumNotification notification) async {
    try {
      await _forumService.deleteNotification(notification.id);
      
      setState(() {
        _notifications.removeWhere((n) => n.id == notification.id);
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Értesítés törölve!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba az értesítés törlésekor: $e')),
      );
    }
  }

  void _handleNotificationTap(ForumNotification notification) {
    _markAsRead(notification);

    if (notification.postId != null) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => PostDetailScreen(postId: notification.postId!),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final unreadCount = _notifications.where((n) => !n.isRead).length;

    return Scaffold(
      backgroundColor: Color(0xFFF5F5F5),
      appBar: AppBar(
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Értesítések',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          if (unreadCount > 0)
            TextButton(
              onPressed: _markAllAsRead,
              child: Text(
                'Mind olvasott',
                style: TextStyle(
                  color: Colors.black87,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // Stats header
          if (unreadCount > 0)
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Color(0xFF00D4A3),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(30),
                  bottomRight: Radius.circular(30),
                ),
              ),
              child: Text(
                '$unreadCount olvasatlan értesítés',
                style: TextStyle(
                  color: Colors.black87,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
              ),
            ),

          // Notifications list
          Expanded(
            child: RefreshIndicator(
              onRefresh: _loadNotifications,
              child: _notifications.isEmpty && !_isLoading
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.notifications_outlined,
                            size: 64,
                            color: Colors.grey[400],
                          ),
                          SizedBox(height: 16),
                          Text(
                            'Nincsenek értesítések',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey[600],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          SizedBox(height: 8),
                          Text(
                            'Itt fogod látni az értesítéseidet',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[500],
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: EdgeInsets.all(16),
                      itemCount: _notifications.length + (_isLoading ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index == _notifications.length) {
                          return Center(
                            child: Padding(
                              padding: EdgeInsets.all(20),
                              child: CircularProgressIndicator(
                                color: Color(0xFF00D4AA),
                              ),
                            ),
                          );
                        }

                        final notification = _notifications[index];
                        return _buildNotificationCard(notification);
                      },
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationCard(ForumNotification notification) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: notification.isRead ? Colors.white : Color(0xFFF0F8FF),
        borderRadius: BorderRadius.circular(12),
        border: notification.isRead 
            ? null 
            : Border.all(color: Color(0xFF00D4AA).withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () => _handleNotificationTap(notification),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Row(
            children: [
              // Notification icon
              Container(
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _getNotificationColor(notification.type).withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  _getNotificationIcon(notification.type),
                  color: _getNotificationColor(notification.type),
                  size: 20,
                ),
              ),
              
              SizedBox(width: 12),
              
              // Notification content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      notification.message,
                      style: TextStyle(
                        fontWeight: notification.isRead ? FontWeight.w500 : FontWeight.bold,
                        fontSize: 14,
                        color: Colors.black87,
                      ),
                    ),
                    
                    SizedBox(height: 4),
                    
                    Text(
                      notification.message,
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey[600],
                        height: 1.3,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    
                    SizedBox(height: 6),
                    
                    Row(
                      children: [
                        if (notification.fromUsername != null)
                          Container(
                            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.grey[100],
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              notification.fromUsername!,
                              style: TextStyle(
                                fontSize: 10,
                                color: Colors.grey[700],
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        
                        Spacer(),
                        
                        Text(
                          _formatDateTime(notification.createdAt),
                          style: TextStyle(
                            fontSize: 10,
                            color: Colors.grey[500],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              
              // Actions
              PopupMenuButton<String>(
                onSelected: (value) {
                  switch (value) {
                    case 'mark_read':
                      _markAsRead(notification);
                      break;
                    case 'delete':
                      _deleteNotification(notification);
                      break;
                  }
                },
                itemBuilder: (context) => [
                  if (!notification.isRead)
                    PopupMenuItem(
                      value: 'mark_read',
                      child: Row(
                        children: [
                          Icon(Icons.check, size: 16, color: Colors.green),
                          SizedBox(width: 8),
                          Text('Olvasottá jelölés'),
                        ],
                      ),
                    ),
                  PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        Icon(Icons.delete, size: 16, color: Colors.red),
                        SizedBox(width: 8),
                        Text('Törlés'),
                      ],
                    ),
                  ),
                ],
                child: Container(
                  padding: EdgeInsets.all(4),
                  child: Icon(
                    Icons.more_vert,
                    color: Colors.grey[600],
                    size: 16,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getNotificationIcon(String type) {
    switch (type) {
      case 'like':
        return Icons.favorite;
      case 'comment':
        return Icons.comment;
      case 'follow':
        return Icons.person_add;
      case 'mention':
        return Icons.alternate_email;
      default:
        return Icons.notifications;
    }
  }

  Color _getNotificationColor(String type) {
    switch (type) {
      case 'like':
        return Colors.red;
      case 'comment':
        return Colors.blue;
      case 'follow':
        return Colors.green;
      case 'mention':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'Most';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes} perce';
    } else if (difference.inDays < 1) {
      return '${difference.inHours} órája';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} napja';
    } else {
      return '${dateTime.year}. ${dateTime.month.toString().padLeft(2, '0')}. ${dateTime.day.toString().padLeft(2, '0')}.';
    }
  }
}