// lib/models/pti_models.dart

enum PTIPeriod {
  weekly('weekly', 'Heti'),
  monthly('monthly', 'Havi'),
  yearly('yearly', 'Éves');

  const PTIPeriod(this.value, this.displayName);
  final String value;
  final String displayName;

  static PTIPeriod fromString(String value) {
    return PTIPeriod.values.firstWhere(
      (period) => period.value == value,
      orElse: () => PTIPeriod.weekly,
    );
  }
}

enum RankingScope {
  private('private', 'Privát'),
  friends('friends', 'Barátok'),
  global('global', 'Globális');

  const RankingScope(this.value, this.displayName);
  final String value;
  final String displayName;

  static RankingScope fromString(String value) {
    return RankingScope.values.firstWhere(
      (scope) => scope.value == value,
      orElse: () => RankingScope.global,
    );
  }
}

class PTIComponentBreakdown {
  final double learningPoints;
  final double learningWeight;
  final double learningContribution;
  final double habitScore;
  final double habitWeight;
  final double habitContribution;
  final double badgeScore;
  final double badgeWeight;
  final double badgeContribution;
  final double limitScore;
  final double limitWeight;
  final double limitContribution;
  final double totalPti;

  const PTIComponentBreakdown({
    required this.learningPoints,
    this.learningWeight = 0.30,
    required this.learningContribution,
    required this.habitScore,
    this.habitWeight = 0.30,
    required this.habitContribution,
    required this.badgeScore,
    this.badgeWeight = 0.20,
    required this.badgeContribution,
    required this.limitScore,
    this.limitWeight = 0.20,
    required this.limitContribution,
    required this.totalPti,
  });

  factory PTIComponentBreakdown.fromJson(Map<String, dynamic> json) {
    return PTIComponentBreakdown(
      learningPoints: (json['learning_points'] ?? 0).toDouble(),
      learningWeight: (json['learning_weight'] ?? 0.30).toDouble(),
      learningContribution: (json['learning_contribution'] ?? 0).toDouble(),
      habitScore: (json['habit_score'] ?? 0).toDouble(),
      habitWeight: (json['habit_weight'] ?? 0.30).toDouble(),
      habitContribution: (json['habit_contribution'] ?? 0).toDouble(),
      badgeScore: (json['badge_score'] ?? 0).toDouble(),
      badgeWeight: (json['badge_weight'] ?? 0.20).toDouble(),
      badgeContribution: (json['badge_contribution'] ?? 0).toDouble(),
      limitScore: (json['limit_score'] ?? 0).toDouble(),
      limitWeight: (json['limit_weight'] ?? 0.20).toDouble(),
      limitContribution: (json['limit_contribution'] ?? 0).toDouble(),
      totalPti: (json['total_pti'] ?? 0).toDouble(),
    );
  }
}

class PTIRankingEntry {
  final int rank;
  final String userId;
  final String? username;
  final String? anonymousName;
  final bool isAnonymous;
  final double ptiScore;
  final PTIComponentBreakdown components;
  final bool isCurrentUser;

  const PTIRankingEntry({
    required this.rank,
    required this.userId,
    this.username,
    this.anonymousName,
    required this.isAnonymous,
    required this.ptiScore,
    required this.components,
    this.isCurrentUser = false,
  });

  factory PTIRankingEntry.fromJson(Map<String, dynamic> json) {
    return PTIRankingEntry(
      rank: json['rank'] ?? 0,
      userId: json['user_id'] ?? '',
      username: json['username'],
      anonymousName: json['anonymous_name'],
      isAnonymous: json['is_anonymous'] ?? false,
      ptiScore: (json['pti_score'] ?? 0).toDouble(),
      components: PTIComponentBreakdown.fromJson(json['components'] ?? {}),
      isCurrentUser: json['is_current_user'] ?? false,
    );
  }

  String get displayName {
    if (isAnonymous && anonymousName != null) {
      return anonymousName!;
    }
    return username ?? 'Ismeretlen';
  }
}

class PTIRankingResponse {
  final PTIPeriod period;
  final String periodKey;
  final RankingScope scope;
  final List<PTIRankingEntry> rankings;
  final int? userRank;
  final double? userScore;
  final int totalParticipants;
  final DateTime generatedAt;

  const PTIRankingResponse({
    required this.period,
    required this.periodKey,
    required this.scope,
    required this.rankings,
    this.userRank,
    this.userScore,
    required this.totalParticipants,
    required this.generatedAt,
  });

