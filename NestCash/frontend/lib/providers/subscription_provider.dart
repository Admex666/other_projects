// lib/providers/subscription_provider.dart
import 'package:flutter/foundation.dart';
import '../models/subscription.dart';
import '../services/subscription_service.dart';
import '../services/habit_service.dart';

class SubscriptionProvider extends ChangeNotifier {
  final SubscriptionService _subscriptionService;
  final HabitService _habitService = HabitService(); // ÚJ sor
  
  int _currentHabitsCount = 0;

  int _dailyLessonCount = 0;
  DateTime? _lastLessonCountReset;
  int get dailyLessonCount => _dailyLessonCount;

  UserSubscription? _subscriptionInfo;
  FeaturesSummary? _featuresSummary;
  List<SubscriptionPlan>? _availablePlans;
  bool _isLoading = false;
  String? _error;
  bool _isInitialized = false;
  
  // Cache timestamps
  DateTime? _lastFetchTime;
  static const Duration _cacheValidDuration = Duration(minutes: 5);

  SubscriptionProvider({required SubscriptionService subscriptionService})
      : _subscriptionService = subscriptionService {
    // Auto-inicializálás amikor létrejön a provider
    _initialize();
  }

  // Auto inicializálás
  Future<void> _initialize() async {
    if (!_isInitialized) {
      await loadSubscriptionInfo();
      _isInitialized = true;
    }
  }

  // Új metódusok hozzáadása
  void incrementDailyLessonCount() {
    _checkAndResetDailyCount();
    _dailyLessonCount++;
    notifyListeners();
  }

