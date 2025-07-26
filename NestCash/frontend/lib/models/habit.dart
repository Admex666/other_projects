// lib/models/habit.dart
enum TrackingType {
  boolean('boolean'),
  numeric('numeric');

  const TrackingType(this.value);
  final String value;

  static TrackingType fromString(String value) {
    return TrackingType.values.firstWhere((e) => e.value == value);
  }
}

enum FrequencyType {
  daily('daily'),
  weekly('weekly'),
  monthly('monthly');

  const FrequencyType(this.value);
  final String value;

  static FrequencyType fromString(String value) {
    return FrequencyType.values.firstWhere((e) => e.value == value);
  }

  String get displayName {
    switch (this) {
      case FrequencyType.daily:
        return 'Napi';
      case FrequencyType.weekly:
        return 'Heti';
      case FrequencyType.monthly:
        return 'Havi';
    }
  }
}

enum HabitCategory {
  financial('Pénzügyi'),
  savings('Megtakarítás'),
  investment('Befektetés'),
  other('Egyéb');

  const HabitCategory(this.value);
  final String value;

  static HabitCategory fromString(String value) {
    return HabitCategory.values.firstWhere((e) => e.value == value);
  }
}

class Habit {
  final String id;
  final String userId;
  final String title;
  final String? description;
  final HabitCategory category;
  final TrackingType trackingType;
  final FrequencyType frequency;
  final bool hasGoal;
  final int? targetValue;
  final FrequencyType? goalPeriod;
  final double? dailyTarget;
  final bool isActive;
  final int streakCount;
  final int bestStreak;
  final String? lastCompleted;
  final bool? isCompletedToday;
  final double? usagePercentage;
  final DateTime createdAt;
  final DateTime? updatedAt;

  Habit({
    required this.id,
    required this.userId,
    required this.title,
    this.description,
    required this.category,
    required this.trackingType,
    required this.frequency,
    required this.hasGoal,
    this.targetValue,
    this.goalPeriod,
    this.dailyTarget,
    required this.isActive,
    required this.streakCount,
    required this.bestStreak,
    this.lastCompleted,
    this.isCompletedToday,
    this.usagePercentage,
    required this.createdAt,
    this.updatedAt,
  });

  factory Habit.fromJson(Map<String, dynamic> json) {
    return Habit(
      id: json['id'],
      userId: json['user_id'],
      title: json['title'],
      description: json['description'],
      category: HabitCategory.fromString(json['category']),
      trackingType: TrackingType.fromString(json['tracking_type']),
      frequency: FrequencyType.fromString(json['frequency']),
      hasGoal: json['has_goal'],
      targetValue: json['target_value'],
      goalPeriod: json['goal_period'] != null 
          ? FrequencyType.fromString(json['goal_period'])
          : null,
      dailyTarget: json['daily_target']?.toDouble(),
      isActive: json['is_active'],
      streakCount: json['streak_count'],
      bestStreak: json['best_streak'],
      lastCompleted: json['last_completed'],
      isCompletedToday: json['is_completed_today'],
      usagePercentage: json['usage_percentage']?.toDouble(),
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'description': description,
      'category': category.value,
      'tracking_type': trackingType.value,
      'frequency': frequency.value,
      'has_goal': hasGoal,
      'target_value': targetValue,
      'goal_period': goalPeriod?.value,
      'is_active': isActive,
    };
  }
}

class HabitLog {
  final String id;
  final String userId;
  final String habitId;
  final String date; // YYYY-MM-DD format
  final bool completed;
  final double? value;
  final String? notes;
  final DateTime createdAt;
  final DateTime? updatedAt;

  HabitLog({
    required this.id,
    required this.userId,
    required this.habitId,
    required this.date,
    required this.completed,
    this.value,
    this.notes,
    required this.createdAt,
    this.updatedAt,
  });

  factory HabitLog.fromJson(Map<String, dynamic> json) {
    return HabitLog(
      id: json['id'],
      userId: json['user_id'],
      habitId: json['habit_id'],
      date: json['date'],
      completed: json['completed'],
      value: json['value']?.toDouble(),
      notes: json['notes'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'completed': completed,
      'value': value,
      'notes': notes,
      'date': date,
    };
  }
}

class HabitStats {
  final String habitId;
  final String habitTitle;
  final HabitProgressStats overall;
  final List<HabitWeeklyStats> weeklyStats;
  final List<HabitMonthlyStats> monthlyStats;