  factory PTIRankingResponse.fromJson(Map<String, dynamic> json) {
    return PTIRankingResponse(
      period: PTIPeriod.fromString(json['period'] ?? 'weekly'),
      periodKey: json['period_key'] ?? '',
      scope: RankingScope.fromString(json['scope'] ?? 'global'),
      rankings: (json['rankings'] as List<dynamic>? ?? [])
          .map((ranking) => PTIRankingEntry.fromJson(ranking))
          .toList(),
      userRank: json['user_rank'],
      userScore: json['user_score']?.toDouble(),
      totalParticipants: json['total_participants'] ?? 0,
      generatedAt: DateTime.parse(json['generated_at'] ?? DateTime.now().toIso8601String()),
    );
  }
}

class PTIScoreResponse {
  final String userId;
  final PTIPeriod period;
  final String periodKey;
  final PTIComponentBreakdown components;
  final double ptiScore;
  final int? rank;
  final int? totalUsers;
  final double? percentile;
  final DateTime calculatedAt;

  const PTIScoreResponse({
    required this.userId,
    required this.period,
    required this.periodKey,
    required this.components,
    required this.ptiScore,
    this.rank,
    this.totalUsers,
    this.percentile,
    required this.calculatedAt,
  });

  factory PTIScoreResponse.fromJson(Map<String, dynamic> json) {
    return PTIScoreResponse(
      userId: json['user_id'] ?? '',
      period: PTIPeriod.fromString(json['period'] ?? 'weekly'),
      periodKey: json['period_key'] ?? '',
      components: PTIComponentBreakdown.fromJson(json['components'] ?? {}),
      ptiScore: (json['pti_score'] ?? 0).toDouble(),
      rank: json['rank'],
      totalUsers: json['total_users'],
      percentile: json['percentile']?.toDouble(),
      calculatedAt: DateTime.parse(json['calculated_at'] ?? DateTime.now().toIso8601String()),
    );
  }
}

class PTIDashboardResponse {
  final PTIScoreResponse currentPti;
  final PTIRankingEntry? weeklyRanking;
  final PTIRankingEntry? monthlyRanking;
  final PTIRankingEntry? yearlyRanking;
  final double? weeklyGoalProgress;
  final double? monthlyGoalProgress;
  final List<String> nextActions;
  final List<Map<String, double>> last7Days;
  final List<Map<String, double>> last4Weeks;
  final List<Map<String, double>> last12Months;

  const PTIDashboardResponse({
    required this.currentPti,
    this.weeklyRanking,
    this.monthlyRanking,
    this.yearlyRanking,
    this.weeklyGoalProgress,
    this.monthlyGoalProgress,
    required this.nextActions,
    this.last7Days = const [],
    this.last4Weeks = const [],
    this.last12Months = const [],
  });

  factory PTIDashboardResponse.fromJson(Map<String, dynamic> json) {
    return PTIDashboardResponse(
      currentPti: PTIScoreResponse.fromJson(json['current_pti'] ?? {}),
      weeklyRanking: json['weekly_ranking'] != null
          ? PTIRankingEntry.fromJson(json['weekly_ranking'])
          : null,
      monthlyRanking: json['monthly_ranking'] != null
          ? PTIRankingEntry.fromJson(json['monthly_ranking'])
          : null,
      yearlyRanking: json['yearly_ranking'] != null
          ? PTIRankingEntry.fromJson(json['yearly_ranking'])
          : null,
      weeklyGoalProgress: json['weekly_goal_progress']?.toDouble(),
      monthlyGoalProgress: json['monthly_goal_progress']?.toDouble(),
      nextActions: List<String>.from(json['next_actions'] ?? []),
      last7Days: (json['last_7_days'] as List<dynamic>? ?? [])
          .map((item) => Map<String, double>.from(item))
          .toList(),
      last4Weeks: (json['last_4_weeks'] as List<dynamic>? ?? [])
          .map((item) => Map<String, double>.from(item))
          .toList(),
      last12Months: (json['last_12_months'] as List<dynamic>? ?? [])
          .map((item) => Map<String, double>.from(item))
          .toList(),
    );
  }
}

