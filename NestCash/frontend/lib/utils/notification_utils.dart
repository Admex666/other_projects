import 'package:flutter/material.dart';
import 'package:frontend/services/notification_service.dart';

class NotificationUtils {
  
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
      default:
        return Icons.notifications;
    }
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

  /// Értesítés típus alapján visszaadja a magyar nyelvű nevet
  static String getTypeDisplayName(String type) {
    switch (type) {
      case 'transaction_added':
        return 'Tranzakció hozzáadva';
      case 'account_balance_low':
        return 'Alacsony egyenleg';
      case 'monthly_summary':
        return 'Havi összesítő';
      case 'budget_exceeded':
        return 'Költségkeret túllépve';
      case 'forum_like':
        return 'Fórum kedvelés';
      case 'forum_comment':
        return 'Fórum komment';
      case 'forum_follow':
        return 'Fórum követés';
      case 'system_message':
        return 'Rendszerüzenet';
      case 'knowledge_progress':
        return 'Tanulási haladás';
      default:
        return 'Értesítés';
    }
  }

  /// Prioritás alapján visszaadja a magyar nyelvű nevet
  static String getPriorityDisplayName(String priority) {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return 'Sürgős';
      case 'high':
        return 'Magas';
      case 'medium':
        return 'Közepes';
      case 'low':
        return 'Alacsony';
      default:
        return 'Ismeretlen';
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
      return '${difference.inDays} napja';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} órája';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} perce';
    } else {
      return 'Most';
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

  /// Értesítési filterek lista
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
    ];
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
Értesítés részletei:
- Cím: ${notification.title}
- Üzenet: ${notification.message}
- Típus: ${getTypeDisplayName(notification.type)}
- Prioritás: ${getPriorityDisplayName(notification.priority)}
- Létrehozva: ${formatRelativeTime(notification.createdAt)}
- Állapot: ${notification.isRead ? 'Olvasott' : 'Olvasatlan'}
${notification.actionText != null ? '- Művelet: ${notification.actionText}' : ''}
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
      onSuccess('$successCount értesítés sikeresen feldolgozva');
    } else {
      onError('$successCount sikeres, $errorCount sikertelen művelet');
    }
  }
}