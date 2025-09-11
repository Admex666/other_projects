import 'package:firebase_analytics/firebase_analytics.dart';

class FirebaseAnalyticsService {
  static final FirebaseAnalytics _analytics = FirebaseAnalytics.instance;

  // ÁLTALÁNOS ESEMÉNY LOGOLÁS
  static Future<void> logEvent({
    required String name,
    Map<String, dynamic>? parameters,
  }) async {
    try {
      await _analytics.logEvent(
        name: name,
        parameters: parameters,
      );
    } catch (e) {
      print('Analytics logEvent error: $e');
    }
  }

  // KÉPERNYŐ ESEMÉNYEK
  static Future<void> logScreenView(String screenName, {String? screenClass}) async {
    try {
      await _analytics.logScreenView(
        screenName: screenName,
        screenClass: screenClass ?? screenName,
      );
    } catch (e) {
      print('Analytics screen view error: $e');
    }
  }

  // FELHASZNÁLÓ BEÁLLÍTÁSOK
  static Future<void> setUserId(String userId) async {
    try {
      await _analytics.setUserId(id: userId);
    } catch (e) {
      print('Analytics setUserId error: $e');
    }
  }

  static Future<void> setUserProperty(String name, String? value) async {
    try {
      await _analytics.setUserProperty(name: name, value: value);
    } catch (e) {
      print('Analytics setUserProperty error: $e');
    }
  }

  // PÉNZÜGYI ESEMÉNYEK
  static Future<void> logTransactionAdded({
    required String type, // 'income' vagy 'expense'
    required double amount,
    required String category,
    String? account,
    String? description,
  }) async {
    try {
      await _analytics.logEvent(
        name: 'transaction_added',
        parameters: {
          'transaction_type': type,
          'amount': amount,
          'category': category,
          'currency': 'HUF',
          if (account != null) 'account': account,
          if (description != null) 'has_description': description.isNotEmpty,
          'timestamp': DateTime.now().millisecondsSinceEpoch,
        },
      );
    } catch (e) {
      print('Analytics transaction error: $e');
    }
  }

  static Future<void> logTransactionEdited({
    required String type,
    required double oldAmount,
    required double newAmount,
    required String category,
  }) async {
    try {
      await _analytics.logEvent(
        name: 'transaction_edited',
        parameters: {
          'transaction_type': type,
          'old_amount': oldAmount,
          'new_amount': newAmount,
          'amount_change': newAmount - oldAmount,
          'category': category,
          'currency': 'HUF',
        },
      );
    } catch (e) {
      print('Analytics transaction edit error: $e');
    }
  }

  static Future<void> logTransactionDeleted({
    required String type,
    required double amount,
    required String category,
  }) async {
    try {
      await _analytics.logEvent(
        name: 'transaction_deleted',
        parameters: {
          'transaction_type': type,
          'amount': amount,
          'category': category,
          'currency': 'HUF',
        },
      );
    } catch (e) {
      print('Analytics transaction delete error: $e');
    }
  }

  // LIMIT ÉS CÉLOK ESEMÉNYEK
  static Future<void> logLimitSet({
    required String category,
    required double amount,
    required String period, // 'monthly', 'weekly', stb.
  }) async {
    try {
      await _analytics.logEvent(
        name: 'limit_set',
        parameters: {
          'category': category,
          'limit_amount': amount,
          'period': period,
          'currency': 'HUF',
        },
      );
    } catch (e) {
      print('Analytics limit set error: $e');
    }
  }

  static Future<void> logLimitExceeded({
    required String category,
    required double limitAmount,
    required double currentAmount,
    required double overageAmount,
  }) async {
    try {
      await _analytics.logEvent(
        name: 'limit_exceeded',
        parameters: {
          'category': category,
          'limit_amount': limitAmount,
          'current_amount': currentAmount,
          'overage_amount': overageAmount,
          'overage_percentage': (overageAmount / limitAmount) * 100,
          'currency': 'HUF',
        },
      );
    } catch (e) {
      print('Analytics limit exceeded error: $e');
    }
  }

  // FELHASZNÁLÓI INTERAKCIÓK
  static Future<void> logButtonPress(String buttonName, {String? screenName, Map<String, dynamic>? additionalParams}) async {
    try {
      await _analytics.logEvent(
        name: 'button_pressed',
        parameters: {
          'button_name': buttonName,
          if (screenName != null) 'screen_name': screenName,
          ...?additionalParams,
        },
      );
    } catch (e) {
      print('Analytics button press error: $e');
    }
  }

  static Future<void> logFeatureUsed(String featureName, {Map<String, dynamic>? parameters}) async {
    try {
      await _analytics.logEvent(
        name: 'feature_used',
        parameters: {
          'feature_name': featureName,
          ...?parameters,
        },
      );
    } catch (e) {
      print('Analytics feature used error: $e');
    }
  }

  // NAVIGÁCIÓ ESEMÉNYEK
  static Future<void> logNavigationEvent({
    required String fromScreen,
    required String toScreen,
    String? navigationMethod, // 'drawer', 'bottom_nav', 'button', stb.
  }) async {
    try {
      await _analytics.logEvent(
        name: 'navigation',
        parameters: {
          'from_screen': fromScreen,
          'to_screen': toScreen,
          if (navigationMethod != null) 'method': navigationMethod,
        },
      );
    } catch (e) {
      print('Analytics navigation error: $e');
    }
  }

