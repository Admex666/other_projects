import 'package:firebase_crashlytics/firebase_crashlytics.dart';

class FirebaseCrashlyticsService {
  static final FirebaseCrashlytics _crashlytics = FirebaseCrashlytics.instance;

  // FELHASZNÁLÓ AZONOSÍTÁS
  static Future<void> setUserId(String userId) async {
    try {
      await _crashlytics.setUserIdentifier(userId);
    } catch (e) {
      print('Crashlytics setUserId error: $e');
    }
  }

  static Future<void> setUserData({
    required String userId,
    String? username,
    String? email,
    String? subscriptionTier,
  }) async {
    try {
      await _crashlytics.setUserIdentifier(userId);
      if (username != null) await _crashlytics.setCustomKey('username', username);
      if (email != null) await _crashlytics.setCustomKey('email', email);
      if (subscriptionTier != null) await _crashlytics.setCustomKey('subscription_tier', subscriptionTier);
      await _crashlytics.setCustomKey('app_version', '1.0.0'); // TODO: Dynamic version
      await _crashlytics.setCustomKey('platform', 'flutter');
    } catch (e) {
      print('Crashlytics setUserData error: $e');
    }
  }

  // CUSTOM KULCSOK
  static Future<void> setCustomKey(String key, dynamic value) async {
    try {
      await _crashlytics.setCustomKey(key, value);
    } catch (e) {
      print('Crashlytics setCustomKey error: $e');
    }
  }

  static Future<void> setCustomKeys(Map<String, dynamic> keys) async {
    try {
      for (final entry in keys.entries) {
        await _crashlytics.setCustomKey(entry.key, entry.value);
      }
    } catch (e) {
      print('Crashlytics setCustomKeys error: $e');
    }
  }

  // LOG ÜZENETEK
  static void log(String message) {
    try {
      _crashlytics.log(message);
    } catch (e) {
      print('Crashlytics log error: $e');
    }
  }

  static void logWithData(String message, Map<String, dynamic> data) {
    try {
      final logMessage = '$message - Data: ${data.toString()}';
      _crashlytics.log(logMessage);
    } catch (e) {
      print('Crashlytics logWithData error: $e');
    }
  }

  // HIBÁK RÖGZÍTÉSE
  static Future<void> recordError(
    dynamic exception,
    StackTrace? stackTrace, {
    String? reason,
    bool fatal = false,
    Iterable<Object> information = const [],
  }) async {
    try {
      await _crashlytics.recordError(
        exception,
        stackTrace,
        reason: reason,
        fatal: fatal,
        information: information,
      );
    } catch (e) {
      print('Crashlytics recordError error: $e');
    }
  }

