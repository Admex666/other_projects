// lib/models/accountability_models.dart

enum PartnershipStatus {
  pending('pending', 'Függőben'),
  active('active', 'Aktív'),
  declined('declined', 'Elutasítva'),
  ended('ended', 'Lezárva'),
  blocked('blocked', 'Blokkolva');

  const PartnershipStatus(this.value, this.displayName);
  final String value;
  final String displayName;

  static PartnershipStatus fromString(String value) {
    return PartnershipStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => PartnershipStatus.pending,
    );
  }
}

enum CheckInFrequency {
  daily('daily', 'Napi'),
  everyOtherDay('every_other_day', 'Minden második nap'),
  weekly('weekly', 'Heti'),
  biWeekly('bi_weekly', 'Kétheti');

  const CheckInFrequency(this.value, this.displayName);
  final String value;
  final String displayName;

  static CheckInFrequency fromString(String value) {
    return CheckInFrequency.values.firstWhere(
      (freq) => freq.value == value,
      orElse: () => CheckInFrequency.weekly,
    );
  }
}

enum MotivationStyle {
  positiveReinforcement('positive_reinforcement', 'Pozitív megerősítés'),
  challengeBased('challenge_based', 'Kihívás alapú'),
  flexible('flexible', 'Rugalmas'),
  balanced('balanced', 'Kiegyensúlyozott');

  const MotivationStyle(this.value, this.displayName);
  final String value;
  final String displayName;

  static MotivationStyle fromString(String value) {
    return MotivationStyle.values.firstWhere(
      (style) => style.value == value,
      orElse: () => MotivationStyle.balanced,
    );
  }
}

enum PersonalityType {
  competitiveDirect('competitive_direct', 'Kompetitív és közvetlen'),
  supportiveGentle('supportive_gentle', 'Támogató és tapintatos'),
  balanced('balanced', 'Kiegyensúlyozott');

  const PersonalityType(this.value, this.displayName);
  final String value;
  final String displayName;

  static PersonalityType fromString(String value) {
    return PersonalityType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => PersonalityType.balanced,
    );
  }
}

enum GoalCategory {
  financial('financial', 'Pénzügyek', '💰'),
  savings('savings', 'Megtakarítás', '🏦'),
  investment('investment', 'Befektetés', '📈'),
  spendingControl('spending_control', 'Kiadások kontroll', '🛡️'),
  habitBuilding('habit_building', 'Szokásépítés', '🎯');

  const GoalCategory(this.value, this.displayName, this.emoji);
  final String value;
  final String displayName;
  final String emoji;

  static GoalCategory fromString(String value) {
    return GoalCategory.values.firstWhere(
      (category) => category.value == value,
      orElse: () => GoalCategory.financial,
    );
  }
}

enum CheckinFrequency {
  daily,
  weekly,
  biweekly,
  monthly;

  String get displayName {
    switch (this) {
      case CheckinFrequency.daily:
        return 'Napi';
      case CheckinFrequency.weekly:
        return 'Heti';
      case CheckinFrequency.biweekly:
        return 'Kétheti';
      case CheckinFrequency.monthly:
        return 'Havi';
    }
  }
}

class AccountabilityProfile {
  final String id;
  final String userId;
  final List<GoalCategory> goalCategories;
  final CheckInFrequency checkinFrequency;
  final MotivationStyle motivationStyle;
  final PersonalityType personalityType;
  final String timezone;
  final Map<String, List<String>> availabilityHours;
  final String? bio;
  final int? maxAgeDifference;
  final String? preferredExperienceLevel;
  final bool isActive;
  final bool isLookingForPartners;
  final DateTime createdAt;
  final DateTime updatedAt;

