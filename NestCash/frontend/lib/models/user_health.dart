// lib/models/user_health.dart
import 'package:flutter/material.dart';

class UserHealthScore {
  final double overallScore;
  final double loginFrequencyScore;
  final double featureUsageScore;
  final double engagementScore;
  final String healthLevel;
  final DateTime calculatedAt;
  final HealthScoreDetails details;
  final List<String> recommendations;

  const UserHealthScore({
    required this.overallScore,
    required this.loginFrequencyScore,
    required this.featureUsageScore,
    required this.engagementScore,
    required this.healthLevel,
    required this.calculatedAt,
    required this.details,
    this.recommendations = const [],
  });

  factory UserHealthScore.fromJson(Map<String, dynamic> json) {
    return UserHealthScore(
      overallScore: (json['overall_score'] ?? 0.0).toDouble(),
      loginFrequencyScore: (json['login_frequency_score'] ?? 0.0).toDouble(),
      featureUsageScore: (json['feature_usage_score'] ?? 0.0).toDouble(),
      engagementScore: (json['engagement_score'] ?? 0.0).toDouble(),
      healthLevel: json['health_level'] ?? 'fair',
      calculatedAt: json['calculated_at'] != null 
          ? DateTime.parse(json['calculated_at']) 
          : DateTime.now(),
      details: HealthScoreDetails.fromJson(json['details'] ?? {}),
      recommendations: List<String>.from(json['recommendations'] ?? []),
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

  Color get healthLevelColor {
    switch (healthLevel) {
      case 'excellent':
        return Colors.green;
      case 'good':
        return Colors.lightGreen;
      case 'fair':
        return Colors.orange;
      case 'poor':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  int get overallScoreInt => overallScore.round();
  int get loginFrequencyScoreInt => loginFrequencyScore.round();
  int get featureUsageScoreInt => featureUsageScore.round();
  int get engagementScoreInt => engagementScore.round();
}

class HealthScoreDetails {
  final int daysSinceLastLogin;
  final int totalSessions;
  final int transactionCount;
  final bool onboardingCompleted;
  final int badgeProgressCount;
  final int forumPostsCount;
  final int forumCommentsCount;
  final bool hasActivePartnership;

  const HealthScoreDetails({
    required this.daysSinceLastLogin,
    required this.totalSessions,
    required this.transactionCount,
    required this.onboardingCompleted,
    required this.badgeProgressCount,
    required this.forumPostsCount,
    required this.forumCommentsCount,
    required this.hasActivePartnership,
  });

  factory HealthScoreDetails.fromJson(Map<String, dynamic> json) {
    return HealthScoreDetails(
      daysSinceLastLogin: json['days_since_last_login'] ?? 999,
      totalSessions: json['total_sessions'] ?? 0,
      transactionCount: json['transaction_count'] ?? 0,
      onboardingCompleted: json['onboarding_completed'] ?? false,
      badgeProgressCount: json['badge_progress_count'] ?? 0,
      forumPostsCount: json['forum_posts_count'] ?? 0,
      forumCommentsCount: json['forum_comments_count'] ?? 0,
      hasActivePartnership: json['has_active_partnership'] ?? false,
    );
  }

  String get lastLoginText {
    if (daysSinceLastLogin == 0) return 'Ma';
    if (daysSinceLastLogin == 1) return 'Tegnap';
    if (daysSinceLastLogin < 7) return '$daysSinceLastLogin napja';
    if (daysSinceLastLogin < 30) return '${(daysSinceLastLogin / 7).floor()} hete';
    return 'Több mint 1 hónapja';
  }
}

// Segédosztály a score kategóriákhoz
class ScoreCategory {
  final String name;
  final double score;
  final double weight;
  final Color color;
  final IconData icon;

  const ScoreCategory({
    required this.name,
    required this.score,
    required this.weight,
    required this.color,
    required this.icon,
  });

  int get scoreInt => score.round();
  double get weightedScore => score * weight;
}

// Extension a UserHealthScore-hoz a kategóriák kinyeréséhez
extension UserHealthScoreExtension on UserHealthScore {
  List<ScoreCategory> get categories {
    return [
      ScoreCategory(
        name: 'Bejelentkezés',
        score: loginFrequencyScore,
        weight: 0.3,
        color: Colors.blue,
        icon: Icons.login,
      ),
      ScoreCategory(
        name: 'Funkciók',
        score: featureUsageScore,
        weight: 0.4,
        color: Colors.purple,
        icon: Icons.functions,
      ),
      ScoreCategory(
        name: 'Közösség',
        score: engagementScore,
        weight: 0.3,
        color: Colors.green,
        icon: Icons.people,
      ),
    ];
  }
}