  void _checkAndResetDailyCount() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    if (_lastLessonCountReset == null || 
        _lastLessonCountReset!.isBefore(today)) {
      _dailyLessonCount = 0;
      _lastLessonCountReset = today;
    }
  }

  // Getters
  UserSubscription? get subscriptionInfo => _subscriptionInfo;
  FeaturesSummary? get featuresSummary => _featuresSummary;
  List<SubscriptionPlan>? get availablePlans => _availablePlans;
  bool get isLoading => _isLoading;
  String? get error => _error;
  SubscriptionTier get currentTier => _subscriptionInfo?.tier ?? SubscriptionTier.free;
  bool get isInitialized => _isInitialized; 

  // Convenience getters - JAVÍTOTT logika
  bool get isSubscribed => currentTier != SubscriptionTier.free && isActive;
  bool get isPlusOrHigher => (currentTier == SubscriptionTier.plus || currentTier == SubscriptionTier.pro) && isActive;
  bool get isPro => currentTier == SubscriptionTier.pro && isActive;
  bool get isActive => _subscriptionInfo?.isActive ?? false;

  // Feature access convenience getters (based on subscription plan)
  bool get canCreateUnlimitedChallenges => _subscriptionInfo?.plan.canCreateUnlimitedChallenges ?? false;
  bool get canCreateUnlimitedHabits => _subscriptionInfo?.plan.canTrackUnlimitedHabits ?? false;
  bool get hasFullAnalytics => _subscriptionInfo?.plan.hasAdvancedAnalytics ?? false;
  bool get hasPersonalizedAnalytics => isPro;
  bool get hasFullKnowledge => _subscriptionInfo?.plan.hasFullKnowledgeAccess ?? false;
  bool get hasExclusiveContent => isPro;
  bool get hasImportFeatures => isPlusOrHigher;
  bool get hasBulkEdit => isPlusOrHigher;
  bool get hasGroups => isPro;
  bool get hasTierBadge => isPlusOrHigher;
  bool get canHaveMultiplePartners => _subscriptionInfo?.plan.canHaveMultiplePartners ?? false;

  /// Load all subscription information
  Future<void> loadSubscriptionInfo({bool forceRefresh = false}) async {
    // Use cache if available and fresh
    if (!forceRefresh && _isCacheValid()) {
      print('Using cached subscription data');
      return;
    }

    print('Loading subscription info, forceRefresh: $forceRefresh');
    _setLoading(true);
    _clearError();

    try {
      // Load subscription first
      print('Loading subscription data...');
      final subscription = await _subscriptionService.getMySubscription();
      _subscriptionInfo = subscription;
      print('Subscription loaded successfully: ${subscription.tier}');
      
      // Load features second
      print('Loading features data...');
      final features = await _subscriptionService.getMyFeatures();
      _featuresSummary = features;
      print('Features loaded successfully');
      
      _lastFetchTime = DateTime.now();
      _setLoading(false);
    } catch (e) {
      print('Error loading subscription info: $e');
      _setError(e.toString());
      _setLoading(false);
    }
  }

  /// Load available subscription plans
  Future<void> loadAvailablePlans() async {
    try {
      _availablePlans = await _subscriptionService.getAvailablePlans();
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading plans: $e');
    }
  }

  /// Check specific feature access
  Future<FeatureAccess> checkFeature(
    String feature, {
    Map<String, dynamic>? context,
  }) async {
    try {
      return await _subscriptionService.checkFeatureAccess(
        feature,
        currentUsageCount: context?['currentUsageCount'],
        currentActiveChallenges: context?['currentActiveChallenges'],
        currentHabitCount: context?['currentHabitCount'],
        dailyLessonCount: context?['dailyLessonCount'],
        currentPartnerCount: context?['currentPartnerCount'],
        analysisType: context?['analysisType'],
      );
    } catch (e) {
      debugPrint('Error checking feature $feature: $e');
      return FeatureAccess(
        hasAccess: false,
        feature: feature,
        upgradeRequired: false,
      );
    }
  }

  /// Upgrade subscription
  Future<bool> upgradeSubscription(
    SubscriptionTier newTier, {
    String? paymentProvider,
    String? externalSubscriptionId,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final success = await _subscriptionService.upgradeSubscription(
        newTier,
        paymentProvider: paymentProvider,
        externalSubscriptionId: externalSubscriptionId,
      );

      if (success) {
        // Reload subscription info after successful upgrade
        await loadSubscriptionInfo(forceRefresh: true);
      }

      _setLoading(false);
      return success;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  /// Cancel subscription
  Future<bool> cancelSubscription({String reason = 'user_request'}) async {
    _setLoading(true);
    _clearError();

    try {
      final success = await _subscriptionService.cancelSubscription();

      if (success) {
        // Reload subscription info after successful cancellation
        await loadSubscriptionInfo(forceRefresh: true);
      }

      _setLoading(false);
      return success;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  // Usage count getters (these would need to be implemented based on your actual data structure)
  int getCurrentChallengesCount() {
    // This should be implemented based on how you track current usage
    // For now, returning 0 as placeholder
    return 0;
  }

  int getChallengesLimit() {
    if (currentTier == SubscriptionTier.free) return 1;
    return -1; // -1 means unlimited
  }

  Future<int> getCurrentHabitsCount() async {
    try {
      final habits = await _habitService.getHabits(activeOnly: true);
      _currentHabitsCount = habits.length; // Cache-eljük a helyi változóban is
      return habits.length;
    } catch (e) {
      debugPrint('Error getting habits count from database: $e');
      return _currentHabitsCount; // Fallback a cached értékre
    }
  }

  // Új getter a cached értékhez (szinkron használathoz)
  int get cachedHabitsCount => _currentHabitsCount;

  int getHabitsLimit() {
    if (currentTier == SubscriptionTier.free) return 5;
    return -1; // -1 means unlimited
  }

  int getCurrentPartnersCount() {
    // This should be implemented based on how you track current usage
    return 0;
  }

  int getPartnersLimit() {
    if (currentTier == SubscriptionTier.free) return 1;
    return -1; // -1 means unlimited
  }

  int getDailyLessonCount() {
    _checkAndResetDailyCount();
    return _dailyLessonCount;
  }

  // Feature check shortcuts
  Future<bool> canCreateChallenge() async {
    final currentCount = getCurrentChallengesCount();
    final access = await _subscriptionService.canCreateChallenge(currentCount);
    return access.hasAccess;
  }

  Future<bool> canCreateHabit() async {
    try {
      // Ellenőrizzük a tier alapján
      if (currentTier != SubscriptionTier.free) {
        return true; // Plus/Pro felhasználók korlátlanul hozhatnak létre
      }
      
      // Free felhasználóknál adatbázisból kérjük le az aktuális számot
      final currentCount = await getCurrentHabitsCount(); // Ez már frissíti a cache-t is
      if (currentCount >= 5) {
        return false;
      }
      
      // Ha van backend ellenőrzés is
      final access = await _subscriptionService.canCreateHabit(currentCount);
      return access.hasAccess;
    } catch (e) {
      debugPrint('Error in canCreateHabit: $e');
      // Ha hiba van, fallback a tier alapú ellenőrzésre és cached értékre
      if (currentTier != SubscriptionTier.free) return true;
      return _currentHabitsCount < 5;
    }
  }

  Future<bool> canAddPartner() async {
    final currentCount = getCurrentPartnersCount();
    final access = await _subscriptionService.canAddPartner(currentCount);
    return access.hasAccess;
  }

  Future<bool> canAccessKnowledge() async {
    final dailyCount = getDailyLessonCount();
    final access = await _subscriptionService.canAccessKnowledge(dailyCount);
    return access.hasAccess;
  }

  Future<bool> canAccessAnalytics(String analysisType) async {
    final access = await _subscriptionService.canAccessAnalytics(analysisType);
    return access.hasAccess;
  }

  // Knowledge base specifikus ellenőrzés
  Future<bool> canAccessLessonToday() async {
    if (hasFullKnowledge) return true;
    
    try {
      final access = await checkFeature(
        'knowledge_base',
        context: {'dailyLessonCount': getDailyLessonCount()},
      );
      return access.hasAccess;
    } catch (e) {
      debugPrint('Error checking lesson access: $e');
      return getDailyLessonCount() < 1; // Fallback
    }
  }

  void updateHabitsCount(int count) {
    _currentHabitsCount = count;
    notifyListeners();
  }

  /// Refresh subscription data
  Future<void> refresh() async {
    await loadSubscriptionInfo(forceRefresh: true);
  }

  /// Clear all cached data
  void clearCache() {
    _subscriptionInfo = null;
    _featuresSummary = null;
    _availablePlans = null;
    _lastFetchTime = null;
    _clearError();
    notifyListeners();
  }

  // Private helper methods
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _error = error;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
  }

  bool _isCacheValid() {
    if (_subscriptionInfo == null || _featuresSummary == null || _lastFetchTime == null) {
      return false;
    }
    
    final now = DateTime.now();
    return now.difference(_lastFetchTime!) < _cacheValidDuration;
  }

  @override
  void dispose() {
    super.dispose();
  }
}