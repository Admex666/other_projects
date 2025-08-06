// lib/models/subscription.dart
enum SubscriptionTier {
  free('free'),
  plus('plus'),
  pro('pro');

  const SubscriptionTier(this.value);
  final String value;

  static SubscriptionTier fromString(String value) {
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
        return 'Free';
      case SubscriptionTier.plus:
        return 'Plus';
      case SubscriptionTier.pro:
        return 'Pro';
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

  static SubscriptionStatus fromString(String value) {
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
      name: json['name'],
      price: (json['price'] as num).toDouble(),
      durationDays: json['duration_days'],
      features: json['features'] as Map<String, dynamic>,
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
            return 'Alap, manuális';
          case 'import_bulk_edit':
            return 'Import, tömeges szerkesztés';
          default:
            return 'Ismeretlen';
        }
      case 'knowledge_base':
        switch (features[featureKey]) {
          case '1_lesson_per_day_with_ads':
            return '1 lecke/nap ingyen, utána 30mp videóért';
          case 'full_unlimited':
            return 'Teljes, korlátlan hozzáférés';
          case 'exclusive_content_learning_paths':
            return 'Exkluzív leckék, tanulási útvonalak';
          default:
            return 'Ismeretlen';
        }
      case 'challenges':
        switch (features[featureKey]) {
          case '1_active':
            return '1 aktív';
          case 'unlimited':
            return 'Korlátlan';
          case 'unlimited_with_exclusive':
            return 'Korlátlan + exkluzív kihívások';
          default:
            return 'Ismeretlen';
        }
      case 'habit_streak':
        switch (features[featureKey]) {
          case 'max_5_habits':
            return 'Maximum 5 szokás';
          case 'unlimited':
            return 'Korlátlan';
          default:
            return 'Ismeretlen';
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
    return UserSubscription(
      id: json['id'],
      userId: json['user_id'],
      tier: SubscriptionTier.fromString(json['tier']),
      status: SubscriptionStatus.fromString(json['status']),
      subscribedAt: DateTime.parse(json['subscribed_at']),
      expiresAt: json['expires_at'] != null ? DateTime.parse(json['expires_at']) : null,
      daysUntilExpiry: json['days_until_expiry'],
      plan: SubscriptionPlan.fromJson(json['plan']),
    );
  }

  bool get isActive => status == SubscriptionStatus.active;
  bool get isExpired => status == SubscriptionStatus.expired;
  bool get isPaid => tier != SubscriptionTier.free;

  String get statusDisplayText {
    switch (status) {
      case SubscriptionStatus.active:
        return isPaid ? 'Aktív előfizetés' : 'Ingyenes felhasználó';
      case SubscriptionStatus.expired:
        return 'Lejárt előfizetés';
      case SubscriptionStatus.cancelled:
        return 'Lemondott előfizetés';
      case SubscriptionStatus.pending:
        return 'Függőben lévő előfizetés';
    }
  }

  String? get expiryDisplayText {
    if (daysUntilExpiry == null) return null;
    
    if (daysUntilExpiry! <= 0) {
      return 'Lejárt';
    } else if (daysUntilExpiry! == 1) {
      return 'Holnap lejár';
    } else if (daysUntilExpiry! <= 7) {
      return '${daysUntilExpiry!} nap múlva lejár';
    } else {
      return '${daysUntilExpiry!} nap hátra';
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
      feature: json['feature'],
      hasAccess: json['has_access'],
      currentLimit: json['current_limit'],
      usageCount: json['usage_count'],
      remaining: json['remaining'],
      upgradeRequired: json['upgrade_required'],
      requiredTier: json['required_tier'] != null 
          ? SubscriptionTier.fromString(json['required_tier']) 
          : null,
      message: json['message'],
    );
  }

  String get displayMessage {
    if (message != null) return message!;
    
    if (!hasAccess && upgradeRequired) {
      return 'Előfizetés frissítés szükséges${requiredTier != null ? ' (${requiredTier!.displayName})' : ''}';
    }
    
    if (hasAccess && currentLimit != null && usageCount != null) {
      return 'Használat: $usageCount/$currentLimit';
    }
    
    return hasAccess ? 'Hozzáférés engedélyezve' : 'Hozzáférés megtagadva';
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
    return FeaturesSummary(
      subscription: UserSubscription.fromJson(json['subscription']),
      plan: SubscriptionPlan.fromJson(json['plan']),
      accessSummary: Map<String, bool>.from(json['access_summary']),
    );
  }
}