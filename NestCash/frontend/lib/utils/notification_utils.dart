import 'package:flutter/material.dart';
import 'package:frontend/services/notification_service.dart';
import 'package:easy_localization/easy_localization.dart';

class NotificationUtils {
  
  /// Értesítés típus alapján visszaadja a megfelelő ikont
  /// Értesítés típus alapján visszaadja a megfelelő ikont
static IconData getTypeIcon(String type) {
    switch (type) {
      case 'transaction_added':
        return Icons.account_balance_wallet;
      case 'account_balance_low':
        return Icons.warning;
      case 'monthly_summary':
        return Icons.assessment;
      case 'budget_exceeded':
        return Icons.error_outline;
      case 'forum_like':
        return Icons.favorite;
      case 'forum_comment':
        return Icons.comment;
      case 'forum_follow':
        return Icons.person_add;
      case 'system_message':
        return Icons.info;
      case 'knowledge_progress':
        return Icons.school;
      case 'badge_earned':
        return Icons.emoji_events;
      case 'challenge_started':
        return Icons.flag;
      case 'challenge_completed':
        return Icons.check_circle;
      case 'limit_warning':
        return Icons.warning_amber;
      case 'pti_ranking':
        return Icons.leaderboard;
      case 'daily_lesson_reminder':
        return Icons.alarm;
      default:
        return Icons.notifications;
    }
  }

  static String getTypeDisplayName(String type) {
    switch (type) {
      case 'transaction_added':
        return 'notification_utils.transaction_added'.tr();
      case 'account_balance_low':
        return 'notification_utils.account_balance_low'.tr();
      case 'monthly_summary':
        return 'notification_utils.monthly_summary'.tr();
      case 'budget_exceeded':
        return 'notification_utils.budget_exceeded'.tr();
      case 'forum_like':
        return 'notification_utils.forum_like'.tr();
      case 'forum_comment':
        return 'notification_utils.forum_comment'.tr();
      case 'forum_follow':
        return 'notification_utils.forum_follow'.tr();
      case 'system_message':
        return 'notification_utils.system_message'.tr();
      case 'knowledge_progress':
        return 'notification_utils.knowledge_progress'.tr();
      case 'badge_earned':
        return 'notification_utils.badge_earned'.tr();
      case 'challenge_started':
        return 'notification_utils.challenge_started'.tr();
      case 'challenge_completed':
        return 'notification_utils.challenge_completed'.tr();
      case 'limit_warning':
        return 'notification_utils.limit_warning'.tr();
      case 'pti_ranking':
        return 'notification_utils.pti_ranking'.tr();
      case 'daily_lesson_reminder':
        return 'notification_utils.daily_lesson_reminder'.tr();
      default:
        return 'notification_utils.notification_default'.tr();
    }
  }

  // Új típusok listájához hozzáadás:
  static List<String> getNotificationTypes() {
    return [
      'transaction_added',
      'account_balance_low',
      'monthly_summary',
      'budget_exceeded',
      'forum_like',
      'forum_comment',
      'forum_follow',
      'system_message',
      'knowledge_progress',
      'badge_earned',
      'challenge_started',
      'challenge_completed',
      'limit_warning',
      'pti_ranking',
      'daily_lesson_reminder',
    ];
  }

