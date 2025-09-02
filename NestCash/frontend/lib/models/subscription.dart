// lib/models/subscription.dart
import 'package:easy_localization/easy_localization.dart';

enum SubscriptionTier {
  free('free'),
  plus('plus'),
  pro('pro');

  const SubscriptionTier(this.value);
  final String value;

  static SubscriptionTier fromString(String? value) {
    if (value == null) return SubscriptionTier.free;
    
    switch (value.toLowerCase()) {
      case 'free':
        return SubscriptionTier.free;
      case 'plus':
        return SubscriptionTier.plus;
      case 'pro':
        return SubscriptionTier.pro;
      default:
        return SubscriptionTier.free;
    }
  }

  String get displayName {
    switch (this) {
      case SubscriptionTier.free:
        return 'subscription_models.subscription_tier.free'.tr();
      case SubscriptionTier.plus:
        return 'subscription_models.subscription_tier.plus'.tr();
      case SubscriptionTier.pro:
        return 'subscription_models.subscription_tier.pro'.tr();
    }
  }

  String get displayPrice {
    switch (this) {
      case SubscriptionTier.free:
        return '0 EUR';
      case SubscriptionTier.plus:
        return '5 EUR';
      case SubscriptionTier.pro:
        return '12,5 EUR';
    }
  }
}

enum SubscriptionStatus {
  active('active'),
  expired('expired'),
  cancelled('cancelled'),
  pending('pending');

  const SubscriptionStatus(this.value);
  final String value;

  static SubscriptionStatus fromString(String? value) {
    if (value == null) return SubscriptionStatus.active;
    
    switch (value.toLowerCase()) {
      case 'active':
        return SubscriptionStatus.active;
      case 'expired':
        return SubscriptionStatus.expired;
      case 'cancelled':
        return SubscriptionStatus.cancelled;
      case 'pending':
        return SubscriptionStatus.pending;
      default:
        return SubscriptionStatus.active;
    }
  }
}

class SubscriptionPlan {
  final SubscriptionTier tier;
  final String name;
  final double price;
  final int durationDays;
  final Map<String, dynamic> features;

  SubscriptionPlan({
    required this.tier,
    required this.name,
    required this.price,
    required this.durationDays,
    required this.features,
  });

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) {
    return SubscriptionPlan(
      tier: SubscriptionTier.fromString(json['tier']),
      name: json['name'] ?? '',
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      durationDays: json['duration_days'] ?? 30,
      features: json['features'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'tier': tier.value,
      'name': name,
      'price': price,
      'duration_days': durationDays,
      'features': features,
    };
  }

  // Feature ellenőrzési helper metódusok
  bool get canCreateUnlimitedChallenges => features['challenges'] != '1_active';
  bool get canTrackUnlimitedHabits => features['habit_streak'] != 'max_5_habits';
  bool get hasFullKnowledgeAccess => features['knowledge_base'] != '1_lesson_per_day_with_ads';
  bool get hasAdvancedAnalytics => features['analysis_insights'] != 'basic_category_only';
  bool get canHaveMultiplePartners => features['accountability_partner'] != 'max_1';

  String getFeatureDescription(String featureKey) {
    switch (featureKey) {
      case 'transaction_management':
        switch (features[featureKey]) {
          case 'basic_manual':
            return 'subscription_models.features.transaction_management.basic_manual'.tr();
          case 'import_bulk_edit':
            return 'subscription_models.features.transaction_management.import_bulk_edit'.tr();
          default:
            return 'subscription_models.features.unknown'.tr();
        }
      case 'knowledge_base':
        switch (features[featureKey]) {
          case '1_lesson_per_day_with_ads':
            return 'subscription_models.features.knowledge_base.one_lesson_with_ads'.tr();
          case 'full_unlimited':
            return 'subscription_models.features.knowledge_base.full_unlimited'.tr();
          case 'exclusive_content_learning_paths':
            return 'subscription_models.features.knowledge_base.exclusive_content'.tr();
          default:
            return 'subscription_models.features.unknown'.tr();
        }
      case 'challenges':
        switch (features[featureKey]) {
          case '1_active':
            return 'subscription_models.features.challenges.one_active'.tr();
          case 'unlimited':
            return 'subscription_models.features.challenges.unlimited'.tr();
          case 'unlimited_with_exclusive':
            return 'subscription_models.features.challenges.unlimited_exclusive'.tr();
          default:
            return 'subscription_models.features.unknown'.tr();
        }
      case 'habit_streak':
        switch (features[featureKey]) {
          case 'max_5_habits':
            return 'subscription_models.features.habit_streak.max_five_habits'.tr();
          case 'unlimited':
            return 'subscription_models.features.habit_streak.unlimited'.tr();
          default:
            return 'subscription_models.features.unknown'.tr();
        }
      default:
        return features[featureKey]?.toString() ?? 'N/A';
    }
  }
}

class UserSubscription {
  final String id;
  final String userId;
  final SubscriptionTier tier;
  final SubscriptionStatus status;
  final DateTime subscribedAt;
  final DateTime? expiresAt;
  final int? daysUntilExpiry;
  final SubscriptionPlan plan;

