// lib/models/challenge.dart
class ChallengeReward {
  final int points;
  final List<String> badges;
  final String? title;

  ChallengeReward({
    required this.points,
    required this.badges,
    this.title,
  });

  factory ChallengeReward.fromJson(Map<String, dynamic> json) {
    return ChallengeReward(
      points: json['points'] ?? 0,
      badges: List<String>.from(json['badges'] ?? []),
      title: json['title'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'points': points,
      'badges': badges,
      'title': title,
    };
  }
}

class ChallengeRule {
  final String type;
  final double value;
  final String description;

  ChallengeRule({
    required this.type,
    required this.value,
    required this.description,
  });

  factory ChallengeRule.fromJson(Map<String, dynamic> json) {
    return ChallengeRule(
      type: json['type'],
      value: json['value'].toDouble(),
      description: json['description'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'value': value,
      'description': description,
    };
  }
}

class ChallengeProgress {
  final double currentValue;
  final double targetValue;
  final String unit;
  final double percentage;

  ChallengeProgress({
    required this.currentValue,
    required this.targetValue,
    required this.unit,
    required this.percentage,
  });

  factory ChallengeProgress.fromJson(Map<String, dynamic> json) {
    return ChallengeProgress(
      currentValue: json['current_value']?.toDouble() ?? 0.0,
      targetValue: json['target_value']?.toDouble() ?? 0.0,
      unit: json['unit'] ?? 'HUF',
      percentage: json['percentage']?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'current_value': currentValue,
      'target_value': targetValue,
      'unit': unit,
      'percentage': percentage,
    };
  }
}

enum ChallengeType {
  savings('savings', 'Megtakarítás'),
  expenseReduction('expense_reduction', 'Kiadás csökkentés'),
  habitStreak('habit_streak', 'Szokás streak'),
  budgetControl('budget_control', 'Költségvetés betartás'),
  investment('investment', 'Befektetés'),
  incomeBoost('income_boost', 'Bevétel növelés');

  const ChallengeType(this.value, this.displayName);
  final String value;
  final String displayName;

  static ChallengeType fromString(String value) {
    return ChallengeType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => ChallengeType.savings,
    );
  }
}

enum ChallengeDifficulty {
  easy('easy', 'Könnyű'),
  medium('medium', 'Közepes'),
  hard('hard', 'Nehéz'),
  expert('expert', 'Szakértő');

  const ChallengeDifficulty(this.value, this.displayName);
  final String value;
  final String displayName;

  static ChallengeDifficulty fromString(String value) {
    return ChallengeDifficulty.values.firstWhere(
      (difficulty) => difficulty.value == value,
      orElse: () => ChallengeDifficulty.easy,
    );
  }
}

enum ChallengeStatus {
  draft('draft', 'Tervezet'),
  active('active', 'Aktív'),
  completed('completed', 'Befejezett'),
  cancelled('cancelled', 'Megszakított');

  const ChallengeStatus(this.value, this.displayName);
  final String value;
  final String displayName;

  static ChallengeStatus fromString(String value) {
    return ChallengeStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ChallengeStatus.active,
    );
  }
}

enum ParticipationStatus {
  active('active', 'Aktív'),
  completed('completed', 'Befejezett'),
  failed('failed', 'Sikertelen'),
  abandoned('abandoned', 'Elhagyott');

  const ParticipationStatus(this.value, this.displayName);
  final String value;
  final String displayName;

  static ParticipationStatus fromString(String value) {
    return ParticipationStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ParticipationStatus.active,
    );
  }
}

class Challenge {
  final String id;
  final String title;
  final String description;
  final String? shortDescription;
  final ChallengeType challengeType;
  final ChallengeDifficulty difficulty;
  final int durationDays;
  final double? targetAmount;
  final List<ChallengeRule> rules;
  final ChallengeReward rewards;
  final ChallengeStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int participantCount;
  final double completionRate;
  final String? imageUrl;
  final List<String> tags;
  final String? creatorUsername;
  final bool isParticipating;
  final ChallengeProgress? myProgress;
  final ParticipationStatus? myStatus;