class PTIUserSettings {
  final String userId;
  final bool showInGlobalRanking;
  final bool showInFriendsRanking;
  final bool isAnonymous;
  final String? anonymousName;
  final bool notifyRankChange;
  final bool notifyWeeklySummary;
  final bool notifyAchievements;
  final double? weeklyPtiGoal;
  final double? monthlyPtiGoal;
  final DateTime createdAt;
  final DateTime updatedAt;

  const PTIUserSettings({
    required this.userId,
    required this.showInGlobalRanking,
    required this.showInFriendsRanking,
    required this.isAnonymous,
    this.anonymousName,
    required this.notifyRankChange,
    required this.notifyWeeklySummary,
    required this.notifyAchievements,
    this.weeklyPtiGoal,
    this.monthlyPtiGoal,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PTIUserSettings.fromJson(Map<String, dynamic> json) {
    return PTIUserSettings(
      userId: json['user_id'] ?? '',
      showInGlobalRanking: json['show_in_global_ranking'] ?? true,
      showInFriendsRanking: json['show_in_friends_ranking'] ?? true,
      isAnonymous: json['is_anonymous'] ?? false,
      anonymousName: json['anonymous_name'],
      notifyRankChange: json['notify_rank_change'] ?? true,
      notifyWeeklySummary: json['notify_weekly_summary'] ?? true,
      notifyAchievements: json['notify_achievements'] ?? true,
      weeklyPtiGoal: json['weekly_pti_goal']?.toDouble(),
      monthlyPtiGoal: json['monthly_pti_goal']?.toDouble(),
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      updatedAt: DateTime.parse(json['updated_at'] ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'show_in_global_ranking': showInGlobalRanking,
      'show_in_friends_ranking': showInFriendsRanking,
      'is_anonymous': isAnonymous,
      'notify_rank_change': notifyRankChange,
      'notify_weekly_summary': notifyWeeklySummary,
      'notify_achievements': notifyAchievements,
    };

    if (anonymousName != null && anonymousName!.isNotEmpty) {
      data['anonymous_name'] = anonymousName;
    }
    if (weeklyPtiGoal != null) {
      data['weekly_pti_goal'] = weeklyPtiGoal;
    }
    if (monthlyPtiGoal != null) {
      data['monthly_pti_goal'] = monthlyPtiGoal;
    }

    return data;
  }

  PTIUserSettings copyWith({
    String? userId,
    bool? showInGlobalRanking,
    bool? showInFriendsRanking,
    bool? isAnonymous,
    String? anonymousName,
    bool? notifyRankChange,
    bool? notifyWeeklySummary,
    bool? notifyAchievements,
    double? weeklyPtiGoal,
    double? monthlyPtiGoal,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return PTIUserSettings(
      userId: userId ?? this.userId,
      showInGlobalRanking: showInGlobalRanking ?? this.showInGlobalRanking,
      showInFriendsRanking: showInFriendsRanking ?? this.showInFriendsRanking,
      isAnonymous: isAnonymous ?? this.isAnonymous,
      anonymousName: anonymousName ?? this.anonymousName,
      notifyRankChange: notifyRankChange ?? this.notifyRankChange,
      notifyWeeklySummary: notifyWeeklySummary ?? this.notifyWeeklySummary,
      notifyAchievements: notifyAchievements ?? this.notifyAchievements,
      weeklyPtiGoal: weeklyPtiGoal ?? this.weeklyPtiGoal,
      monthlyPtiGoal: monthlyPtiGoal ?? this.monthlyPtiGoal,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

class PTIComparisonResponse {
  final PTIScoreResponse currentPeriod;
  final PTIScoreResponse? previousPeriod;
  final double? ptiChange;
  final int? rankChange;
  final List<String> improvements;
  final List<String> declines;

  const PTIComparisonResponse({
    required this.currentPeriod,
    this.previousPeriod,
    this.ptiChange,
    this.rankChange,
    this.improvements = const [],
    this.declines = const [],
  });

  factory PTIComparisonResponse.fromJson(Map<String, dynamic> json) {
    return PTIComparisonResponse(
      currentPeriod: PTIScoreResponse.fromJson(json['current_period'] ?? {}),
      previousPeriod: json['previous_period'] != null
          ? PTIScoreResponse.fromJson(json['previous_period'])
          : null,
      ptiChange: json['pti_change']?.toDouble(),
      rankChange: json['rank_change'],
      improvements: List<String>.from(json['improvements'] ?? []),
      declines: List<String>.from(json['declines'] ?? []),
    );
  }
}