  UserSubscription({
    required this.id,
    required this.userId,
    required this.tier,
    required this.status,
    required this.subscribedAt,
    this.expiresAt,
    this.daysUntilExpiry,
    required this.plan,
  });

  factory UserSubscription.fromJson(Map<String, dynamic> json) {
    try {
      return UserSubscription(
        id: json['id']?.toString() ?? '',
        userId: json['user_id']?.toString() ?? '',
        tier: SubscriptionTier.fromString(json['tier']),
        status: SubscriptionStatus.fromString(json['status']),
        subscribedAt: json['subscribed_at'] != null 
            ? DateTime.parse(json['subscribed_at']) 
            : DateTime.now(),
        expiresAt: json['expires_at'] != null 
            ? DateTime.parse(json['expires_at']) 
            : null,
        daysUntilExpiry: json['days_until_expiry'],
        plan: SubscriptionPlan.fromJson(json['plan'] ?? {}),
      );
    } catch (e) {
      print('Error parsing UserSubscription: $e');
      print('JSON data: $json');
      rethrow;
    }
  }

  bool get isActive => status == SubscriptionStatus.active;
  bool get isExpired => status == SubscriptionStatus.expired;
  bool get isPaid => tier != SubscriptionTier.free;

  String get statusDisplayText {
    switch (status) {
      case SubscriptionStatus.active:
        return isPaid 
            ? 'subscription_models.status_display_text.active_paid'.tr() 
            : 'subscription_models.status_display_text.free_user'.tr();
      case SubscriptionStatus.expired:
        return 'subscription_models.status_display_text.expired'.tr();
      case SubscriptionStatus.cancelled:
        return 'subscription_models.status_display_text.cancelled'.tr();
      case SubscriptionStatus.pending:
        return 'subscription_models.status_display_text.pending'.tr();
    }
  }

  String? get expiryDisplayText {
    if (daysUntilExpiry == null) return null;
    
    if (daysUntilExpiry! <= 0) {
      return 'subscription_models.expiry_display_text.expired_now'.tr();
    } else if (daysUntilExpiry! == 1) {
      return 'subscription_models.expiry_display_text.expires_tomorrow'.tr();
    } else if (daysUntilExpiry! <= 7) {
      return 'subscription_models.expiry_display_text.expires_in_x_days'.tr(namedArgs: {'days': daysUntilExpiry!.toString()});
    } else {
      return 'subscription_models.expiry_display_text.x_days_left'.tr(namedArgs: {'days': daysUntilExpiry!.toString()});
    }
  }
}

class FeatureAccess {
  final String feature;
  final bool hasAccess;
  final int? currentLimit;
  final int? usageCount;
  final int? remaining;
  final bool upgradeRequired;
  final SubscriptionTier? requiredTier;
  final String? message;

  FeatureAccess({
    required this.feature,
    required this.hasAccess,
    this.currentLimit,
    this.usageCount,
    this.remaining,
    required this.upgradeRequired,
    this.requiredTier,
    this.message,
  });

  factory FeatureAccess.fromJson(Map<String, dynamic> json) {
    return FeatureAccess(
      feature: json['feature']?.toString() ?? '',
      hasAccess: json['has_access'] ?? false,
      currentLimit: json['current_limit'],
      usageCount: json['usage_count'],
      remaining: json['remaining'],
      upgradeRequired: json['upgrade_required'] ?? false,
      requiredTier: json['required_tier'] != null 
          ? SubscriptionTier.fromString(json['required_tier']) 
          : null,
      message: json['message']?.toString(),
    );
  }

  String get displayMessage {
    if (message != null) return message!;
    
    if (!hasAccess && upgradeRequired) {
      return 'subscription_models.feature_access.upgrade_required'.tr(namedArgs: {
        'tier': requiredTier != null ? ' (${requiredTier!.displayName})' : ''
      });
    }
    
    if (hasAccess && currentLimit != null && usageCount != null) {
      return 'subscription_models.feature_access.usage_count'.tr(namedArgs: {
        'usage': usageCount!.toString(),
        'limit': currentLimit!.toString()
      });
    }
    
    return hasAccess 
        ? 'subscription_models.feature_access.access_granted'.tr() 
        : 'subscription_models.feature_access.access_denied'.tr();
  }

  bool get isNearLimit {
    if (currentLimit == null || usageCount == null) return false;
    return (usageCount! / currentLimit!) >= 0.8;
  }
}

class FeaturesSummary {
  final UserSubscription subscription;
  final SubscriptionPlan plan;
  final Map<String, bool> accessSummary;

  FeaturesSummary({
    required this.subscription,
    required this.plan,
    required this.accessSummary,
  });

  factory FeaturesSummary.fromJson(Map<String, dynamic> json) {
    try {
      print('FeaturesSummary parsing JSON: $json'); // Debug log
      
      return FeaturesSummary(
        subscription: UserSubscription.fromJson(json['subscription'] ?? {}),
        plan: SubscriptionPlan.fromJson(json['plan'] ?? {}),
        accessSummary: Map<String, bool>.from(json['access_summary'] ?? {}),
      );
    } catch (e) {
      print('Error parsing FeaturesSummary: $e');
      print('JSON data: $json');
      rethrow;
    }
  }
}