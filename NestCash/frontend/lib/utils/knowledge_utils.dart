// lib/utils/knowledge_utils.dart
import 'package:flutter/material.dart';

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
        return 'Kezdő';
      case 'professional':
        return 'Profi';
      default:
        return 'Ismeretlen';
    }
  }

  // Motivációs üzenetek a kvíz eredményekhez
  static String getMotivationalMessage(int score) {
    if (score >= 90) {
      return 'Fantasztikus! Tökéletesen ismered a témát! 🌟';
    } else if (score >= 80) {
      return 'Kiváló munka! Nagyon jól teljesítettél! 🎉';
    } else if (score >= 70) {
      return 'Jó munka! Sikeresen teljesítetted a kvízt! 👏';
    } else if (score >= 60) {
      return 'Nem rossz! Még egy kis gyakorlással tökéletes leszel! 💪';
    } else {
      return 'Ne add fel! Olvasd át újra a leckét és próbáld újra! 📚';
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
      return '$minutes perc';
    } else {
      final hours = minutes ~/ 60;
      final remainingMinutes = minutes % 60;
      if (remainingMinutes == 0) {
        return '$hours óra';
      } else {
        return '$hours óra $remainingMinutes perc';
      }
    }
  }

  // Dátum formázása
  static String formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      return 'Ma';
    } else if (difference.inDays == 1) {
      return 'Tegnap';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} napja';
    } else if (difference.inDays < 30) {
      final weeks = difference.inDays ~/ 7;
      return '$weeks hete';
    } else {
      final months = difference.inDays ~/ 30;
      return '$months hónapja';
    }
  }

  // Streak üzenet generálása
  static String getStreakMessage(int streak) {
    if (streak == 0) {
      return 'Kezdj el egy új sorozatot ma! 🚀';
    } else if (streak == 1) {
      return 'Első nap teljesítve! Folytasd holnap! 🔥';
    } else if (streak < 7) {
      return '$streak napos sorozat! Folytatás! 💪';
    } else if (streak < 30) {
      return 'Fantasztikus! $streak napos sorozat! 🌟';
    } else if (streak < 100) {
      return 'Hihetetlen! $streak napos sorozat! 🏆';
    } else {
      return 'Legenda! $streak napos sorozat! 👑';
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
      return 'Gratulálok! Sikeresen befejezted a leckét! 🎓';
    } else if (quizScore == null) {
      return 'Lecke befejezve! Most jön a kvíz! 📝';
    } else if (quizScore >= 70) {
      return 'Fantasztikus! Lecke és kvíz is sikeresen teljesítve! 🏆';
    } else {
      return 'Lecke befejezve, de a kvízt érdemes újra megcsinálni! 💪';
    }
  }

  // Napi kihívás üzenet
  static String getDailyChallengeMessage(bool isCompleted, int streak) {
    if (isCompleted) {
      if (streak > 1) {
        return 'Szuper! $streak napos sorozatod folytatódik! 🔥';
      } else {
        return 'Napi kihívás teljesítve! Szuper munka! 🎉';
      }
    } else {
      return 'Tanulj 5 percet és teljesítsd a mai kihívást! ⭐';
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
📚 Teljesített leckék: $completedLessons/$totalLessons ($completionRate%)
⏱️ Tanulási idő: ${formatStudyTime(totalMinutes)}
⭐ Átlagos kvíz eredmény: ${averageScore.toInt()}%
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
        return 'Többválasztós';
      case 'single_choice':
        return 'Egyszeres választás';
      case 'true_false':
        return 'Igaz/Hamis';
      case 'text_input':
        return 'Szöveges válasz';
      default:
        return 'Ismeretlen típus';
    }
  }

  // Következő lecke ajánlása
  static String getNextLessonRecommendation(
    bool currentLessonCompleted,
    int? quizScore,
    String difficulty,
  ) {
    if (!currentLessonCompleted) {
      return 'Fejezd be ezt a leckét először! 📖';
    }
    
    if (quizScore != null && quizScore < 70) {
      return 'Ismételd át ezt a témát, mielőtt továbblépsz! 🔄';
    }
    
    if (difficulty == 'beginner') {
      return 'Készen állsz a következő témára! 🚀';
    } else {
      return 'Kiváló munka! Folytasd a tanulást! 💪';
    }
  }

  // Hibakezelés üzenetek
  static String getErrorMessage(String errorType) {
    switch (errorType.toLowerCase()) {
      case 'network':
        return 'Hálózati hiba. Ellenőrizd az internetkapcsolatot! 🌐';
      case 'server':
        return 'Szerver hiba. Próbáld újra később! ⚠️';
      case 'auth':
        return 'Hitelesítési hiba. Jelentkezz be újra! 🔐';
      case 'quiz_not_found':
        return 'A kvíz nem található! 🔍';
      case 'lesson_not_found':
        return 'A lecke nem található! 📚';
      default:
        return 'Ismeretlen hiba történt! ❌';
    }
  }
}