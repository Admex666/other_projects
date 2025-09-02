// lib/utils/anchoring_utils.dart
import 'dart:math';
import '../models/subscription.dart';
import 'package:easy_localization/easy_localization.dart';

class AnchoringUtils {
  static final List<AnchoringComparison> _plusComparisons = [
    AnchoringComparison(
      title: 'anchoring_u.plus_c1_title'.tr(),
      description: 'anchoring_u.plus_c1_desc'.tr(),
      icon: '🚬',
    ),
    AnchoringComparison(
      title: 'anchoring_u.plus_c2_title'.tr(),
      description: 'anchoring_u.plus_c2_desc'.tr(),
      icon: '☕',
    ),
    AnchoringComparison(
      title: 'anchoring_u.plus_c3_title'.tr(),
      description: 'anchoring_u.plus_c3_desc'.tr(),
      icon: '🍔',
    ),
    AnchoringComparison(
      title: 'anchoring_u.plus_c4_title'.tr(),
      description: 'anchoring_u.plus_c4_desc'.tr(),
      icon: '🥤',
    ),
    AnchoringComparison(
      title: 'anchoring_u.plus_c5_title'.tr(),
      description: 'anchoring_u.plus_c5_desc'.tr(),
      icon: '🥪',
    ),
  ];

  static final List<AnchoringComparison> _proComparisons = [
    AnchoringComparison(
      title: 'anchoring_u.pro_c1_title'.tr(),
      description: 'anchoring_u.pro_c1_desc'.tr(),
      icon: '🚬',
    ),
    AnchoringComparison(
      title: 'anchoring_u.pro_c2_title'.tr(),
      description: 'anchoring_u.pro_c2_desc'.tr(),
      icon: '🍕',
    ),
    AnchoringComparison(
      title: 'anchoring_u.pro_c3_title'.tr(),
      description: 'anchoring_u.pro_c3_desc'.tr(),
      icon: '☕',
    ),
    AnchoringComparison(
      title: 'anchoring_u.pro_c4_title'.tr(),
      description: 'anchoring_u.pro_c4_desc'.tr(),
      icon: '🍿',
    ),
    AnchoringComparison(
      title: 'anchoring_u.pro_c5_title'.tr(),
      description: 'anchoring_u.pro_c5_desc'.tr(),
      icon: '🚕',
    ),
    AnchoringComparison(
      title: 'anchoring_u.pro_c6_title'.tr(),
      description: 'anchoring_u.pro_c6_desc'.tr(),
      icon: '🍸',
    ),
  ];

  /// Véletlenszerű anchoring összehasonlítás lekérése a tier alapján
  static AnchoringComparison getRandomComparison(SubscriptionTier tier) {
    final comparisons = tier == SubscriptionTier.plus ? _plusComparisons : _proComparisons;
    final random = Random();
    return comparisons[random.nextInt(comparisons.length)];
  }

  /// Napi költség számítása
  static String getDailyCost(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.plus:
        return '0,17 EUR';
      case SubscriptionTier.pro:
        return '0,42 EUR';
      case SubscriptionTier.free:
        return '0 EUR';
    }
  }

  /// Formázott napi költség leírással
  static String getDailyCostDescription(SubscriptionTier tier) {
    final dailyCost = getDailyCost(tier);
    return 'anchoring_u.daily_cost_description'.tr(namedArgs: {'dailyCost': dailyCost});
  }
}

class AnchoringComparison {
  final String title;
  final String description;
  final String icon;

  const AnchoringComparison({
    required this.title,
    required this.description,
    required this.icon,
  });
}