  const AccountabilityProfile({
    required this.id,
    required this.userId,
    required this.goalCategories,
    required this.checkinFrequency,
    required this.motivationStyle,
    required this.personalityType,
    this.timezone = 'Europe/Budapest',
    this.availabilityHours = const {},
    this.bio,
    this.maxAgeDifference,
    this.preferredExperienceLevel,
    this.isActive = true,
    this.isLookingForPartners = true,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AccountabilityProfile.fromJson(Map<String, dynamic> json) {
    return AccountabilityProfile(
      id: json['id'] ?? '',
      userId: json['user_id'] ?? '',
      goalCategories: (json['goal_categories'] as List?)
          ?.map((e) => GoalCategory.fromString(e.toString()))
          .toList() ?? [],
      checkinFrequency: CheckInFrequency.fromString(json['checkin_frequency'] ?? 'weekly'),
      motivationStyle: MotivationStyle.fromString(json['motivation_style'] ?? 'balanced'),
      personalityType: PersonalityType.fromString(json['personality_type'] ?? 'balanced'),
      timezone: json['timezone'] ?? 'Europe/Budapest',
      availabilityHours: Map<String, List<String>>.from(
        json['availability_hours'] ?? {},
      ),
      bio: json['bio'],
      maxAgeDifference: json['max_age_difference'],
      preferredExperienceLevel: json['preferred_experience_level'],
      isActive: json['is_active'] ?? true,
      isLookingForPartners: json['is_looking_for_partners'] ?? true,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'goal_categories': goalCategories.map((e) => e.value).toList(),
      'checkin_frequency': checkinFrequency.value,
      'motivation_style': motivationStyle.value,
      'personality_type': personalityType.value,
      'timezone': timezone,
      'availability_hours': availabilityHours,
      if (bio != null) 'bio': bio,
      if (maxAgeDifference != null) 'max_age_difference': maxAgeDifference,
      if (preferredExperienceLevel != null) 'preferred_experience_level': preferredExperienceLevel,
    };
  }

  AccountabilityProfile copyWith({
    String? id,
    String? userId,
    List<GoalCategory>? goalCategories,
    CheckInFrequency? checkinFrequency,
    MotivationStyle? motivationStyle,
    PersonalityType? personalityType,
    String? timezone,
    Map<String, List<String>>? availabilityHours,
    String? bio,
    int? maxAgeDifference,
    String? preferredExperienceLevel,
    bool? isActive,
    bool? isLookingForPartners,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return AccountabilityProfile(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      goalCategories: goalCategories ?? this.goalCategories,
      checkinFrequency: checkinFrequency ?? this.checkinFrequency,
      motivationStyle: motivationStyle ?? this.motivationStyle,
      personalityType: personalityType ?? this.personalityType,
      timezone: timezone ?? this.timezone,
      availabilityHours: availabilityHours ?? this.availabilityHours,
      bio: bio ?? this.bio,
      maxAgeDifference: maxAgeDifference ?? this.maxAgeDifference,
      preferredExperienceLevel: preferredExperienceLevel ?? this.preferredExperienceLevel,
      isActive: isActive ?? this.isActive,
      isLookingForPartners: isLookingForPartners ?? this.isLookingForPartners,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

class Partnership {
  final String id;
  final String partnerUserId;
  final String partnerUsername;
  final PartnershipStatus status;
  final CheckInFrequency checkinFrequency;
  final List<String> sharedGoals;
  final DateTime createdAt;
  final DateTime? acceptedAt;
  final int totalCheckins;
  final int successfulCheckins;

  const Partnership({
    required this.id,
    required this.partnerUserId,
    required this.partnerUsername,
    required this.status,
    required this.checkinFrequency,
    this.sharedGoals = const [],
    required this.createdAt,
    this.acceptedAt,
    this.totalCheckins = 0,
    this.successfulCheckins = 0,
  });

  factory Partnership.fromJson(Map<String, dynamic> json) {
    return Partnership(
      id: json['id'] ?? '',
      partnerUserId: json['partner_user_id'] ?? '',
      partnerUsername: json['partner_username'] ?? '',
      status: PartnershipStatus.fromString(json['status'] ?? 'pending'),
      checkinFrequency: CheckInFrequency.fromString(json['checkin_frequency'] ?? 'weekly'),
      sharedGoals: List<String>.from(json['shared_goals'] ?? []),
      createdAt: DateTime.parse(json['created_at']),
      acceptedAt: json['accepted_at'] != null ? DateTime.parse(json['accepted_at']) : null,
      totalCheckins: json['total_checkins'] ?? 0,
      successfulCheckins: json['successful_checkins'] ?? 0,
    );
  }

  double get successRate {
    if (totalCheckins == 0) return 0.0;
    return (successfulCheckins / totalCheckins) * 100;
  }

  String get statusDisplayName => status.displayName;
  
  bool get isActive => status == PartnershipStatus.active;
  bool get isPending => status == PartnershipStatus.pending;
}

class CheckIn {
  final String id;
  final String partnershipId;
  final String userId;
  final String date;
  final bool goalsMet;
  final int progressRating;
  final String? notes;
  final DateTime createdAt;

  const CheckIn({
    required this.id,
    required this.partnershipId,
    required this.userId,
    required this.date,
    required this.goalsMet,
    required this.progressRating,
    this.notes,
    required this.createdAt,
  });

  factory CheckIn.fromJson(Map<String, dynamic> json) {
    return CheckIn(
      id: json['id'] ?? '',
      partnershipId: json['partnership_id'] ?? '',
      userId: json['user_id'] ?? '',
      date: json['date'] ?? '',
      goalsMet: json['goals_met'] ?? false,
      progressRating: json['progress_rating'] ?? 1,
      notes: json['notes'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'goals_met': goalsMet,
      'progress_rating': progressRating,
      if (notes != null) 'notes': notes,
    };
  }
}

class PartnerSuggestion {
  final String userId;
  final String username;
  final String? bio;
  final List<GoalCategory> goalCategories;
  final double compatibilityScore;
  final List<String> commonGoals;
  final Map<String, String> matchingFactors;

  const PartnerSuggestion({
    required this.userId,
    required this.username,
    this.bio,
    required this.goalCategories,
    required this.compatibilityScore,
    this.commonGoals = const [],
    this.matchingFactors = const {},
  });

  factory PartnerSuggestion.fromJson(Map<String, dynamic> json) {
    return PartnerSuggestion(
      userId: json['user_id'] ?? '',
      username: json['username'] ?? '',
      bio: json['bio'],
      goalCategories: (json['goal_categories'] as List?)
          ?.map((e) => GoalCategory.fromString(e.toString()))
          .toList() ?? [],
      compatibilityScore: (json['compatibility_score'] ?? 0.0).toDouble(),
      commonGoals: List<String>.from(json['common_goals'] ?? []),
      matchingFactors: Map<String, String>.from(json['matching_factors'] ?? {}),
    );
  }

  int get compatibilityPercentage => (compatibilityScore * 100).round();
  
  String get compatibilityText {
    if (compatibilityScore >= 0.8) return 'Kiváló egyezés';
    if (compatibilityScore >= 0.6) return 'Jó egyezés';
    if (compatibilityScore >= 0.4) return 'Közepes egyezés';
    return 'Gyenge egyezés';
  }
}

class PartnershipRequest {
  final String targetUserId;
  final String message;
  final CheckinFrequency checkinFrequency;
  final List<String> sharedGoals;

  const PartnershipRequest({
    required this.targetUserId,
    this.message = '',
    required this.checkinFrequency,
    this.sharedGoals = const [],
  });

  Map<String, dynamic> toJson() {
    return {
      'target_user_id': targetUserId,
      'message': message,
      'checkin_frequency': checkinFrequency.name,
      'shared_goals': sharedGoals,
    };
  }
}