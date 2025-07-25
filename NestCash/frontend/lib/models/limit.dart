// lib/models/limit.dart

enum LimitType {
  spending('spending', 'Általános kiadási limit'),
  category('category', 'Kategória specifikus limit'),
  account('account', 'Számla specifikus limit');

  const LimitType(this.value, this.displayName);
  final String value;
  final String displayName;

  static LimitType fromString(String value) {
    return LimitType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => LimitType.spending,
    );
  }
}

enum LimitPeriod {
  daily('daily', 'Napi'),
  weekly('weekly', 'Heti'),
  monthly('monthly', 'Havi'),
  yearly('yearly', 'Éves');

  const LimitPeriod(this.value, this.displayName);
  final String value;
  final String displayName;

  static LimitPeriod fromString(String value) {
    return LimitPeriod.values.firstWhere(
      (period) => period.value == value,
      orElse: () => LimitPeriod.monthly,
    );
  }
}

class Limit {
  final String id;
  final String userId;
  final String name;
  final LimitType type;
  final double amount;
  final LimitPeriod period;
  final String currency;
  final String? category;
  final String? mainAccount;
  final String? subAccountName;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;
  final double? notificationThreshold;
  final bool notifyOnExceed;
  
  // Számított mezők
  final double? currentSpending;
  final double? remainingAmount;
  final double? usagePercentage;
  final DateTime? periodStart;
  final DateTime? periodEnd;

  const Limit({
    required this.id,
    required this.userId,
    required this.name,
    required this.type,
    required this.amount,
    required this.period,
    this.currency = 'HUF',
    this.category,
    this.mainAccount,
    this.subAccountName,
    this.isActive = true,
    required this.createdAt,
    required this.updatedAt,
    this.notificationThreshold,
    this.notifyOnExceed = true,
    this.currentSpending,
    this.remainingAmount,
    this.usagePercentage,
    this.periodStart,
    this.periodEnd,
  });

  factory Limit.fromJson(Map<String, dynamic> json) {
    return Limit(
      id: json['id'] ?? '',
      userId: json['user_id'] ?? '',
      name: json['name'] ?? '',
      type: LimitType.fromString(json['type'] ?? 'spending'),
      amount: (json['amount'] ?? 0).toDouble(),
      period: LimitPeriod.fromString(json['period'] ?? 'monthly'),
      currency: json['currency'] ?? 'HUF',
      category: json['category'],
      mainAccount: json['main_account'],
      subAccountName: json['sub_account_name'],
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      notificationThreshold: json['notification_threshold']?.toDouble(),
      notifyOnExceed: json['notify_on_exceed'] ?? true,
      currentSpending: json['current_spending']?.toDouble(),
      remainingAmount: json['remaining_amount']?.toDouble(),
      usagePercentage: json['usage_percentage']?.toDouble(),
      periodStart: json['period_start'] != null 
          ? DateTime.parse(json['period_start']) 
          : null,
      periodEnd: json['period_end'] != null 
          ? DateTime.parse(json['period_end']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'type': type.value,
      'amount': amount,
      'period': period.value,
      'currency': currency,
      if (category != null) 'category': category,
      if (mainAccount != null) 'main_account': mainAccount,
      if (subAccountName != null) 'sub_account_name': subAccountName,
      if (notificationThreshold != null) 'notification_threshold': notificationThreshold,
      'notify_on_exceed': notifyOnExceed,
    };
  }

  Limit copyWith({
    String? id,
    String? userId,
    String? name,
    LimitType? type,
    double? amount,
    LimitPeriod? period,
    String? currency,
    String? category,
    String? mainAccount,
    String? subAccountName,
    bool? isActive,
    DateTime? createdAt,
    DateTime? updatedAt,
    double? notificationThreshold,
    bool? notifyOnExceed,
    double? currentSpending,
    double? remainingAmount,
    double? usagePercentage,
    DateTime? periodStart,
    DateTime? periodEnd,
  }) {
    return Limit(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      name: name ?? this.name,
      type: type ?? this.type,
      amount: amount ?? this.amount,
      period: period ?? this.period,
      currency: currency ?? this.currency,
      category: category ?? this.category,
      mainAccount: mainAccount ?? this.mainAccount,
      subAccountName: subAccountName ?? this.subAccountName,
      isActive: isActive ?? this.isActive,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      notificationThreshold: notificationThreshold ?? this.notificationThreshold,
      notifyOnExceed: notifyOnExceed ?? this.notifyOnExceed,
      currentSpending: currentSpending ?? this.currentSpending,
      remainingAmount: remainingAmount ?? this.remainingAmount,
      usagePercentage: usagePercentage ?? this.usagePercentage,
      periodStart: periodStart ?? this.periodStart,
      periodEnd: periodEnd ?? this.periodEnd,
    );
  }

  bool get isExceeded => (currentSpending ?? 0) > amount;
  
  bool get isNearLimit {
    if (notificationThreshold == null || currentSpending == null) return false;
    return (usagePercentage ?? 0) >= notificationThreshold!;
  }

  String get statusText {
    if (isExceeded) return 'Túllépve';
    if (isNearLimit) return 'Közel a limithez';
    return 'Rendben';
  }

  String get typeDisplayName {
    switch (type) {
      case LimitType.spending:
        return 'Általános';
      case LimitType.category:
        return 'Kategória: ${category ?? "Nincs megadva"}';
      case LimitType.account:
        return 'Számla: ${mainAccount ?? ""}${subAccountName != null ? " - $subAccountName" : ""}';
    }
  }
}

class LimitCheckResult {
  final bool isAllowed;
  final List<String> exceededLimits;
  final List<String> warnings;
  final String? message;

  const LimitCheckResult({
    required this.isAllowed,
    this.exceededLimits = const [],
    this.warnings = const [],
    this.message,
  });

  factory LimitCheckResult.fromJson(Map<String, dynamic> json) {
    return LimitCheckResult(
      isAllowed: json['is_allowed'] ?? true,
      exceededLimits: List<String>.from(json['exceeded_limits'] ?? []),
      warnings: List<String>.from(json['warnings'] ?? []),
      message: json['message'],
    );
  }
}

class LimitStatus {
  final int totalLimits;
  final int activeLimits;
  final int exceededLimits;
  final int warningLimits;

  const LimitStatus({
    required this.totalLimits,
    required this.activeLimits,
    required this.exceededLimits,
    required this.warningLimits,
  });

  factory LimitStatus.fromJson(Map<String, dynamic> json) {
    return LimitStatus(
      totalLimits: json['total_limits'] ?? 0,
      activeLimits: json['active_limits'] ?? 0,
      exceededLimits: json['exceeded_limits'] ?? 0,
      warningLimits: json['warning_limits'] ?? 0,
    );
  }
}