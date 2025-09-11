import 'firebase_analytics_service.dart';
import 'firebase_crashlytics_service.dart';

/// Központi analytics service a NestCash app számára
/// Kombinálja a Firebase Analytics és Crashlytics funkciókat
class NestCashAnalyticsService {
  
  // INICIALIZÁLÁS ÉS FELHASZNÁLÓ BEÁLLÍTÁS
  static Future<void> initializeUser({
    required String userId,
    String? username,
    String? email,
    String? subscriptionTier,
  }) async {
    // Analytics user beállítás
    await FirebaseAnalyticsService.setUserId(userId);
    if (username != null) {
      await FirebaseAnalyticsService.setUserProperty('username', username);
    }
    if (subscriptionTier != null) {
      await FirebaseAnalyticsService.setUserProperty('subscription_tier', subscriptionTier);
    }
    
    // Crashlytics user beállítás
    await FirebaseCrashlyticsService.setUserData(
      userId: userId,
      username: username,
      email: email,
      subscriptionTier: subscriptionTier,
    );
    
    // Session start logolás
    await FirebaseAnalyticsService.logSessionStart();
  }

  // KÉPERNYŐ ESEMÉNYEK
  static Future<void> trackScreenView(String screenName) async {
    await FirebaseAnalyticsService.logScreenView(screenName);
    FirebaseCrashlyticsService.setCustomKey('last_screen', screenName);
    FirebaseCrashlyticsService.addBreadcrumb('Screen viewed: $screenName');
  }

  // TRANZAKCIÓ ESEMÉNYEK
  static Future<void> trackTransactionAdded({
    required String type,
    required double amount,
    required String category,
    String? account,
    String? description,
  }) async {
    // Analytics esemény
    await FirebaseAnalyticsService.logTransactionAdded(
      type: type,
      amount: amount,
      category: category,
      account: account,
      description: description,
    );
    
    // Breadcrumb hozzáadása
    FirebaseCrashlyticsService.addBreadcrumb(
      'Transaction added: $type',
      data: {
        'amount': amount,
        'category': category,
      },
    );
  }

  static Future<void> trackTransactionError({
    required String operation,
    required String transactionType,
    required dynamic error,
    StackTrace? stackTrace,
    Map<String, dynamic>? transactionData,
  }) async {
    // Hiba rögzítése Crashlytics-ben
    await FirebaseCrashlyticsService.recordTransactionError(
      operation: operation,
      transactionType: transactionType,
      error: error,
      stackTrace: stackTrace,
      transactionData: transactionData,
    );
    
    // Analytics esemény a hibáról
    await FirebaseAnalyticsService.logUserError(
      'transaction_error',
      error.toString(),
      screenName: 'transaction_screen',
    );
  }

