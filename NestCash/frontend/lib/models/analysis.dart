// lib/models/analysis.dart

class BasicStats {
  final double totalIncome;
  final double totalExpense;
  final double netBalance;
  final double dailyAvgExpense;
  final double monthlyAvgExpense;
  final String mostActiveDay;
  final int mostActiveHour;
  final int transactionCount;

  BasicStats({
    required this.totalIncome,
    required this.totalExpense,
    required this.netBalance,
    required this.dailyAvgExpense,
    required this.monthlyAvgExpense,
    required this.mostActiveDay,
    required this.mostActiveHour,
    required this.transactionCount,
  });

  factory BasicStats.fromJson(Map<String, dynamic> json) {
    return BasicStats(
      totalIncome: (json['total_income'] ?? 0).toDouble(),
      totalExpense: (json['total_expense'] ?? 0).toDouble(),
      netBalance: (json['net_balance'] ?? 0).toDouble(),
      dailyAvgExpense: (json['daily_avg_expense'] ?? 0).toDouble(),
      monthlyAvgExpense: (json['monthly_avg_expense'] ?? 0).toDouble(),
      mostActiveDay: json['most_active_day'] ?? 'Hétfő',
      mostActiveHour: json['most_active_hour'] ?? 12,
      transactionCount: json['transaction_count'] ?? 0,
    );
  }
}

class CashflowTrend {
  final String period;
  final double income;
  final double expense;
  final double net;

  CashflowTrend({
    required this.period,
    required this.income,
    required this.expense,
    required this.net,
  });

  factory CashflowTrend.fromJson(Map<String, dynamic> json) {
    return CashflowTrend(
      period: json['period'] ?? '',
      income: (json['income'] ?? 0).toDouble(),
      expense: (json['expense'] ?? 0).toDouble(),
      net: (json['net'] ?? 0).toDouble(),
    );
  }
}

class CashflowAnalysis {
  final List<CashflowTrend> monthlyTrends;
  final List<CashflowTrend> weeklyTrends;
  final String overallTrend;

  CashflowAnalysis({
    required this.monthlyTrends,
    required this.weeklyTrends,
    required this.overallTrend,
  });

  factory CashflowAnalysis.fromJson(Map<String, dynamic> json) {
    return CashflowAnalysis(
      monthlyTrends: (json['monthly_trends'] as List<dynamic>?)
          ?.map((item) => CashflowTrend.fromJson(item))
          .toList() ?? [],
      weeklyTrends: (json['weekly_trends'] as List<dynamic>?)
          ?.map((item) => CashflowTrend.fromJson(item))
          .toList() ?? [],
      overallTrend: json['overall_trend'] ?? 'stabil',
    );
  }
}

class CategoryAnalysis {
  final List<Map<String, dynamic>> topExpenseCategories;
  final Map<String, Map<String, double>> categorySummary;
  final List<String> missingBasicCategories;

  CategoryAnalysis({
    required this.topExpenseCategories,
    required this.categorySummary,
    required this.missingBasicCategories,
  });

  factory CategoryAnalysis.fromJson(Map<String, dynamic> json) {
    return CategoryAnalysis(
      topExpenseCategories: List<Map<String, dynamic>>.from(
        json['top_expense_categories'] ?? []
      ),
      categorySummary: Map<String, Map<String, double>>.from(
        (json['category_summary'] ?? {}).map(
          (key, value) => MapEntry(
            key,
            Map<String, double>.from(value)
          )
        )
      ),
      missingBasicCategories: List<String>.from(
        json['missing_basic_categories'] ?? []
      ),
    );
  }
}

class RiskAnalysis {
  final double expenseIncomeRatio;
  final double savingsRate;
  final double debtIncomeRatio;
  final double emergencyFundMonths;
  final String riskLevel;

  RiskAnalysis({
    required this.expenseIncomeRatio,
    required this.savingsRate,
    required this.debtIncomeRatio,
    required this.emergencyFundMonths,
    required this.riskLevel,
  });

  factory RiskAnalysis.fromJson(Map<String, dynamic> json) {
    return RiskAnalysis(
      expenseIncomeRatio: (json['expense_income_ratio'] ?? 0).toDouble(),
      savingsRate: (json['savings_rate'] ?? 0).toDouble(),
      debtIncomeRatio: (json['debt_income_ratio'] ?? 0).toDouble(),
      emergencyFundMonths: (json['emergency_fund_months'] ?? 0).toDouble(),
      riskLevel: json['risk_level'] ?? 'alacsony',
    );
  }
}

class Recommendations {
  final List<String> savingsSuggestions;
  final List<String> costOptimizationTips;
  final List<String> emergencyFundAdvice;
  final List<String> debtManagementAdvice;

