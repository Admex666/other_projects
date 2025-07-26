// lib/models/badge_models.dart

enum BadgeCategory {
  transaction('transaction', 'Tranzakció'),
  savings('savings', 'Megtakarítás'),
  knowledge('knowledge', 'Tudás'),
  streak('streak', 'Sorozat'),
  milestone('milestone', 'Mérföldkő'),
  social('social', 'Közösségi'),
  special('special', 'Különleges');

  const BadgeCategory(this.value, this.displayName);
  final String value;
  final String displayName;

  static BadgeCategory fromString(String value) {
    return BadgeCategory.values.firstWhere(
      (category) => category.value == value,
      orElse: () => BadgeCategory.transaction,
    );
  }
}

enum BadgeRarity {
  common('common', 'Gyakori', '🟢'),
  uncommon('uncommon', 'Ritka', '🔵'),
  rare('rare', 'Nagyon ritka', '🟣'),
  epic('epic', 'Epikus', '🟠'),
  legendary('legendary', 'Legendás', '🟡');

  const BadgeRarity(this.value, this.displayName, this.colorEmoji);
  final String value;
  final String displayName;
  final String colorEmoji;

  static BadgeRarity fromString(String value) {
    return BadgeRarity.values.firstWhere(
      (rarity) => rarity.value == value,
      orElse: () => BadgeRarity.common,
    );
  }
}

class UserBadge {
  final String id;
  final String userId;
  final String badgeCode;
  final DateTime earnedAt;
  final int level;
  final double progress;
  final Map<String, dynamic> contextData;
  final bool isFavorite;
  final bool isVisible;
  
  // Badge típus adatok
  final String? badgeName;
  final String? badgeDescription;
  final String? badgeIcon;
  final String? badgeColor;
  final BadgeCategory? badgeCategory;
  final BadgeRarity? badgeRarity;
  final int? badgePoints;

  UserBadge({
    required this.id,
    required this.userId,
    required this.badgeCode,
    required this.earnedAt,
    required this.level,
    required this.progress,
    required this.contextData,
    required this.isFavorite,
    required this.isVisible,
    this.badgeName,
    this.badgeDescription,
    this.badgeIcon,
    this.badgeColor,
    this.badgeCategory,
    this.badgeRarity,
    this.badgePoints,
  });

  factory UserBadge.fromJson(Map<String, dynamic> json) {
    return UserBadge(
      id: json['id'],
      userId: json['user_id'],
      badgeCode: json['badge_code'],
      earnedAt: DateTime.parse(json['earned_at']),
      level: json['level'],
      progress: json['progress']?.toDouble() ?? 0.0,
      contextData: Map<String, dynamic>.from(json['context_data'] ?? {}),
      isFavorite: json['is_favorite'] ?? false,
      isVisible: json['is_visible'] ?? true,
      badgeName: json['badge_name'],
      badgeDescription: json['badge_description'],
      badgeIcon: json['badge_icon'],
      badgeColor: json['badge_color'],
      badgeCategory: json['badge_category'] != null 
          ? BadgeCategory.fromString(json['badge_category'])
          : null,
      badgeRarity: json['badge_rarity'] != null 
          ? BadgeRarity.fromString(json['badge_rarity'])
          : null,
      badgePoints: json['badge_points'],
    );
  }
}

class BadgeProgress {
  final String id;
  final String userId;
  final String badgeCode;
  final double currentValue;
  final double targetValue;
  final double progressPercentage;
  final DateTime startedAt;
  final DateTime lastUpdated;
  final Map<String, dynamic> metadata;
  
  // Badge típus adatok
  final String? badgeName;
  final String? badgeDescription;
  final String? badgeIcon;
  final String? badgeColor;

  BadgeProgress({
    required this.id,
    required this.userId,
    required this.badgeCode,
    required this.currentValue,
    required this.targetValue,
    required this.progressPercentage,
    required this.startedAt,
    required this.lastUpdated,
    required this.metadata,
    this.badgeName,
    this.badgeDescription,
    this.badgeIcon,
    this.badgeColor,
  });

  factory BadgeProgress.fromJson(Map<String, dynamic> json) {
    return BadgeProgress(
      id: json['id'],
      userId: json['user_id'],
      badgeCode: json['badge_code'],
      currentValue: json['current_value']?.toDouble() ?? 0.0,
      targetValue: json['target_value']?.toDouble() ?? 0.0,
      progressPercentage: json['progress_percentage']?.toDouble() ?? 0.0,
      startedAt: DateTime.parse(json['started_at']),
      lastUpdated: DateTime.parse(json['last_updated']),
      metadata: Map<String, dynamic>.from(json['metadata'] ?? {}),
      badgeName: json['badge_name'],
      badgeDescription: json['badge_description'],
      badgeIcon: json['badge_icon'],
      badgeColor: json['badge_color'],
    );
  }
}

class BadgeStats {
  final int totalBadges;
  final int totalPoints;
  final Map<String, int> badgesByCategory;
  final Map<String, int> badgesByRarity;
  final List<UserBadge> recentBadges;
  final List<UserBadge> favoriteBadges;
  final int inProgressCount;

  BadgeStats({
    required this.totalBadges,
    required this.totalPoints,
    required this.badgesByCategory,
    required this.badgesByRarity,
    required this.recentBadges,
    required this.favoriteBadges,
    required this.inProgressCount,
  });

  factory BadgeStats.fromJson(Map<String, dynamic> json) {
    return BadgeStats(
      totalBadges: json['total_badges'] ?? 0,
      totalPoints: json['total_points'] ?? 0,
      badgesByCategory: Map<String, int>.from(json['badges_by_category'] ?? {}),
      badgesByRarity: Map<String, int>.from(json['badges_by_rarity'] ?? {}),
      recentBadges: (json['recent_badges'] as List<dynamic>?)
          ?.map((badge) => UserBadge.fromJson(badge))
          .toList() ?? [],
      favoriteBadges: (json['favorite_badges'] as List<dynamic>?)
          ?.map((badge) => UserBadge.fromJson(badge))
          .toList() ?? [],
      inProgressCount: json['in_progress_count'] ?? 0,
    );
  }
}