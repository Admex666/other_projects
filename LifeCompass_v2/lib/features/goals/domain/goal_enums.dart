import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

enum GoalType {
  financial,
  career,
  mental,
  physical,
  spiritual,
  social,
  time;

  Color get color {
    switch (this) {
      case GoalType.financial:
        return AppColors.emerald;
      case GoalType.career:
        return AppColors.indigo;
      case GoalType.mental:
      case GoalType.spiritual:
        return AppColors.amber;
      case GoalType.physical:
        return AppColors.crimson;
      case GoalType.social:
        return AppColors.rose;
      case GoalType.time:
        return AppColors.indigo; // Fallback
    }
  }
}

enum GoalHorizon {
  vision,    // 5y+
  strategy,  // 1-3y
  objective, // 1y
  quarter,   // 3 months
  month;     // 1 month
}

enum GoalStatus {
  planned,
  active,
  completed,
  archived;
}