  Recommendations({
    required this.savingsSuggestions,
    required this.costOptimizationTips,
    required this.emergencyFundAdvice,
    required this.debtManagementAdvice,
  });

  factory Recommendations.fromJson(Map<String, dynamic> json) {
    return Recommendations(
      savingsSuggestions: List<String>.from(json['savings_suggestions'] ?? []),
      costOptimizationTips: List<String>.from(json['cost_optimization_tips'] ?? []),
      emergencyFundAdvice: List<String>.from(json['emergency_fund_advice'] ?? []),
      debtManagementAdvice: List<String>.from(json['debt_management_advice'] ?? []),
    );
  }
}

class FinancialAnalysis {
  final String userId;
  final DateTime analysisDate;
  final BasicStats basicStats;
  final CashflowAnalysis cashflowAnalysis;
  final CategoryAnalysis categoryAnalysis;
  final RiskAnalysis riskAnalysis;
  final Recommendations recommendations;

  FinancialAnalysis({
    required this.userId,
    required this.analysisDate,
    required this.basicStats,
    required this.cashflowAnalysis,
    required this.categoryAnalysis,
    required this.riskAnalysis,
    required this.recommendations,
  });

  factory FinancialAnalysis.fromJson(Map<String, dynamic> json) {
    return FinancialAnalysis(
      userId: json['user_id'] ?? '',
      analysisDate: DateTime.parse(json['analysis_date']),
      basicStats: BasicStats.fromJson(json['basic_stats']),
      cashflowAnalysis: CashflowAnalysis.fromJson(json['cashflow_analysis']),
      categoryAnalysis: CategoryAnalysis.fromJson(json['category_analysis']),
      riskAnalysis: RiskAnalysis.fromJson(json['risk_analysis']),
      recommendations: Recommendations.fromJson(json['recommendations']),
    );
  }
}

// ÚJ MODELLEK - add hozzá a meglévő modellek mellé

class ForecastData {
  final String period;
  final double predictedIncome;
  final double predictedExpense;
  final double predictedNet;
  final double confidenceLower;
  final double confidenceUpper;
  final double seasonalFactor;

  ForecastData({
    required this.period,
    required this.predictedIncome,
    required this.predictedExpense,
    required this.predictedNet,
    required this.confidenceLower,
    required this.confidenceUpper,
    required this.seasonalFactor,
  });

  factory ForecastData.fromJson(Map<String, dynamic> json) {
    return ForecastData(
      period: json['period'] ?? '',
      predictedIncome: (json['predicted_income'] ?? 0).toDouble(),
      predictedExpense: (json['predicted_expense'] ?? 0).toDouble(),
      predictedNet: (json['predicted_net'] ?? 0).toDouble(),
      confidenceLower: (json['confidence_lower'] ?? 0).toDouble(),
      confidenceUpper: (json['confidence_upper'] ?? 0).toDouble(),
      seasonalFactor: (json['seasonal_factor'] ?? 1.0).toDouble(),
    );
  }
}

class ForecastResponse {
  final String forecastType;
  final int periodsAhead;
  final List<ForecastData> forecasts;
  final double modelAccuracy;
  final bool seasonalPatternDetected;
  final String trend;

  ForecastResponse({
    required this.forecastType,
    required this.periodsAhead,
    required this.forecasts,
    required this.modelAccuracy,
    required this.seasonalPatternDetected,
    required this.trend,
  });

  factory ForecastResponse.fromJson(Map<String, dynamic> json) {
    return ForecastResponse(
      forecastType: json['forecast_type'] ?? 'monthly',
      periodsAhead: json['periods_ahead'] ?? 0,
      forecasts: (json['forecasts'] as List<dynamic>?)
          ?.map((item) => ForecastData.fromJson(item))
          .toList() ?? [],
      modelAccuracy: (json['model_accuracy'] ?? 0).toDouble(),
      seasonalPatternDetected: json['seasonal_pattern_detected'] ?? false,
      trend: json['trend'] ?? 'stabil',
    );
  }
}

class AnomalyData {
  final String transactionId;
  final String date;
  final double amount;
  final String category;
  final double anomalyScore;
  final String anomalyType;
  final String severity;

  AnomalyData({
    required this.transactionId,
    required this.date,
    required this.amount,
    required this.category,
    required this.anomalyScore,
    required this.anomalyType,
    required this.severity,
  });

  factory AnomalyData.fromJson(Map<String, dynamic> json) {
    return AnomalyData(
      transactionId: json['transaction_id'] ?? '',
      date: json['date'] ?? '',
      amount: (json['amount'] ?? 0).toDouble(),
      category: json['category'] ?? '',
      anomalyScore: (json['anomaly_score'] ?? 0).toDouble(),
      anomalyType: json['anomaly_type'] ?? '',
      severity: json['severity'] ?? 'low',
    );
  }
}