  // ANALITIKA ESEMÉNYEK
  static Future<void> logAnalysisViewed(String analysisType, {String? period}) async {
    try {
      await _analytics.logEvent(
        name: 'analysis_viewed',
        parameters: {
          'analysis_type': analysisType, // 'monthly_report', 'category_breakdown', stb.
          if (period != null) 'period': period,
        },
      );
    } catch (e) {
      print('Analytics analysis viewed error: $e');
    }
  }

  static Future<void> logChartInteraction(String chartType, String interaction) async {
    try {
      await _analytics.logEvent(
        name: 'chart_interaction',
        parameters: {
          'chart_type': chartType,
          'interaction': interaction, // 'tap', 'zoom', 'filter', stb.
        },
      );
    } catch (e) {
      print('Analytics chart interaction error: $e');
    }
  }

  // KÖZÖSSÉGI FUNKCIÓK
  static Future<void> logForumActivity(String activityType, {Map<String, dynamic>? parameters}) async {
    try {
      await _analytics.logEvent(
        name: 'forum_activity',
        parameters: {
          'activity_type': activityType, // 'post_created', 'comment_added', 'post_liked', stb.
          ...?parameters,
        },
      );
    } catch (e) {
      print('Analytics forum activity error: $e');
    }
  }

  static Future<void> logAccountabilityAction(String action, {Map<String, dynamic>? parameters}) async {
    try {
      await _analytics.logEvent(
        name: 'accountability_action',
        parameters: {
          'action': action, // 'partner_requested', 'goal_shared', stb.
          ...?parameters,
        },
      );
    } catch (e) {
      print('Analytics accountability action error: $e');
    }
  }

  // CHALLENGE ÉS HABITS ESEMÉNYEK
  static Future<void> logChallengeEvent(String eventType, String challengeName, {Map<String, dynamic>? additionalData}) async {
    try {
      await _analytics.logEvent(
        name: 'challenge_event',
        parameters: {
          'event_type': eventType, // 'joined', 'completed', 'failed', stb.
          'challenge_name': challengeName,
          ...?additionalData,
        },
      );
    } catch (e) {
      print('Analytics challenge event error: $e');
    }
  }

  static Future<void> logHabitTracking(String habitName, bool completed, {int? streakCount}) async {
    try {
      await _analytics.logEvent(
        name: 'habit_tracking',
        parameters: {
          'habit_name': habitName,
          'completed': completed,
          if (streakCount != null) 'streak_count': streakCount,
        },
      );
    } catch (e) {
      print('Analytics habit tracking error: $e');
    }
  }

  // ELŐFIZETÉS ESEMÉNYEK
  static Future<void> logSubscriptionEvent(String eventType, {String? planType, double? amount}) async {
    try {
      await _analytics.logEvent(
        name: 'subscription_event',
        parameters: {
          'event_type': eventType, // 'viewed', 'upgraded', 'cancelled', stb.
          if (planType != null) 'plan_type': planType,
          if (amount != null) 'amount': amount,
        },
      );
    } catch (e) {
      print('Analytics subscription error: $e');
    }
  }

  // SESSION TRACKING
  static Future<void> logSessionStart() async {
    try {
      await _analytics.logEvent(
        name: 'session_start',
        parameters: {
          'timestamp': DateTime.now().millisecondsSinceEpoch,
        },
      );
    } catch (e) {
      print('Analytics session start error: $e');
    }
  }

  // KERESÉS ESEMÉNYEK
  static Future<void> logSearch(String searchTerm, String searchContext, {int? resultCount}) async {
    try {
      await _analytics.logEvent(
        name: 'search',
        parameters: {
          'search_term': searchTerm,
          'search_context': searchContext, // 'forum', 'knowledge_base', 'transactions', stb.
          if (resultCount != null) 'result_count': resultCount,
        },
      );
    } catch (e) {
      print('Analytics search error: $e');
    }
  }

  // HIBA ESEMÉNYEK (nem crash-ek, hanem felhasználói hibák)
  static Future<void> logUserError(String errorType, String errorMessage, {String? screenName}) async {
    try {
      await _analytics.logEvent(
        name: 'user_error',
        parameters: {
          'error_type': errorType, // 'validation_error', 'network_error', stb.
          'error_message': errorMessage,
          if (screenName != null) 'screen_name': screenName,
        },
      );
    } catch (e) {
      print('Analytics user error logging error: $e');
    }
  }

  // PERFORMANCE ESEMÉNYEK
  static Future<void> logPerformanceMetric(String metricName, int durationMs, {String? screenName}) async {
    try {
      await _analytics.logEvent(
        name: 'performance_metric',
        parameters: {
          'metric_name': metricName, // 'screen_load_time', 'api_response_time', stb.
          'duration_ms': durationMs,
          if (screenName != null) 'screen_name': screenName,
        },
      );
    } catch (e) {
      print('Analytics performance metric error: $e');
    }
  }
}