// constants.dart - FRISSÍTETT
import '../models/subscription.dart'; // Import the main SubscriptionTier

class SubscriptionConstants {
  // Tier nevek - most a subscription.dart SubscriptionTier-t használjuk
  static const Map<SubscriptionTier, String> tierNames = {
    SubscriptionTier.free: 'Free',
    SubscriptionTier.plus: 'Plus',
    SubscriptionTier.pro: 'Pro',
  };

  // Tier árak (EUR)
  static const Map<SubscriptionTier, double> tierPrices = {
    SubscriptionTier.free: 0.0,
    SubscriptionTier.plus: 5.0,
    SubscriptionTier.pro: 12.5,
  };

  // Feature limitek
  static const int freeChallengesLimit = 1;
  static const int freeHabitsLimit = 5;
  static const int freePartnerLimit = 1;
  static const int freeKnowledgeDailyLimit = 1;
  
  // Knowledge video wait time (seconds)
  static const int knowledgeVideoWaitTime = 30;

  // Feature flags
  static bool canCreateChallenge(SubscriptionTier tier, int currentCount) {
    return tier != SubscriptionTier.free || currentCount < freeChallengesLimit;
  }

  static bool canCreateHabit(SubscriptionTier tier, int currentCount) {
    return tier != SubscriptionTier.free || currentCount < freeHabitsLimit;
  }

  static bool canAddPartner(SubscriptionTier tier, int currentCount) {
    return tier != SubscriptionTier.free || currentCount < freePartnerLimit;
  }

  static bool hasFullAnalytics(SubscriptionTier tier) {
    return tier != SubscriptionTier.free;
  }

  static bool hasPersonalizedAnalytics(SubscriptionTier tier) {
    return tier == SubscriptionTier.pro;
  }

  static bool hasFullKnowledge(SubscriptionTier tier) {
    return tier != SubscriptionTier.free;
  }

  static bool hasExclusiveLessons(SubscriptionTier tier) {
    return tier == SubscriptionTier.pro;
  }

  static bool hasExclusiveChallenges(SubscriptionTier tier) {
    return tier == SubscriptionTier.pro;
  }

  static bool hasGroups(SubscriptionTier tier) {
    return tier == SubscriptionTier.pro;
  }

  static bool hasTierBadge(SubscriptionTier tier) {
    return tier != SubscriptionTier.free;
  }

  static bool hasImportFeatures(SubscriptionTier tier) {
    return tier != SubscriptionTier.free;
  }

  static bool hasBulkEdit(SubscriptionTier tier) {
    return tier != SubscriptionTier.free;
  }

  static bool hasGoalBinding(SubscriptionTier tier) {
    return tier != SubscriptionTier.free;
  }

  static bool hasSuggestions(SubscriptionTier tier) {
    return tier == SubscriptionTier.pro;
  }
}