class AnomalyResponse {
  final int totalAnomalies;
  final Map<String, int> anomaliesBySeverity;
  final List<AnomalyData> recentAnomalies;
  final Map<String, int> anomalyTrends;
  final List<String> recommendations;

  AnomalyResponse({
    required this.totalAnomalies,
    required this.anomaliesBySeverity,
    required this.recentAnomalies,
    required this.anomalyTrends,
    required this.recommendations,
  });

  factory AnomalyResponse.fromJson(Map<String, dynamic> json) {
    return AnomalyResponse(
      totalAnomalies: json['total_anomalies'] ?? 0,
      anomaliesBySeverity: Map<String, int>.from(json['anomalies_by_severity'] ?? {}),
      recentAnomalies: (json['recent_anomalies'] as List<dynamic>?)
          ?.map((item) => AnomalyData.fromJson(item))
          .toList() ?? [],
      anomalyTrends: Map<String, int>.from(json['anomaly_trends'] ?? {}),
      recommendations: List<String>.from(json['recommendations'] ?? []),
    );
  }
}

class BudgetRecommendation {
  final String category;
  final double recommendedLimit;
  final double currentSpending;
  final double confidence;
  final String reasoning;
  final String priority;

  BudgetRecommendation({
    required this.category,
    required this.recommendedLimit,
    required this.currentSpending,
    required this.confidence,
    required this.reasoning,
    required this.priority,
  });

  factory BudgetRecommendation.fromJson(Map<String, dynamic> json) {
    return BudgetRecommendation(
      category: json['category'] ?? '',
      recommendedLimit: (json['recommended_limit'] ?? 0).toDouble(),
      currentSpending: (json['current_spending'] ?? 0).toDouble(),
      confidence: (json['confidence'] ?? 0).toDouble(),
      reasoning: json['reasoning'] ?? '',
      priority: json['priority'] ?? 'low',
    );
  }
}

class MLBudgetResponse {
  final double totalRecommendedBudget;
  final List<BudgetRecommendation> categoryRecommendations;
  final double spendingPatternScore;
  final String riskLevel;
  final List<String> personalizedTips;

  MLBudgetResponse({
    required this.totalRecommendedBudget,
    required this.categoryRecommendations,
    required this.spendingPatternScore,
    required this.riskLevel,
    required this.personalizedTips,
  });

  factory MLBudgetResponse.fromJson(Map<String, dynamic> json) {
    return MLBudgetResponse(
      totalRecommendedBudget: (json['total_recommended_budget'] ?? 0).toDouble(),
      categoryRecommendations: (json['category_recommendations'] as List<dynamic>?)
          ?.map((item) => BudgetRecommendation.fromJson(item))
          .toList() ?? [],
      spendingPatternScore: (json['spending_pattern_score'] ?? 0).toDouble(),
      riskLevel: json['risk_level'] ?? 'medium',
      personalizedTips: List<String>.from(json['personalized_tips'] ?? []),
    );
  }
}

class WhatIfScenario {
  final String scenarioName;
  final Map<String, double> changes;
  final double monthlyImpact;
  final double annualSavings;
  final String feasibility;

  WhatIfScenario({
    required this.scenarioName,
    required this.changes,
    required this.monthlyImpact,
    required this.annualSavings,
    required this.feasibility,
  });

  factory WhatIfScenario.fromJson(Map<String, dynamic> json) {
    return WhatIfScenario(
      scenarioName: json['scenario_name'] ?? '',
      changes: Map<String, double>.from(
        (json['changes'] ?? {}).map((key, value) => MapEntry(key, value.toDouble()))
      ),
      monthlyImpact: (json['monthly_impact'] ?? 0).toDouble(),
      annualSavings: (json['annual_savings'] ?? 0).toDouble(),
      feasibility: json['feasibility'] ?? 'medium',
    );
  }
}

class WhatIfResponse {
  final List<WhatIfScenario> scenarios;
  final String recommendedScenario;
  final double totalPotentialSavings;

  WhatIfResponse({
    required this.scenarios,
    required this.recommendedScenario,
    required this.totalPotentialSavings,
  });

  factory WhatIfResponse.fromJson(Map<String, dynamic> json) {
    return WhatIfResponse(
      scenarios: (json['scenarios'] as List<dynamic>?)
          ?.map((item) => WhatIfScenario.fromJson(item))
          .toList() ?? [],
      recommendedScenario: json['recommended_scenario'] ?? '',
      totalPotentialSavings: (json['total_potential_savings'] ?? 0).toDouble(),
    );
  }
}