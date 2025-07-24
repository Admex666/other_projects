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