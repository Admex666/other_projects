// lib/models/admin_models.dart

class AdminUserHealthScore {
  final String userId;
  final String username;
  final String email;
  final double overallScore;
  final String healthLevel;
  final DateTime calculatedAt;
  final double loginFrequencyScore;
  final double featureUsageScore;
  final double engagementScore;
  final AdminHealthDetails details;

  const AdminUserHealthScore({
    required this.userId,
    required this.username,
    required this.email,
    required this.overallScore,
    required this.healthLevel,
    required this.calculatedAt,
    required this.loginFrequencyScore,
    required this.featureUsageScore,
    required this.engagementScore,
    required this.details,
  });

  factory AdminUserHealthScore.fromJson(Map<String, dynamic> json) {
    return AdminUserHealthScore(
      userId: json['user_id'] ?? '',
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      overallScore: (json['overall_score'] ?? 0.0).toDouble(),
      healthLevel: json['health_level'] ?? 'fair',
      calculatedAt: json['calculated_at'] != null 
          ? DateTime.parse(json['calculated_at']) 
          : DateTime.now(),
      loginFrequencyScore: (json['login_frequency_score'] ?? 0.0).toDouble(),
      featureUsageScore: (json['feature_usage_score'] ?? 0.0).toDouble(),
      engagementScore: (json['engagement_score'] ?? 0.0).toDouble(),
      details: AdminHealthDetails.fromJson(json['details'] ?? {}),
    );
  }

  String get healthLevelDisplayName {
    switch (healthLevel) {
      case 'excellent':
        return 'Kiváló';
      case 'good':
        return 'Jó';
      case 'fair':
        return 'Közepes';
      case 'poor':
        return 'Gyenge';
      default:
        return healthLevel;
    }
  }

  int get overallScoreInt => overallScore.round();
}

class AdminHealthDetails {
  final int daysSinceLastLogin;
  final int totalSessions;
  final int transactionCount;
  final bool onboardingCompleted;
  final int badgeProgressCount;
  final int forumPostsCount;
  final int forumCommentsCount;
  final bool hasActivePartnership;
  final int? knowledgeActivityCount;
  final int? messagesActivityCount; 
  final int? knowledgeLessonsCompleted;
  final int? messagesSentCount;
  final int? habitsActivityCount;
  final int? limitsActivityCount;
  final int? ptiActivityCount;
  final int? badgeActivityCount;


  const AdminHealthDetails({
    required this.daysSinceLastLogin,
    required this.totalSessions,
    required this.transactionCount,
    required this.onboardingCompleted,
    required this.badgeProgressCount,
    required this.forumPostsCount,
    required this.forumCommentsCount,
    required this.hasActivePartnership,
    required this.knowledgeActivityCount,
    required this.messagesActivityCount,
    required this.knowledgeLessonsCompleted,
    required this.messagesSentCount,
    required this.habitsActivityCount,
    required this.limitsActivityCount,
    required this.ptiActivityCount,
    required this.badgeActivityCount,
  });

  factory AdminHealthDetails.fromJson(Map<String, dynamic> json) {
    return AdminHealthDetails(
      daysSinceLastLogin: json['days_since_last_login'] ?? 999,
      totalSessions: json['total_sessions'] ?? 0,
      transactionCount: json['transaction_count'] ?? 0,
      onboardingCompleted: json['onboarding_completed'] ?? false,
      badgeProgressCount: json['badge_progress_count'] ?? 0,
      forumPostsCount: json['forum_posts_count'] ?? 0,
      forumCommentsCount: json['forum_comments_count'] ?? 0,
      hasActivePartnership: json['has_active_partnership'] ?? false,
      knowledgeActivityCount: json['knowledge_activity_count'] ?? 0,
      messagesActivityCount: json['messages_activity_count'] ?? 0,
      knowledgeLessonsCompleted: json['knowledge_lessons_completed'] ?? 0,
      messagesSentCount: json['messages_sent_count'] ?? 0,
      habitsActivityCount: json['habits_activity_count'] ?? 0,
      limitsActivityCount: json['limits_activity_count'] ?? 0,
      ptiActivityCount: json['pti_activity_count'] ?? 0,
      badgeActivityCount: json['badge_activity_count'] ?? 0,
    );
  }
}

class AdminStats {
  final int totalUsers;
  final int activeUsers;
  final Map<String, int> healthDistribution;
  final AdminAverageScores averageScores;
  final double onboardingCompletionRate;
  final double averageTTVMinutes;
  final double inactiveUserRate;

  const AdminStats({
    required this.totalUsers,
    required this.activeUsers,
    required this.healthDistribution,
    required this.averageScores,
    required this.onboardingCompletionRate,
    required this.averageTTVMinutes,
    required this.inactiveUserRate,
  });

  factory AdminStats.fromJson(Map<String, dynamic> json) {
    return AdminStats(
      totalUsers: json['total_users'] ?? 0,
      activeUsers: json['active_users'] ?? 0,
      healthDistribution: Map<String, int>.from(json['health_distribution'] ?? {}),
      averageScores: AdminAverageScores.fromJson(json['average_scores'] ?? {}),
      onboardingCompletionRate: (json['onboarding_completion_rate'] ?? 0.0),
      averageTTVMinutes: (json['average_ttv_minutes'] ?? 0.0),
      inactiveUserRate: (json['inactive_user_rate'] as num).toDouble(),
    );
  }

  double get activeUserPercentage {
    if (totalUsers == 0) return 0;
    return (activeUsers / totalUsers * 100);
  }
}

class AdminAverageScores {
  final double overall;
  final double loginFrequency;
  final double featureUsage;
  final double engagement;

  const AdminAverageScores({
    required this.overall,
    required this.loginFrequency,
    required this.featureUsage,
    required this.engagement,
  });

  factory AdminAverageScores.fromJson(Map<String, dynamic> json) {
    return AdminAverageScores(
      overall: (json['overall'] ?? 0.0).toDouble(),
      loginFrequency: (json['login_frequency'] ?? 0.0).toDouble(),
      featureUsage: (json['feature_usage'] ?? 0.0).toDouble(),
      engagement: (json['engagement'] ?? 0.0).toDouble(),
    );
  }
}