  Challenge({
    required this.id,
    required this.title,
    required this.description,
    this.shortDescription,
    required this.challengeType,
    required this.difficulty,
    required this.durationDays,
    this.targetAmount,
    required this.rules,
    required this.rewards,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    required this.participantCount,
    required this.completionRate,
    this.imageUrl,
    required this.tags,
    this.creatorUsername,
    required this.isParticipating,
    this.myProgress,
    this.myStatus,
  });

  factory Challenge.fromJson(Map<String, dynamic> json) {
    return Challenge(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      shortDescription: json['short_description'],
      challengeType: ChallengeType.fromString(json['challenge_type']),
      difficulty: ChallengeDifficulty.fromString(json['difficulty']),
      durationDays: json['duration_days'],
      targetAmount: json['target_amount']?.toDouble(),
      rules: (json['rules'] as List<dynamic>)
          .map((rule) => ChallengeRule.fromJson(rule))
          .toList(),
      rewards: ChallengeReward.fromJson(json['rewards']),
      status: ChallengeStatus.fromString(json['status']),
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      participantCount: json['participant_count'],
      completionRate: json['completion_rate']?.toDouble() ?? 0.0,
      imageUrl: json['image_url'],
      tags: List<String>.from(json['tags'] ?? []),
      creatorUsername: json['creator_username'],
      isParticipating: json['is_participating'] ?? false,
      myProgress: json['my_progress'] != null 
          ? ChallengeProgress.fromJson(json['my_progress'])
          : null,
      myStatus: json['my_status'] != null 
          ? ParticipationStatus.fromString(json['my_status'])
          : null,
    );
  }
}

class UserChallenge {
  final String id;
  final String userId;
  final String username;
  final String challengeId;
  final ParticipationStatus status;
  final DateTime joinedAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime updatedAt;
  final ChallengeProgress progress;
  final double? personalTarget;
  final String? notes;
  final int earnedPoints;
  final List<String> earnedBadges;
  final int bestStreak;
  final int currentStreak;
  final String challengeTitle;
  final ChallengeType challengeType;
  final ChallengeDifficulty challengeDifficulty;

  UserChallenge({
    required this.id,
    required this.userId,
    required this.username,
    required this.challengeId,
    required this.status,
    required this.joinedAt,
    this.startedAt,
    this.completedAt,
    required this.updatedAt,
    required this.progress,
    this.personalTarget,
    this.notes,
    required this.earnedPoints,
    required this.earnedBadges,
    required this.bestStreak,
    required this.currentStreak,
    required this.challengeTitle,
    required this.challengeType,
    required this.challengeDifficulty,
  });

  factory UserChallenge.fromJson(Map<String, dynamic> json) {
    return UserChallenge(
      id: json['id'],
      userId: json['user_id'],
      username: json['username'],
      challengeId: json['challenge_id'],
      status: ParticipationStatus.fromString(json['status']),
      joinedAt: DateTime.parse(json['joined_at']),
      startedAt: json['started_at'] != null 
          ? DateTime.parse(json['started_at'])
          : null,
      completedAt: json['completed_at'] != null 
          ? DateTime.parse(json['completed_at'])
          : null,
      updatedAt: DateTime.parse(json['updated_at']),
      progress: ChallengeProgress.fromJson(json['progress']),
      personalTarget: json['personal_target']?.toDouble(),
      notes: json['notes'],
      earnedPoints: json['earned_points'],
      earnedBadges: List<String>.from(json['earned_badges'] ?? []),
      bestStreak: json['best_streak'],
      currentStreak: json['current_streak'],
      challengeTitle: json['challenge_title'],
      challengeType: ChallengeType.fromString(json['challenge_type']),
      challengeDifficulty: ChallengeDifficulty.fromString(json['challenge_difficulty']),
    );
  }
}