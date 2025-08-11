// lib/providers/accountability_provider.dart

import 'package:flutter/foundation.dart';
import '../models/accountability_models.dart';
import '../services/accountability_service.dart';
import 'package:flutter/widgets.dart';

class AccountabilityProvider extends ChangeNotifier {
  final AccountabilityService _service;

  AccountabilityProvider({required AccountabilityService service}) : _service = service;

  // State variables
  AccountabilityProfile? _profile;
  List<Partnership> _partnerships = [];
  List<PartnerSuggestion> _suggestions = [];
  List<CheckIn> _recentCheckIns = [];
  
  bool _isLoading = false;
  String? _error;
  bool _isInitialized = false;

  // Getters
  AccountabilityProfile? get profile => _profile;
  List<Partnership> get partnerships => _partnerships;
  List<Partnership> get activePartnerships => 
      _partnerships.where((p) => p.status == PartnershipStatus.active).toList();
  List<Partnership> get pendingPartnerships => 
      _partnerships.where((p) => p.status == PartnershipStatus.pending).toList();
  List<PartnerSuggestion> get suggestions => _suggestions;
  List<CheckIn> get recentCheckIns => _recentCheckIns;
  
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isInitialized => _isInitialized;
  bool get hasProfile => _profile != null;
  
  // Computed properties
  int get activePartnersCount => activePartnerships.length;
  int get pendingRequestsCount => pendingPartnerships.length;
  
  double get averageSuccessRate {
    if (activePartnerships.isEmpty) return 0.0;
    final totalRate = activePartnerships.map((p) => p.successRate).fold(0.0, (a, b) => a + b);
    return totalRate / activePartnerships.length;
  }

  // === INITIALIZATION ===

  Future<void> initialize() async {
    if (_isInitialized) return;
    
    _setLoading(true);
    try {
      await loadProfile();
      if (_profile != null) {
        await loadPartnerships();
      }
      _isInitialized = true;
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  // === PROFILE MANAGEMENT ===

  Future<void> loadProfile() async {
    try {
      _profile = await _service.getMyProfile();
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading accountability profile: $e');
      // Don't throw error - profile might not exist yet
    }
  }

  Future<bool> createProfile(AccountabilityProfile profileData) async {
    _setLoading(true);
    _clearError();

    try {
      _profile = await _service.createProfile(profileData);
      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  Future<bool> updateProfile(Map<String, dynamic> updates) async {
    _setLoading(true);
    _clearError();

    try {
      _profile = await _service.updateProfile(updates);
      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  // === PARTNERSHIPS ===

  Future<void> loadPartnerships() async {
    try {
      _partnerships = await _service.getMyPartnerships();
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading partnerships: $e');
      _setError(e.toString());
    }
  }

  Future<bool> sendPartnershipRequest(PartnershipRequest request) async {
    _setLoading(true);
    _clearError();

    try {
      await _service.sendPartnershipRequest(request);
      await loadPartnerships(); // Refresh partnerships
      _setLoading(false);
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  Future<bool> respondToPartnership(String partnershipId, bool accept, {String? message}) async {
    _setLoading(true);
    _clearError();

    try {
      final success = await _service.respondToPartnership(partnershipId, accept, message: message);
      if (success) {
        await loadPartnerships(); // Refresh partnerships
      }
      _setLoading(false);
      return success;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  Future<bool> endPartnership(String partnershipId, {String? reason}) async {
    _setLoading(true);
    _clearError();

    try {
      final success = await _service.endPartnership(partnershipId, reason: reason);
      if (success) {
        await loadPartnerships(); // Refresh partnerships
      }
      _setLoading(false);
      return success;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  // === MATCHING & SEARCH ===

  Future<void> loadPartnerSuggestions({int limit = 10}) async {
    _setLoading(true);
    _clearError();

    try {
      _suggestions = await _service.getPartnerSuggestions(limit: limit);
      _setLoading(false);
      notifyListeners();
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
    }
  }

  Future<List<PartnerSuggestion>> searchUsers(String query, {int limit = 20}) async {
    try {
      return await _service.searchUsers(query, limit: limit);
    } catch (e) {
      debugPrint('Error searching users: $e');
      return [];
    }
  }

  // === CHECK-INS ===

  Future<void> loadRecentCheckIns(String partnershipId, {int limit = 10}) async {
    try {
      _recentCheckIns = await _service.getCheckIns(partnershipId, limit: limit);
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading check-ins: $e');
    }
  }

  Future<bool> createCheckIn(String partnershipId, CheckIn checkIn) async {
    _setLoading(true);
    _clearError();

    try {
      await _service.createCheckIn(partnershipId, checkIn);
      await loadPartnerships(); // Refresh to update stats
      await loadRecentCheckIns(partnershipId); // Refresh check-ins
      _setLoading(false);
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  Future<bool> hasCheckedInToday(String partnershipId, String userId) async {
    try {
      return await _service.getTodayCheckInStatus(partnershipId, userId);
    } catch (e) {
      debugPrint('Error checking today check-in status: $e');
      return false;
    }
  }

  // === PARTNERSHIP HELPERS ===

  Partnership? getPartnershipById(String partnershipId) {
    try {
      return _partnerships.firstWhere((p) => p.id == partnershipId);
    } catch (e) {
      return null;
    }
  }

  Partnership? getPartnershipByUserId(String userId) {
    try {
      return _partnerships.firstWhere((p) => p.partnerUserId == userId);
    } catch (e) {
      return null;
    }
  }

  bool isPartnerWith(String userId) {
    return _partnerships.any((p) => 
        p.partnerUserId == userId && 
        p.status == PartnershipStatus.active
    );
  }

  bool hasPendingRequestWith(String userId) {
    return _partnerships.any((p) => 
        p.partnerUserId == userId && 
        p.status == PartnershipStatus.pending
    );
  }

  // === UTILITY METHODS ===

  void clearSuggestions() {
    _suggestions.clear();
    notifyListeners();
  }

  void removeSuggestion(String userId) {
    _suggestions.removeWhere((s) => s.userId == userId);
    notifyListeners();
  }

  Future<void> refresh() async {
    await loadProfile();
    if (_profile != null) {
      await loadPartnerships();
    }
  }

  void reset() {
    _profile = null;
    _partnerships.clear();
    _suggestions.clear();
    _recentCheckIns.clear();
    _isInitialized = false;
    _clearError();
    notifyListeners();
  }

  // === PRIVATE HELPERS ===

  void _setLoading(bool loading) {
    _isLoading = loading;
    // Schedule notifyListeners for after the current build cycle
    WidgetsBinding.instance.addPostFrameCallback((_) {
      notifyListeners();
    });
  }

  void _setError(String error) {
    _error = error;
    // Schedule notifyListeners for after the current build cycle
    WidgetsBinding.instance.addPostFrameCallback((_) {
      notifyListeners();
    });
  }

  void _clearError() {
    _error = null;
    // This doesn't need notifyListeners as it's usually called before other operations
  }

  @override
  void dispose() {
    super.dispose();
  }
}