  HabitStats({
    required this.habitId,
    required this.habitTitle,
    required this.overall,
    required this.weeklyStats,
    required this.monthlyStats,
  });

  factory HabitStats.fromJson(Map<String, dynamic> json) {
    return HabitStats(
      habitId: json['habit_id'],
      habitTitle: json['habit_title'],
      overall: HabitProgressStats.fromJson(json['overall']),
      weeklyStats: (json['weekly_stats'] as List)
          .map((e) => HabitWeeklyStats.fromJson(e))
          .toList(),
      monthlyStats: (json['monthly_stats'] as List)
          .map((e) => HabitMonthlyStats.fromJson(e))
          .toList(),
    );
  }
}

class HabitProgressStats {
  final int totalDays;
  final int completedDays;
  final double completionRate;
  final int currentStreak;
  final int bestStreak;
  final double? averageValue;

  HabitProgressStats({
    required this.totalDays,
    required this.completedDays,
    required this.completionRate,
    required this.currentStreak,
    required this.bestStreak,
    this.averageValue,
  });

  factory HabitProgressStats.fromJson(Map<String, dynamic> json) {
    return HabitProgressStats(
      totalDays: json['total_days'],
      completedDays: json['completed_days'],
      completionRate: json['completion_rate'].toDouble(),
      currentStreak: json['current_streak'],
      bestStreak: json['best_streak'],
      averageValue: json['average_value']?.toDouble(),
    );
  }
}

class HabitWeeklyStats {
  final String weekStart;
  final String weekEnd;
  final int completedDays;
  final double? totalValue;

  HabitWeeklyStats({
    required this.weekStart,
    required this.weekEnd,
    required this.completedDays,
    this.totalValue,
  });

  factory HabitWeeklyStats.fromJson(Map<String, dynamic> json) {
    return HabitWeeklyStats(
      weekStart: json['week_start'],
      weekEnd: json['week_end'],
      completedDays: json['completed_days'],
      totalValue: json['total_value']?.toDouble(),
    );
  }
}

class HabitMonthlyStats {
  final String month;
  final int completedDays;
  final int totalDays;
  final double completionRate;
  final double? totalValue;

  HabitMonthlyStats({
    required this.month,
    required this.completedDays,
    required this.totalDays,
    required this.completionRate,
    this.totalValue,
  });

  factory HabitMonthlyStats.fromJson(Map<String, dynamic> json) {
    return HabitMonthlyStats(
      month: json['month'],
      completedDays: json['completed_days'],
      totalDays: json['total_days'],
      completionRate: json['completion_rate'].toDouble(),
      totalValue: json['total_value']?.toDouble(),
    );
  }
}

class UserHabitOverview {
  final int totalHabits;
  final int activeHabits;
  final int archivedHabits;
  final int completedToday;
  final double currentAverageStreak;
  final int bestOverallStreak;
  final Map<String, int> categoriesBreakdown;

  UserHabitOverview({
    required this.totalHabits,
    required this.activeHabits,
    required this.archivedHabits,
    required this.completedToday,
    required this.currentAverageStreak,
    required this.bestOverallStreak,
    required this.categoriesBreakdown,
  });

  factory UserHabitOverview.fromJson(Map<String, dynamic> json) {
    return UserHabitOverview(
      totalHabits: json['total_habits'],
      activeHabits: json['active_habits'],
      archivedHabits: json['archived_habits'],
      completedToday: json['completed_today'],
      currentAverageStreak: json['current_average_streak'].toDouble(),
      bestOverallStreak: json['best_overall_streak'],
      categoriesBreakdown: Map<String, int>.from(json['categories_breakdown']),
    );
  }
}

class PredefinedHabit {
  final String title;
  final String description;
  final TrackingType trackingType;
  final FrequencyType frequency;

  PredefinedHabit({
    required this.title,
    required this.description,
    required this.trackingType,
    required this.frequency,
  });

  factory PredefinedHabit.fromJson(Map<String, dynamic> json) {
    return PredefinedHabit(
      title: json['title'],
      description: json['description'],
      trackingType: TrackingType.fromString(json['tracking_type']),
      frequency: FrequencyType.fromString(json['frequency']),
    );
  }
}