  /// Prioritás alapján visszaadja a megfelelő színt
  static Color getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.blue;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  /// Prioritás alapján visszaadja a magyar nyelvű nevet
  static String getPriorityDisplayName(String priority) {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return 'notification_utils.urgent'.tr();
      case 'high':
        return 'notification_utils.high'.tr();
      case 'medium':
        return 'notification_utils.medium'.tr();
      case 'low':
        return 'notification_utils.low'.tr();
      default:
        return 'notification_utils.unknown'.tr();
    }
  }

  /// Értesítés típus alapján visszaadja a megfelelő háttérszínt
  static Color getTypeBackgroundColor(String type) {
    switch (type) {
      case 'transaction_added':
        return Colors.green.withOpacity(0.1);
      case 'account_balance_low':
        return Colors.orange.withOpacity(0.1);
      case 'monthly_summary':
        return Colors.blue.withOpacity(0.1);
      case 'budget_exceeded':
        return Colors.red.withOpacity(0.1);
      case 'forum_like':
        return Colors.pink.withOpacity(0.1);
      case 'forum_comment':
        return Colors.purple.withOpacity(0.1);
      case 'forum_follow':
        return Colors.indigo.withOpacity(0.1);
      case 'system_message':
        return Colors.grey.withOpacity(0.1);
      case 'knowledge_progress':
        return Colors.teal.withOpacity(0.1);
      case 'badge_earned':
        return Colors.amber.withOpacity(0.1);
      case 'challenge_started':
        return Colors.cyan.withOpacity(0.1);
      case 'challenge_completed':
        return Colors.green.withOpacity(0.1);
      case 'limit_warning':
        return Colors.orange.withOpacity(0.1);
      case 'pti_ranking':
        return Colors.deepPurple.withOpacity(0.1);
      case 'daily_lesson_reminder':
        return Colors.lightBlue.withOpacity(0.1);
      default:
        return Colors.grey.withOpacity(0.1);
    }
  }

  /// Relatív idő formázása magyarul
  static String formatRelativeTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 7) {
      return '${dateTime.year}.${dateTime.month.toString().padLeft(2, '0')}.${dateTime.day.toString().padLeft(2, '0')}';
    } else if (difference.inDays > 0) {
      return 'notification_utils.days_ago'.tr(namedArgs: {'days': difference.inDays.toString()});
    } else if (difference.inHours > 0) {
      return 'notification_utils.hours_ago'.tr(namedArgs: {'hours': difference.inHours.toString()});
    } else if (difference.inMinutes > 0) {
      return 'notification_utils.minutes_ago'.tr(namedArgs: {'minutes': difference.inMinutes.toString()});
    } else {
      return 'notification_utils.now'.tr();
    }
  }

  /// Navigáció az értesítés típusa alapján
  static void handleNotificationTap(
    BuildContext context, 
    NotificationItem notification,
    String userId,
  ) {
    // Itt implementálhatjuk a különböző értesítés típusokhoz tartozó navigációt
    switch (notification.type) {
      case 'transaction_added':
        if (notification.relatedTransactionId != null) {
          // Navigator.pushNamed(context, '/transaction-details', 
          //   arguments: notification.relatedTransactionId);
        }
        break;
      case 'account_balance_low':
        // Navigator.pushNamed(context, '/accounts');
        break;
      case 'forum_like':
      case 'forum_comment':
        if (notification.relatedForumPostId != null) {
          // Navigator.pushNamed(context, '/forum/post', 
          //   arguments: notification.relatedForumPostId);
        }
        break;
      case 'forum_follow':
        if (notification.relatedUserId != null) {
          // Navigator.pushNamed(context, '/forum/user', 
          //   arguments: notification.relatedUserId);
        }
        break;
      case 'monthly_summary':
        // Navigator.pushNamed(context, '/analysis');
        break;
      case 'knowledge_progress':
        // Navigator.pushNamed(context, '/knowledge');
        break;
      default:
        // Default behavior - just mark as read
        break;
    }
  }

  /// SnackBar megjelenítése
  static void showSnackBar(BuildContext context, String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : const Color(0xFF00D4AA),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  /// Prioritási szintek lista
  static List<String> getPriorityLevels() {
    return [
      'urgent',
      'high',
      'medium',
      'low',
    ];
  }

  /// Értesítés exportálása szövegként
  static String exportNotificationAsText(NotificationItem notification) {
    return '''
${'notification_utils.export_details_title'.tr()}
- ${'notification_utils.export_title'.tr()}: ${notification.title}
- ${'notification_utils.export_message'.tr()}: ${notification.message}
- ${'notification_utils.export_type'.tr()}: ${getTypeDisplayName(notification.type)}
- ${'notification_utils.export_priority'.tr()}: ${getPriorityDisplayName(notification.priority)}
- ${'notification_utils.export_created'.tr()}: ${formatRelativeTime(notification.createdAt)}
- ${'notification_utils.export_status'.tr()}: ${notification.isRead ? 'notification_utils.export_read'.tr() : 'notification_utils.export_unread'.tr()}
${notification.actionText != null ? '- ${'notification_utils.export_action'.tr()}: ${notification.actionText}' : ''}
    ''';
  }
  
  /// Batch operations helper
  static Future<void> performBatchOperation(
    List<NotificationItem> notifications,
    Future<bool> Function(String) operation,
    Function(String) onSuccess,
    Function(String) onError,
  ) async {
    int successCount = 0;
    int errorCount = 0;

    for (final notification in notifications) {
      try {
        final success = await operation(notification.id);
        if (success) {
          successCount++;
        } else {
          errorCount++;
        }
      } catch (e) {
        errorCount++;
      }
    }

    if (errorCount == 0) {
      onSuccess('notification_utils.batch_success'.tr(namedArgs: {'count': successCount.toString()}));
    } else {
      onError('notification_utils.batch_partial_success'.tr(namedArgs: {'success_count': successCount.toString(), 'error_count': errorCount.toString()}));
    }
  }
}