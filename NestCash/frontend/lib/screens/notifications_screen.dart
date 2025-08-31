import 'package:flutter/material.dart';
import 'package:frontend/services/notification_service.dart';
import 'package:timeago/timeago.dart' as timeago;
import 'package:frontend/utils/notification_utils.dart';
import 'package:easy_localization/easy_localization.dart';

class NotificationsScreen extends StatefulWidget {
  final String userId;

  const NotificationsScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _NotificationsScreenState createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> 
    with TickerProviderStateMixin {
  final NotificationService _notificationService = NotificationService();
  NotificationListResponse? _notificationResponse;
  bool _isLoading = false;
  bool _showUnreadOnly = false;
  late TabController _tabController;
  String? _selectedType;
  String? _selectedPriority;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchNotifications();
    
    // Set Hungarian locale for timeago
    timeago.setLocaleMessages('hu', timeago.HuMessages());
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchNotifications() async {
    setState(() {
      _isLoading = true;
    });

    final response = await _notificationService.getNotifications(
      unreadOnly: _showUnreadOnly,
      limit: 50,
      notificationType: _selectedType,
      priority: _selectedPriority,
    );

    setState(() {
      _notificationResponse = response;
      _isLoading = false;
    });
  }

  Future<void> _markAsRead(String notificationId) async {
    final success = await _notificationService.markAsRead(notificationId);
    if (success) {
      _fetchNotifications();
    }
  }

  Future<void> _markAllAsRead() async {
    final success = await _notificationService.markAllAsRead();
    if (success) {
      _fetchNotifications();
      _showSnackBar('notifications.snackbar.markAllReadSuccess'.tr());
    }
  }

  Future<void> _deleteNotification(String notificationId) async {
    final success = await _notificationService.deleteNotification(notificationId);
    if (success) {
      _fetchNotifications();
      _showSnackBar('notifications.snackbar.deleteSuccess'.tr());
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: const Color(0xFF00D4AA),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  void _showNotificationDetail(NotificationItem notification) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        padding: const EdgeInsets.all(20),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    color: NotificationUtils.getPriorityColor(notification.priority).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: Icon(
                    NotificationUtils.getTypeIcon(notification.type),
                    color: NotificationUtils.getPriorityColor(notification.priority),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        notification.title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        NotificationUtils.formatRelativeTime(notification.createdAt),
                        style: TextStyle(
                          color: Colors.grey[500],
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Expanded(
              child: SingleChildScrollView(
                child: Text(
                  notification.message,
                  style: const TextStyle(
                    fontSize: 16,
                    height: 1.5,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotificationItem(NotificationItem notification) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Card(
        elevation: notification.isRead ? 1 : 3,
        color: notification.isRead ? Colors.grey[50] : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        child: ListTile(
          leading: Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: NotificationUtils.getPriorityColor(notification.priority).withOpacity(0.1),
              borderRadius: BorderRadius.circular(25),
            ),
            child: Icon(
              NotificationUtils.getTypeIcon(notification.type),
              color: NotificationUtils.getPriorityColor(notification.priority),
              size: 24,
            ),
          ),
          title: Text(
            notification.title,
            style: TextStyle(
              fontWeight: notification.isRead ? FontWeight.normal : FontWeight.bold,
              fontSize: 16,
            ),
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 4),
              Text(
                notification.message,
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 14,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(
                    Icons.access_time,
                    size: 12,
                    color: Colors.grey[500],
                  ),
                  const SizedBox(width: 4),
                  Text(
                    NotificationUtils.formatRelativeTime(notification.createdAt),
                    style: TextStyle(
                      color: Colors.grey[500],
                      fontSize: 12,
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: NotificationUtils.getPriorityColor(notification.priority).withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      NotificationUtils.getPriorityDisplayName(notification.priority),
                      style: TextStyle(
                        color: NotificationUtils.getPriorityColor(notification.priority),
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          trailing: PopupMenuButton<String>(
            onSelected: (value) {
              switch (value) {
                case 'read':
                  if (!notification.isRead) {
                    _markAsRead(notification.id);
                  }
                  break;
                case 'delete':
                  _showDeleteDialog(notification.id);
                  break;
              }
            },
            itemBuilder: (context) => [
              if (!notification.isRead)
                PopupMenuItem(
                  value: 'read',
                  child: Row(
                    children: [
                      const Icon(Icons.mark_email_read),
                      const SizedBox(width: 8),
                      Text('notifications.markAsRead'.tr()),
                    ],
                  ),
                ),
              PopupMenuItem(
                value: 'delete',
                child: Row(
                  children: [
                    const Icon(Icons.delete, color: Colors.red),
                    const SizedBox(width: 8),
                    Text('notifications.delete'.tr(), style: const TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
          ),
          onTap: () {
            if (!notification.isRead) {
              _markAsRead(notification.id);
            }
            _showNotificationDetail(notification);
          },
        ),
      ),
    );
  }

  void _showDeleteDialog(String notificationId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('notifications.deleteTitle'.tr()),
        content: Text('notifications.deleteMessage'.tr()),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('notifications.cancel'.tr()),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _deleteNotification(notificationId);
            },
            child: Text('notifications.delete'.tr(), style: const TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  void _showFilterDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => Container(
        padding: const EdgeInsets.all(20),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'notifications.filtersTitle'.tr(),
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            
            // Típus szűrő
            Text('notifications.type'.tr(), style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String?>(
              value: _selectedType,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: 'notifications.allTypes'.tr(),
              ),
              items: [
                DropdownMenuItem(value: null, child: Text('notifications.allTypes'.tr())),
                ...NotificationUtils.getNotificationTypes().map(
                  (type) => DropdownMenuItem(
                    value: type,
                    child: Text(NotificationUtils.getTypeDisplayName(type)),
                  ),
                ),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedType = value;
                });
              },
            ),
            const SizedBox(height: 16),
            
            // Prioritás szűrő
            Text('notifications.priority'.tr(), style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String?>(
              value: _selectedPriority,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: 'notifications.allPriorities'.tr(),
              ),
              items: [
                DropdownMenuItem(value: null, child: Text('notifications.allPriorities'.tr())),
                ...NotificationUtils.getPriorityLevels().map(
                  (priority) => DropdownMenuItem(
                    value: priority,
                    child: Text(NotificationUtils.getPriorityDisplayName(priority)),
                  ),
                ),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedPriority = value;
                });
              },
            ),
            const SizedBox(height: 20),
            
            // Gombok
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      setState(() {
                        _selectedType = null;
                        _selectedPriority = null;
                      });
                      Navigator.pop(context);
                      _fetchNotifications();
                    },
                    child: Text('notifications.clearFilters'.tr()),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      _fetchNotifications();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00D4AA),
                    ),
                    child: Text('notifications.apply'.tr()),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildUnreadTab() {
    final unreadNotifications = _notificationResponse?.notifications
        .where((n) => !n.isRead)
        .toList() ?? [];

    if (unreadNotifications.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.notifications_off,
              size: 64,
              color: Colors.grey,
            ),
            const SizedBox(height: 16),
            Text(
              'notifications.noUnread'.tr(),
              style: const TextStyle(
                fontSize: 18,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchNotifications,
      child: ListView.builder(
        itemCount: unreadNotifications.length,
        itemBuilder: (context, index) {
          return _buildNotificationItem(unreadNotifications[index]);
        },
      ),
    );
  }

  Widget _buildAllTab() {
    final notifications = _notificationResponse?.notifications ?? [];

    if (notifications.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.notifications_none,
              size: 64,
              color: Colors.grey,
            ),
            const SizedBox(height: 16),
            Text(
              'notifications.noNotifications'.tr(),
              style: const TextStyle(
                fontSize: 18,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchNotifications,
      child: ListView.builder(
        itemCount: notifications.length,
        itemBuilder: (context, index) {
          return _buildNotificationItem(notifications[index]);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.arrow_back, color: Colors.black87),
                  ),
                  Expanded(
                    child: Text(
                      'notifications.title'.tr(),
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  PopupMenuButton<String>(
                    icon: const Icon(Icons.more_vert, color: Colors.black87),
                    onSelected: (value) {
                      switch (value) {
                        case 'mark_all_read':
                          _markAllAsRead();
                          break;
                        case 'filter':
                          _showFilterDialog();
                          break;
                      }
                    },
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        value: 'mark_all_read',
                        child: Row(
                          children: [
                            const Icon(Icons.mark_email_read),
                            const SizedBox(width: 8),
                            Text('notifications.markAllRead'.tr()),
                          ],
                        ),
                      ),
                      PopupMenuItem(
                        value: 'filter',
                        child: Row(
                          children: [
                            const Icon(Icons.filter_list),
                            const SizedBox(width: 8),
                            Text('notifications.filters'.tr()),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            
            // Stats
            if (_notificationResponse != null)
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    Column(
                      children: [
                        Text(
                          _notificationResponse!.totalCount.toString(),
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        Text(
                          'notifications.total'.tr(),
                          style: const TextStyle(color: Colors.black87),
                        ),
                      ],
                    ),
                    Column(
                      children: [
                        Text(
                          _notificationResponse!.unreadCount.toString(),
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        Text(
                          'notifications.unread'.tr(),
                          style: const TextStyle(color: Colors.black87),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

            // Tab Bar
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(25),
              ),
              child: TabBar(
                controller: _tabController,
                indicator: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(25),
                ),
                labelColor: const Color(0xFF00D4AA),
                unselectedLabelColor: Colors.black87,
                tabs: [
                  Tab(text: 'notifications.unreadTab'.tr()),
                  Tab(text: 'notifications.allTab'.tr()),
                ],
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Content
            Expanded(
              child: Container(
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                  ),
                ),
                child: _isLoading
                    ? const Center(
                        child: CircularProgressIndicator(
                          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4AA)),
                        ),
                      )
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildUnreadTab(),
                          _buildAllTab(),
                        ],
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}