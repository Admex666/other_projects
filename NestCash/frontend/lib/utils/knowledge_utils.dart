// lib/utils/knowledge_utils.dart
import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';

class KnowledgeUtils {
  // Színek a különböző nehézségi szintekhez
  static Color getDifficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return Colors.green;
      case 'professional':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  // Emoji a nehézségi szintekhez
  static String getDifficultyEmoji(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return '🟢';
      case 'professional':
        return '🔵';
      default:
        return '⚪';
    }
  }

  // Szöveg a nehézségi szintekhez
  static String getDifficultyText(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return 'knowledge_u.difficulty_text_beginner'.tr();
      case 'professional':
        return 'knowledge_u.difficulty_text_professional'.tr();
      default:
        return 'knowledge_u.difficulty_text_unknown'.tr();
    }
  }

  // Motivációs üzenetek a kvíz eredményekhez
  static String getMotivationalMessage(int score) {
    if (score >= 90) {
      return 'knowledge_u.motivational_message_90'.tr();
    } else if (score >= 80) {
      return 'knowledge_u.motivational_message_80'.tr();
    } else if (score >= 70) {
      return 'knowledge_u.motivational_message_70'.tr();
    } else if (score >= 60) {
      return 'knowledge_u.motivational_message_60'.tr();
    } else {
      return 'knowledge_u.motivational_message_fail'.tr();
    }
  }

  // Kategória ikon alapértelmezett értékek
  static String getDefaultCategoryIcon(String categoryName) {
    final name = categoryName.toLowerCase();
    if (name.contains('pénz') || name.contains('finance')) {
      return '💰';
    } else if (name.contains('befektetés') || name.contains('investment')) {
      return '📈';
    } else if (name.contains('bank') || name.contains('banking')) {
      return '🏦';
    } else if (name.contains('adó') || name.contains('tax')) {
      return '📊';
    } else if (name.contains('kriptó') || name.contains('crypto')) {
      return '₿';
    } else if (name.contains('biztosítás') || name.contains('insurance')) {
      return '🛡️';
    } else if (name.contains('ingatlan') || name.contains('real estate')) {
      return '🏠';
    } else {
      return '📚';
    }
  }

  // Haladás százalék színezése
  static Color getProgressColor(double progress) {
    if (progress >= 0.8) {
      return Colors.green;
    } else if (progress >= 0.5) {
      return Colors.orange;
    } else {
      return Colors.red;
    }
  }

  // Tanulási idő formázása
  static String formatStudyTime(int minutes) {
    if (minutes < 60) {
      return 'knowledge_u.study_time_minutes'.tr(namedArgs: {'minutes': minutes.toString()});
    } else {
      final hours = minutes ~/ 60;
      final remainingMinutes = minutes % 60;
      if (remainingMinutes == 0) {
        return 'knowledge_u.study_time_hours'.tr(namedArgs: {'hours': hours.toString()});
      } else {
        return 'knowledge_u.study_time_hours_minutes'.tr(namedArgs: {'hours': hours.toString(), 'minutes': remainingMinutes.toString()});
      }
    }
  }

  // Dátum formázása
  static String formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      return 'knowledge_u.date_today'.tr();
    } else if (difference.inDays == 1) {
      return 'knowledge_u.date_yesterday'.tr();
    } else if (difference.inDays < 7) {
      return 'knowledge_u.date_days_ago'.tr(namedArgs: {'days': difference.inDays.toString()});
    } else if (difference.inDays < 30) {
      final weeks = difference.inDays ~/ 7;
      return 'knowledge_u.date_weeks_ago'.tr(namedArgs: {'weeks': weeks.toString()});
    } else {
      final months = difference.inDays ~/ 30;
      return 'knowledge_u.date_months_ago'.tr(namedArgs: {'months': months.toString()});
    }
  }

  // Streak üzenet generálása
  static String getStreakMessage(int streak) {
    if (streak == 0) {
      return 'knowledge_u.streak_message_0'.tr();
    } else if (streak == 1) {
      return 'knowledge_u.streak_message_1'.tr();
    } else if (streak < 7) {
      return 'knowledge_u.streak_message_lt_7'.tr(namedArgs: {'streak': streak.toString()});
    } else if (streak < 30) {
      return 'knowledge_u.streak_message_lt_30'.tr(namedArgs: {'streak': streak.toString()});
    } else if (streak < 100) {
      return 'knowledge_u.streak_message_lt_100'.tr(namedArgs: {'streak': streak.toString()});
    } else {
      return 'knowledge_u.streak_message_gte_100'.tr(namedArgs: {'streak': streak.toString()});
    }
  }

  // Kvíz pontszám színezése
  static Color getQuizScoreColor(int score) {
    if (score >= 90) {
      return Colors.green;
    } else if (score >= 80) {
      return Colors.lightGreen;
    } else if (score >= 70) {
      return Colors.orange;
    } else if (score >= 60) {
      return Colors.deepOrange;
    } else {
      return Colors.red;
    }
  }

  // Kvíz pontszám emoji
  static String getQuizScoreEmoji(int score) {
    if (score >= 90) {
      return '🌟';
    } else if (score >= 80) {
      return '🎉';
    } else if (score >= 70) {
      return '👏';
    } else if (score >= 60) {
      return '💪';
    } else {
      return '📚';
    }
  }

  // Kategória színének validálása és konvertálása
  static Color getCategoryColor(String? colorHex) {
    if (colorHex == null || colorHex.isEmpty) {
      return const Color(0xFF00D4A3); // Alapértelmezett szín
    }
    
    try {
      String hex = colorHex;
      if (hex.startsWith('#')) {
        hex = hex.substring(1);
      }
      
      if (hex.length == 6) {
        hex = 'FF$hex'; // Alpha channel hozzáadása
      }
      
      return Color(int.parse(hex, radix: 16));
    } catch (e) {
      return const Color(0xFF00D4A3); // Alapértelmezett szín hiba esetén
    }
  }

  // Lecke befejezési üzenet
  static String getLessonCompletionMessage(bool hasQuiz, int? quizScore) {
    if (!hasQuiz) {
      return 'knowledge_u.lesson_completion_no_quiz'.tr();
    } else if (quizScore == null) {
      return 'knowledge_u.lesson_completion_quiz_pending'.tr();
    } else if (quizScore >= 70) {
      return 'knowledge_u.lesson_completion_quiz_success'.tr();
    } else {
      return 'knowledge_u.lesson_completion_quiz_redo'.tr();
    }
  }

  // Napi kihívás üzenet
  static String getDailyChallengeMessage(bool isCompleted, int streak) {
    if (isCompleted) {
      if (streak > 1) {
        return 'knowledge_u.daily_challenge_completed_streak'.tr(namedArgs: {'streak': streak.toString()});
      } else {
        return 'knowledge_u.daily_challenge_completed_no_streak'.tr();
      }
    } else {
      return 'knowledge_u.daily_challenge_uncompleted'.tr();
    }
  }

  // Tanulási statisztika formázása
  static String formatLearningStats({
    required int totalLessons,
    required int completedLessons,
    required int totalMinutes,
    required double averageScore,
  }) {
    final completionRate = totalLessons > 0 
        ? ((completedLessons / totalLessons) * 100).toInt()
        : 0;
    
    return '''
${'knowledge_u.learning_stats_completed_lessons'.tr(namedArgs: {'completed': completedLessons.toString(), 'total': totalLessons.toString(), 'completionRate': completionRate.toString()})}
${'knowledge_u.learning_stats_study_time'.tr(namedArgs: {'studyTime': formatStudyTime(totalMinutes)})}
${'knowledge_u.learning_stats_average_score'.tr(namedArgs: {'averageScore': averageScore.toInt().toString()})}
    '''.trim();
  }

  // Nehézségi szint alapján ajánlott leckék szűrése
  static List<T> filterLessonsByDifficulty<T>(
    List<T> lessons,
    String? difficulty,
    String Function(T) getDifficulty,
  ) {
    if (difficulty == null || difficulty.isEmpty || difficulty == 'all') {
      return lessons;
    }
    
    return lessons.where((lesson) => 
        getDifficulty(lesson).toLowerCase() == difficulty.toLowerCase()
    ).toList();
  }

  // Haladás animáció időtartama
  static Duration getProgressAnimationDuration(double progress) {
    // Minél nagyobb a haladás, annál lassabb az animáció
    final baseDuration = 800; // milliseconds
    final extraDuration = (progress * 500).toInt();
    return Duration(milliseconds: baseDuration + extraDuration);
  }

  // Siker hang lejátszásához szükséges paraméterek
  static Map<String, dynamic> getSuccessAudioParams(int score) {
    if (score >= 90) {
      return {'volume': 0.8, 'pitch': 1.2, 'duration': 2000};
    } else if (score >= 70) {
      return {'volume': 0.6, 'pitch': 1.0, 'duration': 1500};
    } else {
      return {'volume': 0.4, 'pitch': 0.8, 'duration': 1000};
    }
  }

  // Validáció a kvíz válaszokhoz
  static bool isValidQuizAnswer(dynamic answer) {
    if (answer == null) return false;
    if (answer is String) return answer.trim().isNotEmpty;
    if (answer is List) return answer.isNotEmpty;
    if (answer is int) return answer >= 0;
    return false;
  }

  // Kvíz kérdés típus meghatározása
  static String getQuestionTypeText(String type) {
    switch (type.toLowerCase()) {
      case 'multiple_choice':
        return 'knowledge_u.question_type_multiple_choice'.tr();
      case 'single_choice':
        return 'knowledge_u.question_type_single_choice'.tr();
      case 'true_false':
        return 'knowledge_u.question_type_true_false'.tr();
      case 'text_input':
        return 'knowledge_u.question_type_text_input'.tr();
      default:
        return 'knowledge_u.question_type_unknown'.tr();
    }
  }

  // Következő lecke ajánlása
  static String getNextLessonRecommendation(
    bool currentLessonCompleted,
    int? quizScore,
    String difficulty,
  ) {
    if (!currentLessonCompleted) {
      return 'knowledge_u.next_lesson_recommendation_not_completed'.tr();
    }
    
    if (quizScore != null && quizScore < 70) {
      return 'knowledge_u.next_lesson_recommendation_redo_quiz'.tr();
    }
    
    if (difficulty == 'beginner') {
      return 'knowledge_u.next_lesson_recommendation_ready_next'.tr();
    } else {
      return 'knowledge_u.next_lesson_recommendation_continue_learning'.tr();
    }
  }

  // Hibakezelés üzenetek
  static String getErrorMessage(String errorType) {
    switch (errorType.toLowerCase()) {
      case 'network':
        return 'knowledge_u.error_message_network'.tr();
      case 'server':
        return 'knowledge_u.error_message_server'.tr();
      case 'auth':
        return 'knowledge_u.error_message_auth'.tr();
      case 'quiz_not_found':
        return 'knowledge_u.error_message_quiz_not_found'.tr();
      case 'lesson_not_found':
        return 'knowledge_u.error_message_lesson_not_found'.tr();
      default:
        return 'knowledge_u.error_message_unknown'.tr();
    }
  }
}