  // API HIBA RÖGZÍTÉS
  static Future<void> recordApiError({
    required String endpoint,
    required int statusCode,
    required String method,
    String? errorMessage,
    Map<String, dynamic>? requestData,
  }) async {
    try {
      await setCustomKeys({
        'api_endpoint': endpoint,
        'api_method': method,
        'api_status_code': statusCode,
        if (requestData != null) 'request_data': requestData.toString(),
      });

      final exception = 'API Error: $method $endpoint returned $statusCode';
      await recordError(
        exception,
        StackTrace.current,
        reason: errorMessage ?? 'API request failed',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordApiError error: $e');
    }
  }

  // TRANZAKCIÓ HIBÁK
  static Future<void> recordTransactionError({
    required String operation, // 'add', 'edit', 'delete'
    required String transactionType, // 'income', 'expense'
    required dynamic error,
    StackTrace? stackTrace,
    Map<String, dynamic>? transactionData,
  }) async {
    try {
      await setCustomKeys({
        'transaction_operation': operation,
        'transaction_type': transactionType,
        if (transactionData != null) 'transaction_data': transactionData.toString(),
      });

      log('Transaction error occurred: $operation $transactionType');
      
      await recordError(
        error,
        stackTrace ?? StackTrace.current,
        reason: 'Transaction operation failed: $operation',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordTransactionError error: $e');
    }
  }

  // AUTENTIKÁCIÓ HIBÁK
  static Future<void> recordAuthError({
    required String authOperation, // 'login', 'register', 'logout', 'token_refresh'
    required dynamic error,
    StackTrace? stackTrace,
    String? username,
  }) async {
    try {
      await setCustomKeys({
        'auth_operation': authOperation,
        if (username != null) 'attempted_username': username,
      });

      log('Authentication error: $authOperation');
      
      await recordError(
        error,
        stackTrace ?? StackTrace.current,
        reason: 'Authentication failed: $authOperation',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordAuthError error: $e');
    }
  }

  // NETWORK HIBÁK
  static Future<void> recordNetworkError({
    required String operation,
    required dynamic error,
    StackTrace? stackTrace,
    String? url,
    int? statusCode,
  }) async {
    try {
      await setCustomKeys({
        'network_operation': operation,
        if (url != null) 'network_url': url,
        if (statusCode != null) 'network_status_code': statusCode,
        'network_timestamp': DateTime.now().toIso8601String(),
      });

      log('Network error: $operation${url != null ? ' - $url' : ''}');
      
      await recordError(
        error,
        stackTrace ?? StackTrace.current,
        reason: 'Network operation failed: $operation',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordNetworkError error: $e');
    }
  }

  // VALIDATION HIBÁK
  static Future<void> recordValidationError({
    required String field,
    required String validationType,
    required String errorMessage,
    String? screenName,
    Map<String, dynamic>? formData,
  }) async {
    try {
      await setCustomKeys({
        'validation_field': field,
        'validation_type': validationType,
        if (screenName != null) 'validation_screen': screenName,
        if (formData != null) 'form_data': formData.toString(),
      });

      log('Validation error: $field - $validationType - $errorMessage');
      
      // Validation hibák általában nem exception-ök, de logolni szeretnénk őket
      await recordError(
        'ValidationError: $errorMessage',
        StackTrace.current,
        reason: 'Form validation failed',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordValidationError error: $e');
    }
  }

  // PERFORMANCE PROBLÉMÁK
  static Future<void> recordPerformanceIssue({
    required String operation,
    required int durationMs,
    required int thresholdMs,
    String? screenName,
    Map<String, dynamic>? additionalData,
  }) async {
    try {
      await setCustomKeys({
        'performance_operation': operation,
        'performance_duration_ms': durationMs,
        'performance_threshold_ms': thresholdMs,
        'performance_exceeded_by_ms': durationMs - thresholdMs,
        if (screenName != null) 'performance_screen': screenName,
        if (additionalData != null) 'performance_data': additionalData.toString(),
      });

      log('Performance issue: $operation took ${durationMs}ms (threshold: ${thresholdMs}ms)');
      
      await recordError(
        'PerformanceIssue: $operation exceeded threshold',
        StackTrace.current,
        reason: 'Operation took too long to complete',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordPerformanceIssue error: $e');
    }
  }

  // FEATURE USAGE HIBÁK
  static Future<void> recordFeatureError({
    required String featureName,
    required dynamic error,
    StackTrace? stackTrace,
    String? screenName,
    Map<String, dynamic>? context,
  }) async {
    try {
      await setCustomKeys({
        'feature_name': featureName,
        if (screenName != null) 'feature_screen': screenName,
        if (context != null) 'feature_context': context.toString(),
      });

      log('Feature error: $featureName');
      
      await recordError(
        error,
        stackTrace ?? StackTrace.current,
        reason: 'Feature usage failed: $featureName',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordFeatureError error: $e');
    }
  }

  // SUBSCRIPTION HIBÁK
  static Future<void> recordSubscriptionError({
    required String operation, // 'upgrade', 'cancel', 'restore', stb.
    required dynamic error,
    StackTrace? stackTrace,
    String? planType,
    double? amount,
  }) async {
    try {
      await setCustomKeys({
        'subscription_operation': operation,
        if (planType != null) 'subscription_plan': planType,
        if (amount != null) 'subscription_amount': amount,
      });

      log('Subscription error: $operation');
      
      await recordError(
        error,
        stackTrace ?? StackTrace.current,
        reason: 'Subscription operation failed: $operation',
        fatal: false,
      );
    } catch (e) {
      print('Crashlytics recordSubscriptionError error: $e');
    }
  }

  // BREADCRUMB RENDSZER
  static void addBreadcrumb(String message, {Map<String, dynamic>? data}) {
    try {
      final breadcrumb = data != null 
          ? '$message - ${data.toString()}'
          : message;
      log('BREADCRUMB: $breadcrumb');
    } catch (e) {
      print('Crashlytics addBreadcrumb error: $e');
    }
  }

  // CRASH TESZTELÉS (CSAK DEBUG MÓDBAN)
  static void testCrash() {
    try {
      _crashlytics.crash();
    } catch (e) {
      print('Crashlytics testCrash error: $e');
    }
  }

  // SESSION TRACKING
  static Future<void> setSessionData({
    required String sessionId,
    required DateTime sessionStart,
    String? screenName,
  }) async {
    try {
      await setCustomKeys({
        'session_id': sessionId,
        'session_start': sessionStart.toIso8601String(),
        if (screenName != null) 'current_screen': screenName,
      });
    } catch (e) {
      print('Crashlytics setSessionData error: $e');
    }
  }
}