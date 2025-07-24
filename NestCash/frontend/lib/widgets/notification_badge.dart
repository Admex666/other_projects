import 'package:flutter/material.dart';
import 'package:frontend/services/notification_service.dart';
import 'package:frontend/screens/notifications_screen.dart';

class NotificationBadge extends StatefulWidget {
  final String userId;
  final Color iconColor;
  final double iconSize;

  const NotificationBadge({
    Key? key,
    required this.userId,
    this.iconColor = Colors.grey,
    this.iconSize = 24,
  }) : super(key: key);

  @override
  _NotificationBadgeState createState() => _NotificationBadgeState();
}

class _NotificationBadgeState extends State<NotificationBadge> {
  final NotificationService _notificationService = NotificationService();
  int _unreadCount = 0;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchUnreadCount();
  }

  Future<void> _fetchUnreadCount() async {
    if (_isLoading) return;
    
    setState(() {
      _isLoading = true;
    });

    try {
      final stats = await _notificationService.getNotificationStats();
      if (mounted) {
        setState(() {
          _unreadCount = stats?.unreadCount ?? 0;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _navigateToNotifications() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => NotificationsScreen(userId: widget.userId),
      ),
    ).then((_) {
      // Refresh unread count when returning from notifications screen
      _fetchUnreadCount();
    });
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _navigateToNotifications,
      child: Stack(
        children: [
          Icon(
            Icons.notifications_outlined,
            color: widget.iconColor,
            size: widget.iconSize,
          ),
          if (_unreadCount > 0)
            Positioned(
              right: 0,
              top: 0,
              child: Container(
                padding: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  color: Colors.red,
                  borderRadius: BorderRadius.circular(10),
                ),
                constraints: const BoxConstraints(
                  minWidth: 18,
                  minHeight: 18,
                ),
                child: Text(
                  _unreadCount > 99 ? '99+' : _unreadCount.toString(),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
        ],
      ),
    );
  }

  // Public method to refresh the badge from parent widgets
  void refresh() {
    _fetchUnreadCount();
  }
}

// Alternative version for AppBar usage
class AppBarNotificationBadge extends StatelessWidget {
  final String userId;

  const AppBarNotificationBadge({
    Key? key,
    required this.userId,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: NotificationBadge(
        userId: userId,
        iconColor: Colors.black, // Ez volt Colors.white
        iconSize: 26,
      ),
    );
  }
}