  // NAVIGATION ESEMÉNYEK
  static Future<void> trackNavigation({
    required String fromScreen,
    required String toScreen,
    String? method,
  }) async {
    await FirebaseAnalyticsService.logNavigationEvent(
      fromScreen: fromScreen,
      toScreen: toScreen,
      navigationMethod: method,
    );
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Navigation: $fromScreen -> $toScreen',
      data: {'method': method ?? 'unknown'},
    );
  }

  // FEATURE USAGE ESEMÉNYEK
  static Future<void> trackFeatureUsed(String featureName, {Map<String, dynamic>? parameters}) async {
    await FirebaseAnalyticsService.logFeatureUsed(featureName, parameters: parameters);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Feature used: $featureName',
      data: parameters,
    );
  }

  static Future<void> trackFeatureError({
    required String featureName,
    required dynamic error,
    StackTrace? stackTrace,
    String? screenName,
    Map<String, dynamic>? context,
  }) async {
    // Crashlytics hiba rögzítés
    await FirebaseCrashlyticsService.recordFeatureError(
      featureName: featureName,
      error: error,
      stackTrace: stackTrace,
      screenName: screenName,
      context: context,
    );
    
    // Analytics esemény
    await FirebaseAnalyticsService.logUserError(
      'feature_error',
      error.toString(),
      screenName: screenName,
    );
  }

  // API HÍVÁS ESEMÉNYEK
  static Future<void> trackApiCall({
    required String endpoint,
    required String method,
    required int durationMs,
  }) async {
    await FirebaseAnalyticsService.logPerformanceMetric(
      'api_call_duration',
      durationMs,
      screenName: endpoint,
    );
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'API call: $method $endpoint',
      data: {'duration_ms': durationMs},
    );
  }

  static Future<void> trackApiError({
    required String endpoint,
    required int statusCode,
    required String method,
    String? errorMessage,
    Map<String, dynamic>? requestData,
  }) async {
    await FirebaseCrashlyticsService.recordApiError(
      endpoint: endpoint,
      statusCode: statusCode,
      method: method,
      errorMessage: errorMessage,
      requestData: requestData,
    );
    
    await FirebaseAnalyticsService.logUserError(
      'api_error',
      'API $method $endpoint failed with $statusCode',
      screenName: 'api_call',
    );
  }

  // BUTTON PRESS ESEMÉNYEK
  static Future<void> trackButtonPress(String buttonName, {String? screenName}) async {
    await FirebaseAnalyticsService.logButtonPress(
      buttonName,
      screenName: screenName,
    );
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Button pressed: $buttonName',
      data: {'screen': screenName},
    );
  }

  // LIMITS ÉS GOALS
  static Future<void> trackLimitSet({
    required String category,
    required double amount,
    required String period,
  }) async {
    await FirebaseAnalyticsService.logLimitSet(
      category: category,
      amount: amount,
      period: period,
    );
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Limit set: $category',
      data: {'amount': amount, 'period': period},
    );
  }

  static Future<void> trackLimitExceeded({
    required String category,
    required double limitAmount,
    required double currentAmount,
  }) async {
    final overageAmount = currentAmount - limitAmount;
    
    await FirebaseAnalyticsService.logLimitExceeded(
      category: category,
      limitAmount: limitAmount,
      currentAmount: currentAmount,
      overageAmount: overageAmount,
    );
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Limit exceeded: $category',
      data: {
        'limit': limitAmount,
        'current': currentAmount,
        'overage': overageAmount,
      },
    );
  }

  // ANALYSIS ÉS CHARTS
  static Future<void> trackAnalysisViewed(String analysisType, {String? period}) async {
    await FirebaseAnalyticsService.logAnalysisViewed(analysisType, period: period);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Analysis viewed: $analysisType',
      data: {'period': period},
    );
  }

  static Future<void> trackChartInteraction(String chartType, String interaction) async {
    await FirebaseAnalyticsService.logChartInteraction(chartType, interaction);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Chart interaction: $chartType - $interaction',
    );
  }

  // COMMUNITY FUNKCIÓK
  static Future<void> trackForumActivity(String activityType, {Map<String, dynamic>? parameters}) async {
    await FirebaseAnalyticsService.logForumActivity(activityType, parameters: parameters);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Forum activity: $activityType',
      data: parameters,
    );
  }

  static Future<void> trackAccountabilityAction(String action, {Map<String, dynamic>? parameters}) async {
    await FirebaseAnalyticsService.logAccountabilityAction(action, parameters: parameters);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Accountability action: $action',
      data: parameters,
    );
  }

  // CHALLENGES ÉS HABITS
  static Future<void> trackChallengeEvent(String eventType, String challengeName, {Map<String, dynamic>? additionalData}) async {
    await FirebaseAnalyticsService.logChallengeEvent(eventType, challengeName, additionalData: additionalData);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Challenge event: $eventType - $challengeName',
      data: additionalData,
    );
  }

  static Future<void> trackHabitEvent(String habitName, bool completed, {int? streakCount}) async {
    await FirebaseAnalyticsService.logHabitTracking(habitName, completed, streakCount: streakCount);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Habit tracked: $habitName - ${completed ? 'completed' : 'skipped'}',
      data: {'streak': streakCount},
    );
  }

  // SUBSCRIPTION ESEMÉNYEK
  static Future<void> trackSubscriptionEvent(String eventType, {String? planType, double? amount}) async {
    await FirebaseAnalyticsService.logSubscriptionEvent(eventType, planType: planType, amount: amount);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Subscription event: $eventType',
      data: {'plan': planType, 'amount': amount},
    );
  }

  static Future<void> trackSubscriptionError({
    required String operation,
    required dynamic error,
    StackTrace? stackTrace,
    String? planType,
    double? amount,
  }) async {
    await FirebaseCrashlyticsService.recordSubscriptionError(
      operation: operation,
      error: error,
      stackTrace: stackTrace,
      planType: planType,
      amount: amount,
    );
    
    await FirebaseAnalyticsService.logUserError(
      'subscription_error',
      error.toString(),
      screenName: 'subscription_screen',
    );
  }

  // SEARCH ESEMÉNYEK
  static Future<void> trackSearch(String searchTerm, String searchContext, {int? resultCount}) async {
    await FirebaseAnalyticsService.logSearch(searchTerm, searchContext, resultCount: resultCount);
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'Search performed: $searchContext',
      data: {'term': searchTerm, 'results': resultCount},
    );
  }

  // AUTH ESEMÉNYEK
  static Future<void> trackAuthAction(String action, {bool success = true, String? errorMessage}) async {
    if (success) {
      await FirebaseAnalyticsService.logFeatureUsed('auth_$action');
      FirebaseCrashlyticsService.addBreadcrumb('Auth success: $action');
    } else {
      await FirebaseAnalyticsService.logUserError(
        'auth_error',
        errorMessage ?? 'Authentication failed',
        screenName: 'auth_screen',
      );
      FirebaseCrashlyticsService.addBreadcrumb(
        'Auth failed: $action',
        data: {'error': errorMessage},
      );
    }
  }

  static Future<void> trackAuthError({
    required String authOperation,
    required dynamic error,
    StackTrace? stackTrace,
    String? username,
  }) async {
    await FirebaseCrashlyticsService.recordAuthError(
      authOperation: authOperation,
      error: error,
      stackTrace: stackTrace,
      username: username,
    );
  }

  // PERFORMANCE TRACKING
  static Future<void> trackPerformanceMetric(String operation, int durationMs, {String? screenName, int? thresholdMs}) async {
    await FirebaseAnalyticsService.logPerformanceMetric(operation, durationMs, screenName: screenName);
    
    // Ha van threshold és túllépi, performance issue-t is logoljuk
    if (thresholdMs != null && durationMs > thresholdMs) {
      await FirebaseCrashlyticsService.recordPerformanceIssue(
        operation: operation,
        durationMs: durationMs,
        thresholdMs: thresholdMs,
        screenName: screenName,
      );
    } else {
      FirebaseCrashlyticsService.addBreadcrumb(
        'Performance: $operation took ${durationMs}ms',
        data: {'screen': screenName},
      );
    }
  }

  // NETWORK ESEMÉNYEK
  static Future<void> trackNetworkError({
    required String operation,
    required dynamic error,
    StackTrace? stackTrace,
    String? url,
    int? statusCode,
  }) async {
    await FirebaseCrashlyticsService.recordNetworkError(
      operation: operation,
      error: error,
      stackTrace: stackTrace,
      url: url,
      statusCode: statusCode,
    );
    
    await FirebaseAnalyticsService.logUserError(
      'network_error',
      error.toString(),
      screenName: 'network',
    );
  }

  // VALIDATION HIBÁK
  static Future<void> trackValidationError({
    required String field,
    required String validationType,
    required String errorMessage,
    String? screenName,
  }) async {
    await FirebaseCrashlyticsService.recordValidationError(
      field: field,
      validationType: validationType,
      errorMessage: errorMessage,
      screenName: screenName,
    );
    
    await FirebaseAnalyticsService.logUserError(
      'validation_error',
      '$field: $errorMessage',
      screenName: screenName,
    );
  }

  // SESSION MANAGEMENT
  static Future<void> setSessionInfo({
    required String sessionId,
    required DateTime sessionStart,
    String? currentScreen,
  }) async {
    await FirebaseCrashlyticsService.setSessionData(
      sessionId: sessionId,
      sessionStart: sessionStart,
      screenName: currentScreen,
    );
  }

  // GENERIC ERROR TRACKING
  static Future<void> trackError({
    required dynamic error,
    required String context,
    StackTrace? stackTrace,
    String? screenName,
    Map<String, dynamic>? additionalData,
    bool fatal = false,
  }) async {
    // Crashlytics-ba rögzítés
    await FirebaseCrashlyticsService.recordError(
      error,
      stackTrace ?? StackTrace.current,
      reason: context,
      fatal: fatal,
    );
    
    // Analytics esemény
    await FirebaseAnalyticsService.logUserError(
      'generic_error',
      error.toString(),
      screenName: screenName,
    );
    
    // Breadcrumb hozzáadása
    FirebaseCrashlyticsService.addBreadcrumb(
      'Error in $context: ${error.toString()}',
      data: additionalData,
    );
  }

  // CRASH TESTING (CSAK DEBUG MÓDBAN)
  static void testCrash() {
    assert(() {
      FirebaseCrashlyticsService.testCrash();
      return true;
    }());
  }

  // BATCH TRACKING - több esemény egyszerre
  static Future<void> trackUserFlow({
    required String flowName,
    required List<String> steps,
    required DateTime startTime,
    bool completed = true,
    String? exitStep,
  }) async {
    final duration = DateTime.now().difference(startTime);
    
    await FirebaseAnalyticsService.logEvent(
      name: 'user_flow',
      parameters: {
        'flow_name': flowName,
        'steps_completed': steps.length,
        'total_duration_ms': duration.inMilliseconds,
        'completed': completed,
        if (exitStep != null) 'exit_step': exitStep,
      },
    );
    
    FirebaseCrashlyticsService.addBreadcrumb(
      'User flow: $flowName ${completed ? 'completed' : 'abandoned'}',
      data: {
        'steps': steps.length,
        'duration_ms': duration.inMilliseconds,
        'exit_step': exitStep,
      },
    );
  }
}